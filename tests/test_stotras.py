import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "etl"))
import stotras  # noqa: E402

DATA = json.loads((ROOT / "data" / "stotras.json").read_text(encoding="utf-8"))["stotras"]
KINDS = {"stotra", "stuti", "sahasranama", "namavali", "prayer"}
GP = ROOT / "data" / "gitas.json"
GITAS = json.loads(GP.read_text(encoding="utf-8"))["gitas"] if GP.exists() else []


class TestStotras(unittest.TestCase):
    def test_fields(self):
        ids = set()
        for st in DATA:
            with self.subTest(st=st["id"]):
                self.assertNotIn(st["id"], ids); ids.add(st["id"])
                self.assertIn(st["work"], ("ram", "mbh"))
                self.assertIn(st["kind"], KINDS)
                self.assertIn(st["deity"], {"vishnu", "shiva", "devi", "surya", "other"})
                for k in ("name_iast", "name_en", "by", "to"):
                    self.assertTrue(st[k].strip())
                self.assertTrue(st["loc"].get("vu") or st["loc"].get("ce"), "located in at least one edition")
                self.assertTrue(st["about"]["en"].strip() and st["about"]["kn"].strip(), "notes in both languages")
                self.assertTrue(st["sources"], "at least one source")

    def test_ranges_and_openings(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            bad = stotras.check(ROOT / "data" / "stotras.json")
        self.assertEqual(bad, 0, buf.getvalue())


class TestGitas(unittest.TestCase):
    def test_fields(self):
        ids = {st["id"] for st in DATA}
        for st in GITAS:
            with self.subTest(g=st["id"]):
                self.assertNotIn(st["id"], ids); ids.add(st["id"])
                self.assertEqual(st["work"], "mbh"); self.assertEqual(st["kind"], "gita")
                for k in ("name_iast", "name_en", "by", "to"):
                    self.assertTrue(st[k].strip())
                self.assertTrue(st["loc"].get("vu") or st["loc"].get("ce"))
                self.assertTrue(st["about"]["en"].strip() and st["about"]["kn"].strip(), "notes in both languages")
                self.assertTrue(st["sources"])

    def test_ranges(self):
        if not GITAS:
            self.skipTest("no gītās yet")
        buf = io.StringIO()
        with redirect_stdout(buf):
            bad = stotras.check(GP)
        self.assertEqual(bad, 0, buf.getvalue())


if __name__ == "__main__":
    unittest.main()


class TestUpakhyanas(unittest.TestCase):
    """data/upakhyanas.json: tales told inside the epics (v0.24)."""
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "data" / "upakhyanas.json").read_text(encoding="utf-8"))["upakhyanas"]

    def test_ranges_and_openings(self):
        import subprocess
        out = subprocess.run([sys.executable, str(ROOT / "etl" / "stotras.py"), "check", str(ROOT / "data" / "upakhyanas.json")], capture_output=True, text=True)
        self.assertIn(" 0 problems", out.stdout.strip().splitlines()[-1])

    def test_fields(self):
        ids = [u["id"] for u in self.data]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(self.data), 60)
        for u in self.data:
            for f in ("work", "name_iast", "name_en", "by", "to", "frame", "about", "loc"):
                self.assertTrue(u.get(f), (u["id"], f))
            self.assertTrue(u["about"].get("en") and u["about"].get("kn"), u["id"])
            self.assertEqual(u["kind"], "upakhyana")

    def test_twins_and_contains(self):
        twins = {}
        for u in self.data:
            if u.get("twin") and u["twin"] != "ramayana":
                twins.setdefault(u["twin"], set()).add(u["work"])
        for t, works in twins.items():
            self.assertEqual(works, {"ram", "mbh"}, t)    # a twin is the same tale in both epics
        known = {u["id"] for u in self.data}
        known |= {s["id"] for s in json.loads((ROOT / "data" / "stotras.json").read_text(encoding="utf-8"))["stotras"]}
        known |= {g["id"] for g in json.loads((ROOT / "data" / "gitas.json").read_text(encoding="utf-8"))["gitas"]}
        for u in self.data:
            for c in u.get("contains", []):
                self.assertIn(c, known, u["id"])
