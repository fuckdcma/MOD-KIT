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

SCHEMA = 'modstudio.m03.v0.4'
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
                text==obs.get('evidence_value') and
                obs.get('source_ref')==a.get('source_ref') and
                obs.get('source_type')==a.get('source_type') and
                obs.get('source_type')!='unknown' and
                (obs.get('source_type')!='scriptable_object' or _scriptable_proof_asset(a)) and
                (obs.get('source_type')!='external_json' or a.get('asset_type')=='TextAsset')):
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


class ModelResponseError(RuntimeError):
    """Machine-readable model output problem. Never include untrusted response text in logs."""
    def __init__(self,code,details=''):
        self.code=code
        self.details=str(details)[:200]
        super().__init__(f'{code}: {self.details}' if self.details else code)


def _parse_agent_json(reply,finish_reason='unknown'):
    if not isinstance(reply,str) or not reply.strip():
        raise ModelResponseError('empty_content',f'finish={finish_reason}; likely thinking budget or model output issue')
    try:
        parsed=json.loads(reply)
    except json.JSONDecodeError as exc:
        raise ModelResponseError('invalid_json',f'chars={len(reply)}, line={exc.lineno}, column={exc.colno}, finish={finish_reason}') from exc
    if not isinstance(parsed,dict):
        raise ModelResponseError('unexpected_json_type','expected JSON object, got '+type(parsed).__name__)
    return parsed


def _local_endpoint(server,transport):
    u=urllib.parse.urlparse(server)
    if u.scheme!='http' or u.hostname not in ('127.0.0.1','localhost','::1') or u.username or u.password or u.query or u.fragment:
        raise ValueError('Only localhost HTTP model endpoints are allowed; no cloud API')
    if u.path.rstrip('/') not in ('','/v1'):
        raise ValueError('Expected localhost Ollama root or OpenAI /v1 endpoint')
    if transport not in ('auto','ollama','openai'):
        raise ValueError('Unsupported transport')
    if transport=='auto':
        transport='ollama' if u.port==11434 else 'openai'
    base=f'http://{u.netloc}'
    return (base+'/api/chat' if transport=='ollama' else base+'/v1/chat/completions'),transport


def local_chat(server, model, messages, timeout=180, transport='auto'):
    """Local JSON-only model round-trip. Native Ollama disables thinking explicitly.

    OpenAI-compatible transport is retained for llama-server on localhost:9931.
    HTTP requests never target a remote host, regardless of server argument.
    """
    url,kind=_local_endpoint(server,transport)
    if kind=='ollama':
        payload={'model':model,'messages':messages,'think':False,'format':'json','stream':False,
                 'options':{'temperature':0,'num_predict':2048}}
    else:
        payload={'model':model,'messages':messages,'temperature':0.0,'max_tokens':2048,
                 'stream':False,'response_format':{'type':'json_object'}}
        if urllib.parse.urlparse(server).port==11434:
            payload['reasoning_effort']='none'
    req=urllib.request.Request(url, data=json.dumps(payload,ensure_ascii=False).encode('utf-8'),
       headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=timeout) as resp:
        result=json.load(resp)
    try:
        if kind=='ollama':
            content=result['message'].get('content')
            finish_reason=result.get('done_reason','unknown')
        else:
            choice=result['choices'][0]
            content=choice['message'].get('content')
            finish_reason=choice.get('finish_reason','unknown')
    except (KeyError,IndexError,TypeError,AttributeError) as exc:
        raise ModelResponseError('api_response_shape','missing message.content') from exc
    if isinstance(content,list):
        content=''.join(p.get('text','') for p in content if isinstance(p,dict))
    return _parse_agent_json(content,finish_reason)

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


