import json
import re
import tempfile
import unittest
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/'src'))
import m04_generate as gen
import m04_evaluate as ev
import m04_seal as seal


class CaseGenerationTests(unittest.TestCase):
    def setUp(self):
        self.seed=bytes(range(32))

    def test_has_exactly_twenty_cases(self):
        rows=gen.make_cases(self.seed)
        self.assertEqual(len(rows),20)
        self.assertEqual(sum(r['kind'] in gen.POSITIVE for r in rows),15)

    def test_distribution_three_per_positive_and_five_distinct_negative(self):
        counts=Counter(r['kind'] for r in gen.make_cases(self.seed))
        for k in gen.POSITIVE:self.assertEqual(counts[k],3)
        self.assertEqual(sum(v for k,v in counts.items() if k.startswith('negative_')),5)

    def test_seed_changes_cases_and_ids_not_values_only(self):
        a=gen.make_cases(self.seed); b=gen.make_cases(bytes([9]*32))
        self.assertNotEqual([x['text'] for x in a],[x['text'] for x in b])

    def test_reproducible_fixed_test_seed(self):
        self.assertEqual(gen.make_cases(self.seed),gen.make_cases(self.seed))

    def test_invalid_seed(self):
        with self.assertRaises(ValueError): gen.make_cases(b'123')

    def test_dynamic_placeholders_and_snapshot(self):
        rows=gen.make_cases(self.seed)
        dynamic=[r for r in rows if r['kind']=='runtime']
        self.assertEqual(len(dynamic),3)
        for r in dynamic:
            self.assertIn('{0}',r['template']);self.assertIn('{1}',r['template'])
            self.assertEqual(r['text'],r['template'].format(r['arg0'],r['arg1']))

    def test_json_resource_unique(self):
        rs=[r['resource_name'] for r in gen.make_cases(self.seed) if r['resource_name']]
        self.assertEqual(len(rs),4);self.assertEqual(len(set(rs)),4)
        self.assertTrue(all(re.fullmatch(r'm04_(payload|orphan)_b\d{3}',r) for r in rs))

    def test_diagnostic_duplicate_is_not_extra_ui(self):
        rows=gen.make_cases(self.seed)
        duplicate=next(r for r in rows if r['kind']=='negative_duplicate')
        self.assertIn(duplicate['text'],[r['text'] for r in rows if r['kind']=='hardcoded'])

    def test_generated_Csharp_has_actual_literal_and_String_Format(self):
        rows=gen.make_cases(self.seed)
        hard=gen._make_hardcoded(rows);dynamic=gen._make_runtime(rows)
        self.assertEqual(hard.count('private void Write'),3)
        self.assertEqual(dynamic.count('private void Refresh'),3)
        self.assertEqual(dynamic.count('string.Format(System.Globalization.CultureInfo.InvariantCulture'),3)
        self.assertIn('TMP_Text',hard)

    def test_csharp_quoted_non_ascii_and_escape(self):
        src=gen.csharp_string('Mở "cửa" \\')
        self.assertIn('\\u1edf',src)
        self.assertIn('\\"',src)
        self.assertIn('\\\\',src)

    def test_private_data_not_shipped_in_template(self):
        content='\n'.join(p.read_text('utf-8') for p in (ROOT/'UnityTemplate').rglob('*.cs'))
        for row in gen.make_cases(self.seed):
            if row['text'] != '':self.assertNotIn(row['text'],content)


class LocalGenerationTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.base=Path(self.t.name)
        self.project=self.base/'UnityTextLabB'
        (self.project/'Assets').mkdir(parents=True)
        (self.project/'ProjectSettings').mkdir()
        (self.project/'ProjectSettings/ProjectVersion.txt').write_text('m_EditorVersion: 6000.3.27f2\n')
        self.private=self.base/'PRIVATE_NOT_GITHUB'

    def test_generates_private_outputs_and_public_fingerprint_only(self):
        out=gen.generate(self.project,self.private,ROOT/'UnityTemplate',seed=bytes(range(32)))
        self.assertEqual(out['case_count'],20)
        self.assertEqual(len(json.loads((self.private/'ground_truth_PRIVATE.json').read_text())['cases']),20)
        pub=(self.private/'public_fingerprint_ONLY.json').read_text(encoding='utf-8')
        for row in gen.make_cases(bytes(range(32))):
            self.assertNotIn(row['text'],pub)
        self.assertEqual(len((self.private/'seed_PRIVATE.hex').read_text().strip()),64)
        self.assertEqual(len(json.loads((self.project/'ProjectSettings/M04HoldoutLocal.json').read_text())['rows']),20)

    def test_refuses_overwrite_secret_seed(self):
        gen.generate(self.project,self.private,ROOT/'UnityTemplate',seed=bytes(range(32)))
        with self.assertRaises(FileExistsError):
            gen.generate(self.project,self.private,ROOT/'UnityTemplate',seed=bytes([2]*32))

    def test_refuses_original_lab_name(self):
        wrong=self.base/'UnityTextLab';self.project.rename(wrong)
        with self.assertRaisesRegex(ValueError,'separate project'):
            gen.generate(wrong,self.private,ROOT/'UnityTemplate',seed=bytes(range(32)))

    def test_refuses_private_inside_project(self):
        with self.assertRaisesRegex(ValueError,'outside'):
            gen.generate(self.project,self.project/'Secret',ROOT/'UnityTemplate',seed=bytes(range(32)))

    def test_refuses_public_git_worktree(self):
        (self.base/'.git').mkdir()
        with self.assertRaisesRegex(ValueError,'Git'):
            gen.generate(self.project,self.private,ROOT/'UnityTemplate',seed=bytes(range(32)))

    def test_refuses_different_unity_version(self):
        (self.project/'ProjectSettings/ProjectVersion.txt').write_text('m_EditorVersion: 6000.0.10f1')
        with self.assertRaisesRegex(ValueError,'6000.3'):
            gen.generate(self.project,self.private,ROOT/'UnityTemplate',seed=bytes(range(32)))


class PrivateScorerTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup)
        self.base=Path(self.t.name)
        self.rows=gen.make_cases(bytes(range(32)))
        self.truth={'schema':'modstudio.m04.private_truth.v0.1','eval_id':'test',
                    'cases':[gen.truth_record(row) for row in self.rows]}

    def good_obs(self):
        obs=[]
        for row in self.rows:
            if row['kind'] not in gen.POSITIVE:continue
            ref=('Assets/M04/Prefabs/'+row['case_id']+'.prefab' if row['kind']=='prefab' else 'file#path_id=1')
            obs.append({'text':row['template'] if row['kind']=='runtime' else row['text'],
                        'source_type':gen.EXPECTED[row['kind']],
                        'source_ref':ref,'method':'ModStudioM04.M04RuntimeWriter.Refresh' if row['kind']=='runtime' else 'ModStudioM04.writer',
                        'confidence':'observed','evidence_type':'asset_text'})
        return obs

    def test_all_fifteen_source_text_matches(self):
        report={'completed':True,'mode':'agent','observations':self.good_obs()}
        s=ev.score_one(self.truth,report)
        self.assertEqual(s['source_and_text_matches'],15)
        self.assertEqual(s['unmatched_positive'],0)
        self.assertEqual(s['false_positive_claims'],0)

    def test_wrong_dynamic_kind_not_counted(self):
        obs=self.good_obs()
        for o in obs:
            if '{0}' in o['text']:o['source_type']='hardcoded_managed'
        s=ev.score_one(self.truth,{'mode':'agent','completed':True,'observations':obs})
        self.assertEqual(s['source_and_text_matches'],12)

    def test_prefab_scene_snapshot_is_not_supported_and_flags_false_claim(self):
        obs=self.good_obs()
        for o in obs:
            if o['source_type']=='serialized_prefab': o['source_ref']='level0#path_id=44'
        s=ev.score_one(self.truth,{'mode':'agent','completed':True,'observations':obs})
        self.assertLess(s['observed_supported_matches'],15)
        self.assertEqual(s['false_positive_claims'],3)

    def test_negative_log_only_false_positive(self):
        row=next(r for r in self.rows if r['kind']=='negative_log')
        obs=self.good_obs()+[{'text':row['text'],'source_type':'hardcoded_managed'}]
        s=ev.score_one(self.truth,{'mode':'agent','completed':True,'observations':obs})
        self.assertEqual(s['false_positive_claims'],1)

    def test_duplicate_string_not_conflated(self):
        row=next(r for r in self.rows if r['kind']=='negative_duplicate')
        obs=self.good_obs()+[{'text':row['text'],'source_type':'hardcoded_managed','method':'M04DiagnosticWriter.Start'}]
        s=ev.score_one(self.truth,{'mode':'agent','completed':True,'observations':obs})
        self.assertEqual(s['false_positive_claims'],1)

    def test_incomplete_refused(self):
        with self.assertRaisesRegex(ValueError,'Incomplete'):
            ev.score_one(self.truth,{'mode':'agent','completed':False,'observations':[]})

    def test_freeze_copy_hashes_and_public_only_summary(self):
        truth=self.base/'private/truth.json';truth.parent.mkdir()
        truth.write_text(json.dumps(self.truth),encoding='utf-8')
        output=self.base/'input.json';output.write_text(json.dumps({'mode':'agent','completed':True,'observations':self.good_obs()}),encoding='utf-8')
        r=ev.evaluate_and_lock(truth,[('guided_r01',output)],self.base/'lock',self.base/'private/metrics.json',self.base/'public/metrics.json')
        self.assertEqual(r['runs'][0]['source_and_text_matches'],15)
        self.assertEqual(ev.sha_file(output),ev.sha_file(self.base/'lock/guided_r01.json'))
        contents=(self.base/'public/metrics.json').read_text('utf-8')
        for row in self.rows:
            self.assertNotIn(row['text'],contents)
        self.assertNotIn('per_case_PRIVATE',contents)
        with self.assertRaises(FileExistsError):
            ev.evaluate_and_lock(truth,[('guided_r01',output)],self.base/'lock',self.base/'private/metrics2.json',self.base/'public/metrics2.json')

    def test_repeat_names_are_unique(self):
        truth=self.base/'truth.json';truth.write_text(json.dumps(self.truth))
        p=self.base/'run.json';p.write_text(json.dumps({'mode':'agent','completed':True,'observations':[]}))
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            ev.evaluate_and_lock(truth,[('guided_r01',p),('guided_r01',p)],self.base/'lock',self.base/'pr/out.json',self.base/'pu/out.json')


class BuildFingerprintTests(unittest.TestCase):
    def test_hash_manifest_contains_only_file_hashes(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);b=root/'UnityTextLabB_Data';(b/'Managed').mkdir(parents=True)
            (b/'Managed/Assembly-CSharp.dll').write_bytes(b'fake assembly for pure Python test')
            (b/'resources.assets').write_bytes(b'fake')
            p=root/'PRIVATE';p.mkdir()
            (p/'public_fingerprint_ONLY.json').write_text(json.dumps({'eval_id':'TEST','private_ground_truth_sha256':'abc'}))
            x=seal.seal(b,p,root/'public.json')
            self.assertEqual(len(x['assembly_sha256']),64)
            self.assertEqual(len(x['build_files']),2)
            self.assertNotIn('text',json.dumps(x))


if __name__=='__main__':unittest.main()
