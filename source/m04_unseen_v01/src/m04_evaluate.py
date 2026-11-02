#!/usr/bin/env python3
"""Private M04 holdout scorer. Runs only AFTER all model outputs are locked.

Not a magic provenance oracle: type/text matches are reported separately from
observed build evidence; the latter still requires external reviewer inspection.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

SRC_TYPES = {'serialized_prefab', 'scriptable_object', 'hardcoded_managed',
             'runtime_generated', 'external_json'}


def sha_file(path: Path):
    h = hashlib.sha256()
    with path.open('rb') as reader:
        for b in iter(lambda: reader.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def load_json(path):
    with Path(path).open('r', encoding='utf-8-sig') as f:
        return json.load(f)


def _positive_matching(row, obs):
    expected = row['template'] if row['origin_kind'] == 'runtime' else row['text']
    return (obs.get('text') == expected and obs.get('source_type') == row['expected_source_type'])


def score_one(truth: dict, report: dict):
    if report.get('completed') is not True:
        raise ValueError('Incomplete Agent report cannot be evaluated.')
    if report.get('mode') not in ('agent', 'baseline'):
        raise ValueError('Not an M03 agent/baseline output.')
    observations = report.get('observations')
    if not isinstance(observations, list):
        raise ValueError('M03 observations must be an array.')
    positives = [r for r in truth['cases'] if r['is_positive']]
    negatives = [r for r in truth['cases'] if not r['is_positive']]
    matched_indices, matching = set(), []
    per_case=[]
    for case in positives:
        hits = [(i, o) for i, o in enumerate(observations)
                if isinstance(o, dict) and _positive_matching(case, o)]
        if not hits:
            per_case.append({'case_id':case['case_id'],'origin_kind':case['origin_kind'],
                             'text_source_match':False,'observed_supported':False})
            continue
        # Prefer a source-qualified match; do not rely solely on a text comparison.
        idx, selected = max(hits, key=lambda item: int(item[1].get('confidence') == 'observed'))
        matched_indices.add(idx)
        supported = (selected.get('confidence') == 'observed' and
                     bool(selected.get('evidence_type')) and
                     bool(selected.get('source_ref') or selected.get('method')))
        # UI scene snapshot alone cannot substantiate prefab origin.
        if case['origin_kind']=='prefab' and not (
                '.prefab' in str(selected.get('source_ref','')).lower() and
                'level' not in str(selected.get('source_ref','')).lower()):
            supported = False
        per_case.append({'case_id':case['case_id'],'origin_kind':case['origin_kind'],
                         'text_source_match':True,'observed_supported':supported,
                         'observation_index':idx,'confidence':selected.get('confidence','')})
        matching.append((case,selected))

    negative_texts = {r['text'] for r in negatives if r['origin_kind']!='negative_duplicate'}
    duplicate_texts = {r['text'] for r in negatives if r['origin_kind']=='negative_duplicate'}
    false_positives=[]
    undecidable_duplicate_count=0
    for i,o in enumerate(observations):
        if not isinstance(o,dict): continue
        val=o.get('text','')
        if val in negative_texts and o.get('source_type') in SRC_TYPES:
            false_positives.append({'index':i,'reason':'negative_control_non_ui','text':val})
        elif val in duplicate_texts and i not in matched_indices:
            # Same bytes as legitimate UI. Without logging method call provenance,
            # string equality cannot identify whether it is a false positive.
            if re.search(r'diagnostic|log|neverused',
                         str(o.get('method',''))+' '+str(o.get('source_ref','')), re.I):
                false_positives.append({'index':i,'reason':'log_only_duplicate','text':val})
            else:
                undecidable_duplicate_count += 1
        if o.get('source_type') == 'serialized_prefab' and 'level' in str(o.get('source_ref','')).lower():
            false_positives.append({'index':i,'reason':'scene_snapshot_claimed_as_prefab','text':val})
    return {
        'positive_total':len(positives),'negative_total':len(negatives),
        'source_and_text_matches':len(matching),
        'observed_supported_matches':sum(bool(x['observed_supported']) for x in per_case),
        'unmatched_positive':len(positives)-len(matching),
        'false_positive_claims':len(false_positives),
        'ambiguous_duplicate_observations':undecidable_duplicate_count,
        'observations_total':len(observations),
        'per_case_PRIVATE':per_case, 'false_positives_PRIVATE':false_positives,
        'caveat':'Method/asset-level confidence is NOT full runtime stack dataflow proof.'
    }


def evaluate_and_lock(truth_path: Path, named_reports: list, lock_dir: Path,
                      private_output: Path, public_output: Path):
    truth_path = truth_path.resolve()
    lock_dir = lock_dir.resolve()
    private_output = private_output.resolve()
    public_output = public_output.resolve()
    if truth_path == public_output or truth_path == private_output:
        raise ValueError('Outputs must not overwrite the private truth.')
    if public_output == private_output or private_output.parent == public_output.parent:
        raise ValueError('Keep per-case private score and aggregate public summary in separate folders.')
    if lock_dir.exists() and any(lock_dir.iterdir()):
        raise FileExistsError('Output lock directory already exists: never overwrite old model predictions.')
    truth=load_json(truth_path)
    if truth.get('schema')!='modstudio.m04.private_truth.v0.1' or len(truth.get('cases',[]))!=20:
        raise ValueError('Unsupported M04 private truth format.')
    if not named_reports:
        raise ValueError('Provide at least one named run.')
    prepared=[]
    for name,path in named_reports:
        if not re.fullmatch(r'(guided|autonomous|baseline)_r\d\d',name):
            raise ValueError('Run must be named guided_r01, autonomous_r02 or baseline_r01.')
        data = load_json(path)
        scores=score_one(truth,data)
        prepared.append((name,Path(path).resolve(),scores))
    if len(set(x[0] for x in prepared))!=len(prepared):
        raise ValueError('Duplicate run names.')
    lock_dir.mkdir(parents=True,exist_ok=False)
    private_runs=[]; public_runs=[]
    for name,path,metrics in prepared:
        dest=lock_dir/(name+'.json')
        shutil.copyfile(path,dest)
        original_sha=sha_file(path)
        if original_sha!=sha_file(dest):
            raise RuntimeError('Run freeze hash mismatch.')
        public_row={'run':name,'sha256':original_sha,
                    **{k:v for k,v in metrics.items() if not k.endswith('_PRIVATE')}}
        public_runs.append(public_row)
        private_runs.append({**public_row,
                             'per_case_PRIVATE':metrics['per_case_PRIVATE'],
                             'false_positives_PRIVATE':metrics['false_positives_PRIVATE']})
    private = {'schema':'modstudio.m04.private_eval.v0.1','eval_id':truth['eval_id'],
               'truth_sha256':sha_file(truth_path),'runs':private_runs}
    public = {'schema':'modstudio.m04.aggregate_eval.v0.1',
              'truth_sha256':sha_file(truth_path),
              'runs':public_runs,
              'warning':'No private answer strings or per-case labels. Public repo can carry this AFTER evaluation.'}
    private_output.parent.mkdir(parents=True,exist_ok=True)
    public_output.parent.mkdir(parents=True,exist_ok=True)
    private_output.write_text(json.dumps(private,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    public_output.write_text(json.dumps(public,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return public


def main(argv=None):
    p=argparse.ArgumentParser(description='PRIVATE post-freeze scorer for M04 Unity holdout')
    p.add_argument('--truth',type=Path,required=True)
    p.add_argument('--run',action='append',required=True,
                   help='strategy_rNN=path/to/M03/report.json; repeat for each report')
    p.add_argument('--lock-dir',type=Path,required=True)
    p.add_argument('--out-private',type=Path,required=True)
    p.add_argument('--out-public',type=Path,required=True)
    a=p.parse_args(argv)
    pairs=[]
    for value in a.run:
        if '=' not in value: p.error('--run requires NAME=PATH')
        name,path=value.split('=',1)
        pairs.append((name,Path(path)))
    result=evaluate_and_lock(a.truth,pairs,a.lock_dir,a.out_private,a.out_public)
    print(json.dumps({'status':'scored','runs':len(result['runs']),
                      'public_aggregate_only':str(a.out_public)},ensure_ascii=False))
    return 0


if __name__=='__main__':
    try: sys.exit(main())
    except (OSError,ValueError) as ex:
        print('ERROR:',ex,file=sys.stderr)
        sys.exit(2)
