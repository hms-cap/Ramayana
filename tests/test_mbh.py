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


class MahabharataWords(unittest.TestCase):
    """DCS word analysis, glosses (English and Kannada) and the Kumbakonam-to-Pune cross-walk."""

    @classmethod
    def setUpClass(cls):
        import gzip
        cls.words = [json.loads(l) for l in gzip.open(ROOT / "data" / "normalized" / "mbh" / "words.jsonl.gz", "rt", encoding="utf-8")]
        cls.ce_uids = {r["uid"] for r in load("ce")}
        cls.gloss = json.loads((ROOT / "data" / "lexicon" / "gloss.json").read_text(encoding="utf-8"))
        cls.kn = json.loads((ROOT / "data" / "lexicon" / "gloss_kn.json").read_text(encoding="utf-8"))

    def test_words_follow_pune_ids_and_cover_nearly_all(self):
        uids = {r["uid"] for r in self.words}
        self.assertEqual(len(uids), len(self.words))
        self.assertLessEqual(uids, self.ce_uids)
        self.assertGreater(len(uids) / len(self.ce_uids), 0.98)

    def test_every_tag_has_a_label(self):
        import grammar
        missing = Counter()
        for r in self.words:
            for u in r["units"]:
                self.assertTrue(u["f"] and len(u["f"]) == len(u["l"]))
                for m in grammar.check_tags(u["t"]):
                    missing[m] += 1
        self.assertEqual(dict(missing), {})

    def test_gita_is_the_known_gap(self):
        have = {tuple(map(int, r["uid"].split("-")[1:3])) for r in self.words}
        self.assertFalse(any((6, s) in have for s in range(23, 41)))
        self.assertIn((6, 41), have)

    def test_gloss_coverage_of_the_text(self):
        freq = Counter(l for r in self.words for u in r["units"] for l in u["l"])
        cover = sum(n for l, n in freq.items() if l in self.gloss) / sum(freq.values())
        self.assertGreater(cover, 0.93)

    def test_kannada_glosses_are_kannada_and_have_english(self):
        import re
        self.assertGreater(len(self.kn), 400)
        for lemma, g in self.kn.items():
            self.assertIn(lemma, self.gloss)
            self.assertTrue(re.search(r"[\u0C80-\u0CFF]", g), (lemma, g))
            self.assertFalse(re.search(r"[A-Za-z]{3,}", g), (lemma, g))

    def test_crosswalk_targets_exist_and_rate(self):
        cw = json.loads((ROOT / "data" / "crosswalk" / "mbh" / "verses.json").read_text(encoding="utf-8"))
        vu_uids = {r["uid"] for r in load("vu")}
        self.assertEqual(set(cw["vu"]), vu_uids)
        self.assertEqual(set(cw["ce"]), self.ce_uids)
        for side, ids in (("vu", self.ce_uids), ("ce", vu_uids)):
            for e in cw[side].values():
                for t in e.get("targets", []):
                    self.assertIn(t, ids)
        share = sum(1 for e in cw["ce"].values() if e["status"] == "match") / len(cw["ce"])
        self.assertGreater(share, 0.8)


if __name__ == "__main__":
    unittest.main()
