"""Synthetic-only regression tests; all labels invented for this test suite."""
import importlib.util
import os
import sys
import unittest
import json
import io
from unittest.mock import patch
from pathlib import Path

CODE = Path(__file__).resolve().parents[1] / 'src' / 'm04_evidence_agent_v10.py'
spec = importlib.util.spec_from_file_location('m04_agent_v10', CODE)
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
M03 = Path(os.environ.get('MODSTUDIO_FROZEN_M03',
          r'D:\ModStudioAI\Milestone03\src\modstudio_m03.py'))


def method(name='Acme.Demo.Awake', text='OPEN MAP', setter=True, fmt=False, extra=None):
    calls = ([{'target':'TMPro.TMP_Text.set_text'}] if setter else [])
    if fmt: calls.append({'target':'System.String.Format'})
    if extra: calls += [{'target':x} for x in extra]
    return {'method':name,'method_token':'0x06000001',
            'assembly_sha256':'b'*64,'evidence_kind':'rea_managed_static',
            'strings_loaded_by_method':[{'literal':text,'literal_token':'0x70000001','il_offset':13}],
            'call_targets':calls}


def asset(text='SYNTHETIC SAY HELLO',source='external_json',
          ref='resources.assets#path_id=17',key='message',asset_type='TextAsset',
          class_name='Acme.Table',path='message'):
    return {'text':text,'source_type':source,'source_ref':ref,'asset_type':asset_type,
            'evidence_type':'asset_text',
            'metadata':{'key':key,'field_path':path,'mono_script':{'full_class_name':class_name},
                        'entry_key':'intro' if source=='scriptable_object' else None}}


def scan(assets=None,raw=None):
    return {'source':'read_only_build_asset_scan','assets':assets or [],
            'raw_candidates':raw or [],'errors':[]}


