"""Transliteration tests.

Run:  python -m unittest discover -s tests
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "etl"))
import meter  # noqa: E402
from translit import (anusvara_before_stops, ascii_query_to_loose, brahmic_to_slp1, iast_to_slp1, join_for_display,  # noqa: E402
                      loose_for_index, render, slp1_to_iast)

CE = ROOT / "data" / "normalized" / "ce.jsonl"


def ce_lines(limit=None):
    out = []
    with open(CE, encoding="utf-8") as f:
        for i, l in enumerate(f):
            if limit and i >= limit:
                break
            r = json.loads(l)
            out += [" ".join(p) for p in r["lines"]]
    return out


class Golden(unittest.TestCase):
    """Specimen 1.1.1 as given in the project plan."""

    def test_kannada(self):
        s = iast_to_slp1("nāradaṃ paripapraccha vālmīkir munipuṃgavam")
        self.assertEqual(render(s, "knda"), "ನಾರದಂ ಪರಿಪಪ್ರಚ್ಛ ವಾಲ್ಮೀಕಿರ್ಮುನಿಪುಂಗವಮ್")
        self.assertEqual(render(s, "knda", savarna=True), "ನಾರದಂ ಪರಿಪಪ್ರಚ್ಛ ವಾಲ್ಮೀಕಿರ್ಮುನಿಪುಙ್ಗವಮ್")

    def test_devanagari(self):
        s = iast_to_slp1("tapaḥsvādhyāyanirataṃ tapasvī vāgvidāṃ varam")
        self.assertEqual(render(s, "deva"), "तपःस्वाध्यायनिरतं तपस्वी वाग्विदां वरम्")

    def test_avagraha_and_vocalic_l(self):
        self.assertEqual(render(iast_to_slp1("śūdro 'pi"), "knda"), "ಶೂದ್ರೋಽಪಿ")
        self.assertEqual(render(iast_to_slp1("kḷptam"), "deva"), "कॢप्तम्")

    def test_loose_search_keys(self):
        target = loose_for_index(iast_to_slp1("mārīca"))
        self.assertEqual(target, "marica")
        self.assertEqual(ascii_query_to_loose("maricha"), target)
        self.assertEqual(loose_for_index(brahmic_to_slp1("ಮಾರೀಚ")), target)
        self.assertEqual(loose_for_index(brahmic_to_slp1("मारीच")), target)
        self.assertEqual(ascii_query_to_loose("krishna"), loose_for_index(iast_to_slp1("kṛṣṇa")))
        self.assertEqual(ascii_query_to_loose("Seetha"), loose_for_index(iast_to_slp1("sītā")))


class KannadaAnusvara(unittest.TestCase):
    def test_class_nasal_becomes_anusvara_in_kannada_only(self):
        s = iast_to_slp1("saṅgo'stvakarmaṇi kāñcanaḥ kampa anta")
        self.assertEqual(render(s, "knda"), "ಸಂಗೋಽಸ್ತ್ವಕರ್ಮಣಿ ಕಾಂಚನಃ ಕಂಪ ಅಂತ")
        self.assertEqual(render(s, "deva"), "सङ्गोऽस्त्वकर्मणि काञ्चनः कम्प अन्त")
        self.assertEqual(render(s, "knda", savarna=True), "ಸಙ್ಗೋಽಸ್ತ್ವಕರ್ಮಣಿ ಕಾಞ್ಚನಃ ಕಮ್ಪ ಅನ್ತ")

    def test_not_across_words_or_classes(self):
        self.assertEqual(render(iast_to_slp1("tasmin tu"), "knda"), "ತಸ್ಮಿನ್ತು")     # word boundary: left alone
        self.assertEqual(render(iast_to_slp1("yasmin gatā"), "knda"), "ಯಸ್ಮಿನ್ಗತಾ")  # n before g: not the same class


class PancamaSwitch(unittest.TestCase):
    """"Classical pañcama" (pref key savarna) is Kannada-only."""

    S = iast_to_slp1("nāradaṃ paripapraccha vālmīkir munipuṃgavam saṅgo'stvakarmaṇi kāñcanaḥ")

    def test_devanagari_and_iast_ignore_it(self):
        for sc in ("deva", "iast"):
            self.assertEqual(render(self.S, sc, savarna=True), render(self.S, sc), sc)
        self.assertEqual(render(iast_to_slp1("munipuṃgavam"), "deva", savarna=True), "मुनिपुंगवम्")

    def test_kannada_switches_to_class_nasal(self):
        self.assertIn("ಪುಂಗವ", render(self.S, "knda"))
        self.assertIn("ಪುಙ್ಗವ", render(self.S, "knda", savarna=True))
        self.assertNotIn("ಂಗ", render(iast_to_slp1("munipuṃgavam"), "knda", savarna=True))

    def test_built_verse_has_kannada_variant_only(self):
        sys.path.insert(0, str(ROOT / "site"))
        import build
        ed = build.load_editions()[0]
        rec = json.loads((ROOT / "data" / "normalized" / "ce.jsonl").read_text(encoding="utf-8").splitlines()[0])
        t = build.render_verse(rec, ed)["text"]
        self.assertTrue(t["knda"]["savarna"])             # 1.1.1 has "puṃgavam"
        self.assertIsNone(t["deva"]["savarna"])
        self.assertIsNone(t["iast"]["savarna"])
        from jinja2 import Environment, FileSystemLoader
        env = Environment(loader=FileSystemLoader(str(ROOT / "site" / "templates")), autoescape=True)
        html = env.from_string('{% from "_verse.html" import verse_text %}{{ verse_text(v) }}').render(v={**build.render_verse(rec, ed), "speaker": None})
        self.assertEqual(html.count('class="ps1"'), 1)
        self.assertEqual(html.count('class="ps0"'), 1)
        self.assertEqual(html.count("ps1"), 1)
        self.assertIn('<span class="d">', html)
        self.assertNotIn("&lt;span", html)


class RoundTrip(unittest.TestCase):
    def test_whole_ce_round_trips(self):
        bad = []
        for line in ce_lines():
            slp = iast_to_slp1(line)
            if slp1_to_iast(slp) != line:
                bad.append(("iast", line))
            for sc in ("knda", "deva"):
                want = join_for_display(anusvara_before_stops(slp) if sc == "knda" else slp)   # Kannada writes ಂ before a same-class stop
                if brahmic_to_slp1(render(slp, sc)) != want:
                    bad.append((sc, line))
        self.assertEqual(bad[:5], [])

    def test_no_stray_latin_in_brahmic(self):
        for line in ce_lines(3000):
            out = render(iast_to_slp1(line), "knda")
            self.assertRegex(out, r"^[ಀ-೿ ]+$", line)


class Metre(unittest.TestCase):
    def test_anustubh(self):
        r = meter.identify([[iast_to_slp1("tapaḥsvādhyāyanirataṃ tapasvī vāgvidāṃ varam")],
                            [iast_to_slp1("nāradaṃ paripapraccha vālmīkir munipuṃgavam")]])
        self.assertEqual(r["name"], "Anuṣṭubh")

    def test_upajati(self):
        r = meter.identify([[iast_to_slp1("paṭhan dvijo vāgṛṣabhatvam īyāt"), iast_to_slp1("syāt kṣatriyo bhūmipatitvam īyāt")],
                            [iast_to_slp1("vaṇigjanaḥ paṇyaphalatvam īyāj"), iast_to_slp1("janaś ca śūdro 'pi mahattvam īyāt")]])
        self.assertIn(r["name"], ("Upajāti", "Indravajrā", "Upendravajrā"))


class JsParity(unittest.TestCase):
    """site/static/translit.js must produce exactly what etl/translit.py does."""

    def test_parity(self):
        lines = ce_lines(4000)
        py = [[render(iast_to_slp1(l), "knda"), render(iast_to_slp1(l), "deva"),
               render(iast_to_slp1(l), "knda", savarna=True), slp1_to_iast(iast_to_slp1(l)),
               loose_for_index(iast_to_slp1(l))] for l in lines]
        js = r"""
