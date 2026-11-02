#!/usr/bin/env python3
"""Generate a locally secret 20-case Unity Mono provenance holdout.

The distributable ZIP and public GitHub source contain NO generated seed, text, or answer key.
Do not upload the generated ProjectSettings spec, Unity source, or private answer key
before all model predictions have been frozen and scored.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import hmac
import json
import random
import secrets
import shutil
import sys
from collections import Counter
from pathlib import Path

CATEGORIES = (['prefab'] * 3 + ['table'] * 3 + ['hardcoded'] * 3 +
              ['runtime'] * 3 + ['json'] * 3 +
              ['negative_log', 'negative_duplicate', 'negative_table',
               'negative_json', 'negative_unused'])
POSITIVE = {'prefab', 'table', 'hardcoded', 'runtime', 'json'}
EXPECTED = {'prefab': 'serialized_prefab', 'table': 'scriptable_object',
            'hardcoded': 'hardcoded_managed', 'runtime': 'runtime_generated',
            'json': 'external_json'}


def _tag(seed: bytes, label: str) -> str:
    return hmac.new(seed, label.encode('ascii'), hashlib.sha256).hexdigest()[:10].upper()


def csharp_string(value: str) -> str:
    """JSON quoted ASCII is also a valid C# string literal for our constrained text."""
    return json.dumps(value, ensure_ascii=True)


def make_cases(seed: bytes):
    if not isinstance(seed, bytes) or len(seed) != 32:
        raise ValueError('A fresh 256-bit binary seed is required')
    types = CATEGORIES.copy()
    random.Random(int.from_bytes(hashlib.sha256(seed + b'order').digest(), 'big')).shuffle(types)
    first_hardcoded = None
    rows = []
    slots = Counter()
    for n, kind in enumerate(types, 1):
        cid = f'B{n:03d}'
        code = _tag(seed, f'{cid}:{kind}')
        index = slots[kind]
        slots[kind] += 1
        row = dict(case_id=cid, kind=kind, text='', template='', key='',
                   resource_name='', kind_index=index, arg0=0, arg1=0)
        if kind == 'prefab':
            row['text'] = ('Continue mission', 'Mở giao diện', 'Inspect sector')[index] + ' ' + code
        elif kind == 'table':
            row['key'] = 'ui.' + _tag(seed, cid + ':key').lower()
            row['text'] = ('Inventory ready', 'Mở bản đồ', 'Captain briefing')[index] + ' ' + code
        elif kind == 'hardcoded':
            row['text'] = ('Quest notice', 'Security checkpoint', 'Nhiệm vụ mới')[index] + ' ' + code
            if first_hardcoded is None:
                first_hardcoded = row['text']
        elif kind == 'runtime':
            row['template'] = ('Fuel {0}/{1}', 'Tài nguyên {0}/{1}', 'Units: {0} of {1}')[index] + ' ' + code
            row['arg0'] = 17 + n
            row['arg1'] = 80 + n
            row['text'] = row['template'].format(row['arg0'], row['arg1'])
        elif kind == 'json':
            row['key'] = 'dialogue.' + _tag(seed, cid + ':key').lower()
            row['resource_name'] = f'm04_payload_{cid.lower()}'
            row['text'] = ('Hello navigator', 'Lệnh mới', 'Warning received')[index] + ' ' + code
        elif kind == 'negative_log':
            row['text'] = 'WARN_ONLY ' + code
        elif kind == 'negative_duplicate':
            # Copy a real visible UI text to a log-only call: string alone cannot prove UI origin.
            row['text'] = ''
        elif kind == 'negative_table':
            row['key'] = 'unused.' + _tag(seed, cid + ':key').lower()
            row['text'] = 'ORPHAN_TABLE ' + code
        elif kind == 'negative_json':
            row['key'] = 'unused.json.' + code.lower()
            row['resource_name'] = f'm04_orphan_{cid.lower()}'
            row['text'] = 'ORPHAN_JSON ' + code
        elif kind == 'negative_unused':
            row['text'] = 'UNUSED_IL ' + code
        rows.append(row)
    assert first_hardcoded is not None
    for row in rows:
        if row['kind'] == 'negative_duplicate':
            row['text'] = first_hardcoded
    return rows


def _assert_not_in_git_tree(path: Path, label: str):
    for ancestor in (path, *path.parents):
        if (ancestor / '.git').exists():
            raise ValueError(f'{label} must not be under a Git repository: {ancestor}')


