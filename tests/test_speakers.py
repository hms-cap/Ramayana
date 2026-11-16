"""Mahābhārata speaker lines and Pune appendix passages (etl/split_speakers.py)."""
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "etl"))
from split_speakers import raw_layout  # noqa: E402

SPK = re.compile(r"\S+ (uvāca|ūcuḥ|ūcatuḥ)")


def load(ed):
    return [json.loads(l) for l in open(ROOT / "data" / "normalized" / "mbh" / f"{ed}.jsonl", encoding="utf-8")]


class Speakers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ce, cls.vu = load("ce"), load("vu")
        cls.by = {r["uid"]: r for r in cls.ce + cls.vu}

    def test_no_speaker_left_in_verse_lines(self):
        for rows in (self.ce, self.vu):
            left = [(r["uid"], " ".join(l)) for r in rows for l in r["lines"] if SPK.fullmatch(" ".join(l))]
            self.assertEqual(left, [])

    def test_speaker_counts(self):
        self.assertGreater(sum(len(r.get("spk", [])) for r in self.ce), 6000)
        self.assertGreater(sum(len(r.get("spk", [])) for r in self.vu), 8000)

    def test_speaker_stands_before_a_line(self):
        for rows in (self.ce, self.vu):
            for r in rows:
                for s in r.get("spk", []):
                    self.assertTrue(0 <= s["at"] < len(r["lines"]) or not r["lines"], (r["uid"], s))

    def test_bhishma_opening(self):
        # Kumbakonam prints "sañjaya uvāca" as the last line of 6.25.1: it belongs to 6.25.2
        v1, v2 = self.by["VU-6-025-001"], self.by["VU-6-025-002"]
        self.assertEqual([s["t"] for s in v1["spk"]], ["dhṛtarāṣṭra uvāca"])
        self.assertEqual(len(v1["lines"]), 2)
        self.assertEqual(v2["spk"], [{"at": 0, "t": "sañjaya uvāca", "from": "VU-6-025-001"}])
        c1 = self.by["CE-6-023-001"]
        self.assertEqual(c1["spk"], [{"at": 0, "t": "dhṛtarāṣṭra uvāca"}])
        self.assertEqual(c1["meter"], "Anuṣṭubh")

    def test_metres_found_again(self):
        self.assertGreater(sum(1 for r in self.vu if r.get("meter")), 83000)
        self.assertGreater(sum(1 for r in self.ce if r.get("meter")), 68000)

    def test_appendix_passages(self):
        app = [a for r in self.ce for a in r.get("app", [])]
        self.assertGreater(len(app), 400)
        self.assertGreater(sum(len(a["lines"]) for a in app), 36000)
        r = self.by["CE-1-019-017"]
        self.assertEqual(len(r["lines"]), 2)
        self.assertEqual(r["app"][0]["id"], "012")
        self.assertEqual(r["app"][0]["spk"][0], {"at": 0, "t": "sautir uvāca"})
        self.assertFalse(any("app" in r for r in self.vu))

    def test_raw_layout_restores_old_lines(self):
        lay = raw_layout(self.vu)
        self.assertEqual(lay["VU-6-025-001"][-1], ["sañjaya uvāca"])
        self.assertEqual(lay["VU-6-025-001"][0], ["dhṛtarāṣṭra uvāca"])


if __name__ == "__main__":
    unittest.main()