def run_agent(items, assets, server, model, max_steps=12, transport='auto', max_retries=2):
    verify_rea_evidence(items)
    # Validate endpoint BEFORE starting the investigation. Fail closed for cloud URLs.
    _local_endpoint(server,transport)
    messages=[{'role':'system','content':SYSTEM},
              {'role':'user','content':json.dumps({'task':'Find all evidence of text origin, text generation and text rendering in this Unity game. Do not guess unseen asset text.',
                         'methods':method_summary(items),'asset_scan_count':len(assets)},ensure_ascii=False)}]
    trace=[]; observations=[]; finished=False
    max_steps=max(1,min(30,max_steps))
    max_retries=max(0,min(3,max_retries))
    for step in range(max_steps):
        response=None
        for retry in range(max_retries+1):
            try:
                response=local_chat(server,model,messages,transport=transport)
                if response.get('action') not in TOOLS:
                    raise ModelResponseError('invalid_action','Expected one of: '+', '.join(sorted(TOOLS)))
                break
            except ModelResponseError as ex:
                response=None
                trace.append({'step':step+1,'attempt':retry+1,'status':'model_response_error','code':ex.code,'detail':ex.details})
                if retry==max_retries: break
                # Avoid repeating or logging raw reasoning/text; request a clean answer.
                repair={'role':'user','content':'Previous model response was not a valid action JSON. Return exactly ONE JSON object with an allowed action and its required fields, no thinking, no markdown.'}
                messages.append(repair)
            except Exception as ex:
                response=None
                trace.append({'step':step+1,'status':'transport_error','error_type':type(ex).__name__,
                              'detail':str(ex)[:200]})
                break
        if response is None: break
        action=response['action']
        if action=='finish':
            observations=response.get('observations',[])
            if not isinstance(observations,list): observations=[]
            trace.append({'step':step+1,'action':'finish','candidate_count':len(observations)})
            finished=True; break
        result=tool_result(action,response,items,assets)
        result_json=json.dumps(result,ensure_ascii=False)
        max_chars=4500  # Qwen running with 4096-token context: bound tool feedback.
        truncated=len(result_json)>max_chars
        if truncated:result_json=result_json[:max_chars]+' [TRUNCATED; narrow your next query]'
        trace.append({'step':step+1,'action':action,'request':response,
                      'result_count':len(result) if isinstance(result,list) else 1,
                      'tool_result_truncated':truncated})
        messages.append({'role':'assistant','content':json.dumps(response,ensure_ascii=False)})
        messages.append({'role':'user','content':'RESULT from '+action+': '+result_json+
                         '\nContinue investigation or finish with evidence-grounded observations. Return JSON ONLY.'})
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


def _table_entry_lookup(data, field_path):
    """Extract key paired with value from the SAME decoded, build-only object."""
    m=re.fullmatch(r'entries\[(\d+)\]\.value',field_path)
    if not m or not isinstance(data,dict): return None
    rows=data.get('entries')
    if not isinstance(rows,list): return None
    i=int(m.group(1))
    if i>=len(rows) or not isinstance(rows[i],dict): return None
    row=rows[i]
    key=row.get('key')
    value=row.get('value')
    return key if isinstance(key,str) and key.strip() and isinstance(value,str) else None


def scan_table_asset_field(data, script_identity, field_path, text):
    """Class + serialized member + paired key are required, not string similarity."""
    if script_identity.get('full_class_name')!='ModStudioLab.LabStringTable':
        return 'unknown',{}
    key=_table_entry_lookup(data,field_path)
    if key is None or not re.fullmatch(r'entries\[\d+\]\.value',field_path):
        return 'unknown',{}
    if text!=data['entries'][int(re.search(r'\[(\d+)\]',field_path).group(1))]['value']:
        return 'unknown',{}
    return 'scriptable_object',{'entry_key':key,'key_field_path':field_path[:-len('value')]+'key'}


def pointer_file_lookup(pointer, serialized_file, source_file):
    """Resolve the *file name* part of a Unity serialized PPtr using its own external table.

    m_FileID == 0 is local. Positive m_FileID indexes serialized_file.externals
    at m_FileID - 1. Do not infer external identity from a matching PathID or key.
    This function does NOT prove the referenced object exists or is loaded.
    """
    fid=pointer.get('m_FileID') if isinstance(pointer,dict) else None
    pid=pointer.get('m_PathID') if isinstance(pointer,dict) else None
    out={'status':'not_resolved','source_file':source_file,
         'm_FileID':fid,'m_PathID':pid}
    if type(fid) is not int or type(pid) is not int or fid<0 or pid<=0:
        out['reason']='PPtr file/path ID missing or invalid'
        return out
    if fid==0:
        out.update({'status':'file_mapped','reference_kind':'local',
                    'file_name':source_file,'external_index':None,
                    'external_path':None})
        return out
    externals=getattr(serialized_file,'externals',None)
    if not isinstance(externals,(list,tuple)) or fid>len(externals):
        out['reason']='External references missing or m_FileID out of bounds'
        return out
    external=externals[fid-1]
    external_path=getattr(external,'path',None)
    if not isinstance(external_path,str) or not external_path.strip():
        out['reason']='External reference path missing'
        return out
    name=external_path.replace('\\','/').rstrip('/').rsplit('/',1)[-1]
    if not name or name in ('.','..'):
        out['reason']='External file name invalid'
        return out
    out.update({'status':'file_mapped','reference_kind':'external',
                'file_name':name,'external_index':fid-1,
                'external_path':external_path})
    return out


