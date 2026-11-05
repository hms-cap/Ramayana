import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
V = ROOT / "vendor" / "kosha"


class DictionaryVendor(unittest.TestCase):
    def test_source_is_recorded(self):
        t = (V / "SOURCE.txt").read_text(encoding="utf-8")
        self.assertIn("hms-cap/VedaAlokana", t)
        self.assertRegex(t, r"Commit: [0-9a-f]{40}")

    def test_shards_and_keys_are_complete(self):
        man = json.loads((V / "data" / "kosha" / "shards.json").read_text(encoding="utf-8"))
        for _, f, _ in man["shards"]:
            self.assertTrue((V / "data" / "kosha" / f"{f}.json").exists(), f)
        n = sum(1 for l in open(V / "data" / "kosha" / "keys.tsv", encoding="utf-8") if "\t" in l)
        self.assertGreater(n, 40000)

    def test_app_shell_files_all_exist(self):
        sw = (V / "kosha" / "sw.js").read_text(encoding="utf-8")
        files = re.findall(r"'([^']+\.(?:js|css|woff|png|svg|html|webmanifest))'", sw.split("const SHELL_FILES")[1].split("];")[0])
        self.assertGreater(len(files), 15)
        for f in files:
            self.assertTrue((V / "kosha" / f).resolve().exists(), f)

    def test_offline_pack_lists_existing_files(self):
        off = json.loads((V / "data" / "offline.json").read_text(encoding="utf-8"))
        pack = next(p for p in off["packs"] if p["id"] == "kosha")
        for f in pack["files"]:
            self.assertTrue((V / f).exists(), f)


if __name__ == "__main__":
    unittest.main()
