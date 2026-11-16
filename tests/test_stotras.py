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


class TestStotras(unittest.TestCase):
    def test_fields(self):
        ids = set()
        for st in DATA:
            with self.subTest(st=st["id"]):
                self.assertNotIn(st["id"], ids); ids.add(st["id"])
                self.assertIn(st["work"], ("ram", "mbh"))
                self.assertIn(st["kind"], KINDS)
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


if __name__ == "__main__":
    unittest.main()
