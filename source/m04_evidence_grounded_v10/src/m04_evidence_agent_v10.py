#!/usr/bin/env python3
"""M04 v1.0 EXPERIMENTAL: evidence-indexed, local-only Qwen selector.

Reads only frozen M03 v0.8 REA/UnityPy outputs. Model returns IDs, never source
claims. All observation attributes are copied from exact verified evidence rows.
This static checker does NOT prove runtime UI dataflow, prefab ownership or use.
No generated game source, private seed or ground truth is needed or read.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import importlib.util
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SCHEMA = 'modstudio.m04.evidence_grounded.v1.0-experimental'
MAX_INVENTORY = 2000
VALID_TEMPLATE = re.compile(r'\{\d+(?::[^{}]*)?\}')


class AgentProtocolError(ValueError):
    def __init__(self, code, details=''):
        self.code = code
        self.details = str(details)[:180]
        super().__init__(code + ': ' + self.details)


def load_m03(path):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError('Frozen M03 v0.8 source not found: ' + str(path))
    spec = importlib.util.spec_from_file_location('frozen_m03_v08_readonly', str(path))
    m03 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m03)
    return m03


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for buf in iter(lambda: f.read(65536), b''):
            h.update(buf)
    return h.hexdigest()


def stable_id(entry):
    """Identity over complete material evidence, never truncated display content."""
    canonical = json.dumps(entry, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
    return 'EV_' + hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:20]


def _verify_and_add(m03, items, assets, observation, key_extra, seen, accepted):
    checked = m03.validate_observations([observation], items, assets)
    if len(checked) != 1:
        raise AgentProtocolError('validator_failure', 'Unexpected frozen validator result')
    row = checked[0]
    if row['validation_status'] != 'observed':
        return False
    # Do NOT accept model-reported confidence/fields. This is constructed from evidence.
    key = {k: row.get(k, '') for k in
           ('text', 'source_type', 'method', 'source_ref', 'evidence_type', 'evidence_value')}
    key['origin_unique'] = key_extra
    candidate_id = stable_id(key)
    if candidate_id in seen:
        if seen[candidate_id]['observation'] != row:
            raise AgentProtocolError('hash_collision', 'Evidence identity collision')
        return True
    seen[candidate_id] = {'id': candidate_id, 'observation': row,
                          'origin_unique': key_extra}
    accepted.append(seen[candidate_id])
    return True


def candidate_inventory(m03, items, scan):
    """Create precise, allowlisted candidates from source-qualified build evidence.

    Return (candidates, diagnostics). Unknown MonoBehaviour/source fields remain
    unknown, even if they look like serialized ScriptableObject entries. Do not
    infer that TMP scene snapshots came from a prefab.
    """
    m03.verify_rea_evidence(items)
    if not isinstance(scan, dict) or scan.get('source') != 'read_only_build_asset_scan':
        raise AgentProtocolError('invalid_scan', 'Expected M03 read-only build asset scan')
    assets = scan.get('assets', [])
    if not isinstance(assets, list):
        raise AgentProtocolError('invalid_scan', 'Assets must be a list')
    observed, seen = [], {}
    diags = collections.Counter()
    unique_methods = set()
    for m in sorted(items, key=lambda x: (str(x.get('method_token','')), x['method'])):
        name = m['method']
        if name in unique_methods:
            raise AgentProtocolError('duplicate_method', 'Ambiguous full method name in REA evidence')
        unique_methods.add(name)
        calls = m03.calls_for(m)
        has_setter = 'TMPro.TMP_Text.set_text' in calls
        has_formatter = 'System.String.Format' in calls
        for lit in m.get('strings_loaded_by_method', []):
            text = lit.get('literal')
            if not isinstance(text, str) or not text or len(text) > 1500:
                diags['empty_or_oversize_literal'] += 1
                continue
            if m03.diagnostic_literal(text):
                diags['diagnostic_literal_excluded'] += 1
                continue
            if not has_setter:
                diags['literal_without_tmp_setter'] += 1
                continue
            template = bool(VALID_TEMPLATE.search(text))
            if template and not has_formatter:
                diags['ambiguous_template_excluded'] += 1
                continue
            source_type = 'runtime_generated' if template and has_formatter else 'hardcoded_managed'
            # No guessing raw runtime formatted values; preserve exact template only.
            observation = {'text': text, 'source_type': source_type, 'method': name,
                           'source_ref': name, 'evidence_type': 'il_literal',
                           'evidence_value': text, 'confidence': 'observed',
                           'note': 'Exact REA ldstr with TMP setter in method; no IL stack-flow/runtime proof.'}
            unique = {'kind': 'il_literal', 'method_token': m.get('method_token'),
                      'literal_token': lit.get('literal_token'), 'il_offset': lit.get('il_offset')}
            if _verify_and_add(m03, items, assets, observation, unique, seen, observed):
                diags['il_accepted'] += 1
            else:
                diags['il_rejected_by_frozen_validator'] += 1
    for a in sorted(assets, key=lambda x: (str(x.get('source_ref','')), str(x.get('text','')))):
        kind = a.get('source_type')
        text = a.get('text')
        ref = a.get('source_ref')
        meta = a.get('metadata') or {}
        if a.get('evidence_type') != 'asset_text' or not isinstance(text,str) or not text or not isinstance(ref,str) or not ref:
            diags['nonqualifying_asset_record'] += 1
            continue
        if (kind == 'external_json' and a.get('asset_type') == 'TextAsset'
                and meta.get('key') in ('message', 'value', 'text')):
            pass
        elif kind == 'scriptable_object' and m03._scriptable_proof_asset(a):
            pass
        else:
            diags['unproven_serialized_source_excluded'] += 1
            continue
        observation = {'text': text, 'source_type': kind, 'method': '',
                       'source_ref': ref, 'evidence_type': 'asset_text',
                       'evidence_value': text, 'confidence': 'observed',
                       'note': 'Decoded build asset field only; live UI use/source project path not proven.'}
        unique = {'kind': 'asset_text', 'source_ref': ref,
                  'field_path': meta.get('field_path'), 'entry_key': meta.get('entry_key')}
        if _verify_and_add(m03, items, assets, observation, unique, seen, observed):
            diags['asset_accepted'] += 1
        else:
            diags['asset_rejected_by_frozen_validator'] += 1
    observed.sort(key=lambda row: (row['observation']['source_type'],
                                   row['observation']['method'],
                                   row['observation']['source_ref'], row['id']))
    if len(observed) > MAX_INVENTORY:
        raise AgentProtocolError('inventory_limit', 'Review scanner: too many evidenced candidates')
    return observed, dict(sorted(diags.items()))


def model_view(entry):
    """Bound prompt but never mutate the authoritative evidence behind its ID."""
    o = entry['observation']
    return {'id': entry['id'], 'source_type': o['source_type'],
            'text': o['text'][:160], 'method': o['method'][:115],
            'source_ref': o['source_ref'][:110],
            'evidence_type': o['evidence_type']}


def _check_local_server(server):
    u = urllib.parse.urlparse(server)
    if (u.scheme != 'http' or u.hostname not in ('localhost','127.0.0.1','::1')
            or u.username or u.password or u.query or u.fragment or
            u.path.rstrip('/') not in ('',) or u.port != 11434):
        raise AgentProtocolError('server_not_local', 'Only Ollama http://127.0.0.1:11434 accepted')
    return 'http://127.0.0.1:11434/api/chat'


def local_select(server, model, candidates, timeout=900, num_ctx=8192, num_predict=512):
    url = _check_local_server(server)
    if not 30 <= timeout <= 1800 or not 4096 <= num_ctx <= 32768 or not 64 <= num_predict <= 4096:
        raise AgentProtocolError('invalid_budget', 'Timeout/context/output limit invalid')
    allowed = {x['id'] for x in candidates}
    message = {
       'task': 'Select ALL and ONLY IDs plausibly displaying UI text in this Unity build. '
               'Reject diagnostic/unused/unrelated text; an exact literal in the same method '
               'as TMP set_text is static co-occurrence only, not full dataflow proof. '
               'Do not derive new strings, modify IDs, or claim unknown prefab origin. '
               'If unsure, favor evidence-rich candidates over guesses.',
       'candidates': [model_view(x) for x in candidates],
       'response': {'select': ['EV_...']},
       'instructions': 'Output exactly one JSON object with key select, array of IDs from candidates. '
                       'Empty [] is valid; no explanations or extra fields.',
    }
    payload = {'model': model, 'messages': [
        {'role':'system','content':'You are a local Unity RE evidence selector. Reply with a complete JSON object only.'},
        {'role':'user','content':json.dumps(message,ensure_ascii=False,separators=(',',':'))}],
        'think': False, 'format': 'json', 'stream': False,
        'options': {'temperature':0,'num_predict':num_predict,'num_ctx':num_ctx}}
    req = urllib.request.Request(url,data=json.dumps(payload,ensure_ascii=False).encode('utf-8'),
                                 headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=timeout) as resp:
        response = json.load(resp)
    finish = response.get('done_reason','unknown')
    content = (response.get('message') or {}).get('content','')
    if not isinstance(content,str):
        raise AgentProtocolError('invalid_model_shape', 'message.content must be a string')
    try:
        answer = json.loads(content)
    except json.JSONDecodeError as ex:
        raise AgentProtocolError('invalid_json', 'chars=%s,column=%s,finish=%s' %
                                 (len(content),ex.colno,finish)) from ex
    if finish == 'length':
        raise AgentProtocolError('finish_length', 'Output truncated at token budget')
    if not isinstance(answer,dict) or set(answer) != {'select'} or not isinstance(answer['select'],list):
        raise AgentProtocolError('invalid_selection_schema', 'Expected {"select":[...]} only')
    ids = answer['select']
    if (len(ids) != len(set(x for x in ids if isinstance(x,str))) or
            any(not isinstance(x,str) or x not in allowed for x in ids)):
        raise AgentProtocolError('unknown_or_duplicate_id', 'Model must select unique allowlisted evidence IDs')
    return ids


def run_indexed_selector(m03, items, scan, model, server, timeout, num_ctx,
                         num_predict, batch_size, retries=2, selector=None):
    """No completion claim if model/validation fails. Failure never silently recovers to baseline."""
    if not 1 <= batch_size <= 20:
        raise AgentProtocolError('invalid_batch_size', 'Choose 1..20')
    catalog, diagnostics = candidate_inventory(m03,items,scan)
    trace = [{'step':0,'action':'catalog_preflight','candidate_count':len(catalog),
              'num_ctx':num_ctx,'num_predict':num_predict,'batch_size':batch_size,
              'strategy':'evidence_grounded_v10_experimental'}]
    if not catalog:
        trace.append({'step':0,'action':'no_evidence_candidates','status':'incomplete'})
        return [],trace,False,0,diagnostics
    selected=[]; chosen=set(); failed=False
    select = selector or local_select
    for batch_idx, offset in enumerate(range(0,len(catalog),batch_size),1):
        batch = catalog[offset:offset+batch_size]
        new_ids = None
        for attempt in range(1,retries+2):
            try:
                new_ids = select(server,model,batch,timeout=timeout,num_ctx=num_ctx,num_predict=num_predict)
                # Also enforce exact ID allowlist for synthetic/test selectors.
                allowed = {x['id'] for x in batch}
                if not isinstance(new_ids,list) or any(not isinstance(x,str) for x in new_ids) or len(set(new_ids)) != len(new_ids) or any(x not in allowed for x in new_ids):
                    raise AgentProtocolError('invalid_selection_ids', 'Batch selected unknown/duplicate ID')
                break
            except AgentProtocolError as ex:
                new_ids = None
                trace.append({'step':batch_idx,'attempt':attempt,'status':'model_protocol_error',
                              'code':ex.code,'detail':ex.details})
            except (OSError,TimeoutError,urllib.error.URLError) as ex:
                new_ids = None
                trace.append({'step':batch_idx,'attempt':attempt,'status':'transport_error',
                              'error_type':type(ex).__name__})
                break
        if new_ids is None:
            failed=True
            break
        chosen.update(new_ids)
        trace.append({'step':batch_idx,'action':'select_evidence_ids','batch_candidates':len(batch),
                      'selected_count':len(new_ids)})
    # Fail-closed: incomplete response is NOT a successful partially selected report.
    if failed:
        return [],trace,False,len(catalog),diagnostics
    for x in catalog:
        if x['id'] in chosen:
            row=dict(x['observation'])
            row['observation_id']='O%04d'%(len(selected)+1)
            selected.append(row)
    trace.append({'step':len(trace),'action':'finish','candidate_count':len(selected)})
    return selected,trace,True,len(catalog),diagnostics


def run_cli(args):
    m03 = load_m03(args.m03)
    items = m03.load_jsonl(args.rea)
    scan = m03.load(args.assets)
    m03.verify_rea_evidence(items)
    if args.mode == 'inventory':
        catalog,diags=candidate_inventory(m03,items,scan)
        result={'schema':SCHEMA,'kind':'inventory_only','completed':True,
                'candidate_count':len(catalog),'candidate_types':dict(sorted(collections.Counter(
                    x['observation']['source_type'] for x in catalog).items())),
                'excluded':diags,'warning':'Inventory counts are not model selections or truth matches.'}
        if args.out: m03.dump(args.out,result)
        print(json.dumps(result,ensure_ascii=False))
        return 0
    if not args.out: raise AgentProtocolError('missing_output', 'Mode agent requires --out')
    if Path(args.out).exists(): raise AgentProtocolError('output_exists','Refusing to overwrite predictions')
    rows,trace,completed,inventory_count,diagnostics=run_indexed_selector(
        m03,items,scan,args.model,args.server,args.timeout,args.num_ctx,args.num_predict,args.batch_size)
    report={'schema':SCHEMA,'mode':'agent','assembly_sha256':m03.verify_rea_evidence(items),
            'completed':completed,'strategy':'evidence_grounded_v10_experimental',
            'observations':rows,'trace':trace,
            'evidence_catalog_count':inventory_count,
            'candidate_source_diagnostics':diagnostics,
            'limitations':['No private ground truth/Editor source is used.',
                           'All observed claims are exact frozen M03 validated static evidence.',
                           'Same-method TMP setter and ldstr does NOT prove IL stack-to-setter flow.',
                           'Only qualified serialized asset sources accepted; unknowns remain unknown.',
                           'Model chooses only exact evidence IDs; run may underselect UI sources.']}
    m03.dump(args.out,report)
    print(json.dumps({'command':'agent','completed':completed,'observations':len(rows),
                      'candidate_count':inventory_count,'out':str(args.out)},ensure_ascii=False))
    return 0


def main():
    p=argparse.ArgumentParser(description='M04 v1.0 experimental evidence-grounded local Qwen')
    p.add_argument('mode',choices=['inventory','agent'])
    p.add_argument('--m03',required=True,help='Frozen M03 v0.8 Python module path')
    p.add_argument('--rea',required=True)
    p.add_argument('--assets',required=True)
    p.add_argument('--out')
    p.add_argument('--server',default='http://127.0.0.1:11434')
    p.add_argument('--model',default='qwen3.5:4b')
    p.add_argument('--timeout',type=int,default=900)
    p.add_argument('--num-ctx',type=int,default=8192)
    p.add_argument('--num-predict',type=int,default=512)
    p.add_argument('--batch-size',type=int,default=10)
    args=p.parse_args()
    try:
        return run_cli(args)
    except (OSError,ValueError,KeyError,TypeError) as ex:
        # Avoid dumping raw private build text and model messages in stderr.
        if isinstance(ex,AgentProtocolError):
            print('ERROR:',ex.code,ex.details,file=sys.stderr)
        else:
            print('ERROR:',type(ex).__name__,file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
