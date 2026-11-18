"""Gaps in our copies of the texts are known and listed here; a new gap (or a fixed one) fails this test so the
list, the reader's gap notes and the release notes are updated together (v0.25)."""
import collections
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = {("ram", "vu"): "vu.jsonl", ("ram", "ce"): "ce.jsonl", ("mbh", "vu"): "mbh/vu.jsonl", ("mbh", "ce"): "mbh/ce.jsonl"}
# missing whole chapters, and chapters with missing verse numbers (count), per text
KNOWN = {
    ("ram", "vu"): ([], {}), ("ram", "ce"): ([], {}),
    ("mbh", "vu"): ([(3, 109), (3, 110), (7, 15), (7, 137), (7, 138)], None),   # Kumbakonam (SARIT): empty in the source
    ("mbh", "ce"): ([], {(1, 151): 27, (2, 41): 8}),                             # Pune (GRETIL): 1.151.25–51, 2.41.34–41
}


def scan(path):
    by = collections.defaultdict(set)
    for line in open(path, encoding="utf-8"):
        r = json.loads(line); by[(r["k"], r["s"])].add(r["v"])
    ks = collections.defaultdict(set)
    for k, s in by:
        ks[k].add(s)
    chapters = sorted((k, s) for k in ks for s in range(1, max(ks[k]) + 1) if s not in ks[k])
    verses = {}
    for key, vs in by.items():
        miss = [v for v in range(1, max(vs) + 1) if v not in vs]
        if miss:
            verses[key] = len(miss)
    return chapters, verses


class Gaps(unittest.TestCase):
    def test_known_gaps(self):
        for key, fn in FILES.items():
            with self.subTest(text=key):
                ch, vs = scan(ROOT / "data" / "normalized" / fn)
                kch, kvs = KNOWN[key]
                self.assertEqual(ch, kch)
                if kvs is not None:
                    self.assertEqual(vs, kvs)
                else:   # Kumbakonam: many small numbering holes; only the total is pinned
                    self.assertLessEqual(sum(vs.values()), 100, vs)


if __name__ == "__main__":
    unittest.main()
