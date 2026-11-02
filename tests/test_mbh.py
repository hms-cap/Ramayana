import json
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "etl"))
sys.path.insert(0, str(ROOT / "site"))


def load(ed):
    return [json.loads(l) for l in open(ROOT / "data" / "normalized" / "mbh" / f"{ed}.jsonl", encoding="utf-8")]


class MahabharataData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ce, cls.vu = load("ce"), load("vu")

    def test_counts(self):
        self.assertEqual(len(self.ce), 73821)
        self.assertEqual(len(self.vu), 96415)
        self.assertEqual(len({(r["k"], r["s"]) for r in self.ce}), 1995)

    def test_eighteen_parvans_and_unique_ids(self):
        for rows in (self.ce, self.vu):
            self.assertEqual(sorted({r["k"] for r in rows}), list(range(1, 19)))
            self.assertEqual(len({r["uid"] for r in rows}), len(rows))

    def test_every_verse_has_text(self):
        for rows in (self.ce, self.vu):
            for r in rows:
                self.assertTrue(r["lines"] and all(l and all(p.strip() for p in l) for l in r["lines"]), r["uid"])

    def test_pune_has_no_gaps(self):
        per = {}
        for r in self.ce:
            per.setdefault(r["k"], set()).add(r["s"])
        for k, ss in per.items():
            self.assertEqual(sorted(ss), list(range(1, max(ss) + 1)), f"parvan {k}")


class MahabharataBuild(unittest.TestCase):
    def test_works_and_editions(self):
        import build
        self.assertEqual(len(build.PARVANS), 18)
        self.assertEqual([e["id"] for e in build.load_editions(build.WORKS["mbh"])], ["vu", "ce"])
        self.assertEqual(build.unit_info(build.WORKS["mbh"], 7)["en"], "Droṇa Parva")
        self.assertTrue(build.unit_info(build.WORKS["mbh"], 3)["svg"].startswith("<svg"))

    def test_lean_verse_is_iast_with_marks(self):
        import build
        v = build.lean_verse(self.ce_first())
        self.assertEqual(v["ref"], "1.1.0")
        self.assertTrue(v["iast"][-1].endswith("|| 1.1.0 ||".replace(" ", " ")))
        self.assertIn("nārāyaṇaṃ", v["iast"][0])

    def ce_first(self):
        return load("ce")[0]

    def test_sources_credit_both_texts(self):
        src = json.loads((ROOT / "etl" / "sources.json").read_text(encoding="utf-8"))
        for key in ("mbh_ce", "mbh_vu"):
            self.assertTrue(src[key]["commit"] and src[key]["credits"] and src[key]["licence"])
        self.assertIn("Bhandarkar", src["mbh_ce"]["credits"])

    def test_daily_cards_for_mbh_are_deterministic(self):
        import build
        import daily
        recs = load("vu")
        accept = lambda r: r["v"] >= 1 and sum(len(" ".join(l)) for l in r["lines"]) <= 130
        words = {r["uid"]: range(8) for r in recs}
        a = daily.select(recs, words, lambda r: r.get("meter"), accept)
        b = daily.select(recs, words, lambda r: r.get("meter"), accept)
        self.assertEqual([r["uid"] for r in a], [r["uid"] for r in b])
        self.assertEqual(len(a), daily.N)


if __name__ == "__main__":
    unittest.main()