def scan_reader_binding(data, script_identity, ref, serialized_file=None):
    """Inspect reader config and serialized external table; not runtime execution."""
    if script_identity.get('full_class_name')!='ModStudioLab.TableTextExample' or not isinstance(data,dict):
        return None
    key=data.get('key')
    if not isinstance(key,str) or not key.strip(): return None
    ptr=data.get('table')
    if isinstance(ptr,dict):
        pointer={k:int(ptr[k]) for k in ('m_FileID','m_PathID') if k in ptr and type(ptr[k]) is int}
    else: pointer={}
    source_file=ref.partition('#path_id=')[0]
    return {'source_ref':ref,'reader_class':script_identity['full_class_name'],
            'reader_key':key,'table_pointer':pointer,
            'pointer_file_lookup':pointer_file_lookup(pointer,serialized_file,source_file),
            'binding_status':'unresolved_build_pointer'}


def resolve_reader_bindings(bindings, assets, scanned_files):
    """Match a PPtr to the exact serialized table object via external file index,
    unique file basename, object PathID, script class and the reader's key.

    Input only from the build scanner. A shared PathID/key without its external
    map MUST remain unresolved. This proves serialized config, NOT live runtime.
    """
    from collections import Counter
    name_counts=Counter(Path(str(p)).name.casefold() for p in scanned_files)
    for b in bindings:
        lookup=b.get('pointer_file_lookup') or {}
        if lookup.get('status')!='file_mapped': continue
        name=lookup.get('file_name','')
        if not isinstance(name,str) or name_counts[name.casefold()]!=1:
            b['binding_reason']='External file basename is not unique among scanned files'
            continue
        pid=lookup.get('m_PathID')
        if type(pid) is not int or pid<=0: continue
        target=f'{name}#path_id={pid}'
        matches=[a for a in assets if
                 a.get('source_ref','').casefold()==target.casefold() and
                 _scriptable_proof_asset(a) and
                 (a.get('metadata') or {}).get('entry_key')==b.get('reader_key')]
        if len(matches)!=1:
            b['binding_reason']='Target object absent, wrong script class/key, or ambiguous table entries'
            continue
        b['binding_status']='serialized_pointer_resolved'
        b['resolved_target_ref']=matches[0]['source_ref']
        b['resolution_evidence']={
            'reader_ref':b.get('source_ref',''),
            'serialized_file':lookup.get('source_file'),
            'm_FileID':lookup.get('m_FileID'),
            'm_PathID':pid,
            'external_index':lookup.get('external_index'),
            'external_path':lookup.get('external_path'),
            'target_ref':matches[0]['source_ref'],
            'target_class':'ModStudioLab.LabStringTable',
            'target_key':b.get('reader_key'),
            'proof_kind':'build_serialized_pointer_not_runtime_behavior'}
    return bindings


def rea_table_call_chain(items):
    """Evidence of a lookup-and-setter METHOD PATH, not runtime pointer identity."""
    by={r['method']:r for r in items}
    method='ModStudioLab.TableTextExample.Start'
    start=by.get(method)
    if not start:return {'supported':False,'reason':'Reader Start method missing'}
    calls=calls_for(start)
    lookup='ModStudioLab.LabStringTable.TryGet'
    if lookup not in calls or 'TMPro.TMP_Text.set_text' not in calls:
        return {'supported':False,'reason':'TryGet or TMP setter call missing'}
    return {'supported':True,'reader_method':method,'table_method':lookup,
            'setter':'TMPro.TMP_Text.set_text',
            'implementation_available':lookup in by,
            'evidence_refs':[t for t in (start.get('method_token'),by.get(lookup,{}).get('method_token')) if t]}


