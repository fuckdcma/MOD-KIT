import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNTIME = ROOT / 'UnityPatch/Assets/M04/Runtime'
EDITOR = ROOT / 'UnityPatch/Assets/Editor/M04RepairMissingScripts.cs'
INSTALL = ROOT / 'Scripts/Install_M04_ScriptBindingFix.ps1'

class M04RepairContractTests(unittest.TestCase):
    def test_only_one_named_unity_component_per_source(self):
        for name, base in [('M04Table', 'ScriptableObject'),
                           ('M04TableReader', 'MonoBehaviour'),
                           ('M04JsonReader', 'MonoBehaviour')]:
            s = (RUNTIME / f'{name}.cs').read_text()
            self.assertRegex(s, rf'class\s+{name}\s*:\s*{base}')
            self.assertEqual(len(re.findall(r'class\s+\w+\s*:\s*(?:MonoBehaviour|ScriptableObject)', s)),1)

    def test_serialization_contract_fields_preserved(self):
        table = (RUNTIME/'M04Table.cs').read_text()
        for field in ['M04TableEntry', 'public string key', 'public string value', 'public M04TableEntry[] entries', 'TryGet']:
            self.assertIn(field,table)
        for field in ['public M04Table table', 'public TMP_Text label', 'public string key']:
            self.assertIn(field,(RUNTIME/'M04TableReader.cs').read_text())
        for field in ['public string resourceName', 'public TMP_Text label', 'Resources.Load<TextAsset>', 'JsonUtility.FromJson']:
            self.assertIn(field,(RUNTIME/'M04JsonReader.cs').read_text())

    def test_repair_uses_existing_spec_and_no_new_seed(self):
        s=EDITOR.read_text()
        self.assertIn('M04HoldoutLocal.json',s)
        self.assertIn('LoadPrivateSpec',s)
        self.assertNotIn('secrets.token_bytes',s)
        self.assertNotIn('ground_truth_PRIVATE.json',s)
        self.assertNotIn('seed_PRIVATE.hex',s)
        self.assertNotIn('GenerateScene()',s)

    def test_repair_only_known_reader_kinds(self):
        s=EDITOR.read_text()
        self.assertIn('x.kind == "table" || x.kind == "json"',s)
        self.assertIn('FindUnique(scene, "M04_Reader_" + row.case_id)',s)
        self.assertIn('GameObjectUtility.RemoveMonoBehavioursWithMissingScript',s)
        self.assertIn('reader.label = label',s)
        self.assertIn('reader.table = table',s)
        self.assertIn('reader.resourceName = row.resource_name',s)

    def test_table_recreated_from_same_local_spec(self):
        s=EDITOR.read_text()
        self.assertIn('x.kind == "negative_table"',s)
        self.assertIn('AssetDatabase.DeleteAsset(TablePath)',s)
        self.assertIn('AssetDatabase.CreateAsset(table, TablePath)',s)
        self.assertIn('M04RepairBackups',s)
        self.assertIn('File.Copy(oldPath',s)

    def test_build_guard_requires_valid_assets_and_missing_count_zero(self):
        s=EDITOR.read_text()
        self.assertIn('public static void ValidateBeforeBuild()',s)
        self.assertIn('GameObjectUtility.GetMonoBehavioursWithMissingScriptCount',s)
        self.assertIn('reader.table != table',s)
        self.assertIn('M04HardcodedWriter',s)
        self.assertIn('M04RuntimeWriter',s)
        self.assertIn('M04DiagnosticWriter',s)

    def test_script_asset_class_mapping_verified_before_repair(self):
        s=EDITOR.read_text()
        self.assertIn('AssetDatabase.LoadAssetAtPath<MonoScript>',s)
        self.assertIn('script.GetClass() != expected',s)
        self.assertIn('RequireMonoScripts();',s)

    def test_installer_targets_only_separate_project(self):
        s=INSTALL.read_text()
        self.assertIn("-cne 'UnityTextLabB'",s)
        self.assertIn('Get-Process -Name Unity',s)
        self.assertIn('M04HoldoutLocal.json',s)
        self.assertIn('M04PatchBackups',s)
        self.assertIn('M04LabRuntime.cs.meta',s)
        self.assertIn('BuildPipeline.BuildPlayer(options)',s)
        self.assertIn('M04RepairMissingScripts.ValidateBeforeBuild();',s)

    def test_no_hardcoded_hidden_case_text(self):
        all_text='\n'.join(p.read_text() for p in list(RUNTIME.glob('*.cs'))+[EDITOR,INSTALL])
        self.assertNotRegex(all_text, r'(?i)B00[1-9][\s_]*(?:quest|game|ui)')

if __name__=='__main__': unittest.main()
