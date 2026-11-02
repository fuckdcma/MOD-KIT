import importlib.util
import struct
import sys
import unittest
from pathlib import Path

SRC=Path(__file__).resolve().parents[1]/'src'/'modstudio_m03.py'
spec=importlib.util.spec_from_file_location('modstudio_m03_patch',SRC)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class ScannerPatchTests(unittest.TestCase):
    def test_raw_strings_offsets_and_utf8(self):
        # Artificial serialized-like payload (NOT a real Unity fixture)
        payload=b'\0'*12+struct.pack('<I',8)+b'New Game'+b'\0'*4+struct.pack('<I',9)+b'Load Game'+b'\0'*3
        candidates=m.scan_raw_unity_strings(payload)
        self.assertEqual([i['text'] for i in candidates],['New Game','Load Game'])
        self.assertEqual([i['raw_offset'] for i in candidates],[12,28])
    def test_raw_not_promoted_to_proof(self):
        assets=[{'text':'New Game','evidence_type':'raw_string_candidate','source_type':'unknown','source_ref':'level0#path_id=1'}]
        self.assertEqual(m.baseline_asset_observations(assets),[])
        x={'text':'New Game','source_type':'serialized_prefab','source_ref':'level0#path_id=1',
           'evidence_type':'asset_text','evidence_value':'New Game'}
        self.assertEqual(m.is_present_in_evidence(x,{},assets)[0],'rejected')
    def test_real_textasset_proven_no_type_forgery(self):
        assets=[{'text':'Hello, Commander','source_type':'external_json','source_ref':'resources.assets#path_id=9',
                 'asset_type':'TextAsset','evidence_type':'asset_text','metadata':{'key':'message'}}]
        out=m.baseline_asset_observations(assets)
        self.assertEqual(len(out),1)
        self.assertEqual(m.is_present_in_evidence(out[0],{},assets)[0],'observed')
        fake=dict(out[0]); fake['source_type']='serialized_prefab'
        self.assertEqual(m.is_present_in_evidence(fake,{},assets)[0],'rejected')
    def test_typed_nested_strings(self):
        obj={'entries':[{'key':'menu.load','value':'Load Game'}]}
        self.assertEqual(m.walk_typed_strings(obj), [('entries[0].value','Load Game')])
    def test_text_only_data_has_no_ground_truth_paths(self):
        self.assertFalse(hasattr(m,'GROUND_TRUTH'))

if __name__=='__main__':unittest.main()