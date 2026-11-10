import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "etl"))

COUNTS = [47, 72, 43, 42, 29, 47, 30, 28, 34, 42, 55, 20, 34, 27, 20, 24, 28, 78]
SPEAKER = re.compile(r"^(dhṛtarāṣṭra|saṃjaya|sañjaya|arjuna|śrībhagavān|śrībhagavan) ?uvāca$")


def load(path):
    return [json.loads(l) for l in open(path, encoding="utf-8")]


class GitaData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g = {ed: load(ROOT / "data" / "normalized" / "gita" / f"{ed}.jsonl") for ed in ("ce", "vu")}
        cls.mbh = {ed: {r["uid"]: r for r in load(ROOT / "data" / "normalized" / "mbh" / f"{ed}.jsonl")} for ed in ("ce", "vu")}

    def get(self, ed, ch, v):
        return next(r for r in self.g[ed] if r["ch"] == ch and r["v"] == v)

    def test_chapters_and_counts(self):
        for ed, rows in self.g.items():
            self.assertEqual(sorted({r["ch"] for r in rows}), list(range(1, 19)))
            self.assertEqual([sum(1 for r in rows if r["ch"] == c) for c in range(1, 19)], COUNTS)
            self.assertEqual(len({r["uid"] for r in rows}), len(rows))
        self.assertEqual(len(self.g["ce"]), 700)
        self.assertEqual([r["v"] for r in self.g["ce"] if r["ch"] == 13], list(range(1, 35)))

    def test_order_and_uids(self):
        for ed, rows in self.g.items():
            keys = [(r["ch"], r["v"]) for r in rows]
            self.assertEqual(keys, sorted(keys))
            for r in rows:
                self.assertEqual(r["uid"], f"BG-{ed.upper()}-{r['ch']:02d}-{r['v']:03d}")

    def test_known_verses(self):
        self.assertTrue(self.get("ce", 2, 47)["lines"][0][0].startswith("karmaṇy evādhikāras te"))
        self.assertTrue(self.get("ce", 18, 66)["lines"][0][0].startswith("sarvadharmān parityajya"))
        self.assertTrue(self.get("vu", 18, 66)["lines"][0][0].startswith("sarvadharmān"))

    def test_verse_1_1_clean(self):
        for ed in ("ce", "vu"):
            r = self.get(ed, 1, 1)
            self.assertEqual(r["speaker"], "dhṛtarāṣṭra uvāca")
            self.assertEqual(len(r["lines"]), 2)
            for l in r["lines"]:
                for p in l:
                    self.assertNotIn("namaḥ |", p)
                    self.assertNotIn("(Gītā", p)

    def test_speaker_lines_are_removed_and_no_junk(self):
        for rows in self.g.values():
            for r in rows:
                self.assertTrue(r["lines"], r["uid"])
                self.assertIn(len(r["lines"]), (1, 2, 3, 4), r["uid"])
                for l in r["lines"]:
                    t = " ".join(l)
                    self.assertFalse(SPEAKER.match(t), r["uid"])
                    self.assertNotIn("(Gītā", t)
                    self.assertNotIn("namaḥ |", t)
                    self.assertNotIn("....", t)
        self.assertEqual(self.get("ce", 18, 78)["lines"][-1][0], "tatra śrīr vijayo bhūtir dhruvā nītir matir mama")

    def test_speakers_kumbakonam_moved_forward(self):
        vu = self.g["vu"]
        self.assertEqual(self.get("vu", 1, 2)["speaker"], "sañjaya uvāca")
        self.assertEqual(self.get("vu", 2, 1)["speaker"], "sañjaya uvāca")
        self.assertEqual(self.get("vu", 2, 2)["speaker"], "śrībhagavānuvāca")
        self.assertEqual(self.get("vu", 13, 1)["speaker"], "arjuna uvāca")
        self.assertEqual(self.get("vu", 13, 2)["speaker"], "śrībhagavānuvāca")
        self.assertEqual(self.get("ce", 13, 1)["speaker"], "śrībhagavān uvāca")
        self.assertEqual(self.get("ce", 2, 47)["speaker"], None)
        self.assertTrue(all(r["speaker"] for r in vu if (r["ch"], r["v"]) in ((3, 1), (4, 1), (18, 1))))

    def test_chapter_13_numbering(self):
        vs = [r["v"] for r in self.g["vu"] if r["ch"] == 13]
        self.assertEqual(len(vs), 34)
        self.assertNotIn(27, vs)
        self.assertEqual(max(vs), 35)

    def test_mbh_uid_exists(self):
        for ed, rows in self.g.items():
            for r in rows:
                self.assertIn(r["mbh_uid"], self.mbh[ed], r["uid"])
                self.assertEqual(self.mbh[ed][r["mbh_uid"]]["v"], r["v"])

    def test_mbh_preface_removed(self):
        r = self.mbh["ce"]["CE-6-023-001"]
        self.assertEqual(len(r["lines"]), 3)
        self.assertNotIn("atha dhyānaṃ", json.dumps(r, ensure_ascii=False))
        self.assertTrue((ROOT / "data" / "gita" / "gretil_preface.txt").read_text(encoding="utf-8").count("\n") > 30)

    def test_fix_script_is_idempotent(self):
        import fix_mbh_gita_preface as f
        before = f.CE.read_bytes()
        f.main()
        self.assertEqual(f.CE.read_bytes(), before)

    def test_crosswalk(self):
        cw = json.loads((ROOT / "data" / "crosswalk" / "gita" / "verses.json").read_text(encoding="utf-8"))
        ids = {ed: {r["uid"] for r in rows} for ed, rows in self.g.items()}
        self.assertEqual(set(cw["ce"]), ids["ce"])
        self.assertEqual(set(cw["vu"]), ids["vu"])
        for side, other in (("ce", "vu"), ("vu", "ce")):
            for e in cw[side].values():
                for t in e.get("targets", []):
                    self.assertIn(t, ids[other])
        share = sum(1 for e in cw["ce"].values() if e["status"] == "match") / 700
        self.assertGreater(share, 0.95)


if __name__ == "__main__":
    unittest.main()