def _make_hardcoded(rows):
    data = sorted((r for r in rows if r['kind'] == 'hardcoded'), key=lambda x: x['kind_index'])
    body = '\n'.join(f'            Write{r["kind_index"]}();' for r in data)
    methods = '\n'.join(
        f'        private void Write{r["kind_index"]}() {{ if (labels != null && labels.Length > {r["kind_index"]} && labels[{r["kind_index"]}] != null) labels[{r["kind_index"]}].text = {csharp_string(r["text"])}; }}'
        for r in data)
    return ('// AUTO-GENERATED LOCALLY; PRIVATE HOLDOUT SOURCE. DO NOT COMMIT.\n'
            'using UnityEngine;\nusing TMPro;\nnamespace ModStudioM04 {\n'
            '  public sealed class M04HardcodedWriter : MonoBehaviour {\n'
            '    public TMP_Text[] labels;\n'
            f'    private void Start() {{\n{body}\n    }}\n{methods}\n'
            '  }\n}\n')


def _make_runtime(rows):
    data = sorted((r for r in rows if r['kind'] == 'runtime'), key=lambda x: x['kind_index'])
    body = '\n'.join(f'            Refresh{r["kind_index"]}();' for r in data)
    methods = '\n'.join(
        f'        private void Refresh{r["kind_index"]}() {{ if (labels != null && labels.Length > {r["kind_index"]} && labels[{r["kind_index"]}] != null) labels[{r["kind_index"]}].text = string.Format(System.Globalization.CultureInfo.InvariantCulture, {csharp_string(r["template"])}, {r["arg0"]}, {r["arg1"]}); }}'
        for r in data)
    return ('// AUTO-GENERATED LOCALLY; PRIVATE HOLDOUT SOURCE. DO NOT COMMIT.\n'
            'using UnityEngine;\nusing TMPro;\nnamespace ModStudioM04 {\n'
            '  public sealed class M04RuntimeWriter : MonoBehaviour {\n'
            '    public TMP_Text[] labels;\n'
            f'    private void Start() {{\n{body}\n    }}\n{methods}\n'
            '  }\n}\n')


def _make_negatives(rows):
    logs = [r for r in rows if r['kind'] in ('negative_log', 'negative_duplicate')]
    unused = next(r for r in rows if r['kind'] == 'negative_unused')
    body = '\n'.join(f'       Debug.LogWarning({csharp_string(r["text"])});' for r in logs)
    return ('// AUTO-GENERATED LOCALLY; PRIVATE HOLDOUT SOURCE. DO NOT COMMIT.\n'
            'using UnityEngine;\nusing UnityEngine.Scripting;\nnamespace ModStudioM04 {\n'
            '  public sealed class M04DiagnosticWriter : MonoBehaviour {\n'
            f'    private void Start() {{\n{body}\n    }}\n'
            f'    [Preserve] public static string NeverUsedByUI() {{ return {csharp_string(unused["text"])}; }}\n'
            '  }\n}\n')


def truth_record(row):
    kind = row['kind']
    out = {'case_id': row['case_id'], 'is_positive': kind in POSITIVE,
           'origin_kind': kind, 'expected_source_type': EXPECTED.get(kind, 'negative_non_ui'),
           'text': row['text'], 'template': row['template'], 'key': row['key'],
           'resource_name': row['resource_name'],
           'expected_origin': ('Assets/M04/Prefabs/' + row['case_id'] + '.prefab' if kind=='prefab'
                               else ('M04Table.entries[*].value' if kind in ('table','negative_table')
                               else ('Resources/' + row['resource_name'] + '.json' if kind in ('json','negative_json')
                                     else 'Assembly-CSharp.dll:ModStudioM04'))),
           'verification': 'local_authoring_reference_not_runtime_proven'}
    return out


