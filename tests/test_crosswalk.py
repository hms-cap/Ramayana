"""Sanity checks on the generated Vulgate <-> Critical Edition cross-walk."""
import collections
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CW = ROOT / "data" / "crosswalk"


@unittest.skipUnless((CW / "verses.json").exists(), "cross-walk not generated")
class Crosswalk(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v = json.loads((CW / "verses.json").read_text(encoding="utf-8"))
        cls.s = json.loads((CW / "sargas.json").read_text(encoding="utf-8"))

    def test_known_verses(self):
        # opening verse, the krauñca verse (Vulgate 1.2.15 = CE 1.2.14), and the phalaśruti of 1.1
        self.assertEqual(self.v["vu"]["VU-1-001-001"]["targets"], ["CE-1-001-001"])
        self.assertEqual(self.v["vu"]["VU-1-002-015"]["targets"], ["CE-1-002-014"])
        self.assertEqual(self.v["vu"]["VU-1-001-100"]["targets"], ["CE-1-001-079"])

    def test_known_interpolation_absent(self):
        # Ādityahṛdaya (Vulgate Yuddha 107 in this numbering) is not in the CE
        st = collections.Counter(x["status"] for u, x in self.v["vu"].items() if u.startswith("VU-6-107-"))
        self.assertGreater(st["absent"], 0.9 * sum(st.values()))

    def test_ce_coverage(self):
        st = collections.Counter(x["status"] for x in self.v["ce"].values())
        self.assertLess(st["absent"] / sum(st.values()), 0.05)

    def test_sargas_monotone(self):
        """Within a kāṇḍa, mapped CE sargas should mostly increase with the Vulgate sarga number.
        A few real transpositions exist (e.g. Vulgate 6.23, the omens, sits at CE 6.31)."""
        for k in range(1, 8):
            pairs = sorted((int(a.split(".")[1]), int(b.split(":")[1].split(".")[1]))
                           for a, b in self.s.items() if a.startswith(f"vu:{k}."))
            drops = sum(1 for (_, x), (_, y) in zip(pairs, pairs[1:]) if y < x)
            self.assertLessEqual(drops, 6, f"kāṇḍa {k}")

    def test_links_are_symmetric(self):
        bad = 0
        for u, x in self.v["vu"].items():
            for t in x.get("targets", []):
                if u not in self.v["ce"][t].get("targets", []):
                    bad += 1
        self.assertEqual(bad, 0)


if __name__ == "__main__":
    unittest.main()
