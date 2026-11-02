import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "etl"))
import daily  # noqa: E402


class DailyCards(unittest.TestCase):
    def test_stride_visits_every_card_in_a_year(self):
        for start in (0, 20000, 20454):
            self.assertEqual(len({daily.day_index(d) for d in range(start, start + 365)}), 365)

    def test_stride_is_coprime(self):
        from math import gcd
        self.assertEqual(gcd(daily.STRIDE, daily.N), 1)

    def test_selection_is_deterministic_and_complete(self):
        words = {}
        for l in open(ROOT / "data/normalized/words.jsonl", encoding="utf-8"):
            r = json.loads(l)
            words[r["uid"]] = r["units"]
        recs = [json.loads(l) for l in open(ROOT / "data/normalized/ce.jsonl", encoding="utf-8")]
        a = daily.select(recs, words, lambda r: r.get("meter"))
        b = daily.select(recs, words, lambda r: r.get("meter"))
        self.assertEqual([r["uid"] for r in a], [r["uid"] for r in b])
        self.assertEqual(len(a), daily.N)
        self.assertEqual(len({r["uid"] for r in a}), daily.N)
        self.assertEqual({r["k"] for r in a}, set(range(1, 8)))


class Release(unittest.TestCase):
    def test_version_matches_changes(self):
        v = re.search(r"version:\s*'([\d.]+)'", (ROOT / "site/static/version.js").read_text()).group(1)
        changes = json.loads((ROOT / "data/changes.json").read_text(encoding="utf-8"))
        self.assertEqual(v, changes[0][0])
        self.assertRegex(v, r"^\d+\.\d+\.\d+$")

    def test_every_static_script_parses(self):
        for f in (ROOT / "site/static").glob("*.js"):
            r = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, f"{f.name}: {r.stderr}")
        r = subprocess.run(["node", "--check", str(ROOT / "site/sw.js")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_curated_notes_are_bilingual_pairs(self):
        cur = json.loads((ROOT / "data/daily/curated.json").read_text(encoding="utf-8"))
        cur.pop("_comment", None)
        for uid, note in cur.items():
            for k, v in note.items():
                self.assertIn(k, ("m", "u"))
                self.assertEqual(len(v), 2, uid)


if __name__ == "__main__":
    unittest.main()
