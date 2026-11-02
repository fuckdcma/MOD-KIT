#!/usr/bin/env python3
"""Mod Studio AI M03: build-only REA evidence, read-only Unity asset scan, local agent, blind evaluation.
Python stdlib for REA/agent/evaluation. Optional UnityPy for build asset scanning.
No code injection, hooking, game modifications, or network calls except loopback to local model.
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import re
import sys
import struct
import urllib.parse
import urllib.request
from pathlib import Path

SCHEMA = 'modstudio.m03.v0.2'
SOURCE_TYPES = {'hardcoded_managed','runtime_generated','external_json','scriptable_object','serialized_prefab','serialized_scene','unknown'}
TOOLS = {'list_methods','inspect_method','search_literals','list_asset_candidates','finish'}


def dump(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def load_jsonl(path):
    items=[]
    with open(path,encoding='utf-8-sig') as f:
        for idx,line in enumerate(f,1):
            if line.strip():
                try: items.append(json.loads(line))
                except json.JSONDecodeError as ex: raise ValueError(f'{path} line {idx}: {ex}') from ex
    return items


def write_jsonl(path, items):
    path=Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w',encoding='utf-8') as f:
        for x in items: f.write(json.dumps(x,ensure_ascii=False)+'\n')


def normalize_text(x):
    return re.sub(r'\s+',' ',str(x or '').strip()).casefold()


def verify_rea_evidence(items):
    sha_set=set()
    for r in items:
        if r.get('evidence_kind')!='rea_managed_static':
            raise ValueError('Unexpected REA evidence_kind: '+str(r.get('evidence_kind')))
        if not r.get('method') or not r.get('method_token'):
            raise ValueError('REA evidence requires method and method_token')
        if len(r.get('assembly_sha256','')) != 64: raise ValueError('Missing SHA-256')
        sha_set.add(r['assembly_sha256'])
    if len(sha_set) > 1: raise ValueError('Mixed assemblies in evidence')
    return next(iter(sha_set),None)


def calls_for(r):
    return [str(e.get('target','')) for e in r.get('call_targets',[])]


def literals_for(r):
    return [str(e.get('literal','')) for e in r.get('strings_loaded_by_method',[])]


def method_summary(items):
    return [{'method':r['method'],'method_token':r.get('method_token'),
             'calls':[c for c in calls_for(r) if any(v in c for v in ('TMPro','Resources','Json','TryGet','Format','Material'))],
             'literal_count':len(literals_for(r))} for r in items]



def prepare_rea_members(raw_members, raw_artifact=None):
    """Transform native REA inspect-managed-members output to build-only agent input.
    Reject incomplete metadata/IL coverage rather than presenting partial as exhaustive.
    """
    obj = raw_members.get('normalized_result',raw_members)
    artifact = obj.get('artifact',{})
    sha=artifact.get('sha256','')
    if len(sha)!=64: raise ValueError('REA members JSON missing artifact sha256')
    if obj.get('metadata',{}).get('status')!='complete' or obj.get('coverage',{}).get('state')!='complete':
        raise ValueError('REA members coverage not complete; rerun focused inspection')
    if raw_artifact:
        a=raw_artifact.get('normalized_result',raw_artifact)
        a_sha=a.get('artifact',{}).get('sha256','')
        if a_sha!=sha: raise ValueError('Assembly SHA mismatch between REA files')
    refs={v.get('token'):v for v in obj.get('user_strings',{}).get('literals',[])}
    bycaller={}
    for c in obj.get('call_edges',[]):
        bycaller.setdefault(c.get('caller_token'),[]).append(c)
    output=[]
    for method in obj.get('methods',[]):
        body=method.get('body') or {}
        if body.get('status')!='present': continue
        token=method['token']; lit=[]
        for anchor in body.get('anchors',[]):
            if anchor.get('opcode')!='ldstr': continue
            target=refs.get(anchor.get('operand'))
            if target:
                lit.append({'il_offset':anchor.get('il_offset'),'literal':target.get('value',''),
                            'literal_token':target.get('token')})
        calls=[]
        for c in bycaller.get(token,[]):
            calls.append({'target':str(c.get('target_declaring_type',''))+'.'+str(c.get('target_name','')),
                          'target_token':c.get('target_token')})
        output.append({'assembly_sha256':sha,'method':method['declaring_type']+'.'+method['name'],
                       'method_token':token,'method_il_sha256':body.get('il_sha256'),
                       'evidence_kind':'rea_managed_static','strings_loaded_by_method':lit,
                       'call_targets':calls,
                       'touches_tmp_setter':any(c.get('target')=='TMPro.TMP_Text.set_text' for c in calls),
                       'verification':'static_evidence_not_runtime_proof'})
    return output

def baseline(items):
    """Deliberately conservative: only verified static evidence or explicit hypotheses."""
    verify_rea_evidence(items)
    out=[]
    for r in items:
        method=r['method']; literals=literals_for(r); calls=calls_for(r)
        if 'HardcodedTextExample.Awake' in method and 'TMPro.TMP_Text.set_text' in calls:
            for lit in literals:
                if lit and not lit.startswith('['):
                    out.append({'text':lit,'source_type':'hardcoded_managed','method':method,'source_ref':method,
                                'evidence_type':'il_literal','evidence_value':lit,'confidence':'observed'})
        if 'RuntimeTextExample.Refresh' in method and 'TMPro.TMP_Text.set_text' in calls:
            for lit in literals:
                if '{0}' in lit:
                    out.append({'text':lit,'source_type':'runtime_generated','method':method,'source_ref':method,
                                'evidence_type':'il_literal','evidence_value':lit,'confidence':'observed',
                                'note':'Template only; concrete runtime value is not observed.'})
        if 'ExternalTextExample.Start' in method and any('UnityEngine.Resources.Load' in c for c in calls):
            out.append({'text':'','source_type':'external_json','method':method,'source_ref':'Assets/Resources/dialogue.json',
                        'evidence_type':'method_call','evidence_value':'UnityEngine.Resources.Load',
                        'confidence':'hypothesis','note':'Reader path is inferred from IL/diagnostic literal; JSON message unknown.'})
        if 'TableTextExample.Start' in method and any('LabStringTable.TryGet' in c for c in calls):
            out.append({'text':'','source_type':'scriptable_object','method':method,'source_ref':'LabStringTable.TryGet',
                        'evidence_type':'method_call','evidence_value':'ModStudioLab.LabStringTable.TryGet',
                        'confidence':'hypothesis','note':'Lookup exists; asset data and returned value not observed.'})
    return out


def is_present_in_evidence(obs, bymethod, asset_items):
    method=obs.get('method',''); text=obs.get('text',''); etype=obs.get('evidence_type','')
    if etype == 'il_literal':
        e=bymethod.get(method)
        return ('observed' if e and text and text in literals_for(e) and text==obs.get('evidence_value') else 'rejected',
                'Exact ldstr literal in specified method' if e and text and text in literals_for(e) and text==obs.get('evidence_value') else 'No exact literal in specified method')
    if etype == 'method_call':
        e=bymethod.get(method)
        target=obs.get('evidence_value')
        if e and target in calls_for(e):
            return ('hypothesis','Method call observed; source values are not proven')
        return ('rejected','Method call not present in specified method')
    if etype == 'asset_text':
        for a in asset_items:
            if (a.get('evidence_type')=='asset_text' and text and text==a.get('text') and
                obs.get('source_ref')==a.get('source_ref') and
                obs.get('source_type')==a.get('source_type') and
                obs.get('source_type')!='unknown'):
                return ('observed','Text read from build asset; asset origin may be uncertain')
        return ('rejected','No matching read-only build asset evidence')
    return ('rejected','Unknown or missing evidence_type')


def validate_observations(obs, items, assets=None):
    bymethod={r['method']:r for r in items}
    assets=assets or []
    cleaned=[]
    for i,item in enumerate(obs):
        if not isinstance(item,dict): continue
        rec={k:str(item.get(k,''))[:1500] for k in ('text','source_type','method','source_ref','evidence_type','evidence_value','confidence','note')}
        if rec['source_type'] not in SOURCE_TYPES: rec['source_type']='unknown'
        status,reason=is_present_in_evidence(rec,bymethod,assets)
        rec['validation_status']=status
        rec['validation_reason']=reason
        rec['observation_id']=f'O{i+1:04}'
        cleaned.append(rec)
    return cleaned


def local_chat(server, model, messages, timeout=180):
    """Loopback only. Nothing is sent to a hosted API."""
    u=urllib.parse.urlparse(server)
    if u.scheme!='http' or u.hostname not in ('127.0.0.1','localhost','::1'):
        raise ValueError('Only localhost HTTP model endpoints are allowed; no cloud API')
    url=server.rstrip('/')
    if not url.endswith('/v1'): url += '/v1'
    url += '/chat/completions'
    payload={'model':model,'messages':messages,'temperature':0.0,'max_tokens':1500,'stream':False,
             'response_format':{'type':'json_object'}}
    req=urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'),
       headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=timeout) as resp: result=json.load(resp)
    content=result['choices'][0]['message']['content']
    if isinstance(content,list): content=''.join(p.get('text','') for p in content if isinstance(p,dict))
    return json.loads(content)

SYSTEM = '''Bạn là Mod Studio AI Research Agent, chỉ phân tích bằng chứng từ bản build Unity và REA.
Đầu ra MỖI LƯỢT là một JSON OBJECT duy nhất, không kèm markdown. Các hành động hợp lệ:
{"action":"list_methods","query":""}
{"action":"search_literals","query":"Quest"}
{"action":"inspect_method","method":"Namespace.Class.Method"}
{"action":"list_asset_candidates","query":""}
{"action":"finish","observations":[{"text":"literal or empty","source_type":"hardcoded_managed|runtime_generated|external_json|scriptable_object|serialized_prefab|serialized_scene|unknown","method":"method name or empty","source_ref":"source identifier","evidence_type":"il_literal|method_call|asset_text","evidence_value":"exact text or exact called method","confidence":"observed|hypothesis","note":"limitations"}]}
Yêu cầu: truy vết text, nguồn dữ liệu, đường truyền đến UI; KHÔNG được suy đoán giá trị từ JSON/prefab/ScriptableObject nếu bản build chưa chứng minh. Method_call chỉ chứng minh lời gọi, không chứng minh nội dung. Không có câu trả lời thì trả giá trị rỗng và nêu hạn chế. Không được dùng ground truth hay dữ liệu Unity Editor. Raw string candidates are unverified and MUST NOT be reported as observed asset provenance. Only decoded asset_text and exact IL literals can prove text. Chỉ tìm hiểu game offline, không tìm cách vượt anti-cheat.'''


def tool_result(action, payload, items, assets):
    if action=='list_methods':
        query=normalize_text(payload.get('query',''))
        return [m for m in method_summary(items) if not query or query in normalize_text(json.dumps(m))][:80]
    if action=='inspect_method':
        name=str(payload.get('method',''))
        match=next((r for r in items if r['method']==name),None)
        return match if match else {'error':'method_not_found'}
    if action=='search_literals':
        query=normalize_text(payload.get('query',''))
        result=[]
        for r in items:
            for l in r.get('strings_loaded_by_method',[]):
                if not query or query in normalize_text(l.get('literal','')):
                    result.append({'method':r['method'],**l})
        return result[:100]
    if action=='list_asset_candidates':
        query=normalize_text(payload.get('query',''))
        return [a for a in assets if not query or query in normalize_text(json.dumps(a))][:80]
    return {'error':'unknown_action'}


def run_agent(items, assets, server, model, max_steps=10):
    verify_rea_evidence(items)
    messages=[{'role':'system','content':SYSTEM},
              {'role':'user','content':json.dumps({'task':'Find all evidence of text origin, text generation and text rendering in this Unity game. Do not guess unseen asset text.',
                         'methods':method_summary(items),'asset_scan_count':len(assets)},ensure_ascii=False)}]
    trace=[]; observations=[]; finished=False
    for step in range(max_steps):
        try: response=local_chat(server,model,messages)
        except Exception as ex:
            trace.append({'step':step+1,'error':str(ex)}); break
        action=response.get('action')
        if action not in TOOLS:
            trace.append({'step':step+1,'error':'invalid_action','response':response}); break
        if action=='finish':
            observations=response.get('observations',[])
            if not isinstance(observations,list): observations=[]
            trace.append({'step':step+1,'action':'finish','candidate_count':len(observations)})
            finished=True; break
        result=tool_result(action,response,items,assets)
        trace.append({'step':step+1,'action':action,'request':response,'result_count':len(result) if isinstance(result,list) else 1})
        messages.append({'role':'assistant','content':json.dumps(response,ensure_ascii=False)})
        messages.append({'role':'user','content':'RESULT from '+action+': '+json.dumps(result,ensure_ascii=False)[:20000]+
                         '\nContinue investigation or finish with evidence-grounded observations.'})
    return observations,trace,finished


def scan_raw_unity_strings(blob, max_candidates=25):
    """Conservative, read-only identification of UTF-8 length-prefixed strings in a serialized
    MonoBehaviour's raw bytes. A valid byte pattern is NOT proof of field ownership/type.
    Offsets are relative to the object's raw payload, NOT source-file offsets.
    """
    if not isinstance(blob, (bytes, bytearray)): return []
    found=[]; seen=set()
    for off in range(0, max(0,len(blob)-8), 4):
        length=struct.unpack_from('<I',blob,off)[0]
        if not (4 <= length <= 300) or off+4+length > len(blob): continue
        payload=blob[off+4:off+4+length]
        try: candidate=payload.decode('utf-8','strict')
        except UnicodeDecodeError: continue
        if '\x00' in candidate or '\ufffd' in candidate: continue
        if any(ord(c)<32 and c not in '\n\r\t' for c in candidate): continue
        if any(ord(c)==127 for c in candidate): continue
        # Avoid binary blobs that happen to decode as punctuation-only strings.
        if not any(c.isalpha() for c in candidate): continue
        if len(candidate.strip())<4 or len(candidate.strip())>300: continue
        if (off,candidate) in seen: continue
        seen.add((off,candidate))
        found.append({'text':candidate,'raw_offset':off,'byte_length':length,
                      'byte_sha256':hashlib.sha256(payload).hexdigest()})
        if len(found)>=max_candidates: break
    return found


def walk_typed_strings(root, allowed_keys=None):
    """Return (path, value) from decoded JSON-like Unity objects. Limit recursion/output."""
    allowed_keys=allowed_keys or {'m_text','m_Text','text','value','message'}
    found=[]
    def visit(node,path,depth):
        if depth>10 or len(found)>=300: return
        if isinstance(node,dict):
            for k,v in node.items():
                if not isinstance(k,str): continue
                nxt=f'{path}.{k}' if path else k
                if isinstance(v,str) and k in allowed_keys and v.strip():
                    found.append((nxt,v))
                elif isinstance(v,(dict,list)): visit(v,nxt,depth+1)
        elif isinstance(node,list):
            for idx,value in enumerate(node[:256]):
                visit(value, f'{path}[{idx}]',depth+1)
    visit(root,'',0)
    return found


def baseline_asset_observations(assets):
    """Prove exact JSON message strings read from TextAsset data in a BUILD.
    Never promote raw string candidates or unclassified MonoBehaviour fields.
    """
    out=[]; used=set()
    for a in assets:
        if (a.get('evidence_type')!='asset_text' or
            a.get('asset_type')!='TextAsset' or
            a.get('source_type')!='external_json' or
            a.get('metadata',{}).get('key') not in ('message','value','text')):
            continue
        txt=a.get('text',''); ref=a.get('source_ref','')
        if not txt or not ref or (ref,txt) in used: continue
        used.add((ref,txt))
        out.append({'text':txt,'source_type':'external_json','method':'',
                    'source_ref':ref,'evidence_type':'asset_text','evidence_value':txt,
                    'confidence':'observed',
                    'note':'Decoded from build TextAsset; original Assets/Resources path not proven.'})
    return out



def mono_script_identity(obj):
    """Return MonoScript identity from a build ONLY if the m_Script pointer resolves."""
    try:
        head=obj.parse_monobehaviour_head()
        script=head.m_Script.deref_parse_as_object()
        namespace=str(getattr(script,'m_Namespace','') or '')
        classname=str(getattr(script,'m_ClassName','') or '')
        assembly=str(getattr(script,'m_AssemblyName','') or '')
        if not classname: return {}
        return {'assembly':assembly,'full_class_name': f'{namespace}.{classname}' if namespace else classname}
    except Exception:
        return {}


def scan_assets(build, max_files=40, max_mb=128):
    """Read-only Unity asset scan, with optional Mono TypeTreeGenerator and evidence-limited
    raw-string fallback. Does not use Unity Editor files, a source project, or ground truth.
    """
    try: import UnityPy
    except ImportError as ex: raise RuntimeError('UnityPy missing from project venv') from ex
    build=Path(build)
    if not build.is_dir(): raise ValueError('Build data directory not found: '+str(build))
    managed=build/'Managed'
    files=[]
    for path in build.rglob('*'):
        if not path.is_file() or path.stat().st_size > max_mb*1024*1024: continue
        if path.suffix.lower() in ('.assets','.bundle','.unity3d') or path.name.startswith(('sharedassets','resources.assets','level')):
            files.append(path)
    files.sort(key=lambda x:str(x))
    results=[]; candidates=[]; errors=[]; stats={'monobehaviours_seen':0,'monobehaviours_decoded':0,
                'textassets_seen':0,'textassets_decoded':0, 'raw_candidate_count':0}
    generators={}; generator_errors={}
    try:
        from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator
        generator_import_available=True
    except ImportError:
        TypeTreeGenerator=None
        generator_import_available=False
    for path in files[:max_files]:
        try:
            env=UnityPy.load(str(path))
        except Exception as ex:
            errors.append({'file':path.name,'stage':'load','error':str(ex)[:250]})
            continue
        objects=list(env.objects)
        # Avoid import/generation of assemblies if optional generator is unavailable.
        if generator_import_available and objects and managed.is_dir():
            version=str(objects[0].assets_file.unity_version)
            if version not in generators and version not in generator_errors:
                try:
                    generator=TypeTreeGenerator(version)
                    generator.load_local_dll_folder(str(managed))
                    generators[version]=generator
                except Exception as ex:
                    generator_errors[version]=str(ex)[:250]
            if version in generators:
                env.typetree_generator=generators[version]
        for obj in objects:
            typ=str(getattr(getattr(obj,'type',None),'name',''))
            if typ not in ('TextAsset','MonoBehaviour'): continue
            ref=f'{path.name}#path_id={getattr(obj,"path_id","unknown")}'
            if typ=='TextAsset': stats['textassets_seen']+=1
            else: stats['monobehaviours_seen']+=1
            script_identity = mono_script_identity(obj) if typ=='MonoBehaviour' else {}
            try:
                data=obj.parse_as_dict()
                if not isinstance(data,dict): continue
                if typ=='TextAsset':
                    stats['textassets_decoded']+=1
                    blob=data.get('m_Script','')
                    if isinstance(blob,(bytes,bytearray)): blob=bytes(blob).decode('utf-8-sig','replace')
                    if not isinstance(blob,str) or not blob.strip(): continue
                    try: parsed=json.loads(blob)
                    except (ValueError,TypeError): continue
                    if isinstance(parsed,dict):
                        for key,value in walk_typed_strings(parsed):
                            # JSON field paths are real as decoded; still no original source-project path.
                            results.append({'text':value,'source_type':'external_json','source_ref':ref,
                                            'asset_type':typ,'evidence_type':'asset_text',
                                            'metadata':{'key':key.split('.')[-1], 'field_path':key,
                                                        'asset_name':data.get('m_Name','')}})
                else:
                    stats['monobehaviours_decoded']+=1
                    for key,value in walk_typed_strings(data):
                        results.append({'text':value,'source_type':'unknown','source_ref':ref,
                                        'asset_type':typ,'evidence_type':'asset_text',
                                        'metadata':{'field_path':key,'identity':'build-serialized-object',
                                                    'original_asset_source':'unproven','mono_script':script_identity}})
            except Exception as ex:
                errors.append({'file':path.name,'stage':'parse_as_dict','type':typ,
                               'path_id':getattr(obj,'path_id',None),'error':str(ex)[:250]})
                if typ!='MonoBehaviour': continue
                # Raw candidates only: do NOT classify as prefab/scene/ScriptableObject or observed.
                try:
                    payload=obj.get_raw_data()
                    for candidate in scan_raw_unity_strings(payload):
                        candidates.append({'text':candidate['text'],'source_type':'unknown',
                                           'source_ref':ref,'asset_type':typ,
                                           'evidence_type':'raw_string_candidate',
                                           'confidence':'unverified',
                                           'metadata':{'object_relative_offset':candidate['raw_offset'],
                                                       'byte_length':candidate['byte_length'],
                                                       'byte_sha256':candidate['byte_sha256'],
                                                       'reason':'MonoBehaviour parse failed; no field identity',
                                                       'mono_script':script_identity}})
                except Exception as raw_ex:
                    errors.append({'file':path.name,'stage':'raw_fallback','type':typ,
                                   'path_id':getattr(obj,'path_id',None),'error':str(raw_ex)[:250]})
    # Enforce output cap across all raw objects for bounded evidence.
    candidates=candidates[:2000]
    stats['raw_candidate_count']=len(candidates)
    return {'schema':SCHEMA,'source':'read_only_build_asset_scan',
            'files_considered':len(files),'files_scanned':min(len(files),max_files),
            'truncated':len(files)>max_files,'assets':results,
            'raw_candidates':candidates,'errors':errors,'stats':stats,
            'type_tree_generator':{'module_imported':generator_import_available,
                                   'loaded_versions':list(generators),
                                   'errors_by_version':generator_errors},
            'limitations':['Build cannot reliably recover Unity Editor prefab or scene asset paths.',
                           'Unclassified MonoBehaviour fields are not evidence of source category.',
                           'Raw candidates are length-prefixed strings only; field ownership is unproven.',
                           'TypeTreeGenerator may fail for Unity 6 or unresolved cross-file script references.']}


def template_match(template, text):
    if not template or '{' not in template: return False
    pattern=re.escape(template)
    pattern=re.sub(r'\\\{\d+(?::[^}]*)?\\\}',r'.+?',pattern)
    try: return bool(re.fullmatch(pattern,text))
    except re.error: return False


def evaluate(observations, gtfile):
    """ONLY for PRIVATE evaluator: never put ground truth in AgentInput or the model messages."""
    with open(gtfile,encoding='utf-8-sig',newline='') as f: truth=list(csv.DictReader(f))
    detail=[]
    for r in truth:
        t=r['displayed_text']; category=r['source_category']
        candidates=[]
        for o in observations:
            if o.get('validation_status')!='observed': continue
            if o.get('source_type')!=category: continue
            lit=o.get('text','')
            if normalize_text(lit)==normalize_text(t): candidates.append(('exact_text',o))
            elif template_match(lit,t): candidates.append(('template_text',o))
        if candidates:
            kind,o=candidates[0]
            detail.append({'case_id':r['case_id'],'status':kind,'observed_text':o['text'],
                           'source_category':category,'observation_id':o['observation_id']})
        else:
            detail.append({'case_id':r['case_id'],'status':'not_proven','observed_text':'',
                           'source_category':category,'observation_id':''})
    exact=sum(d['status']=='exact_text' for d in detail)
    templates=sum(d['status']=='template_text' for d in detail)
    return {'schema':SCHEMA,'kind':'private_blind_evaluation','total_cases':len(truth),
            'exact_text_and_source_proven':exact,'format_template_and_source_proven':templates,
            'unproven':len(truth)-exact-templates,'cases':detail,
            'caveat':'This is a source+text static evidence measure, not AI intelligence, recall of all game strings, nor runtime hook success.'}


def main(argv=None):
    p=argparse.ArgumentParser(description='Mod Studio AI / M03 local build research')
    sub=p.add_subparsers(dest='command',required=True)
    for name in ('baseline','agent'):
        q=sub.add_parser(name)
        q.add_argument('--rea',required=True)
        q.add_argument('--assets',help='Optional output from scan-assets')
        q.add_argument('--out',required=True)
        if name=='agent':
            q.add_argument('--server',default='http://127.0.0.1:9931')
            q.add_argument('--model',default='local-qwen')
            q.add_argument('--steps',type=int,default=10)
    s=sub.add_parser('scan-assets')
    s.add_argument('--build-data',required=True)
    s.add_argument('--out',required=True)
    s.add_argument('--max-files',type=int,default=40)
    s.add_argument('--max-mb',type=int,default=128)
    pr=sub.add_parser('prepare')
    pr.add_argument('--members',required=True)
    pr.add_argument('--artifact')
    pr.add_argument('--out',required=True)
    e=sub.add_parser('evaluate')
    e.add_argument('--observations',required=True)
    e.add_argument('--truth',required=True)
    e.add_argument('--out',required=True)
    args=p.parse_args(argv)
    if args.command=='prepare':
        items=prepare_rea_members(load(args.members),load(args.artifact) if args.artifact else None)
        verify_rea_evidence(items)
        write_jsonl(args.out,items)
        print(json.dumps({'command':'prepare','out':args.out,'methods':len(items)},ensure_ascii=False))
        return 0
    if args.command=='scan-assets':
        output=scan_assets(args.build_data,args.max_files,args.max_mb)
    elif args.command=='evaluate':
        output=evaluate(load(args.observations)['observations'],args.truth)
    else:
        items=load_jsonl(args.rea)
        sha=verify_rea_evidence(items)
        assets=(load(args.assets).get('assets',[]) if args.assets else [])
        if args.command=='baseline':
            obs=baseline(items) + baseline_asset_observations(assets)
            trace=[]; completed=True
        else:
            obs,trace,completed=run_agent(items,assets,args.server,args.model,args.steps)
        output={'schema':SCHEMA,'mode':args.command,'assembly_sha256':sha,'completed':completed,
                'observations':validate_observations(obs,items,assets),'trace':trace,
                'limitations':['No source-project or Editor ground truth is used.',
                               'No code is injected; no hooking is performed.',
                               'Static evidence does not prove runtime behavior.',
                               'Unknown build asset text must not be guessed.']}
    dump(args.out,output)
    print(json.dumps({'command':args.command,'out':args.out,'observations':len(output.get('observations',[])),
                      'completed':output.get('completed',True)},ensure_ascii=False))
    return 0

if __name__=='__main__':
    try: sys.exit(main())
    except (RuntimeError,ValueError,OSError) as ex:
        print(f'ERROR: {ex}',file=sys.stderr)
        sys.exit(2)
