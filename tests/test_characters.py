"""Characters (Pariśiṣṭa): data files, derived relations, lemmas, family-tree layout, verse links.
Works with partial data (characters still being written are skipped); the strict citation check runs only when all are present."""
import json
import subprocess
import sys
import unittest
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "etl"))

import characters as C  # noqa: E402


def mk(chars, work="mbh"):
    """A small in-memory work: chars = [(id, gender, [(type, to)...])]."""
    d = OrderedDict()
    for i, (cid, g, rel) in enumerate(chars):
        d[cid] = {"id": cid, "name": cid.title(), "group": "x", "gender": g, "rank": 2, "idx": i, "has": True, "epithets": [],
                  "moments": [], "relations": [{"type": t, "to": o} for t, o in rel]}
    return {"work": work, "groups": [], "chars": d}


class Data(unittest.TestCase):
    def test_files_parse_and_targets_exist(self):
        for w in C.WORKS:
            W = C.load(w)
            ids = set(W["chars"])
            seed = json.loads((ROOT / "data" / "characters" / f"seed_{w}.json").read_text(encoding="utf-8"))
            self.assertEqual(ids, {c["id"] for c in seed["characters"]})
            for c in W["chars"].values():
                for r in c["relations"]:
                    self.assertIn(r["to"], ids, f'{w}/{c["id"]} -> {r["to"]}')
                    self.assertIn(r["type"], C.KIND_OF.keys() | {"parent", "spouse", "sibling", "teacher", "ally", "enemy", "friend", "serves", "killed_by", "other"})

    def test_moment_links_resolve(self):
        for w, base in (("ram", ROOT / "data" / "normalized"), ("mbh", ROOT / "data" / "normalized" / "mbh")):
            need = {}
            for c in C.load(w)["chars"].values():
                for m in c["moments"]:
                    need.setdefault(m.get("ed", "vu"), set()).add(m["ref"])
            for ed, refs in need.items():
                have = set()
                with open(base / f"{ed}.jsonl", encoding="utf-8") as f:
                    for line in f:
                        r = json.loads(line)
                        have.add(f'{r["k"]}.{r["s"]}.{r["v"]}')
                self.assertFalse(refs - have, f"{w} {ed}: no such verse {sorted(refs - have)[:5]}")

    def test_check_script_when_complete(self):
        for w in C.WORKS:
            W = C.load(w)
            if not all(c["has"] for c in W["chars"].values()):
                print(f"\n  (check_characters skipped for {w}: {sum(not c['has'] for c in W['chars'].values())} characters not written yet)")
                continue
            r = subprocess.run([sys.executable, str(ROOT / "etl" / "check_characters.py"), w], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout[-2000:])


class Relations(unittest.TestCase):
    def setUp(self):
        self.W = mk([("pandu", "m", [("spouse", "kunti")]), ("kunti", "f", []), ("madri", "f", [("spouse", "pandu")]),
                     ("arjuna", "m", [("parent", "pandu"), ("parent", "kunti"), ("teacher", "drona"), ("serves", "krishna")]),
                     ("bhima", "m", [("parent", "pandu"), ("parent", "kunti")]), ("nakula", "m", [("parent", "pandu"), ("parent", "madri")]),
                     ("drona", "m", []), ("krishna", "m", []), ("karna", "m", [("killed_by", "arjuna"), ("parent", "kunti")])])
        self.F = C.facts(self.W)

    def keys(self, a, b):
        return self.F[a][b]["keys"]

    def test_parent_child(self):
        self.assertIn("parent", self.keys("arjuna", "pandu"))
        self.assertIn("child", self.keys("pandu", "arjuna"))

    def test_siblings_from_shared_parents(self):
        self.assertIn("sibling", self.keys("arjuna", "bhima"))
        self.assertIn("sibling", self.keys("bhima", "arjuna"))
        self.assertIn("sibling", self.keys("arjuna", "nakula"))     # shared father
        self.assertIn("sibling", self.keys("karna", "arjuna"))      # shared mother
        self.assertNotIn("kunti", self.F["nakula"])                 # no relation stored for the stepmother

    def test_other_inverses(self):
        self.assertIn("student", self.keys("drona", "arjuna"))
        self.assertIn("servant", self.keys("krishna", "arjuna"))
        self.assertIn("killed", self.keys("arjuna", "karna"))
        self.assertIn("spouse", self.keys("kunti", "pandu"))        # stored once, shown both ways

    def test_labels_and_circle_limit(self):
        rows = C.edges_for(self.W, self.F, "arjuna")
        lab = {r["id"]: r["en"] for r in rows}
        self.assertEqual(lab["pandu"], "father")
        self.assertEqual(lab["kunti"], "mother")
        top, rest = C.pick_circle(rows, limit=3)
        self.assertEqual(len(top), 3)
        self.assertEqual(len(top) + len(rest), len(rows))
        self.assertTrue(all(r["kind"] == "fam" for r in top))        # family first


