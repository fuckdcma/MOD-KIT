import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "Tools" / "analyze_provenance.py"
spec = importlib.util.spec_from_file_location("analyze_provenance", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class EvidenceTests(unittest.TestCase):
    def test_health_template(self):
        self.assertTrue(module.matches_template("Health: {0}/100", "Health: 65/100"))
        self.assertFalse(module.matches_template("Health: {0}/100", "Health: ABC/100"))

    def test_real_rea_input_when_supplied(self):
        target = Path(__file__).resolve().parents[2] / "members.json"
        if not target.exists():
            self.skipTest("No mounted user members.json outside package")
        records, hash_ = module.parse_managed(target)
        self.assertTrue(records)
        self.assertTrue(hash_)
        self.assertTrue(any(r["method"].endswith("HardcodedTextExample.Awake") for r in records))
        self.assertTrue(any(r["touches_tmp_setter"] for r in records))

    def test_jsonl_unicode(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "out.jsonl"
            module.write_jsonl(path, [{"record_id": "x", "text": "Tiếng Việt"}])
            self.assertEqual(module.read_jsonl(path)[0]["text"], "Tiếng Việt")

if __name__ == "__main__":
    unittest.main()