const fs=require('fs'); require(process.argv[1]); const T=globalThis.Translit;
const lines=JSON.parse(fs.readFileSync(0,'utf8'));
const out=lines.map(l=>{const s=T.iastToSlp1(l);return [T.render(s,'knda'),T.render(s,'deva'),T.render(s,'knda',true),T.slp1ToIast(s),T.looseForIndex(s)];});
const q=['maricha','Seetha','krishna','ಮಾರೀಚ','मारीच','mārīca','hanuman'].map(T.queryToLoose);
process.stdout.write(JSON.stringify({out,q}));
"""
        try:
            res = subprocess.run(["node", "-e", js, str(ROOT / "site" / "static" / "translit.js")],
                                 input=json.dumps(lines), capture_output=True, text=True, check=True)
        except FileNotFoundError:
            self.skipTest("node not installed")
        got = json.loads(res.stdout)
        mism = [(lines[i], a, b) for i, (a, b) in enumerate(zip(py, got["out"])) if a != b]
        self.assertEqual(mism[:3], [])
        expect_q = [ascii_query_to_loose("maricha"), ascii_query_to_loose("Seetha"), ascii_query_to_loose("krishna"),
                    loose_for_index(brahmic_to_slp1("ಮಾರೀಚ")), loose_for_index(brahmic_to_slp1("मारीच")),
                    loose_for_index(iast_to_slp1("mārīca")), ascii_query_to_loose("hanuman")]
        self.assertEqual(got["q"], expect_q)


if __name__ == "__main__":
    unittest.main()