class Names(unittest.TestCase):
    def test_lemmas(self):
        self.assertEqual(C.lemma_forms("Hanumat"), {"hanumat"})
        self.assertIn("karRa", C.lemma_forms("Karṇa"))
        self.assertIn("SiKaRqin", C.lemma_forms("Śikhaṇḍin"))
        self.assertIn("drOpadI", C.lemma_forms("Draupadī"))

    def test_unique_lemmas_only(self):
        W = mk([("a", "m", []), ("b", "m", [])])
        W["chars"]["a"]["epithets"] = ["Pārtha", "Arjuna"]
        W["chars"]["a"]["name"] = "Arjuna"
        W["chars"]["b"]["name"] = "Bhima"
        W["chars"]["b"]["epithets"] = ["Pārtha"]
        u = C.unique_lemmas(W)
        self.assertEqual(u.get("arjuna"), "a")
        self.assertNotIn("pArTa", u)
        cnt = C.count_mentions(W, {"arjuna": [1, 2], "pArTa": [9, 9]}, 2)
        self.assertEqual(cnt["a"], [1, 2])

    def test_kannada_names(self):
        self.assertEqual(C.names3("Sītā", "f")[0], "ಸೀತೆ")
        self.assertEqual(C.names3("Hanumat", "m")[0], "ಹನುಮಂತ")
        self.assertEqual(C.names3("Karṇa", "m")[0], "ಕರ್ಣ")


class Trees(unittest.TestCase):
    def test_layout(self):
        W = mk([("shantanu", "m", [("spouse", "ganga")]), ("ganga", "f", []), ("bhishma", "m", [("parent", "shantanu"), ("parent", "ganga")]),
                ("satyavati", "f", [("spouse", "shantanu")]), ("vichitra", "m", [("parent", "shantanu"), ("parent", "satyavati")]),
                ("vyasa", "m", [("parent", "satyavati")]), ("pandu", "m", [("parent", "vyasa")])])
        F = C.facts(W)
        lay = C.tree_layout(W, F, {"id": "t", "roots": ["shantanu"], "side": [], "full": "t"})
        pos, rows = lay["pos"], lay["rows"]
        self.assertEqual(set(pos), set(W["chars"]))
        self.assertEqual([rows[x] for x in ("shantanu", "ganga", "satyavati")], [0, 0, 0])
        self.assertEqual(rows["bhishma"], 1)
        self.assertEqual(rows["pandu"], 2)
        # spouses next to each other on the same row; no two nodes overlap
        self.assertEqual(pos["shantanu"][1], pos["ganga"][1])
        by_row = {}
        for m, (x, y) in pos.items():
            by_row.setdefault(y, []).append(x)
        for xs in by_row.values():
            xs.sort()
            self.assertTrue(all(b - a >= C.NW for a, b in zip(xs, xs[1:])), xs)
        svg = C.tree_svg(W, F, lay, {"bhishma": "../bhishma/"}, C.parent_rels(W))
        self.assertIn('href="../bhishma/"', svg)
        self.assertIn("t-kid", svg)

    def test_real_lines_do_not_crash(self):
        for w in C.WORKS:
            W = C.load(w)
            F = C.facts(W)
            for line in C.LINES[w]:
                lay = C.tree_layout(W, F, line)
                C.tree_svg(W, F, lay, {}, C.parent_rels(W))


if __name__ == "__main__":
    unittest.main()
