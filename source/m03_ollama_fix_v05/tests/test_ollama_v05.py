"""Contract tests for Qwen 3.5 JSON agent with native local Ollama API.
No external network calls are made in these tests.
"""
from pathlib import Path
import io
import json
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
import modstudio_m03 as m
ROOT=Path(__file__).resolve().parents[1]

class OllamaTransportTests(unittest.TestCase):
    def fake(self, reply, collection):
        def urlopen(req, timeout=None):
            collection.append({'url':req.full_url,'payload':json.loads(req.data.decode('utf-8')),'timeout':timeout})
            return io.BytesIO(json.dumps(reply).encode('utf-8'))
        return urlopen

    def test_auto_ollama_uses_native_api_and_think_false(self):
        collection=[]
        response={'message':{'role':'assistant','content':'{"action":"list_methods","query":""}'},'done_reason':'stop'}
        with patch.object(m.urllib.request,'urlopen',self.fake(response,collection)):
            result=m.local_chat('http://127.0.0.1:11434','qwen3.5:4b',[{'role':'user','content':'hello'}])
        self.assertEqual(result['action'],'list_methods')
        self.assertEqual(collection[0]['url'],'http://127.0.0.1:11434/api/chat')
        self.assertIs(collection[0]['payload']['think'],False)
        self.assertEqual(collection[0]['payload']['format'],'json')
        self.assertFalse(collection[0]['payload']['stream'])
        self.assertEqual(collection[0]['payload']['model'],'qwen3.5:4b')

    def test_v1_suffix_is_accepted_and_native_api_is_used(self):
        collection=[]
        response={'message':{'content':'{"action":"finish","observations":[]}'},'done_reason':'stop'}
        with patch.object(m.urllib.request,'urlopen',self.fake(response,collection)):
            result=m.local_chat('http://localhost:11434/v1','qwen3.5:4b',[])
        self.assertEqual(result['action'],'finish')
        self.assertEqual(collection[0]['url'],'http://localhost:11434/api/chat')

    def test_legacy_llamacpp_still_openai_compatible(self):
        collection=[]
        response={'choices':[{'message':{'content':'{"action":"finish","observations":[]}'},'finish_reason':'stop'}]}
        with patch.object(m.urllib.request,'urlopen',self.fake(response,collection)):
            result=m.local_chat('http://127.0.0.1:9931','local-qwen',[])
        self.assertEqual(result['action'],'finish')
        self.assertEqual(collection[0]['url'],'http://127.0.0.1:9931/v1/chat/completions')
        self.assertNotIn('reasoning_effort',collection[0]['payload'])

    def test_openai_ollama_uses_reasoning_effort_none(self):
        col=[]
        response={'choices':[{'message':{'content':'{"action":"finish","observations":[]}'},'finish_reason':'stop'}]}
        with patch.object(m.urllib.request,'urlopen',self.fake(response,col)):
            m.local_chat('http://127.0.0.1:11434','qwen3.5:4b',[],transport='openai')
        self.assertEqual(col[0]['payload']['reasoning_effort'],'none')

    def test_incomplete_agent_cannot_be_scored_as_zero_five(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            inp=p/'agent.json'; out=p/'evaluation.json'
            inp.write_text(json.dumps({'mode':'agent','completed':False,'observations':[]}),encoding='utf-8')
            with self.assertRaises(ValueError):
                m.main(['evaluate','--observations',str(inp),'--truth',str(ROOT/'PrivateEvaluation/ground_truth_v01.csv'),'--out',str(out)])
            self.assertFalse(out.exists())

    def test_explicit_ollama_transport_overrides_custom_port(self):
        self.assertEqual(m._local_endpoint('http://127.0.0.1:9999','ollama')[0],
                         'http://127.0.0.1:9999/api/chat')

    def test_empty_content_produces_diagnostic_not_json_exception(self):
        collection=[]
        response={'message':{'content':'','thinking':'many tokens'},'done_reason':'length'}
        with patch.object(m.urllib.request,'urlopen',self.fake(response,collection)):
            with self.assertRaises(m.ModelResponseError) as cm:
                m.local_chat('http://127.0.0.1:11434','qwen3.5:4b',[])
        self.assertEqual(cm.exception.code,'empty_content')
        self.assertIn('length',cm.exception.details)
        self.assertNotIn('many tokens',str(cm.exception))

    def test_malformed_json_has_safe_diagnostic(self):
        with self.assertRaises(m.ModelResponseError) as cm:
            m._parse_agent_json('not json, possibly private content', 'stop')
        self.assertEqual(cm.exception.code,'invalid_json')
        self.assertNotIn('private content',cm.exception.details)

    def test_array_is_rejected(self):
        with self.assertRaises(m.ModelResponseError) as cm:
            m._parse_agent_json('[]','stop')
        self.assertEqual(cm.exception.code,'unexpected_json_type')

    def test_remote_hosts_disallowed_even_when_ollama_selected(self):
        for host in ['https://ollama.com','http://192.168.1.22:11434','http://api.external.com:11434']:
            with self.assertRaises(ValueError):m._local_endpoint(host,'ollama')

    def test_unexpected_server_path_is_rejected(self):
        with self.assertRaises(ValueError):m._local_endpoint('http://localhost:11434/other','auto')

    def test_missing_api_content_errors_cleanly(self):
        with patch.object(m.urllib.request,'urlopen',self.fake({'message':{}},[])):
            with self.assertRaises(m.ModelResponseError) as cm:
                m.local_chat('http://localhost:11434','qwen3.5:4b',[])
        self.assertEqual(cm.exception.code,'empty_content')

class AgentRetryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rea=m.load_jsonl(ROOT/'AgentInput/rea_evidence.jsonl')

    def test_retries_empty_then_finish(self):
        state={'calls':0}
        def mock_chat(*args,**kwargs):
            state['calls']+=1
            if state['calls']==1:raise m.ModelResponseError('empty_content','finish=length')
            return {'action':'finish','observations':[]}
        with patch.object(m,'local_chat',side_effect=mock_chat):
            observations,trace,done=m.run_agent(self.rea,[], 'http://localhost:11434','qwen3.5:4b',max_steps=3)
        self.assertEqual(observations,[])
        self.assertTrue(done)
        self.assertEqual(state['calls'],2)
        self.assertEqual(trace[0]['code'],'empty_content')
        self.assertEqual(trace[-1]['action'],'finish')

    def test_all_empty_stops_without_claiming_completion(self):
        with patch.object(m,'local_chat',side_effect=m.ModelResponseError('empty_content','finish=length')):
            observations,trace,done=m.run_agent(self.rea,[], 'http://localhost:11434','qwen3.5:4b',max_steps=2)
        self.assertFalse(done)
        self.assertEqual(observations,[])
        self.assertEqual(len(trace),3)

    def test_invalid_action_is_retried(self):
        calls=[{'action':'unknown_operation'},{'action':'finish','observations':[]}]
        with patch.object(m,'local_chat',side_effect=calls):
            obs,trace,done=m.run_agent(self.rea,[], 'http://127.0.0.1:11434','qwen3.5:4b')
        self.assertTrue(done)
        self.assertEqual(trace[0]['code'],'invalid_action')

    def test_all_invalid_actions_stops_without_fake_tool(self):
        with patch.object(m,'local_chat',return_value={'action':'not_a_tool'}):
            obs,trace,done=m.run_agent(self.rea,[],'http://localhost:11434','qwen3.5:4b')
        self.assertFalse(done)
        self.assertEqual(obs,[])
        self.assertEqual(len(trace),3)
        self.assertTrue(all(t['code']=='invalid_action' for t in trace))

    def test_tool_feedback_is_bounded(self):
        events=[]
        def fake_chat(server,model,messages,transport='auto'):
            events.append(messages[:])
            if len(events)==1:return {'action':'list_asset_candidates','query':''}
            return {'action':'finish','observations':[]}
        enormous_assets=[{'source_ref':'a#1','text':'A'*10000,'source_type':'unknown'}]
        with patch.object(m,'local_chat',side_effect=fake_chat):
            _,trace,done=m.run_agent(self.rea,enormous_assets,'http://127.0.0.1:11434','qwen3.5:4b')
        self.assertTrue(done)
        self.assertTrue(trace[0]['tool_result_truncated'])
        feedback=events[1][-1]['content']
        self.assertLess(len(feedback),5000)
        self.assertIn('TRUNCATED',feedback)

if __name__=='__main__':unittest.main()