@unittest.skipUnless(M03.is_file(), 'Frozen M03 source required for integration tests')
class EvidenceIndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m03=a.load_m03(M03)

    def inventory(self,items=None,assets=None,raw=None):
        return a.candidate_inventory(self.m03,items if items is not None else [method()],scan(assets,raw))

    def test_hardcoded_literal_in_exact_method_is_validated(self):
        inv,stats=self.inventory()
        self.assertEqual(len(inv),1)
        self.assertEqual(inv[0]['observation']['source_type'],'hardcoded_managed')
        self.assertEqual(inv[0]['observation']['validation_status'],'observed')
        self.assertEqual(inv[0]['observation']['evidence_value'],'OPEN MAP')

    def test_runtime_template_requires_string_format(self):
        inv,_=self.inventory([method(text='HP {0}',fmt=True)])
        self.assertEqual(inv[0]['observation']['source_type'],'runtime_generated')
        self.assertEqual(inv[0]['observation']['text'],'HP {0}')
        inv2,stats=self.inventory([method(text='HP {0}',fmt=False)])
        self.assertEqual(inv2,[])
        self.assertEqual(stats['ambiguous_template_excluded'],1)

    def test_missing_tmp_setter_cannot_claim_ui(self):
        inv,stats=self.inventory([method(setter=False)])
        self.assertEqual(inv,[])
        self.assertEqual(stats['literal_without_tmp_setter'],1)

    def test_log_literal_excluded_even_with_setter(self):
        inv,stats=self.inventory([method(text='[ERR] Missing file')])
        self.assertEqual(inv,[])
        self.assertEqual(stats['diagnostic_literal_excluded'],1)

    def test_textasset_exact_asset_evidence(self):
        inv,stats=self.inventory([method(setter=False,text='')],[asset()])
        self.assertEqual(len(inv),1)
        self.assertEqual(inv[0]['observation']['source_type'],'external_json')
        self.assertEqual(inv[0]['observation']['source_ref'],'resources.assets#path_id=17')

    def test_non_textasset_never_promoted_to_external_json(self):
        inv,_=self.inventory([method(setter=False,text='')],[asset(asset_type='MonoBehaviour')])
        self.assertEqual(inv,[])

    def test_unknown_serialized_mono_field_never_promoted(self):
        unknown=asset(text='SYNTHETIC SECRET',source='unknown',asset_type='MonoBehaviour',
                      class_name='Acme.ScriptableProbably',path='entries[0].value')
        inv,stats=self.inventory([method(setter=False,text='')],[unknown])
        self.assertEqual(inv,[])
        self.assertEqual(stats['unproven_serialized_source_excluded'],1)

    def test_source_qualified_scriptable_old_A_may_pass_but_new_class_does_not(self):
        old=asset(text='SYNTHETIC TABLE',source='scriptable_object',asset_type='MonoBehaviour',
                  class_name='ModStudioLab.LabStringTable',path='entries[0].value')
        new=asset(text='SYNTHETIC TABLE OTHER',source='scriptable_object',asset_type='MonoBehaviour',
                  class_name='Acme.WrongClass',path='entries[1].value',ref='resources.assets#path_id=19')
        inv,stats=self.inventory([method(setter=False,text='')],[old,new])
        self.assertEqual(len(inv),1)
        self.assertEqual(inv[0]['observation']['text'],'SYNTHETIC TABLE')
        self.assertEqual(stats['unproven_serialized_source_excluded'],1)

    def test_raw_candidate_not_promoted(self):
        inv,stats=self.inventory([method(setter=False,text='')],[],[{'text':'RANDOM BYTES'}])
        self.assertEqual(inv,[])

    def test_wrong_evidence_kind_fails_closed(self):
        bad=method();bad['evidence_kind']='private_editor_truth'
        with self.assertRaises(ValueError):
            self.inventory([bad])

    def test_duplicate_method_names_refused(self):
        m1=method();m2=method()
        with self.assertRaises(a.AgentProtocolError):
            self.inventory([m1,m2])

    def test_stable_ids_and_distinct_provenance(self):
        i1,_=self.inventory()
        i2,_=self.inventory()
        self.assertEqual(i1[0]['id'],i2[0]['id'])
        m=method();m['strings_loaded_by_method'][0]['il_offset']=14
        i3,_=self.inventory([m])
        self.assertNotEqual(i1[0]['id'],i3[0]['id'])

    def test_successfully_selects_exact_id_no_free_text(self):
        def choose(server,model,batch,**kw):
            return [x['id'] for x in batch]
        obs,trace,completed,n,diags=a.run_indexed_selector(
            self.m03,[method()],scan([asset()]),'fake','http://127.0.0.1:11434',
            900,8192,512,1,selector=choose)
        self.assertTrue(completed)
        self.assertEqual(n,2)
        self.assertEqual(len(obs),2)
        self.assertTrue(all(x['validation_status']=='observed' for x in obs))
        self.assertEqual(trace[-1]['action'],'finish')

    def test_unknown_or_duplicate_id_fails_closed(self):
        def spoof(server,model,batch,**kw): return ['EV_FAKE']
        obs,trace,completed,n,_=a.run_indexed_selector(
            self.m03,[method()],scan(),'fake','http://127.0.0.1:11434',
            900,8192,512,3,selector=spoof)
        self.assertFalse(completed)
        self.assertEqual(obs,[])
        self.assertEqual(sum(x.get('code')=='invalid_selection_ids' for x in trace),3)

    def test_transient_error_then_valid_id(self):
        tries=[0]
        def choose(server,model,batch,**kw):
            tries[0]+=1
            if tries[0]==1: raise a.AgentProtocolError('invalid_json','finish=length')
            return [batch[0]['id']]
        obs,trace,completed,n,_=a.run_indexed_selector(
            self.m03,[method()],scan(),'fake','http://127.0.0.1:11434',
            900,8192,512,3,selector=choose)
        self.assertTrue(completed)
        self.assertEqual(len(obs),1)
        self.assertEqual(tries[0],2)

    def test_failing_batch_discards_partial_matches(self):
        called=[0]
        def choose(server,model,batch,**kw):
            called[0]+=1
            if called[0]>=2: raise a.AgentProtocolError('invalid_json','finish=length')
            return [batch[0]['id']]
        obs,trace,completed,n,_=a.run_indexed_selector(
            self.m03,[method()],scan([asset()]),'fake','http://127.0.0.1:11434',
            900,8192,512,1,selector=choose)
        self.assertFalse(completed)
        self.assertEqual(obs,[])
        self.assertEqual(n,2)

    def test_empty_catalog_is_incomplete_not_model_success(self):
        obs,trace,completed,n,_=a.run_indexed_selector(
            self.m03,[method(setter=False)],scan(),'fake','http://127.0.0.1:11434',
            900,8192,512,5,selector=lambda *args,**kwargs: [])
        self.assertFalse(completed)
        self.assertEqual(n,0)
        self.assertEqual(trace[-1]['action'],'no_evidence_candidates')

    def test_empty_selection_valid_but_no_claims(self):
        obs,trace,completed,n,_=a.run_indexed_selector(
            self.m03,[method()],scan(),'fake','http://127.0.0.1:11434',
            900,8192,512,5,selector=lambda *args,**kwargs: [])
        self.assertTrue(completed)
        self.assertEqual(obs,[])

    def test_mixed_assembly_rejected(self):
        m1=method();m2=method(name='Acme.X.Refresh');m2['assembly_sha256']='f'*64
        with self.assertRaises(ValueError):
            self.inventory([m1,m2])

    def test_local_ollama_json_selection_only(self):
        catalog,_=self.inventory()
        wanted=catalog[0]['id']
        body={'message':{'content':json.dumps({'select':[wanted]})},'done_reason':'stop'}
        data=json.dumps(body).encode('utf-8')
        class HttpResponse(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self,*exc): self.close()
        with patch.object(a.urllib.request,'urlopen',return_value=HttpResponse(data)) as api:
            selected=a.local_select('http://127.0.0.1:11434','fake',catalog)
        self.assertEqual(selected,[wanted])
        request=api.call_args.args[0]
        payload=json.loads(request.data)
        self.assertIs(payload['think'],False)
        self.assertEqual(payload['options']['num_ctx'],8192)
        self.assertEqual(payload['options']['num_predict'],512)

    def test_local_ollama_rejects_unknown_ids_from_json(self):
        catalog,_=self.inventory()
        body={'message':{'content':json.dumps({'select':['EV_NOT_IN_CATALOG']})},'done_reason':'stop'}
        with patch.object(a.urllib.request,'urlopen',return_value=io.BytesIO(json.dumps(body).encode())):
            with self.assertRaises(a.AgentProtocolError):
                a.local_select('http://127.0.0.1:11434','fake',catalog)

    def test_local_ollama_rejects_length_even_if_valid_json(self):
        catalog,_=self.inventory()
        body={'message':{'content':json.dumps({'select':[]})},'done_reason':'length'}
        with patch.object(a.urllib.request,'urlopen',return_value=io.BytesIO(json.dumps(body).encode())):
            with self.assertRaises(a.AgentProtocolError) as err:
                a.local_select('http://127.0.0.1:11434','fake',catalog)
        self.assertEqual(err.exception.code,'finish_length')

    def test_model_extra_claim_fields_rejected(self):
        catalog,_=self.inventory()
        body={'message':{'content':json.dumps({'select':[],'invented_text':'FAKE'})},'done_reason':'stop'}
        with patch.object(a.urllib.request,'urlopen',return_value=io.BytesIO(json.dumps(body).encode())):
            with self.assertRaises(a.AgentProtocolError) as err:
                a.local_select('http://127.0.0.1:11434','fake',catalog)
        self.assertEqual(err.exception.code,'invalid_selection_schema')

    def test_remote_hosts_blocked_before_any_network(self):
        for server in ('https://example.com','http://192.168.0.1:11434',
                       'http://127.0.0.1:1234','http://127.0.0.1:11434/prompt'):
            with self.assertRaises(a.AgentProtocolError):
                a._check_local_server(server)


if __name__=='__main__':
    unittest.main()
