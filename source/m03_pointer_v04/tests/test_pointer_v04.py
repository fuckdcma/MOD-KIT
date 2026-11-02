"""Synthetic contract tests for external-file PPtr handling, no Unity game execution."""
import copy
import importlib.util
import json
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('modstudio_v04_pointer',ROOT/'src'/'modstudio_m03.py')
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def table(key='menu.load',value='Load Game',ref='sharedassets0.assets#path_id=16'):
    data={'entries':[{'key':key,'value':value}]}
    kind,proof=m.scan_table_asset_field(data,{'full_class_name':'ModStudioLab.LabStringTable'},
                                        'entries[0].value',value)
    return {'text':value,'source_type':kind,'source_ref':ref,'asset_type':'MonoBehaviour',
            'evidence_type':'asset_text','metadata':{
                'field_path':'entries[0].value',
                'mono_script':{'full_class_name':'ModStudioLab.LabStringTable'},**proof}}


class ExternalPointerUnitTests(unittest.TestCase):
    def test_index_three_maps_third_external_not_matching_pathid(self):
        sf=types.SimpleNamespace(externals=[types.SimpleNamespace(path='resources.assets'),
           types.SimpleNamespace(path='globalgamemanagers.assets'),
           types.SimpleNamespace(path='sharedassets0.assets')])
        hint=m.pointer_file_lookup({'m_FileID':3,'m_PathID':16},sf,'level0')
        self.assertEqual(hint['external_index'],2)
        self.assertEqual(hint['file_name'],'sharedassets0.assets')
        self.assertEqual(hint['status'],'file_mapped')

    def test_index_out_of_range_is_never_guessed(self):
        sf=types.SimpleNamespace(externals=[types.SimpleNamespace(path='sharedassets0.assets')])
        hint=m.pointer_file_lookup({'m_FileID':3,'m_PathID':16},sf,'level0')
        self.assertEqual(hint['status'],'not_resolved')

    def test_boolean_pointer_ids_rejected(self):
        sf=types.SimpleNamespace(externals=[])
        hint=m.pointer_file_lookup({'m_FileID':True,'m_PathID':16},sf,'level0')
        self.assertEqual(hint['status'],'not_resolved')

    def test_pointer_mapped_but_wrong_target_key_stays_unresolved(self):
        sf=types.SimpleNamespace(externals=[types.SimpleNamespace(path='sharedassets0.assets')])
        b=m.scan_reader_binding({'key':'menu.load','table':{'m_FileID':1,'m_PathID':16}},
                {'full_class_name':'ModStudioLab.TableTextExample'},'level0#path_id=40',sf)
        m.resolve_reader_bindings([b],[table(key='not.menu.load')],[Path('level0'),Path('sharedassets0.assets')])
        self.assertEqual(b['binding_status'],'unresolved_build_pointer')

    def test_key_match_but_wrong_external_file_stays_unresolved(self):
        sf=types.SimpleNamespace(externals=[types.SimpleNamespace(path='resources.assets')])
        b=m.scan_reader_binding({'key':'menu.load','table':{'m_FileID':1,'m_PathID':16}},
                 {'full_class_name':'ModStudioLab.TableTextExample'},'level0#path_id=40',sf)
        m.resolve_reader_bindings([b],[table()],[Path('level0'),Path('sharedassets0.assets'),Path('resources.assets')])
        self.assertEqual(b['binding_status'],'unresolved_build_pointer')

    def test_duplicate_file_name_never_resolves(self):
        sf=types.SimpleNamespace(externals=[types.SimpleNamespace(path='sharedassets0.assets')])
        b=m.scan_reader_binding({'key':'menu.load','table':{'m_FileID':1,'m_PathID':16}},
                 {'full_class_name':'ModStudioLab.TableTextExample'},'level0#path_id=40',sf)
        m.resolve_reader_bindings([b],[table()],[Path('a/sharedassets0.assets'),Path('b/sharedassets0.assets'),Path('level0')])
        self.assertEqual(b['binding_status'],'unresolved_build_pointer')

    def test_same_file_pointer_zero_can_resolve_if_table_object_exists(self):
        sf=types.SimpleNamespace(externals=[])
        b=m.scan_reader_binding({'key':'menu.load','table':{'m_FileID':0,'m_PathID':16}},
                 {'full_class_name':'ModStudioLab.TableTextExample'},'level0#path_id=40',sf)
        m.resolve_reader_bindings([b],[table(ref='level0#path_id=16')],[Path('level0')])
        self.assertEqual(b['binding_status'],'serialized_pointer_resolved')
        self.assertEqual(b['resolved_target_ref'],'level0#path_id=16')
        self.assertEqual(b['resolution_evidence']['external_index'],None)

    def test_absent_externals_stays_unresolved(self):
        b=m.scan_reader_binding({'key':'menu.load','table':{'m_FileID':3,'m_PathID':16}},
                {'full_class_name':'ModStudioLab.TableTextExample'},'level0#path_id=40',None)
        m.resolve_reader_bindings([b],[table()],[Path('level0'),Path('sharedassets0.assets')])
        self.assertEqual(b['binding_status'],'unresolved_build_pointer')

    def test_old_v03_output_not_auto_upgraded(self):
        old=json.loads((ROOT/'Fixtures'/'build_assets_v03.json').read_text(encoding='utf-8'))
        m.resolve_reader_bindings(old['reader_bindings'],old['assets'],[Path('level0'),Path('sharedassets0.assets')])
        self.assertEqual(old['reader_bindings'][0]['binding_status'],'unresolved_build_pointer')

    def test_resolved_binding_has_rea_flow_but_no_runtime_execution_claim(self):
        sf=types.SimpleNamespace(externals=[types.SimpleNamespace(path='sharedassets0.assets')])
        b=m.scan_reader_binding({'key':'menu.load','table':{'m_FileID':1,'m_PathID':16}},
                {'full_class_name':'ModStudioLab.TableTextExample'},'level0#path_id=40',sf)
        m.resolve_reader_bindings([b],[table()],[Path('level0'),Path('sharedassets0.assets')])
        rea=m.load_jsonl(ROOT/'AgentInput'/'rea_evidence.jsonl')
        report=m.provenance_links(rea,{'assets':[table()],'reader_bindings':[b]})
        record=report['observations'][0]
        self.assertEqual(record['serialized_reader_binding'],'pointer_to_this_table_proven')
        self.assertEqual(record['runtime_binding'],'serialized_pointer_and_lookup_flow_proven_runtime_unverified')
        self.assertIn('sharedassets0.assets#path_id=16',record['proof_refs'])
        self.assertIn('level0#path_id=40',record['proof_refs'])

    def test_pointer_to_different_table_even_same_key_does_not_link_other_table(self):
        sf=types.SimpleNamespace(externals=[types.SimpleNamespace(path='sharedassets0.assets')])
        b=m.scan_reader_binding({'key':'menu.load','table':{'m_FileID':1,'m_PathID':16}},
                {'full_class_name':'ModStudioLab.TableTextExample'},'level0#path_id=40',sf)
        assets=[table(ref='sharedassets0.assets#path_id=16'), table(ref='sharedassets0.assets#path_id=17')]
        m.resolve_reader_bindings([b],assets,[Path('level0'),Path('sharedassets0.assets')])
        report=m.provenance_links(m.load_jsonl(ROOT/'AgentInput'/'rea_evidence.jsonl'),
                                   {'assets':assets,'reader_bindings':[b]})
        first,second=report['observations']
        self.assertEqual(first['serialized_reader_binding'],'pointer_to_this_table_proven')
        self.assertNotIn('serialized_reader_binding',second)