def _write_json(path: Path, object_):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(object_, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def generate(project: Path, private: Path, template_root: Path, *, seed: bytes | None = None):
    project = project.resolve()
    private = private.resolve()
    if not project.is_dir() or not (project / 'Assets').is_dir() or not (project / 'ProjectSettings/ProjectVersion.txt').is_file():
        raise ValueError('Create an EMPTY Unity project in Unity Hub first (Assets + ProjectSettings required).')
    if project.name.lower() != 'unitytextlabb':
        raise ValueError('Safety: use a separate project folder named UnityTextLabB (never the original UnityTextLab).')
    if private == project or project in private.parents:
        raise ValueError('Private answer directory MUST be outside the Unity project.')
    _assert_not_in_git_tree(project, 'Holdout Unity project')
    _assert_not_in_git_tree(private, 'Private answer directory')
    version=(project/'ProjectSettings/ProjectVersion.txt').read_text(encoding='utf-8-sig')
    if '6000.3.' not in version:
        raise ValueError('M04 v0.1 is scoped to Unity Editor 6000.3.x; selected project version differs.')
    generated_paths = [project/'Assets/M04/Runtime/M04GeneratedHardcoded.cs',
                       project/'Assets/M04/Runtime/M04GeneratedFormat.cs',
                       project/'Assets/M04/Runtime/M04GeneratedDiagnostics.cs',
                       project/'Assets/M04/Runtime/M04LabRuntime.cs',
                       project/'Assets/Editor/M04LabBuilder.cs',
                       project/'ProjectSettings/M04HoldoutLocal.json',
                       private/'ground_truth_PRIVATE.json',private/'seed_PRIVATE.hex',
                       private/'holdout_manifest_PRIVATE.json']
    if any(x.exists() for x in generated_paths):
        raise FileExistsError('M04 already initialized; refusing overwrite of seed, scene spec or private answers.')
    if not template_root.is_dir():
        raise ValueError('Missing UnityTemplate folder.')
    seed = seed if seed is not None else secrets.token_bytes(32)
    rows = make_cases(seed)
    eval_id = 'M04-' + _tag(seed, 'eval-id')
    spec = {'schema':'modstudio.m04.unseen_lab_spec.v0.1','eval_id':eval_id,'rows':rows}
    truth = {'schema':'modstudio.m04.private_truth.v0.1','eval_id':eval_id,
             'positive_count':15,'negative_count':5,'cases':[truth_record(r) for r in rows]}
    private.mkdir(parents=True, exist_ok=True)
    (private/'seed_PRIVATE.hex').write_text(seed.hex()+'\n', encoding='ascii')
    _write_json(private/'ground_truth_PRIVATE.json',truth)
    truth_sha=hashlib.sha256((private/'ground_truth_PRIVATE.json').read_bytes()).hexdigest()
    _write_json(private/'holdout_manifest_PRIVATE.json',
                {'eval_id':eval_id,'truth_sha256':truth_sha,'source':'local_private_generator',
                 'never_publish_seed_or_answer_key':True})
    for rel in ('Assets/M04/Runtime/M04LabRuntime.cs','Assets/Editor/M04LabBuilder.cs'):
        src = template_root / rel
        target = project / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src,target)
    path = project/'Assets/M04/Runtime'
    (path/'M04GeneratedHardcoded.cs').write_text(_make_hardcoded(rows),encoding='utf-8')
    (path/'M04GeneratedFormat.cs').write_text(_make_runtime(rows),encoding='utf-8')
    (path/'M04GeneratedDiagnostics.cs').write_text(_make_negatives(rows),encoding='utf-8')
    _write_json(project/'ProjectSettings/M04HoldoutLocal.json',spec)
    # Neither real text nor secret seed is included in this public, hash-only handoff.
    public = {'schema':'modstudio.m04.public_build_fingerprint.v0.1','eval_id':eval_id,
              'cases_total':20,'positives':15,'negatives':5,
              'private_ground_truth_sha256':truth_sha,
              'unity_editor_required':'6000.3.x',
              'warning':'No secret labels or answers in this file. The Unity project itself is PRIVATE.'}
    _write_json(private/'public_fingerprint_ONLY.json',public)
    return {'status':'created','eval_id':eval_id,'case_count':20,
            'unity_project':str(project), 'private_directory':str(private),
            'instructions':'Open project in Unity; import TMP Essentials; Tools > Mod Studio AI > M04 > Generate Unseen Lab B Scene.'}


def main(argv=None):
    ap=argparse.ArgumentParser(description='Create local PRIVATE UnityTextLabB holdout. Never publish outputs.')
    ap.add_argument('--project',required=True,type=Path)
    ap.add_argument('--private-dir',required=True,type=Path)
    args=ap.parse_args(argv)
    template_root=Path(__file__).resolve().parent.parent/'UnityTemplate'
    print(json.dumps(generate(args.project,args.private_dir,template_root),ensure_ascii=False,indent=2))
    return 0


if __name__=='__main__':
    try: sys.exit(main())
    except (ValueError,OSError) as exc:
        print('ERROR:',exc,file=sys.stderr)
        sys.exit(2)
