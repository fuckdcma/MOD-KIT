"""Synthetic-only QA. No user case text, seed or game data."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / 'src' / 'm04_evaluate_v02.py'
spec=importlib.util.spec_from_file_location('scorer_v02',MODULE_PATH)
scorer=importlib.util.module_from_spec(spec)
spec.loader.exec_module(scorer)


def truth():
    rows=[]
    for i in range(15):
        rows.append({'case_id':f'P{i:02}','origin_kind':'hardcoded', 'expected_source_type':'hardcoded_managed',
                     'is_positive':True,'text':f'SYNTHETIC_POS_{i}','template':''})
    for i in range(5):
        rows.append({'case_id':f'N{i:02}','origin_kind':'negative_log','expected_source_type':'negative_non_ui',
                     'is_positive':False,'text':f'SYNTHETIC_NEG_{i}','template':''})
    return {'schema':'modstudio.m04.private_truth.v0.1','eval_id':'SYNTHETIC','cases':rows}


def obs(status='observed',text='SYNTHETIC_POS_0',source='hardcoded_managed',confidence='observed'):
    return {'text':text,'source_type':source,'validation_status':status,'confidence':confidence,
            'evidence_type':'il_literal','evidence_value':text,'source_ref':'A.B','method':'A.B'}


def report(items,mode='agent',strategy='guided',complete=True):
    return {'mode':mode,'strategy':strategy,'completed':complete,'observations':items,'assembly_sha256':'a'*64,'trace':[]}


class MixedScoreTests(unittest.TestCase):
    def test_v01_false_support_rejected_confidence_is_blocked(self):
        s=scorer.score_one(truth(),report([obs(status='rejected')]))
        self.assertEqual(s['source_and_text_matches'],1)
        self.assertEqual(s['observed_supported_matches'],0)

    def test_validated_observed_supported(self):
        s=scorer.score_one(truth(),report([obs()]))
        self.assertEqual(s['observed_supported_matches'],1)

    def test_candidate_only_confidence_not_enough(self):
        s=scorer.score_one(truth(),report([obs(status='candidate_only')]))
        self.assertEqual(s['observed_supported_matches'],0)

    def test_prefer_validated_hit_over_rejected_hit(self):
        s=scorer.score_one(truth(),report([obs('rejected'),obs('observed')]))
        self.assertEqual(s['observed_supported_matches'],1)
        self.assertEqual(s['per_case_PRIVATE'][0]['observation_index'],1)

    def test_source_mismatch_not_matched(self):
        s=scorer.score_one(truth(),report([obs(source='scriptable_object')]))
        self.assertEqual(s['source_and_text_matches'],0)

    def test_incomplete_report_not_scored(self):
        with self.assertRaisesRegex(ValueError,'Incomplete'):
            scorer.score_one(truth(),report([obs()],complete=False))

    def test_private_lock_and_public_no_case_strings(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            priv=root/'PRIVATE_DO_NOT_UPLOAD';priv.mkdir()
            pub=root/'Runs_MIXED_SCORE_LOCAL';pub.mkdir()
            gt=priv/'ground_truth_PRIVATE.json'; gt.write_text(json.dumps(truth()),encoding='utf-8')
            reports=[]
            for strategy in ('baseline','guided','autonomous'):
                count=1 if strategy=='baseline' else 3
                for i in range(1,count+1):
                    name=f'{strategy}_r{i:02}'
                    file=root/f'{name}.json'
                    mode='baseline' if strategy=='baseline' else 'agent'
                    value=report([obs()],mode,strategy if strategy!='baseline' else 'static_baseline')
                    file.write_text(json.dumps(value),encoding='utf-8')
                    reports.append((name,file))
            lock=priv/'locked'; private_out=priv/'private_metrics.json';public_out=pub/'agg.json'
            result=scorer.evaluate_and_lock(gt,reports,lock,private_out,public_out)
            self.assertEqual(len(result['runs']),7)
            self.assertEqual(len(list(lock.glob('*.json'))),7)
            self.assertEqual(result['study_type'],'EXPLORATORY_MIXED_VERSION_NOT_ORIGINAL_V08_BENCHMARK')
            self.assertEqual(result['runs'][1]['version'],'M03_Guided_v08_FROZEN')
            self.assertEqual(result['runs'][4]['version'],'M04_Autonomous_Bounded_v09_EXPERIMENTAL')
            public_text=public_out.read_text(encoding='utf-8')
            self.assertNotIn('SYNTHETIC_POS_0',public_text)
            self.assertNotIn('per_case_PRIVATE',public_text)
            self.assertNotIn('false_positives_PRIVATE',public_text)
            self.assertIn('SYNTHETIC',private_out.read_text(encoding='utf-8'))
            with self.assertRaises(FileExistsError):
                scorer.evaluate_and_lock(gt,reports,lock,priv/'other.json',pub/'other.json')

    def test_negative_false_positive_stays_detected(self):
        s=scorer.score_one(truth(),report([obs(text='SYNTHETIC_NEG_2')]))
        self.assertEqual(s['false_positive_claims'],1)


if __name__=='__main__': unittest.main()
