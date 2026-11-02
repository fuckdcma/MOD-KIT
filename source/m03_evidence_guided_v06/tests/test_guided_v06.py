"""v0.6 regression tests: guided evidence is build-only, not private answers."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import modstudio_m03 as m

ROOT=Path(__file__).resolve().parents[1]

class GuidedBriefTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rea=m.load_jsonl(ROOT/'AgentInput/rea_evidence.jsonl')
        cls.assets=m.load(ROOT/'Fixtures/build_assets_v03.json')['assets']
    def test_contains_source_qualified_both_classes(self):
        p=m.guided_evidence_brief(self.rea,self.assets)
        kinds={a['source_type'] for a in p['qualified_source_assets']}
        self.assertEqual(kinds,{'external_json','scriptable_object'})
        table=next(a for a in p['qualified_source_assets'] if a['source_type']=='scriptable_object')
        self.assertEqual(table['entry_key'],'menu.load')
        self.assertEqual(table['source_ref'],'sharedassets0.assets#path_id=16')
    def test_unknown_tmp_is_not_prefab_proof(self):
        p=m.guided_evidence_brief(self.rea,self.assets)
        self.assertTrue(all(a['source_type']=='unknown' for a in p['ui_snapshots_without_provenance']))
        self.assertTrue(all(a['source_type']!='serialized_prefab' for a in p['qualified_source_assets']))
    def test_cil_methods_and_format_present(self):
        p=m.guided_evidence_brief(self.rea,self.assets)
        methods={r['method']:r for r in p['relevant_methods']}
        self.assertIn('ModStudioLab.RuntimeTextExample.Refresh',methods)
        self.assertIn('Health: {0}/100',[x['text'] for x in methods['ModStudioLab.RuntimeTextExample.Refresh']['literals']])
        self.assertIn('ModStudioLab.TableTextExample.Start',methods)
        self.assertIn('ModStudioLab.TableTextExample..ctor',methods)
    def test_diagnostic_marked_not_removed(self):
        p=m.guided_evidence_brief(self.rea,self.assets)
        r=next(x for x in p['relevant_methods'] if x['method']=='ModStudioLab.HardcodedTextExample.Awake')
        d=next(x for x in r['literals'] if 'missing label' in x['text'])
        self.assertTrue(d['diagnostic_candidate'])
    def test_brief_never_loads_editor_reference_or_private_csv(self):
        p=m.guided_evidence_brief(self.rea,self.assets)
        encoded=json.dumps(p,ensure_ascii=False)
        self.assertNotIn('Assets/Prefabs/Prefab_NewGame.prefab',encoded)
        self.assertNotIn('ground_truth_v01.csv',encoded)
        self.assertNotIn('T001',encoded)
    def test_bounded_brief(self):
        bloated=self.assets*200
        p=m.guided_evidence_brief(self.rea,bloated,max_chars=7600)
        self.assertLess(len(json.dumps(p,ensure_ascii=False,separators=(',',':'))),7900)
        self.assertTrue(p['coverage']['truncated'])
    def test_source_class_not_inferred_from_unknown(self):
        wrong={'text':'New Game','source_type':'serialized_prefab','method':'',
             'source_ref':'level0#path_id=35','evidence_type':'asset_text',
             'evidence_value':'New Game','confidence':'observed'}
        result=m.validate_observations([wrong],self.rea,self.assets)
        self.assertEqual(result[0]['validation_status'],'rejected')

class GuidedStrategyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rea=m.load_jsonl(ROOT/'AgentInput/rea_evidence.jsonl')
        cls.assets=m.load(ROOT/'Fixtures/build_assets_v03.json')['assets']
    def test_immediate_finish_receives_broad_evidence(self):
        collected=[]
        def mock_chat(server,model,messages,**kwargs):
            collected.append(messages)
            return {'action':'finish','observations':[]}
        with patch.object(m,'local_chat',side_effect=mock_chat):
            obs,trace,complete=m.run_guided_agent(self.rea,self.assets,'http://localhost:11434','qwen3.5:4b')
        self.assertTrue(complete)
        self.assertEqual(len(obs),0)  # Controller MUST NOT synthesize answers!
        self.assertEqual(trace[0]['action'],'controller_evidence_brief')
        self.assertGreaterEqual(trace[0]['methods_included'],4)
        self.assertEqual(trace[0]['qualified_sources_included'],2)
        self.assertTrue('qualified_source_assets' in collected[0][1]['content'])
    def test_model_results_validated_not_auto_promoted(self):
        mock=[{'text':'Quest Completed','source_type':'hardcoded_managed',
           'method':'ModStudioLab.HardcodedTextExample.Awake','source_ref':'0x70000221',
           'evidence_type':'il_literal','evidence_value':'Quest Completed','confidence':'observed'},
           {'text':'[ModStudioLab] HardcodedTextExample: missing label.',
           'source_type':'hardcoded_managed','method':'ModStudioLab.HardcodedTextExample.Awake',
           'source_ref':'0x70000241','evidence_type':'il_literal',
           'evidence_value':'[ModStudioLab] HardcodedTextExample: missing label.',
           'confidence':'observed'}]
        with patch.object(m,'local_chat',return_value={'action':'finish','observations':mock}):
            obs,trace,complete=m.run_guided_agent(self.rea,self.assets,'http://localhost:11434','qwen3.5:4b')
        statuses=[x['validation_status'] for x in m.validate_observations(obs,self.rea,self.assets)]
        self.assertTrue(complete)
        self.assertEqual(statuses,['observed','candidate_only'])
    def test_trace_says_guided_not_autonomous(self):
        with patch.object(m,'local_chat',return_value={'action':'finish','observations':[]}):
            _,trace,_=m.run_guided_agent(self.rea,self.assets,'http://localhost:11434','qwen3.5:4b')
        self.assertEqual(trace[-1]['strategy'],'guided_model_synthesis')
    def test_retries_and_stops_if_model_empty(self):
        with patch.object(m,'local_chat',side_effect=m.ModelResponseError('empty_content','stop')):
            _,trace,complete=m.run_guided_agent(self.rea,self.assets,'http://localhost:11434','qwen3.5:4b',max_steps=2)
        self.assertFalse(complete)
        self.assertEqual(len([x for x in trace if x.get('code')=='empty_content']),3)
    def test_tools_can_still_be_invoked(self):
        responses=iter([{'action':'search_literals','query':'Health'},
                        {'action':'finish','observations':[]}])
        with patch.object(m,'local_chat',side_effect=lambda *a,**k:next(responses)):
            _,trace,done=m.run_guided_agent(self.rea,self.assets,'http://localhost:11434','qwen3.5:4b',max_steps=3)
        self.assertTrue(done)
        self.assertEqual(trace[1]['action'],'search_literals')
        self.assertEqual(trace[2]['action'],'finish')
    def test_max_steps_not_false_completion(self):
        with patch.object(m,'local_chat',return_value={'action':'list_methods','query':''}):
            _,trace,done=m.run_guided_agent(self.rea,self.assets,'http://localhost:11434','qwen3.5:4b',max_steps=1)
        self.assertFalse(done)
        self.assertEqual(trace[-1]['action'],'max_steps_reached')
    def test_diagnostic_candidate_does_not_raise_evaluation_score(self):
        row={'text':'[ModStudioLab] HardcodedTextExample: missing label.',
             'source_type':'hardcoded_managed','method':'ModStudioLab.HardcodedTextExample.Awake',
             'source_ref':'0x70000241','evidence_type':'il_literal',
             'evidence_value':'[ModStudioLab] HardcodedTextExample: missing label.'}
        records=m.validate_observations([row],self.rea,self.assets)
        self.assertEqual(records[0]['validation_status'],'candidate_only')
    def test_baseline_evaluation_still_three_exact_one_template(self):
        obs=m.baseline(self.rea)+m.baseline_asset_observations(self.assets,self.rea)
        valid=m.validate_observations(obs,self.rea,self.assets)
        result=m.evaluate(valid,ROOT/'PrivateEvaluation/ground_truth_v01.csv')
        self.assertEqual((result['exact_text_and_source_proven'],result['format_template_and_source_proven'],result['unproven']),(3,1,1))

if __name__=='__main__':unittest.main()
