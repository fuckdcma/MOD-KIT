import json
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import modstudio_m03 as m

ROOT=Path(__file__).resolve().parents[1]
REA=ROOT/'AgentInput'/'rea_evidence.jsonl'
GT=ROOT/'PrivateEvaluation'/'ground_truth_v01.csv'

class TestM03(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.items=m.load_jsonl(REA)
    def test_sha_and_inventory(self):
        self.assertEqual(m.verify_rea_evidence(self.items),'ab9cf9e569815b6d1d1f49dbc455521bb426b6118b891c8c0a3052244d24a29e')
        self.assertEqual(len(self.items),6)
    def test_baseline_and_proof(self):
        b=m.validate_observations(m.baseline(self.items),self.items)
        self.assertEqual(len(b),4)
        self.assertEqual(sum(x['validation_status']=='observed' for x in b),2)
        self.assertEqual(sum(x['validation_status']=='hypothesis' for x in b),2)
    def test_fake_lit_rejected(self):
        x={'text':'New Game','source_type':'hardcoded_managed','method':'ModStudioLab.HardcodedTextExample.Awake',
           'source_ref':'','evidence_type':'il_literal','evidence_value':'New Game'}
        z=m.validate_observations([x],self.items)
        self.assertEqual(z[0]['validation_status'],'rejected')
    def test_eval_honesty(self):
        b=m.validate_observations(m.baseline(self.items),self.items)
        result=m.evaluate(b,GT)
        self.assertEqual(result['total_cases'],5)
        self.assertEqual(result['exact_text_and_source_proven'],1)
        self.assertEqual(result['format_template_and_source_proven'],1)
        self.assertEqual(result['unproven'],3)
    def test_localhost_only(self):
        with self.assertRaises(ValueError): m.local_chat('https://api.external.com','test',[])
    def test_prepare_from_actual_rea(self):
        parent=ROOT.parents[0]
        members=parent/'members.json'
        artifact=parent/'assembly_identity.json'
        if members.exists() and artifact.exists():
            converted=m.prepare_rea_members(m.load(members),m.load(artifact))
            self.assertEqual(len(converted),16)
            self.assertEqual(m.verify_rea_evidence(converted),m.verify_rea_evidence(self.items))
            self.assertTrue(any('Quest Completed' in m.literals_for(r) for r in converted))
    def test_tool_access(self):
        p=m.tool_result('search_literals',{'query':'Quest Completed'},self.items,[])
        self.assertEqual(len(p),1)
        self.assertEqual(p[0]['literal'],'Quest Completed')

if __name__=='__main__': unittest.main()