class ScannerSyntheticIntegrationTests(unittest.TestCase):
    def test_scan_gathers_actual_external_table(self):
        class Obj:
            def __init__(self,name,pid,cls,data,externals=None):
                self.type=types.SimpleNamespace(name=name)
                self.path_id=pid
                self.assets_file=types.SimpleNamespace(unity_version='6000.3.27f2', externals=externals or [])
                self.cls=cls
                self.data=data
            def parse_as_dict(self):return self.data
            def parse_monobehaviour_head(self):
                cls=self.cls
                def deref():return types.SimpleNamespace(m_Namespace='ModStudioLab',m_ClassName=cls,m_AssemblyName='Assembly-CSharp')
                return types.SimpleNamespace(m_Script=types.SimpleNamespace(deref_parse_as_object=deref))
        ext=[types.SimpleNamespace(path='resources.assets'),
             types.SimpleNamespace(path='globalgamemanagers.assets'),
             types.SimpleNamespace(path='sharedassets0.assets')]
        reader=Obj('MonoBehaviour',40,'TableTextExample',
                   {'key':'menu.load','table':{'m_FileID':3,'m_PathID':16}},ext)
        tab=Obj('MonoBehaviour',16,'LabStringTable',{'entries':[{'key':'menu.load','value':'Load Game'}]})
        by_name={'level0':[reader],'sharedassets0.assets':[tab]}
        mod=types.ModuleType('UnityPy')
        mod.load=lambda p:types.SimpleNamespace(objects=by_name[Path(p).name])
        helpers=types.ModuleType('UnityPy.helpers')
        tt=types.ModuleType('UnityPy.helpers.TypeTreeGenerator')
        class Generator:
            def __init__(self,version):pass
            def load_local_dll_folder(self,path):pass
        tt.TypeTreeGenerator=Generator
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/'Managed').mkdir()
            for name in by_name:(root/name).write_bytes(b'fixture')
            with patch.dict('sys.modules',{'UnityPy':mod,'UnityPy.helpers':helpers,'UnityPy.helpers.TypeTreeGenerator':tt}):
                report=m.scan_assets(root)
        self.assertEqual(report['errors'],[])
        self.assertEqual(report['stats']['reader_pointers_resolved'],1)
        b=report['reader_bindings'][0]
        self.assertEqual(b['resolved_target_ref'],'sharedassets0.assets#path_id=16')
        self.assertEqual(b['resolution_evidence']['external_path'],'sharedassets0.assets')
        self.assertEqual(b['pointer_file_lookup']['external_index'],2)


if __name__=='__main__':unittest.main()