def provenance_links(items, scan):
    """Build-only provenance summary. Does NOT read project source/Editor ground truth."""
    verify_rea_evidence(items)
    assets=scan.get('assets',[]); bindings=scan.get('reader_bindings',[])
    flow=rea_table_call_chain(items)
    out=[]
    for a in assets:
        if a.get('evidence_type')!='asset_text':continue
        typ=a.get('source_type'); md=a.get('metadata') or {}
        r={'text':a.get('text',''), 'source_ref':a.get('source_ref',''),
           'source_type':typ,'field_path':md.get('field_path',''),
           'mono_class':(md.get('mono_script') or {}).get('full_class_name',''),
           'source_status':'unproven','runtime_binding':'not_proven',
           'proof_refs':[a.get('source_ref','')]}
        if typ=='external_json' and a.get('asset_type')=='TextAsset':
            r['source_status']='source_value_observed'
        elif typ=='scriptable_object' and _scriptable_proof_asset(a):
            r['source_status']='source_key_value_observed'
            key=md['entry_key']; r['key']=key
            r['reader_flow']=flow
            matches=[b for b in bindings if b.get('reader_key')==key and
                     b.get('reader_class')=='ModStudioLab.TableTextExample']
            resolved=[b for b in matches if b.get('binding_status')=='serialized_pointer_resolved' and
                      b.get('resolved_target_ref')==a.get('source_ref')]
            if resolved:
                r['serialized_reader_binding']='pointer_to_this_table_proven'
                r['reader_bindings']=resolved
                r['proof_refs'].extend(b['source_ref'] for b in resolved)
                r['runtime_binding']=('serialized_pointer_and_lookup_flow_proven_runtime_unverified'
                                      if flow['supported'] else 'serialized_pointer_proven_method_flow_unverified')
            elif matches and flow['supported']:
                r['runtime_binding']='lookup_call_and_key_supported_pointer_unresolved'
                r['candidate_reader_bindings']=matches
            elif flow['supported']:
                r['runtime_binding']='reader_calls_observed_key_or_pointer_not_linked'
        elif a.get('asset_type')=='MonoBehaviour' and md.get('mono_script',{}).get('full_class_name')=='TMPro.TextMeshProUGUI':
            r['source_status']='ui_snapshot_only'
            r['warning']='TMP m_text in level0 is not proof of prefab/source ownership'
        out.append(r)
    return {'schema':SCHEMA,'kind':'build_only_provenance_links',
            'assets_scanned':len(assets),'observations':out,
            'rea_table_call_chain':flow,
            'limitations':['No editor data, source project, or ground truth used.',
                           'Unity source prefab path is not recoverable from TMP m_text alone.',
                           'Serialized key/value proves a table source; call path and binding require separate evidence.',
                           'External-table pointer resolution proves serialized instance configuration, not runtime execution.']}


def _scriptable_proof_asset(a):
    md=a.get('metadata') or {}
    return (a.get('evidence_type')=='asset_text' and
            a.get('source_type')=='scriptable_object' and
            a.get('asset_type')=='MonoBehaviour' and
            (md.get('mono_script') or {}).get('full_class_name')=='ModStudioLab.LabStringTable' and
            isinstance(md.get('entry_key'),str) and bool(md['entry_key'].strip()) and
            bool(re.fullmatch(r'entries\[\d+\]\.value',md.get('field_path',''))))

