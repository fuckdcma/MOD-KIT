"""v0.8 semantic checks: protect observed status from incorrect source attribution.

All fixtures are read-only local REA+Unity evidence; no live model calls.
"""
import contextlib
import io
import json
import tempfile
import unittest
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import modstudio_m03 as m

ROOT = Path(__file__).resolve().parents[1]


class SemanticConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rea = m.load_jsonl(ROOT / 'AgentInput' / 'rea_evidence.jsonl')
        cls.assets = m.load(ROOT / 'Fixtures' / 'build_assets_v03.json')['assets']
        cls.methods = {r['method']:r for r in cls.rea}

    def il(self, method, text, stype='hardcoded_managed'):
        return {'method':method, 'text':text, 'source_type':stype,
                'source_ref':method, 'evidence_type':'il_literal',
                'evidence_value':text, 'confidence':'observed'}

    def status(self, item):
        return m.validate_observations([item],self.rea,self.assets)[0]['validation_status']

    def test_template_as_hardcoded_not_accepted(self):
        r=self.il('ModStudioLab.RuntimeTextExample.Refresh','Health: {0}/100')
        self.assertEqual(self.status(r),'candidate_only')

    def test_correct_dynamic_template_accepted(self):
        r=self.il('ModStudioLab.RuntimeTextExample.Refresh','Health: {0}/100','runtime_generated')
        self.assertEqual(self.status(r),'observed')

    def test_static_hardcoded_text_still_accepted(self):
        r=self.il('ModStudioLab.HardcodedTextExample.Awake','Quest Completed')
        self.assertEqual(self.status(r),'observed')

    def test_diagnostic_is_candidate_only(self):
        r=self.il('ModStudioLab.HardcodedTextExample.Awake','[ModStudioLab] HardcodedTextExample: missing label.')
        self.assertEqual(self.status(r),'candidate_only')

    def test_lookup_key_not_ui_proof(self):
        r=self.il('ModStudioLab.TableTextExample..ctor','menu.load')
        self.assertEqual(self.status(r),'candidate_only')

    def test_il_literal_cannot_claim_scriptable_source(self):
        r=self.il('ModStudioLab.HardcodedTextExample.Awake','Quest Completed','scriptable_object')
        self.assertEqual(self.status(r),'candidate_only')

    def test_il_literal_cannot_claim_prefab(self):
        r=self.il('ModStudioLab.HardcodedTextExample.Awake','Quest Completed','serialized_prefab')
        self.assertEqual(self.status(r),'candidate_only')

    def test_missing_il_literal_rejected(self):
        r=self.il('ModStudioLab.HardcodedTextExample.Awake','Not in the assembly')
        self.assertEqual(self.status(r),'rejected')

    def test_dynamic_without_formatter_not_promoted(self):
        r=self.il('ModStudioLab.HardcodedTextExample.Awake','Quest Completed','runtime_generated')
        self.assertEqual(self.status(r),'candidate_only')

    def test_literal_braces_without_formatter_not_forcibly_dynamic(self):
        # A hardcoded placeholder can be rendered literally: don't apply the
        # formatter rule without an observed String.Format call.
        method='Example.Label.Awake'
        evidence={'method':method, 'method_token':'0x0600ABCD',
                  'assembly_sha256':'a'*64,'evidence_kind':'rea_managed_static',
                  'strings_loaded_by_method':[{'literal':'Literal {0}'}],
                  'call_targets':[{'target':'TMPro.TMP_Text.set_text'}]}
        result=m.validate_observations([self.il(method,'Literal {0}')],[evidence],[])
        self.assertEqual(result[0]['validation_status'],'observed')

    def test_wrong_type_not_counted_for_template(self):
        r=self.il('ModStudioLab.RuntimeTextExample.Refresh','Health: {0}/100')
        record=m.validate_observations([r],self.rea,self.assets)
        ev=m.evaluate(record,ROOT/'PrivateEvaluation'/'ground_truth_v01.csv')
        self.assertEqual(ev['format_template_and_source_proven'],0)
        self.assertEqual(ev['exact_text_and_source_proven'],0)

    def test_static_baseline_remains_three_plus_one(self):
        obs=m.baseline(self.rea)+m.baseline_asset_observations(self.assets,self.rea)
        val=m.validate_observations(obs,self.rea,self.assets)
        ev=m.evaluate(val,ROOT/'PrivateEvaluation'/'ground_truth_v01.csv')
        self.assertEqual((ev['exact_text_and_source_proven'],
                          ev['format_template_and_source_proven'],ev['unproven']), (3,1,1))

    def test_conservative_replay_guided_three_exact_zero_template(self):
        # Mirror v0.7's observed source categories without relying on any
        # privileged Editor/ground-truth records in model input.
        rows=[
            {'text':'Hello, Commander','source_type':'external_json','source_ref':'resources.assets#path_id=9',
             'evidence_type':'asset_text','evidence_value':'Hello, Commander'},
            self.il('ModStudioLab.HardcodedTextExample.Awake','Quest Completed'),
            self.il('ModStudioLab.RuntimeTextExample.Refresh','Health: {0}/100'),
            {'text':'Load Game','source_type':'scriptable_object','source_ref':'sharedassets0.assets#path_id=16',
             'evidence_type':'asset_text','evidence_value':'Load Game'}
        ]
        val=m.validate_observations(rows,self.rea,self.assets)
        self.assertEqual([r['validation_status'] for r in val],
                         ['observed','observed','candidate_only','observed'])
        ev=m.evaluate(val,ROOT/'PrivateEvaluation'/'ground_truth_v01.csv')
        self.assertEqual((ev['exact_text_and_source_proven'],
                          ev['format_template_and_source_proven'],ev['unproven']),(3,0,2))

    def test_guided_prompt_explains_format_vs_hardcoded(self):
        self.assertIn('String.Format',m.GUIDED_SYSTEM)
        self.assertIn('runtime_generated',m.GUIDED_SYSTEM)
        self.assertIn('diagnostic',m.GUIDED_SYSTEM.lower())
        self.assertIn('prefab',m.GUIDED_SYSTEM.lower())

    def test_guided_does_not_inject_evaluator_knowledge(self):
        seen=[]
        def fake(server,model,messages,**kwargs):
            seen.extend(messages)
            return {'action':'finish','observations':[]}
        with patch.object(m,'local_chat',side_effect=fake):
            _,trace,complete=m.run_guided_agent(self.rea,self.assets,'http://127.0.0.1:11434','qwen3.5:4b')
        self.assertTrue(complete)
        content=json.dumps(seen,ensure_ascii=False)
        self.assertIn('System.String.Format',content)
        self.assertNotIn('ground_truth_v01.csv',content)
        self.assertNotIn('T001',content)

    def test_cli_evaluation_prints_scores_not_zero_observations(self):
        r=self.il('ModStudioLab.HardcodedTextExample.Awake','Quest Completed')
        with tempfile.TemporaryDirectory() as tmp:
            report=Path(tmp)/'report.json'; result=Path(tmp)/'score.json'
            m.dump(report,{'mode':'agent','completed':True,
                    'observations':m.validate_observations([r],self.rea,self.assets)})
            stream=io.StringIO()
            with contextlib.redirect_stdout(stream):
                ret=m.main(['evaluate','--observations',str(report),
                    '--truth',str(ROOT/'PrivateEvaluation'/'ground_truth_v01.csv'),'--out',str(result)])
            self.assertEqual(ret,0)
            printed=json.loads(stream.getvalue())
            self.assertEqual(printed['exact_text_and_source_proven'],1)
            self.assertEqual(printed['total_cases'],5)
            self.assertNotIn('observations',printed)
            self.assertEqual(m.load(result)['exact_text_and_source_proven'],1)


if __name__ == '__main__':
    unittest.main()
