"""Chandas appendix: the metre census and the catalogue agree, and the examples are spread out."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "etl"))

import chandas  # noqa: E402


class Chandas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cen = chandas.census()

    def test_every_stored_metre_is_catalogued(self):
        seen = {m for w in self.cen.values() for e in w.values() for m in e["by"]}
        self.assertFalse(seen - set(chandas.BY_NAME), seen - set(chandas.BY_NAME))

    def test_counts_add_up(self):
        for w in self.cen.values():
            for e in w.values():
                named = sum(sum(c.values()) for c in e["by"].values())
                self.assertEqual(named + e["none"], e["total"])

    def test_slugs_unique_ascii(self):
        slugs = [m["slug"] for m in chandas.CATALOGUE]
        self.assertEqual(len(slugs), len(set(slugs)))
        self.assertTrue(all(s.isascii() for s in slugs))

    def test_spread(self):
        self.assertEqual(chandas.spread([1, 2, 3], 8), [1, 2, 3])
        pick = chandas.spread(list(range(100)), 8)
        self.assertEqual(len(pick), 8)
        self.assertEqual(pick, sorted(pick))
        self.assertGreater(pick[0], -1)
        self.assertLess(pick[-1], 100)


if __name__ == "__main__":
    unittest.main()