def baseline_asset_observations(assets, rea_items=None):
    """Build-only source proofs; never promote unknown TMP display snapshots.

    For LabStringTable this proves KEY+VALUE in a serialized object, NOT the
    runtime binding from the reader component to that exact table instance.
    """
    out=[]; used=set()
    for a in assets:
        kind=a.get('source_type'); md=a.get('metadata') or {}
        txt=a.get('text',''); ref=a.get('source_ref','')
        if a.get('evidence_type')!='asset_text' or not txt or not ref:continue
        if (kind=='external_json' and a.get('asset_type')=='TextAsset' and
            md.get('key') in ('message','value','text')):
            key=('external_json',ref,txt)
            if key in used:continue
            used.add(key)
            out.append({'text':txt,'source_type':'external_json','method':'',
                'source_ref':ref,'evidence_type':'asset_text','evidence_value':txt,
                'confidence':'observed','note':'Build TextAsset JSON field; original source path not proven.'})
        elif _scriptable_proof_asset(a):
            key=('scriptable_object',ref,md['entry_key'],txt)
            if key in used:continue
            used.add(key)
            chain=rea_table_call_chain(rea_items or []) if rea_items is not None else {'supported':False}
            out.append({'text':txt,'source_type':'scriptable_object','method':'',
                'source_ref':ref,'evidence_type':'asset_text','evidence_value':txt,
                'confidence':'observed',
                'note':'Paired serialized LabStringTable key/value = '+md['entry_key']+
                       '; actual reader-to-asset binding NOT proven.'+
                       (' REA lookup/setter method path supported.' if chain['supported'] else '')})
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
    results=[]; candidates=[]; errors=[]; reader_bindings=[]; stats={'monobehaviours_seen':0,'monobehaviours_decoded':0,
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
                    b=scan_reader_binding(data,script_identity,ref,getattr(obj,'assets_file',None))
                    if b is not None:reader_bindings.append(b)
                    for key,value in walk_typed_strings(data):
                        source_type,proof=scan_table_asset_field(data,script_identity,key,value)
                        results.append({'text':value,'source_type':source_type,'source_ref':ref,
                                        'asset_type':typ,'evidence_type':'asset_text',
                                        'metadata':{'field_path':key,'identity':'build-serialized-object',
                                                    'original_asset_source':'unproven','mono_script':script_identity,
                                                    **proof}})
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
    # Resolve from the ACTUAL per-file external-reference table and target object.
    # Key or PathID similarity alone never upgrades the binding status.
    resolve_reader_bindings(reader_bindings,results,files[:max_files])
    stats['reader_pointers_resolved']=sum(b.get('binding_status')=='serialized_pointer_resolved'
                                         for b in reader_bindings)
    # Enforce output cap across all raw objects for bounded evidence.
    candidates=candidates[:2000]
    stats['raw_candidate_count']=len(candidates)
    return {'schema':SCHEMA,'source':'read_only_build_asset_scan',
            'files_considered':len(files),'files_scanned':min(len(files),max_files),
            'truncated':len(files)>max_files,'assets':results,
            'raw_candidates':candidates,'reader_bindings':reader_bindings,'errors':errors,'stats':stats,
            'type_tree_generator':{'module_imported':generator_import_available,
                                   'loaded_versions':list(generators),
                                   'errors_by_version':generator_errors},
            'limitations':['Build cannot reliably recover Unity Editor prefab or scene asset paths.',
                           'Unclassified MonoBehaviour fields are not evidence of source category.',
                           'Raw candidates are length-prefixed strings only; field ownership is unproven.',
                           'TypeTreeGenerator may fail for Unity 6 or unresolved cross-file script references.',
                           'Pointer file ID mapping requires exact external-reference table and unique file name.']}


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
            q.add_argument('--steps',type=int,default=12)
            q.add_argument('--transport',choices=('auto','ollama','openai'),default='auto')
            q.add_argument('--retries',type=int,default=2)
    s=sub.add_parser('scan-assets')
    s.add_argument('--build-data',required=True)
    s.add_argument('--out',required=True)
    s.add_argument('--max-files',type=int,default=40)
    s.add_argument('--max-mb',type=int,default=128)
    pr=sub.add_parser('prepare')
    pr.add_argument('--members',required=True)
    pr.add_argument('--artifact')
    pr.add_argument('--out',required=True)
    li=sub.add_parser('provenance')
    li.add_argument('--rea',required=True)
    li.add_argument('--assets',required=True)
    li.add_argument('--out',required=True)
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
    elif args.command=='provenance':
        output=provenance_links(load_jsonl(args.rea),load(args.assets))
    elif args.command=='evaluate':
        report=load(args.observations)
        if report.get('mode')=='agent' and report.get('completed') is not True:
            raise ValueError('Agent run is incomplete; evaluation skipped. Inspect qwen_agent.json trace instead of treating missing observations as 0/5.')
        output=evaluate(report['observations'],args.truth)
    else:
        items=load_jsonl(args.rea)
        sha=verify_rea_evidence(items)
        assets=(load(args.assets).get('assets',[]) if args.assets else [])
        if args.command=='baseline':
            obs=baseline(items) + baseline_asset_observations(assets,items)
            trace=[]; completed=True
        else:
            obs,trace,completed=run_agent(items,assets,args.server,args.model,args.steps,args.transport,args.retries)
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
