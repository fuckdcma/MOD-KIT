import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SRC=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('m04_score_v10_regression',SRC/'src'/'score_v10_regression.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

class ScoreRegressionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        cases=[dict(case_id=f'T{i:02}',is_positive=True,origin_kind='managed',
                    text=f'UI_{i:02}',template='',expected_source_type='hardcoded_managed') for i in range(15)]
        cases.extend(dict(case_id=f'N{i:02}',is_positive=False,origin_kind='negative_log',
                          text=f'LOG_{i:02}',template='',expected_source_type='hardcoded_managed') for i in range(5))
        self.truth=self.root/'truth.json'
        self.truth.write_text(json.dumps({'schema':'modstudio.m04.private_truth.v0.1', 'eval_id':'SYNTHETIC_ONLY', 'cases':cases}),encoding='utf-8')
        self.fp={'assembly_sha256':'a'*64,'rea_input_sha256':'b'*64,'assets_input_sha256':'c'*64}
        self.reports=[]
        for i in range(1,4):
            p=self.root/f'evidence_r{i:02}.json'
            valid=dict(text='UI_01',source_type='hardcoded_managed',method='Some.Case.Start',source_ref='Some.Case.Start',
                       evidence_type='il_literal',evidence_value='UI_01',confidence='observed',validation_status='observed')
            negative=dict(valid,text='LOG_01',evidence_value='LOG_01')
            data={'mode':'agent','completed':True,'strategy':mod.EXPECTED_STRATEGY,
                  'assembly_sha256':'a'*64,'evidence_catalog_count':10,
                  'observations':[valid,negative],
                  'trace':[{'action':'catalog_preflight'},{'action':'finish'}]}
            p.write_text(json.dumps(data),encoding='utf-8');self.reports.append(p)
        self.lock=self.root/'private'/'lock'
        self.lock.parent.mkdir()
        self.private=self.root/'private'/'metrics_private.json'
        self.aggregate=self.root/'public'/'metrics_aggregate.json'
    def run_score(self):
        return mod.evaluate(self.truth,self.reports,self.fp,self.lock,self.private,self.aggregate,'d'*64,'e'*64)
    def edit(self,i,fn):
        r=json.loads(self.reports[i].read_text());fn(r)
        self.reports[i].write_text(json.dumps(r),encoding='utf-8')
    def test_scoring_uses_v02_contract_and_locks_sha(self):
        result=self.run_score();self.assertEqual(result['runs'],3)
        pub=json.loads(self.aggregate.read_text());self.assertEqual(pub['runs'][0]['source_and_text_matches'],1)
        self.assertEqual(pub['runs'][0]['observed_supported_matches'],1)
        self.assertEqual(pub['runs'][0]['false_positive_claims'],1)
        self.assertEqual(pub['runs'][1]['observed_supported_matches'],1)
        self.assertEqual(pub['runs'][0]['report_sha256'],mod.sha_file(self.reports[0]))
        self.assertEqual(mod.sha_file(self.reports[2]),mod.sha_file(self.lock/'evidence_r03.json'))
        self.assertNotIn('per_case_PRIVATE', self.aggregate.read_text())
        self.assertNotIn('false_positives_PRIVATE', self.aggregate.read_text())
        self.assertNotIn('UI_01', self.aggregate.read_text())
        self.assertNotIn('LOG_01', self.aggregate.read_text())
        self.assertIn('per_case_PRIVATE',self.private.read_text())
    def test_no_overwrite_even_after_success(self):
        self.run_score()
        with self.assertRaises(FileExistsError): self.run_score()
    def test_three_required(self):
        with self.assertRaises(ValueError):mod.check_reports(self.reports[:2],'a'*64)
    def test_name_order_required(self):
        with self.assertRaises(ValueError):mod.check_reports(list(reversed(self.reports)),'a'*64)
    def test_incomplete_rejected(self):
        self.edit(0,lambda r:r.update(completed=False))
        with self.assertRaises(ValueError):self.run_score()
        self.assertFalse(self.aggregate.exists())
    def test_wrong_strategy_rejected(self):
        self.edit(0,lambda r:r.update(strategy='autonomous'))
        with self.assertRaises(ValueError):self.run_score()
    def test_wrong_assembly_rejected(self):
        self.edit(0,lambda r:r.update(assembly_sha256='bad'))
        with self.assertRaises(ValueError):self.run_score()
    def test_unvalidated_claim_rejected(self):
        self.edit(0,lambda r:r['observations'][0].update(validation_status='rejected'))
        with self.assertRaises(ValueError):self.run_score()
    def test_wrong_confidence_rejected(self):
        self.edit(0,lambda r:r['observations'][0].update(confidence='hypothesis'))
        with self.assertRaises(ValueError):self.run_score()
    def test_missing_finish_rejected(self):
        self.edit(0,lambda r:r['trace'][-1].update(action='inspect'))
        with self.assertRaises(ValueError):self.run_score()
    def test_protocol_error_rejected(self):
        self.edit(0,lambda r:r['trace'].insert(0,{'status':'model_protocol_error','code':'invalid_selection'}))
        with self.assertRaises(ValueError):self.run_score()
    def test_catalog_count_diff_rejected(self):
        self.edit(0,lambda r:r.update(evidence_catalog_count=9))
        with self.assertRaises(ValueError):self.run_score()
    def test_no_traces_or_input_strings_in_public(self):
        self.run_score()
        doc=json.loads(self.aggregate.read_text())
        for row in doc['runs']:
            self.assertNotIn('trace',row)
            self.assertNotIn('observations',row)
        self.assertEqual(doc['study_type'],'EXPOSED_B_INTEGRATION_REGRESSION_NOT_BLIND')
    def test_score_contract_file_unchanged(self):
        vendor=SRC/'vendor'/'m04_evaluate_v02.py'
        self.assertEqual(hashlib.sha256(vendor.read_bytes()).hexdigest(),
                         '77de1425502c5912e972c873c0d96ba177140e77036d113d8e617522af9f69df')
        self.assertTrue(mod.load_frozen_scorer().score_one)

if __name__=='__main__': unittest.main()
