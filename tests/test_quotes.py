"""Today's śloka set (data/daily/quotes_*.json): every verse exists in its edition, has a Kannada and an
English meaning, and none is listed twice."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NORM = {"ram": ROOT / "data/normalized", "mbh": ROOT / "data/normalized/mbh", "gita": ROOT / "data/normalized/gita"}


class Quotes(unittest.TestCase):
    def test_quotes(self):
        for w, d in NORM.items():
            qs = json.loads((ROOT / f"data/daily/quotes_{w}.json").read_text(encoding="utf-8"))["quotes"]
            self.assertGreaterEqual(len(qs), 30, w)
            refs = {}
            for ed in ("vu", "ce"):
                for line in open(d / f"{ed}.jsonl", encoding="utf-8"):
                    r = json.loads(line)
                    refs[(ed, f'{r["ch"]}.{r["v"]}' if w == "gita" else f'{r["k"]}.{r["s"]}.{r["v"]}')] = r
            seen = set()
            for q in qs:
                key = (q["ed"], q["ref"])
                self.assertIn(key, refs, f"{w} {key}")
                self.assertNotIn(key, seen, f"{w} {key} twice"); seen.add(key)
                self.assertTrue(re.search(r"[ಀ-೿]", q["kn"]), f"{w} {key} kn")
                self.assertTrue(q["en"].strip(), f"{w} {key} en")


if __name__ == "__main__":
    unittest.main()
