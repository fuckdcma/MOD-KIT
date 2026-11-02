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
import urllib.parse
import urllib.request
from pathlib import Path

SCHEMA = 'modstudio.m03.v0.1'
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
            if text and text==a.get('text') and obs.get('source_ref')==a.get('source_ref'):
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
Yêu cầu: truy vết text, nguồn dữ liệu, đường truyền đến UI; KHÔNG được suy đoán giá trị từ JSON/prefab/ScriptableObject nếu bản build chưa chứng minh. Method_call chỉ chứng minh lời gọi, không chứng minh nội dung. Không có câu trả lời thì trả giá trị rỗng và nêu hạn chế. Không được dùng ground truth hay dữ liệu Unity Editor. Chỉ tìm hiểu game offline, không tìm cách vượt anti-cheat.'''


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


def scan_assets(build, max_files=40, max_mb=128):
    """Read-only experimental scan using UnityPy. NOT proof of original Unity asset path."""
    try: import UnityPy
    except ImportError as ex: raise RuntimeError('Install optional UnityPy first: py -3 -m pip install UnityPy') from ex
    build=Path(build)
    if not build.is_dir(): raise ValueError('Build data directory not found: '+str(build))
    files=[]
    for p in build.rglob('*'):
        if not p.is_file() or p.stat().st_size>max_mb*1024*1024: continue
        if p.suffix.lower() in ('.assets','.bundle','.unity3d') or p.name.startswith(('sharedassets','resources.assets','level')):
            files.append(p)
    results=[]; errors=[]
    for path in files[:max_files]:
        try:
            env=UnityPy.load(str(path))
            for obj in env.objects:
                ty=str(getattr(getattr(obj,'type',None),'name',''))
                if ty not in ('TextAsset','MonoBehaviour'): continue
                try:
                    data=obj.parse_as_dict()
                    if not isinstance(data,dict): continue
                    # Unity build does not promise original asset source path or authored C# class.
                    source_ref=f'{path.name}#path_id={getattr(obj,"path_id","unknown")}'
                    if ty=='TextAsset':
                        blob=data.get('m_Script','')
                        if isinstance(blob,(bytes,bytearray)):
                            blob=bytes(blob).decode('utf-8-sig','replace')
                        if isinstance(blob,str) and blob.strip():
                            try:
                                parsed=json.loads(blob)
                                if isinstance(parsed,dict):
                                    for k in ('message','value','text'):
                                        val=parsed.get(k)
                                        if isinstance(val,str):
                                            results.append({'text':val,'source_type':'external_json','source_ref':source_ref,
                                                            'asset_type':ty,'evidence_type':'asset_text',
                                                            'metadata':{'key':k,'asset_name':data.get('m_Name','')}})
                            except (ValueError,TypeError):
                                pass
                    if ty=='MonoBehaviour':
                        for k in ('m_text','m_Text'):
                            value=data.get(k)
                            if isinstance(value,str) and value.strip():
                                results.append({'text':value,'source_type':'unknown','source_ref':source_ref,
                                                'asset_type':ty,'evidence_type':'asset_text',
                                                'metadata':{'field':k,'identity':'scene_or_prefab_unknown'}})
                except Exception as ex: errors.append({'file':path.name,'type':ty,'error':str(ex)[:250]})
        except Exception as ex: errors.append({'file':path.name,'error':str(ex)[:250]})
    return {'schema':SCHEMA,'source':'read_only_build_asset_scan','files_considered':len(files),
            'files_scanned':min(len(files),max_files),'truncated':len(files)>max_files,
            'assets':results,'errors':errors,
            'limitation':'Build data cannot reliably recover original prefab/scene path; UnityPy may fail on stripped typetrees or Unity versions.'}


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
            obs=baseline(items); trace=[]; completed=True
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