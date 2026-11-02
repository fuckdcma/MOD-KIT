"""M03 v0.7: reproduce real v0.6 timeout, isolate slow Ollama with probe,
bound guided prompt/generation without touching evidence or private truth.
"""
import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import modstudio_m03 as m

class TimeoutV07Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.items=m.load_jsonl(ROOT/'AgentInput/rea_evidence.jsonl')
        cls.assets=m.load(ROOT/'Fixtures/build_assets_v03.json')['assets']

    def test_previous_guided_trace_is_http_timeout_not_invalid_json(self):
        old=m.load(ROOT/'Fixtures/guided_v06_timeout.json')
        self.assertIs(old['completed'],False)
        self.assertEqual(old['trace'][1]['status'],'transport_error')
        self.assertEqual(old['trace'][1]['error_type'],'TimeoutError')
        self.assertEqual(old['trace'][0]['evidence_chars'],4706)
        self.assertEqual(old['observations'],[])

    def test_guided_brief_budget_keeps_sources_and_methods(self):
        brief=m.guided_evidence_brief(self.items,self.assets,max_chars=3900)
        self.assertEqual(brief['coverage']['qualified_sources_included'],2)
        self.assertEqual(brief['coverage']['methods_included'],6)
        self.assertTrue(brief['coverage']['truncated'])
        self.assertLessEqual(len(json.dumps({k:v for k,v in brief.items() if k!='coverage'},ensure_ascii=False,separators=(',',':'))),3900)

    def test_native_payload_uses_smaller_predict_and_context4096(self):
        captured={}
        class FakeResp:
            def __enter__(self):return self
            def __exit__(self,*exc):return False
            def read(self):return b'{}'
        def urlopen(req,timeout):
            captured['timeout']=timeout
            captured['payload']=json.loads(req.data)
            return FakeResp()
        with patch.object(m.urllib.request,'urlopen',side_effect=urlopen),patch.object(m.json,'load',return_value={'message':{'content':'{"ok":true}'}}):
            result=m.local_chat('http://127.0.0.1:11434','qwen3.5:4b',[{'role':'user','content':'hi'}],transport='ollama')
        self.assertTrue(result['ok'])
        self.assertEqual(captured['timeout'],600)
        self.assertEqual(captured['payload']['options']['num_predict'],1280)
        self.assertEqual(captured['payload']['options']['num_ctx'],4096)
        self.assertFalse(captured['payload']['think'])
        self.assertFalse(captured['payload']['stream'])

    def test_custom_timeout_and_predict_passed(self):
        captured={}
        def mock_chat(*args,**kwargs):
            captured.update(kwargs)
            return {'action':'finish','observations':[]}
        with patch.object(m,'local_chat',side_effect=mock_chat):
            _,trace,done=m.run_guided_agent(self.items,self.assets,'http://127.0.0.1:11434','qwen3.5:4b',timeout=480,num_predict=768,brief_max_chars=3900)
        self.assertTrue(done)
        self.assertEqual(captured['timeout'],480)
        self.assertEqual(captured['num_predict'],768)
        self.assertEqual(trace[0]['model_timeout_seconds'],480)
        self.assertEqual(trace[0]['num_predict'],768)

    def test_guided_timeout_traces_and_does_not_finish(self):
        with patch.object(m,'local_chat',side_effect=TimeoutError('timed out')):
            obs,trace,done=m.run_guided_agent(self.items,self.assets,'http://127.0.0.1:11434','qwen3.5:4b',timeout=600)
        self.assertFalse(done)
        self.assertEqual(obs,[])
        self.assertEqual(trace[1]['error_type'],'TimeoutError')
        self.assertEqual(trace[1]['attempt'],1)
        self.assertEqual(trace[1]['timeout_seconds'],600)

    def test_guided_bad_context_rejected(self):
        with self.assertRaisesRegex(ValueError,'brief'):
            m.run_guided_agent(self.items,self.assets,'http://localhost:11434','x',brief_max_chars=1)

    def test_cloud_url_rejected_before_model_probe(self):
        with self.assertRaises(ValueError):
            m.probe_local_model('https://example.com','qwen3.5:4b')

    def test_probe_is_small_no_rea_or_ground_truth(self):
        captured={}
        def mock_chat(server,model,messages,**kwargs):
            captured['messages']=messages
            captured['options']=kwargs
            return {'ok':True}
        with patch.object(m,'local_chat',side_effect=mock_chat):
            out=m.probe_local_model('http://127.0.0.1:11434','qwen3.5:4b',timeout=120,transport='ollama')
        self.assertEqual(out['status'],'ok')
        self.assertEqual(captured['options']['num_predict'],64)
        self.assertEqual(captured['options']['timeout'],120)
        self.assertNotIn('Quest Completed',json.dumps(captured['messages']))
        self.assertNotIn('ground_truth',json.dumps(captured['messages']))

    def test_probe_invalid_reply_is_clean_error(self):
        with patch.object(m,'local_chat',return_value={'ok':False}):
            with self.assertRaises(m.ModelResponseError) as ctx:
                m.probe_local_model('http://127.0.0.1:11434','qwen3.5:4b')
        self.assertEqual(ctx.exception.code,'probe_invalid_reply')

    def test_timeout_validation(self):
        for timeout in [0,19,1801,True]:
            with self.subTest(timeout=timeout):
                with self.assertRaises(ValueError):
                    m.local_chat('http://127.0.0.1:11434','x',[],timeout=timeout)

    def test_predict_validation(self):
        for num_predict in [0,63,4097,False]:
            with self.subTest(num_predict=num_predict):
                with self.assertRaises(ValueError):
                    m.local_chat('http://127.0.0.1:11434','x',[],num_predict=num_predict)

    def test_cli_probe_out_has_status_no_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=pathlib.Path(tmp)/'probe.json'
            with patch.object(m,'probe_local_model',return_value={'status':'ok','elapsed_seconds':1.1}):
                result=m.main(['probe','--model','qwen3.5:4b','--out',str(out)])
            self.assertEqual(result,0)
            self.assertEqual(m.load(out)['status'],'ok')

    def test_autonomous_default_fake_chat_compatibility(self):
        calls=[]
        def old_mock(server,model,messages,transport='auto'):
            calls.append(transport)
            return {'action':'finish','observations':[]}
        with patch.object(m,'local_chat',side_effect=old_mock):
            _,trace,done=m.run_agent(self.items,[],'http://127.0.0.1:11434','qwen3.5:4b')
        self.assertTrue(done)
        self.assertEqual(calls,['auto'])

    def test_private_evaluator_still_does_not_score_failed_run(self):
        bad=m.load(ROOT/'Fixtures/guided_v06_timeout.json')
        self.assertFalse(bad['completed'])
        # Run remains uncompleted regardless of the number of static assets.
        self.assertEqual(len(bad['observations']),0)

if __name__=='__main__':unittest.main()
