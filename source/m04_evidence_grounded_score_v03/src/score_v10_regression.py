#!/usr/bin/env python3
"""B-only exploratory regression scoring for completed, frozen v1.0 evidence-ID reports.

Reuses UNMODIFIED v0.2 scoring semantics, which require validator-observed support.
Never print private case values, source strings or entire observations.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

SCHEMA = 'modstudio.m04.v10.integration_regression_score.v0.3'
EXPECTED_STRATEGY = 'evidence_grounded_v10_experimental'
VERSION = 'M04_EvidenceGrounded_v10_EXPERIMENTAL_B_REGRESSION'


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    with path.open('r', encoding='utf-8-sig') as f:
        return json.load(f)


def load_frozen_scorer():
    original = Path(__file__).resolve().parents[1] / 'vendor' / 'm04_evaluate_v02.py'
    spec = importlib.util.spec_from_file_location('m04_score_contract_v02', original)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_reports(paths: list[Path], assembly_sha: str) -> list[dict]:
    if len(paths) != 3 or len(set(map(str, paths))) != 3:
        raise ValueError('Require exactly three distinct v1.0 report paths.')
    reports = []
    counts = set()
    for i, path in enumerate(paths, 1):
        if path.name != f'evidence_r{i:02}.json':
            raise ValueError('Report order/name mismatch; expected evidence_r01..r03.')
        r = load_json(path)
        if (r.get('completed') is not True or r.get('mode') != 'agent'
                or r.get('strategy') != EXPECTED_STRATEGY):
            raise ValueError('Incomplete or wrong strategy report; cannot score.')
        if r.get('assembly_sha256', '').lower() != assembly_sha.lower():
            raise ValueError('Assembly mismatch in report.')
        if not isinstance(r.get('observations'), list):
            raise ValueError('Missing observations array.')
        if not isinstance(r.get('evidence_catalog_count'), int) or r['evidence_catalog_count'] <= 0:
            raise ValueError('Invalid evidence catalog count.')
        counts.add(r['evidence_catalog_count'])
        if len(r['observations']) > r['evidence_catalog_count']:
            raise ValueError('Selected more observations than catalog candidates.')
        if any(not isinstance(o, dict) or o.get('validation_status') != 'observed'
               or o.get('confidence') != 'observed' for o in r['observations']):
            raise ValueError('Evidence-grounded report contains unsupported candidate.')
        trace = r.get('trace')
        if (not isinstance(trace, list) or not trace or trace[-1].get('action') != 'finish'
                or any(t.get('status') in ('model_protocol_error', 'transport_error') for t in trace)):
            raise ValueError('Invalid terminal trace state or model errors.')
        reports.append(r)
    if len(counts) != 1:
        raise ValueError('Candidate inventory count inconsistent across runs.')
    return reports


def evaluate(truth_path: Path, report_paths: list[Path], fingerprint: dict,
             lock_dir: Path, private_path: Path, aggregate_path: Path,
             v10_config_sha: str, v10_agent_sha: str) -> dict:
    # Fail before reading private ground truth on invalid report shape, if possible.
    for p in [truth_path, *report_paths]:
        if not p.is_file():
            raise FileNotFoundError('Required truth/report file missing.')
    for p in [lock_dir, private_path, aggregate_path]:
        if p.exists():
            raise FileExistsError('Output exists; never replace an old score/lock.')
    if (aggregate_path.parent.resolve() == private_path.parent.resolve()
            or lock_dir.parent.resolve() != private_path.parent.resolve()
            or aggregate_path.resolve() == truth_path.resolve()):
        raise ValueError('Private per-case files must be separate from aggregate output.')
    reports = check_reports(report_paths, fingerprint['assembly_sha256'])
    truth = load_json(truth_path)
    if truth.get('schema') != 'modstudio.m04.private_truth.v0.1' or len(truth.get('cases', [])) != 20:
        raise ValueError('Unexpected private M04 truth schema/case count.')
    scorer = load_frozen_scorer()
    private_rows, public_rows = [], []
    for i, (p, r) in enumerate(zip(report_paths, reports), 1):
        scored = scorer.score_one(truth, r)
        public = { 'run': f'evidence_r{i:02}', 'version': VERSION,
                   'report_sha256': sha_file(p),
                   **{k: v for k, v in scored.items() if not k.endswith('_PRIVATE')} }
        public_rows.append(public)
        private_rows.append({**public,
                             'per_case_PRIVATE': scored['per_case_PRIVATE'],
                             'false_positives_PRIVATE': scored['false_positives_PRIVATE']})
    agg = {'schema': SCHEMA, 'study_type': 'EXPOSED_B_INTEGRATION_REGRESSION_NOT_BLIND',
           'scoring_contract': 'Unmodified m04_evaluate_v02.py score_one',
           'truth_sha256': sha_file(truth_path),
           'v10_experiment_config_sha256': v10_config_sha,
           'v10_agent_sha256': v10_agent_sha,
           'sealed_rea_sha256': fingerprint['rea_input_sha256'],
           'sealed_assets_sha256': fingerprint['assets_input_sha256'],
           'runs': public_rows,
           'caveat': ('Observed static evidence is not proof of runtime UI setter dataflow. '
                      'B seed already inspected in earlier regressions; do not claim blind holdout. '
                      'M03 v0.8 operational failures remain separately recorded.')}
    private = {**agg, 'runs': private_rows,
               'privacy': 'PRIVATE DO NOT UPLOAD: per-case labels and negative strings'}
    # Lock exact run bytes in a PRIVATE folder; exclude text from aggregate output.
    lock_dir.mkdir(parents=False, exist_ok=False)
    for i, p in enumerate(report_paths, 1):
        dst = lock_dir / f'evidence_r{i:02}.json'
        shutil.copyfile(p, dst)
        if sha_file(dst) != sha_file(p):
            raise RuntimeError('Prediction freeze SHA-256 mismatch.')
    private_path.write_text(json.dumps(private, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    aggregate_path.parent.mkdir(parents=False, exist_ok=False)
    aggregate_path.write_text(json.dumps(agg, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {'status': 'scored', 'runs': len(report_paths), 'public_aggregate_only': str(aggregate_path)}


def main(argv=None):
    p = argparse.ArgumentParser(description='M04 v1.0 private B integration-regression scorer')
    p.add_argument('--truth', required=True, type=Path)
    p.add_argument('--report', action='append', required=True, type=Path)
    p.add_argument('--fingerprint', required=True, type=Path)
    p.add_argument('--lock-dir', required=True, type=Path)
    p.add_argument('--out-private', required=True, type=Path)
    p.add_argument('--out-aggregate', required=True, type=Path)
    p.add_argument('--v10-config-sha', required=True)
    p.add_argument('--v10-agent-sha', required=True)
    a = p.parse_args(argv)
    try:
        result = evaluate(a.truth, a.report, load_json(a.fingerprint), a.lock_dir,
                          a.out_private, a.out_aggregate, a.v10_config_sha, a.v10_agent_sha)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (OSError, ValueError, TypeError, KeyError, RuntimeError) as exc:
        # Do not print private candidate values, paths to truth or full exception payloads.
        print('SCORING FAILED: ' + type(exc).__name__, file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
