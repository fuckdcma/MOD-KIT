import importlib.util
import json
import pathlib
import unittest
from unittest.mock import patch

ROOT=pathlib.Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('m03v09',ROOT/'src/modstudio_m03_v09.py')
mod=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def fixture(n=12):
    return [{'assembly_sha256':'a'*64,'method':f'Game.Text.Method{i}',
             'method_token':f'0x0600{i:04x}','evidence_kind':'rea_managed_static',
             'strings_loaded_by_method':[{'literal':f'Lab string #{i}','il_offset':0}],
             'call_targets':[{'target':'TMPro.TMP_Text.set_text'}]}
            for i in range(n)]


class BoundedAgentTests(unittest.TestCase):
    def test_ollama_native_context_and_output_budget_sent(self):
        class Reply:
            def __enter__(self): return self
            def __exit__(self,*args): return False
            def read(self,*args): return b'{}'
        # json.load is called on the mocked HTTP response; verify the actual
        # outbound request body rather than just a source-code string.
        def receive(req,timeout):
            body=json.loads(req.data.decode('utf-8'))
            self.assertEqual(8192,body['options']['num_ctx'])
            self.assertEqual(2560,body['options']['num_predict'])
            self.assertIs(False,body['think'])
            self.assertEqual('json',body['format'])
            self.assertEqual(900,timeout)
            import io
            payload={'done_reason':'stop','message':{'content':'{"action":"finish","observations":[]}'}}
            return io.BytesIO(json.dumps(payload).encode('utf-8'))
        with patch.object(mod.urllib.request,'urlopen',side_effect=receive):
            result=mod.local_chat('http://127.0.0.1:11434','qwen3.5:4b',
                                  [{'role':'user','content':'test'}],timeout=900,num_predict=2560)
        self.assertEqual('finish',result['action'])

    def test_bounded_input_through_12_calls_and_final(self):
        items=fixture(12); calls=[]
        def fake_chat(server,model,messages,**kw):
            self.assertEqual(2,len(messages))
            prompt=json.loads(messages[1]['content'])
            self.assertLess(len(messages[1]['content']),10000)
            self.assertNotIn('ground_truth',messages[1]['content'])
            self.assertEqual(kw['num_predict'],2560)
            calls.append(prompt)
            if len(calls)<=12:
                return {'action':'inspect_method','method':items[(len(calls)-1)%12]['method']}
            return {'action':'finish','observations':[{'text':'Lab string #1','source_type':'hardcoded_managed',
                     'method':items[1]['method'],'evidence_type':'il_literal','evidence_value':'Lab string #1'}]}
        with patch.object(mod,'local_chat',side_effect=fake_chat):
            obs,trace,ok=mod.run_agent(items,[], 'http://127.0.0.1:11434','qwen3.5:4b',max_steps=14,num_predict=2560,timeout=900)
        self.assertTrue(ok)
        self.assertEqual(13,len(calls))
        self.assertEqual(1,len(obs))
        self.assertEqual('bounded_context_configuration',trace[0]['action'])
        self.assertEqual('finish',trace[-1]['action'])
        self.assertFalse(any('request' in x or 'text' in x for x in trace))
        self.assertGreater(len(calls[-1]['evidence_ledger']),0)

    def test_retry_discards_bad_response_without_growth(self):
        items=fixture(2); calls=[]
        def fake_chat(server,model,messages,**kw):
            calls.append(json.loads(messages[1]['content']))
            if len(calls)==1:raise mod.ModelResponseError('invalid_json','chars=900, finish=length')
            return {'action':'finish','observations':[]}
        with patch.object(mod,'local_chat',side_effect=fake_chat):
            obs,trace,ok=mod.run_agent(items,[],'http://127.0.0.1:11434','qwen3.5:4b',num_predict=2560)
        self.assertTrue(ok)
        self.assertEqual(2,len(calls))
        self.assertIn('retry_instruction',calls[1])
        self.assertEqual('invalid_json',trace[1]['code'])

    def test_no_fabrication_when_steps_exhausted(self):
        def fake_chat(server,model,messages,**kw):return {'action':'list_methods','query':''}
        with patch.object(mod,'local_chat',side_effect=fake_chat):
            obs,trace,ok=mod.run_agent(fixture(2),[], 'http://127.0.0.1:11434','qwen3.5:4b',max_steps=3)
        self.assertFalse(ok)
        self.assertEqual([],obs)
        self.assertEqual('max_steps_reached',trace[-1]['action'])

    def test_ledger_is_bounded_even_with_many_records(self):
        rows=[{'action':'inspect_method','method':f'Example.Method{i}',
               'literals':[{'literal':'x'*1600}],'calls':['TMP_Text.set_text']} for i in range(90)]
        prompt=json.loads(mod._v09_bounded_messages(fixture(21),[],rows,15)[1]['content'])
        self.assertLessEqual(len(json.dumps(prompt['evidence_ledger'],ensure_ascii=False)),5400)
        self.assertLess(len(json.dumps(prompt,ensure_ascii=False)),10000)

    def test_compact_evidence_does_not_upgrade_unknown(self):
        rec={'text':'secret','source_type':'unknown','source_ref':'level0#path_id=1',
             'evidence_type':'asset_text','asset_type':'MonoBehaviour'}
        got=mod._v09_compact_tool('list_asset_candidates',{'query':''},[rec])
        self.assertEqual('unknown',got['assets'][0]['source_type'])

    def test_source_keeps_frozen_verifier_and_guided(self):
        import hashlib
        source=(ROOT/'src/modstudio_m03_v09.py').read_text(encoding='utf-8')
        # SHA256 of exact, *unmodified* function blocks in the public M03 v0.8 source.
        fingerprints={
          ('def verify_rea_evidence','def calls_for'):'7076985160b1b9724c2aae37c7f8da988d93b6a444223c3184c8c105d54256ec',
          ('def validate_observations','class ModelResponseError'):'eece50d85ef3c0654eb5d6c1f5820851e855e6c521522abe7fd84f78f7cfea16',
          ('def run_guided_agent','def probe_local_model'):'d47b53d4218a94530784251ca39baf77f09494590fe03b4f4cf48191ea496746',
          ('def scan_assets','def template_match'):'c82aa97c706cab4977ceef9c9dcf68017b28887c4954e00ea82d60b02f01a834',
          ('def baseline_asset_observations','def mono_script_identity'):'b29d5781fe28cab0d6a777ab89b20b0e700851846ef717aef7a2a5b379a69467',
        }
        for (a,b),sha in fingerprints.items():
            block=source[source.index(a):source.index(b,source.index(a))]
            self.assertEqual(sha,hashlib.sha256(block.encode('utf-8')).hexdigest())
        self.assertIn("'num_ctx':8192",source)
        self.assertNotIn("'num_ctx':4096",source)



if __name__=='__main__':unittest.main()
