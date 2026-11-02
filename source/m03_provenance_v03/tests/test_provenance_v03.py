"""Evidence-level tests for M03 v0.3, built with synthetic serialized fixtures."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('modstudio_m03_v03',BASE/'src'/'modstudio_m03.py')
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
REA=Path(__file__).resolve().parents[1]/'AgentInput'/'rea_evidence.jsonl'
LOCAL=BASE/'AgentInput'/'rea_evidence.jsonl'


def table_asset(key='menu.load',value='Load Game'):
    data={'entries':[{'key':key,'value':value}]}
    kind,md=m.scan_table_asset_field(data,{'full_class_name':'ModStudioLab.LabStringTable'},'entries[0].value',value)
    return {'text':value,'source_type':kind,'source_ref':'sharedassets0.assets#path_id=16',
            'asset_type':'MonoBehaviour','evidence_type':'asset_text',
            'metadata':{'field_path':'entries[0].value',
                        'mono_script':{'full_class_name':'ModStudioLab.LabStringTable','assembly':'Assembly-CSharp'},**md}}

class ProvenanceV03Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rea=m.load_jsonl(LOCAL if LOCAL.exists() else REA)

    def test_real_rea_has_lookup_setter(self):
        flow=m.rea_table_call_chain(self.rea)
        self.assertTrue(flow['supported'],flow)
        self.assertEqual(flow['reader_method'],'ModStudioLab.TableTextExample.Start')

    def test_table_pairs_key_and_value(self):
        self.assertEqual(m._table_entry_lookup({'entries':[{'key':'menu.load','value':'Load Game'}]},'entries[0].value'),'menu.load')
        self.assertIsNone(m._table_entry_lookup({'entries':[{'value':'Load Game'}]},'entries[0].value'))
        self.assertIsNone(m._table_entry_lookup({'entries':[{'key':'menu.load','value':'Load Game'}]},'entries[9].value'))
        self.assertIsNone(m._table_entry_lookup({'entries':[{'key':'menu.load','value':'Load Game'}]},'m_text'))

    def test_value_only_not_proven_as_source(self):
        kind,md=m.scan_table_asset_field({'entries':[{'value':'Load Game'}]},
            {'full_class_name':'ModStudioLab.LabStringTable'},'entries[0].value','Load Game')
        self.assertEqual(kind,'unknown')
        self.assertEqual(md,{})

    def test_wrong_class_never_promoted(self):
        kind,md=m.scan_table_asset_field({'entries':[{'key':'menu.load','value':'Load Game'}]},
            {'full_class_name':'TMPro.TextMeshProUGUI'},'entries[0].value','Load Game')
        self.assertEqual(kind,'unknown')

    def test_scriptable_source_can_be_proven_not_runtime_binding(self):
        a=table_asset()
        self.assertEqual(a['source_type'],'scriptable_object')
        obs=m.baseline_asset_observations([a],self.rea)
        self.assertEqual(len(obs),1)
        self.assertIn('NOT proven',obs[0]['note'])
        validated=m.validate_observations(obs,self.rea,[a])
        self.assertEqual(validated[0]['validation_status'],'observed')
        result=m.provenance_links(self.rea,{'assets':[a]})
        self.assertEqual(result['observations'][0]['source_status'],'source_key_value_observed')
        self.assertEqual(result['observations'][0]['runtime_binding'],'reader_calls_observed_key_or_pointer_not_linked')

    def test_table_reader_key_pointer_unresolved(self):
        a=table_asset()
        binding=m.scan_reader_binding({'key':'menu.load','table':{'m_FileID':1,'m_PathID':16}},
            {'full_class_name':'ModStudioLab.TableTextExample'},'level0#path_id=40')
        self.assertEqual(binding['reader_key'],'menu.load')
        result=m.provenance_links(self.rea,{'assets':[a],'reader_bindings':[binding]})
        self.assertIn('pointer_unresolved',result['observations'][0]['runtime_binding'])
        self.assertEqual(result['observations'][0]['source_status'],'source_key_value_observed')

    def test_preexisting_v02_is_not_auto_upgraded(self):
        old={'schema':'modstudio.m03.v0.2','assets':[
            {'text':'Load Game','source_type':'unknown','source_ref':'sharedassets0.assets#path_id=16',
             'asset_type':'MonoBehaviour','evidence_type':'asset_text',
             'metadata':{'field_path':'entries[0].value','mono_script':{'full_class_name':'ModStudioLab.LabStringTable'}}},
            {'text':'New Game','source_type':'unknown','source_ref':'level0#path_id=35',
             'asset_type':'MonoBehaviour','evidence_type':'asset_text',
             'metadata':{'field_path':'m_text','mono_script':{'full_class_name':'TMPro.TextMeshProUGUI'}}},
            {'text':'Hello, Commander','source_type':'external_json','source_ref':'resources.assets#path_id=9',
             'asset_type':'TextAsset','evidence_type':'asset_text','metadata':{'key':'message'}}]}
        self.assertEqual(old['schema'],'modstudio.m03.v0.2')
        self.assertEqual(len(m.baseline_asset_observations(old['assets'],self.rea)),1)
        report=m.provenance_links(self.rea,old)
        self.assertTrue(any(x['source_status']=='ui_snapshot_only' and x['text']=='New Game' for x in report['observations']))
        self.assertFalse(any(x['source_status']=='source_key_value_observed' for x in report['observations']))

    def test_faked_observation_rejected(self):
        a=table_asset()
        fake=copy.deepcopy(a)
        fake['metadata'].pop('entry_key')
        obs=m.baseline_asset_observations([fake],self.rea)
        self.assertEqual(obs,[])
        claim={'text':'Load Game','source_type':'scriptable_object','source_ref':fake['source_ref'],
               'evidence_type':'asset_text','evidence_value':'Load Game'}
        validated=m.validate_observations([claim],self.rea,[fake])
        self.assertEqual(validated[0]['validation_status'],'rejected')

    def test_wrong_key_never_linked(self):
        a=table_asset(key='not.menu.load')
        binding=m.scan_reader_binding({'key':'menu.load','table':{}},
             {'full_class_name':'ModStudioLab.TableTextExample'},'level0#path_id=40')
        report=m.provenance_links(self.rea,{'assets':[a],'reader_bindings':[binding]})
        self.assertEqual(report['observations'][0]['runtime_binding'],'reader_calls_observed_key_or_pointer_not_linked')

if __name__=='__main__': unittest.main()

class BuildOnlyScannerIntegrationTests(unittest.TestCase):
    def test_fake_UnityPy_objects_source_identity_and_reader_binding(self):
        """Mocks UnityPy API boundary; no claim of Unity 6 runtime validation."""
        import tempfile, types
        from unittest.mock import patch

        class Obj:
            def __init__(self,name,pid,cls,data):
                self.type=types.SimpleNamespace(name=name)
                self.path_id=pid
                self.assets_file=types.SimpleNamespace(unity_version='6000.3.27f2')
                self.cls=cls
                self.data=data
            def parse_as_dict(self):return self.data
            def parse_monobehaviour_head(self):
                cl=self.cls
                def resolve():
                    return types.SimpleNamespace(m_Namespace='ModStudioLab' if cl in ('LabStringTable','TableTextExample') else 'TMPro',
                        m_ClassName=cl,m_AssemblyName='Assembly-CSharp' if cl in ('LabStringTable','TableTextExample') else 'Unity.TextMeshPro')
                return types.SimpleNamespace(m_Script=types.SimpleNamespace(deref_parse_as_object=resolve))

        table=Obj('MonoBehaviour',16,'LabStringTable',{'entries':[{'key':'menu.load','value':'Load Game'}]})
        reader=Obj('MonoBehaviour',40,'TableTextExample',{'key':'menu.load','table':{'m_FileID':1,'m_PathID':16}})
        tmp=Obj('MonoBehaviour',31,'TextMeshProUGUI',{'m_text':'Load Game'})
        by_name={'level0':[reader,tmp],'sharedassets0.assets':[table]}
        fakepy=types.ModuleType('UnityPy')
        def load(path):return types.SimpleNamespace(objects=by_name[Path(path).name])
        fakepy.load=load
        helpers=types.ModuleType('UnityPy.helpers')
        tt=types.ModuleType('UnityPy.helpers.TypeTreeGenerator')
        class Generator:
            def __init__(self,version):pass
            def load_local_dll_folder(self,path):pass
        tt.TypeTreeGenerator=Generator
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/'Managed').mkdir()
            (root/'level0').write_bytes(b'x')
            (root/'sharedassets0.assets').write_bytes(b'x')
            with patch.dict('sys.modules',{'UnityPy':fakepy,'UnityPy.helpers':helpers,'UnityPy.helpers.TypeTreeGenerator':tt}):
                found=m.scan_assets(root)
            self.assertEqual(found['stats']['monobehaviours_decoded'],3)
            self.assertEqual(len(found['errors']),0)
            paired=[a for a in found['assets'] if a['source_type']=='scriptable_object']
            self.assertEqual(len(paired),1)
            self.assertEqual(paired[0]['metadata']['entry_key'],'menu.load')
            self.assertEqual(found['reader_bindings'][0]['reader_key'],'menu.load')
            self.assertEqual(found['reader_bindings'][0]['table_pointer'],{'m_FileID':1,'m_PathID':16})
            displayed=[a for a in found['assets'] if a['metadata']['mono_script']['full_class_name']=='TMPro.TextMeshProUGUI']
            self.assertEqual(len(displayed),1)
            self.assertEqual(displayed[0]['source_type'],'unknown')
