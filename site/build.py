"""Stage 2+4: normalized JSONL -> static site in dist/

    python site/build.py [--out dist]

Pre-renders every verse in Kannada script, Devanāgarī and IAST (plus the
para-savarṇa nasal variant where it differs), writes one HTML page per
sarga, per-sarga JSON, and a compact per-edition search index.
"""
from __future__ import annotations

import argparse
import re
import json
import shutil
import sys
from collections import defaultdict
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "etl"))
import daily  # noqa: E402
import grammar  # noqa: E402
import card_art  # noqa: E402
import mbh_art  # noqa: E402
import meter  # noqa: E402
from translit import iast_to_slp1, render, slp1_to_brahmic, to_digits  # noqa: E402

SCRIPTS = ("knda", "deva", "iast")

KANDAS = [
    # (iast, kannada-ui, english)
    ("bālakāṇḍam", "ಬಾಲಕಾಂಡ", "Bāla Kāṇḍa"),
    ("ayodhyākāṇḍam", "ಅಯೋಧ್ಯಾಕಾಂಡ", "Ayodhyā Kāṇḍa"),
    ("araṇyakāṇḍam", "ಅರಣ್ಯಕಾಂಡ", "Araṇya Kāṇḍa"),
    ("kiṣkindhākāṇḍam", "ಕಿಷ್ಕಿಂಧಾಕಾಂಡ", "Kiṣkindhā Kāṇḍa"),
    ("sundarakāṇḍam", "ಸುಂದರಕಾಂಡ", "Sundara Kāṇḍa"),
    ("yuddhakāṇḍam", "ಯುದ್ಧಕಾಂಡ", "Yuddha Kāṇḍa"),
    ("uttarakāṇḍam", "ಉತ್ತರಕಾಂಡ", "Uttara Kāṇḍa"),
]


PARVANS = [(en.lower().replace(" ", ""), kn, en) for kn, en in mbh_art._NAMES]

WORKS = {
    "ram": dict(id="ram", prefix="", kn="ವಾಲ್ಮೀಕಿ ರಾಮಾಯಣ", en="Vālmīki Rāmāyaṇa", short_en="Rāmāyaṇa", short_kn="ರಾಮಾಯಣ", kn_chip="ರಾಮಾಯಣ",
                tile="ರಾ", theme="#1B2358", blurb="Sanskrit text with Kannada",
                editions="editions.json", units=KANDAS, unit="kāṇḍa", units_pl="kāṇḍas", Unit="Kāṇḍa",
                sub="sarga", subs="sargas", Sub="Sarga", sub_kn="ಸರ್ಗ", sub_deva="सर्गः", sub_iast="sargaḥ",
                epic_kn="ರಾಮಾಯಣದಲ್ಲಿ", lean=False, site="hms-cap.github.io/Ramayana",
                credit='Baroda Critical Edition text from <a href="https://gretil.sub.uni-goettingen.de/">GRETIL</a>, CC BY-NC-SA 4.0; Traditional (Vulgate) text from <a href="https://sa.wikisource.org/">Sanskrit Wikisource</a>, CC BY-SA 4.0. Not for commercial use.'),
    "mbh": dict(id="mbh", prefix="mbh/", kn="ಮಹಾಭಾರತ", en="Mahābhārata", short_en="Mahābhārata", short_kn="ಮಹಾಭಾರತ", kn_chip="ಮಹಾಭಾರತ",
                tile="ಮ", theme="#3B1220", blurb="Sanskrit text with Kannada",
                editions="editions_mbh.json", units=PARVANS, unit="parvan", units_pl="parvans", Unit="Parvan",
                sub="adhyāya", subs="adhyāyas", Sub="Adhyāya", sub_kn="ಅಧ್ಯಾಯ", sub_deva="अध्यायः", sub_iast="adhyāyaḥ",
                epic_kn="ಮಹಾಭಾರತದಲ್ಲಿ", lean=True, site="hms-cap.github.io/Ramayana/mbh",
                credit='Pune critical text © Bhandarkar Oriental Research Institute, via <a href="https://gretil.sub.uni-goettingen.de/">GRETIL</a>, shown with attribution for non-commercial reading; Traditional (Kumbakonam) text from <a href="https://github.com/sarit/SARIT-corpus">SARIT</a>, CC BY-SA 3.0. Not for commercial use.'),
}


def load_editions(W=None):
    return json.loads((ROOT / "data" / (W or WORKS["ram"])["editions"]).read_text(encoding="utf-8"))


def norm_path(W: dict, ed: str) -> Path:
    base = ROOT / "data" / "normalized"
    return (base / "mbh" if W["id"] == "mbh" else base) / f"{ed}.jsonl"


def unit_info(W: dict, k: int) -> dict:
    iast, kn, en = W["units"][k - 1]
    d = {"n": k, "iast": iast, "kn": kn, "en": en,
         "deva": slp1_to_brahmic(iast_to_slp1(iast), "deva"),
         "n_knda": to_digits(k, "knda")}
    if W["id"] == "mbh":
        bg, panel = mbh_art.PAL[(k - 1) % 6]
        d.update(kb=bg, kp=panel, svg=mbh_art.svg(k).replace('class="kart"', 'class="kart" data-v="0"', 1))
    d["alts"] = card_art.alts(W["id"], k)
    return d


def kanda_info(k: int) -> dict:
    return unit_info(WORKS["ram"], k)


def end_marks(script: str, ref: str) -> tuple[str, str]:
    nb = "\u00a0"  # keep daṇḍas on the line they close
    if script == "iast":
        return f"{nb}|", f"{nb}||{nb}{ref}{nb}||"
    return f"{nb}।", f"{nb}॥{nb}{to_digits(ref, script)}{nb}॥"


def render_verse(rec: dict, ed: dict) -> dict:
    slp_lines = [" ".join(iast_to_slp1(p) for p in line) for line in rec["lines"]]
    ref = f'{rec["k"]}.{rec["s"]}.{rec["v"]}'
    out = {}
    for sc in SCRIPTS:
        mid, last = end_marks(sc, ref)
        base = [render(l, sc) for l in slp_lines]
        base = [l + (last if i == len(base) - 1 else mid) for i, l in enumerate(base)]
        alt = None
        if sc != "iast":
            ps = [render(l, sc, savarna=True) for l in slp_lines]
            ps = [l + (last if i == len(ps) - 1 else mid) for i, l in enumerate(ps)]
            if ps != base:
                alt = ps
        out[sc] = {"lines": base, "savarna": alt}
    met = meter.identify([[iast_to_slp1(p) for p in line] for line in rec["lines"]])
    scan = [" ".join("".join("ऽ" if w == "G" else "।" for w in pada) for pada in line)
            for line in met["scansion"]]
    return {
        "lines": rec["lines"],
        "uid": rec["uid"], "k": rec["k"], "s": rec["s"], "v": rec["v"], "ref": ref,
        "v_knda": to_digits(rec["v"], "knda"), "v_deva": to_digits(rec["v"], "deva"),
        "text": out, "meter": rec.get("meter"), "scan": scan,
        "slp1": " / ".join(slp_lines),
        "ids": rec_ids(rec, ed),
        "crosswalk": crosswalk_for(rec, ed),
        "flags": rec.get("flags", []),
    }


def lean_verse(rec: dict, ed: dict | None = None, W: dict | None = None) -> dict:
    """Mahābhārata verse: IAST only (lean.js builds Kannada and Devanāgarī from it).
    With ed and W it also carries the cross-walk link and where its word-by-word data lives."""
    slp_lines = [" ".join(iast_to_slp1(p) for p in line) for line in rec["lines"]]
    ref = f'{rec["k"]}.{rec["s"]}.{rec["v"]}'
    mid, last = end_marks("iast", ref)
    lines = [render(l, "iast") + (last if i == len(slp_lines) - 1 else mid) for i, l in enumerate(slp_lines)]
    scan = []
    if rec.get("meter"):
        met = meter.identify([[iast_to_slp1(p) for p in line] for line in rec["lines"]])
        scan = [" ".join("".join("ऽ" if w == "G" else "।" for w in pada) for pada in line) for line in met["scansion"]]
    out = {"uid": rec["uid"], "k": rec["k"], "s": rec["s"], "v": rec["v"], "ref": ref, "iast": lines,
           "meter": rec.get("meter"), "scan": scan, "slp1": " / ".join(slp_lines), "flags": rec.get("flags", []),
           "ids": [{"label": "GRETIL", "value": rec["gretil_id"]}] if rec.get("gretil_id") else
                  [{"label": "Source", "value": rec["source_ref"]}] if rec.get("source_ref") else [],
           "crosswalk": None, "wsrc": None}
    if ed is not None:
        cw = crosswalk_for(rec, ed, W)
        out["crosswalk"] = cw
        if ed["id"] == "ce":
            if rec["uid"] in MBH_WORD_UIDS:
                out["wsrc"] = {"url": "words.json", "vn": rec["v"], "note": ""}
        elif cw and len(cw["links"]) == 1 and cw["status"] in ("match", "variant", "partial", "regrouped"):
            oe, tk, ts, tv = uid_ref(cw_target_uid(cw))
            if f"CE-{tk}-{ts:03d}-{tv:03d}" in MBH_WORD_UIDS:
                out["wsrc"] = {"url": cw["links"][0]["path"].split("#")[0] + "words.json", "vn": tv,
                               "note": "" if cw["status"] == "match" else cw["status"]}
    return out


def cw_target_uid(cw: dict) -> str:
    """'ce/6/23/#v4' -> 'CE-6-23-4' (uid_ref only needs the four parts)."""
    e, k, s, frag = cw["links"][0]["path"].split("/")
    return f"{e.upper()}-{k}-{s}-{frag[2:]}"


_CW: dict = {}                       # work id -> {"vu": {...}, "ce": {...}}
_SARGA_CW: dict = {}
WORDS: dict[str, list] = {}          # Rāmāyaṇa: CE verse uid -> word units
MBH_WORDS: dict[tuple, str] = {}     # Mahābhārata: (parvan, adhyāya) -> words.json text (built while reading, to keep memory low)
MBH_WORD_UIDS: set[str] = set()      # Pune verse uids that have words
GLOSS: dict[str, str] = {}
GLOSS_KN: dict[str, str] = {}


def _words_json(verses: dict, lemmas: set) -> str:
    return json.dumps({"verses": verses,
                       "gloss": {l: GLOSS[l] for l in sorted(lemmas) if l in GLOSS},
                       "kn": {l: GLOSS_KN[l] for l in sorted(lemmas) if l in GLOSS_KN}},
                      ensure_ascii=False, separators=(",", ":"))


def load_words() -> None:
    """Word-by-word analysis (DCS) and lemma glosses, keyed by Critical Edition verse uid."""
    import gzip
    wp = ROOT / "data" / "normalized" / "words.jsonl"
    gp = ROOT / "data" / "lexicon" / "gloss.json"
    kp = ROOT / "data" / "lexicon" / "gloss_kn.json"
    if wp.exists():
        for line in open(wp, encoding="utf-8"):
            r = json.loads(line)
            WORDS[r["uid"]] = r["units"]
    if gp.exists():
        GLOSS.update(json.loads(gp.read_text(encoding="utf-8")))
    if kp.exists():
        GLOSS_KN.update(json.loads(kp.read_text(encoding="utf-8")))
    mp = ROOT / "data" / "normalized" / "mbh" / "words.jsonl.gz"
    if mp.exists():
        cur, verses, lemmas, seen = None, {}, set(), set()
        for line in gzip.open(mp, "rt", encoding="utf-8"):
            r = json.loads(line)
            _, k, s, v = r["uid"].split("-")
            key = (int(k), int(s))
            if key != cur:
                if cur is not None:
                    MBH_WORDS[cur] = _words_json(verses, lemmas)
                assert key not in seen, f"words for {key} are not contiguous in {mp.name}"
                cur, verses, lemmas = key, {}, set()
                seen.add(key)
            verses[int(v)] = r["units"]
            MBH_WORD_UIDS.add(r["uid"])
            for u in r["units"]:
                lemmas.update(u["l"])
        if cur is not None:
            MBH_WORDS[cur] = _words_json(verses, lemmas)


_EDITION_LABEL = {"ce": "Baroda Text", "vu": "Traditional Text"}


def edition_label(W: dict | None, ed_id: str) -> str:
    if W is not None and W["id"] == "mbh":
        return {"ce": "Pune Text", "vu": "Traditional Text"}[ed_id]
    return _EDITION_LABEL[ed_id]
STATUS_TEXT = {
    "match": "{other} {refs}",
    "variant": "Different reading in the {other} ({refs})",
    "regrouped": "Lines grouped differently in the {other} ({refs})",
    "partial": "Only partly in the {other} ({refs})",
    "absent": "Not in the {other}",
}


def uid_ref(uid: str) -> tuple[str, int, int, int]:
    ed, k, s, v = uid.split("-")
    return ed.lower(), int(k), int(s), int(v)


def crosswalk_for(rec: dict, ed: dict, W: dict | None = None):
    """Per-verse link to the other edition, from data/crosswalk/[mbh/]verses.json."""
    wid = W["id"] if W else "ram"
    if wid not in _CW:
        p = ROOT / "data" / "crosswalk" / ("mbh" if wid == "mbh" else "") / "verses.json"
        _CW[wid] = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    entry = _CW[wid].get(ed["id"], {}).get(rec["uid"])
    if not entry:
        return None
    other = "ce" if ed["id"] == "vu" else "vu"
    links = []
    for t in entry.get("targets", []):
        oe, k, s, v = uid_ref(t)
        links.append({"ref": f"{k}.{s}.{v}", "path": f"{oe}/{k}/{s}/#v{v}"})
    return {"status": entry["status"], "other": other, "other_label": edition_label(W, other),
            "links": links, "score": entry.get("score")}


def rec_ids(rec: dict, ed: dict) -> list[dict]:
    ids = []
    if rec.get("gretil_id"):
        ids.append({"label": "GRETIL", "value": rec["gretil_id"]})
    if rec.get("source_ref"):
        ids.append({"label": ed.get("source_label", "Source"), "value": rec["source_ref"]})
    return ids


def make_env() -> Environment:
    env = Environment(loader=FileSystemLoader(ROOT / "site" / "templates"),
                      autoescape=select_autoescape(["html"]), trim_blocks=True, lstrip_blocks=True)
    env.filters["knda"] = lambda n: to_digits(n, "knda")
    env.filters["deva"] = lambda n: to_digits(n, "deva")
    return env


NO_WORDS_CE: set = set()


def no_words_note(k: int, s: int) -> str:
    if (k, s) == (6, 23) or (k == 6 and 23 <= s <= 40):
        return ("Word-by-word meanings are not available for the Bhagavadgītā (Bhīṣma Parvan 23–40 in the Pune text): "
                "the Digital Corpus of Sanskrit's Mahābhārata file leaves it out.")
    return "Word-by-word meanings are not available for this adhyāya: the Digital Corpus of Sanskrit's Mahābhārata file does not include it."


def build_work(W: dict, out: Path, env: Environment) -> dict:
    """One work (Rāmāyaṇa at the site root, Mahābhārata under /mbh/). Returns what the shared pages need."""
    pre = W["prefix"]
    wdir = out / pre if pre else out
    up = "../" * len([x for x in pre.split("/") if x])          # work root -> site root
    editions = load_editions(W)
    nu = len(W["units"])
    works_list = [{**w, "n_units": len(w["units"]), "n_eds": len(load_editions(w)), "icons": card_art.chip_icons(w["id"])} for w in WORKS.values()]
    base = dict(W=W, works_list=works_list, rail_kandas=[unit_info(W, k) for k in range(1, nu + 1)], rail_eds=editions, editions=editions)

    def ctx(depth: int, **kw) -> dict:
        return {**base, "wroot": "../" * depth, "root": up + "../" * depth, **kw}

    (wdir / "data").mkdir(parents=True, exist_ok=True)
    global NO_WORDS_CE
    if W["lean"]:
        ce_keys = {(r["k"], r["s"]) for r in map(json.loads, open(norm_path(W, "ce"), encoding="utf-8"))}
        NO_WORDS_CE = {key for key in ce_keys if key not in MBH_WORDS}
    summaries = []
    ce_titles = {}
    for ed in editions:
        recs = [json.loads(l) for l in open(norm_path(W, ed["id"]), encoding="utf-8")]
        by_sarga = defaultdict(list)
        for r in recs:
            by_sarga[(r["k"], r["s"])].append(r)
        sarga_keys = sorted(by_sarga)
        titles = {}
        tpath = ROOT / "data" / "normalized" / f'{ed["id"]}_sargas.json'
        if not W["lean"] and tpath.exists():
            for t in json.loads(tpath.read_text(encoding="utf-8")):
                titles[(t["k"], t["s"])] = t
        kandas = []
        for k in range(1, nu + 1):
            ks = [s for (kk, s) in sarga_keys if kk == k]
            kandas.append({**unit_info(W, k), "sargas": len(ks),
                           "verses": sum(len(by_sarga[(k, s)]) for s in ks)})
        summary = {**ed, "kandas": kandas, "verses": len(recs), "sargas": len(sarga_keys)}
        summaries.append(summary)
        if ed["id"] == "ce":
            ce_titles = titles

        index_rows = []
        for i, (k, s) in enumerate(sarga_keys):
            prev_key = sarga_keys[i - 1] if i > 0 else None
            next_key = sarga_keys[i + 1] if i + 1 < len(sarga_keys) else None
            page = wdir / ed["id"] / str(k) / str(s) / "index.html"
            page.parent.mkdir(parents=True, exist_ok=True)
            if W["lean"]:
                verses = [lean_verse(r, ed, W) for r in by_sarga[(k, s)]]
                other_id = "ce" if ed["id"] == "vu" else "vu"
                alt = alt_edition_href(ed, editions, k, s, W)
                wnote = ""
                if ed["id"] == "ce" and (k, s) in NO_WORDS_CE:
                    wnote = no_words_note(k, s)
                elif ed["id"] == "vu" and alt and tuple(map(int, alt["ref"].split("."))) in NO_WORDS_CE:
                    wnote = no_words_note(*map(int, alt["ref"].split(".")))
                if ed["id"] == "ce" and (k, s) in MBH_WORDS:
                    (page.parent / "words.json").write_text(MBH_WORDS[(k, s)], encoding="utf-8")
                page.write_text(env.get_template("sarga.html").render(**ctx(
                    3, ed=summary, kanda=kandas[k - 1], s=s, title=None, verses=verses, prev=prev_key, next=next_key,
                    total_in_kanda=kandas[k - 1]["sargas"], page="sarga", alt_href=alt,
                    shared=sum(1 for v in verses if v["crosswalk"] and v["crosswalk"]["status"] != "absent"),
                    has_cw=any(v["crosswalk"] for v in verses), wnote=wnote,
                    other_label=edition_label(W, other_id), other_id=other_id, iitk=False)), encoding="utf-8")
                for v in verses:
                    index_rows.append([k, s, v["v"], v["slp1"]])
                continue
            verses = [render_verse(r, ed) for r in by_sarga[(k, s)]]
            words = {}
            if ed["id"] == "ce":
                for v in verses:
                    if v["uid"] in WORDS:
                        words[v["v"]] = WORDS[v["uid"]]
                for v in verses:
                    v["has_words"] = v["v"] in words
            page.write_text(env.get_template("sarga.html").render(**ctx(
                3, ed=summary, kanda=kanda_info(k), s=s,
                title=titles.get((k, s)), verses=verses, prev=prev_key, next=next_key,
                total_in_kanda=kandas[k - 1]["sargas"], page="sarga",
                alt_href=alt_edition_href(ed, editions, k, s), wnote="",
                shared=sum(1 for v in verses if v["crosswalk"] and v["crosswalk"]["status"] != "absent"),
                has_cw=any(v["crosswalk"] for v in verses),
                other_label=_EDITION_LABEL["ce" if ed["id"] == "vu" else "vu"], other_id="ce" if ed["id"] == "vu" else "vu",
                iitk=any("iitk_restored" in v["flags"] for v in verses),
            )), encoding="utf-8")
            (page.parent / "sarga.json").write_text(json.dumps(
                {"edition": ed["id"], "kanda": k, "sarga": s,
                 "verses": [{key: v[key] for key in ("uid", "ref", "lines", "meter", "ids", "crosswalk", "flags")}
                            for v in verses]},
                ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
            if words:
                lemmas = {l for us in words.values() for u in us for l in u["l"]}
                (page.parent / "words.json").write_text(_words_json(words, lemmas), encoding="utf-8")
            for v in verses:
                index_rows.append([k, s, v["v"], v["slp1"]])

        for k in range(1, nu + 1):
            ks = [s for (kk, s) in sarga_keys if kk == k]
            items = []
            for s in ks:
                if W["lean"]:
                    r0 = next((r for r in by_sarga[(k, s)] if r["v"] >= 1), by_sarga[(k, s)][0])
                    line = render(" ".join(iast_to_slp1(p) for p in r0["lines"][0]), "knda")
                    first = {"text": {"knda": {"lines": [line]}}}
                else:
                    first = render_verse(by_sarga[(k, s)][0], ed)
                items.append({"s": s, "count": len(by_sarga[(k, s)]), "first": first, "title": titles.get((k, s))})
            page = wdir / ed["id"] / str(k) / "index.html"
            page.write_text(env.get_template("kanda.html").render(**ctx(
                2, ed=summary, kanda=kandas[k - 1], items=items, page="kanda")), encoding="utf-8")

        (wdir / "data" / f'search-{ed["id"]}.json').write_text(
            json.dumps(index_rows, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    fallback = build_daily(out, editions, ce_titles) if not W["lean"] else build_daily_mbh(wdir, W, editions)
    # work pages: home, read, search, edition lists
    common = dict(fallback=json.dumps(fallback, ensure_ascii=False), eds=summaries, ed=summaries[0])
    (wdir / "index.html").write_text(env.get_template("home.html").render(**ctx(0, page="home", **common)), encoding="utf-8")
    for name in ("search", "read"):
        p = wdir / name / "index.html"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(env.get_template(f"{name}.html").render(**ctx(1, page=name, **common)), encoding="utf-8")
    for ed in summaries:
        p = wdir / ed["id"] / "index.html"
        p.write_text(env.get_template("edition.html").render(**ctx(1, page="edition", **{**common, "ed": ed})), encoding="utf-8")
    print(f'  {W["id"]}: {sum(e["sargas"] for e in summaries)} pages for {", ".join(e["id"] for e in summaries)}')
    return {"W": W, "eds": summaries, "base": base}


def build(out: Path, only: str | None = None) -> None:
    env = make_env()
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(ROOT / "site" / "static", out / "static")
    sources = json.loads((ROOT / "etl" / "sources.json").read_text(encoding="utf-8"))
    load_words()
    (out / "data").mkdir(exist_ok=True)
    (out / "data" / "grammar.json").write_text(
        json.dumps(grammar.as_json(), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    build_dict(out)
    done = [build_work(W, out, env) for key, W in WORKS.items() if only in (None, key)]
    ram = next(d for d in done if d["W"]["id"] == "ram") if only in (None, "ram") else done[0]
    # shared pages at the site root: About and Saved (their tab bar is the Rāmāyaṇa's; app.js points it at the last-used work)
    cw_report = ROOT / "data" / "crosswalk" / "report.json"
    changes = json.loads((ROOT / "data" / "changes.json").read_text(encoding="utf-8"))
    mbh_rep = ROOT / "data" / "crosswalk" / "mbh" / "report.json"
    shared = dict(**ram["base"], mbh_cw=json.loads(mbh_rep.read_text()) if mbh_rep.exists() else None, wroot="../", root="../", changes=changes, sources=sources, eds=ram["eds"], ed=ram["eds"][0],
                  works=[(d["W"], d["eds"]) for d in done],
                  crosswalk=json.loads(cw_report.read_text()) if cw_report.exists() and len(ram["eds"]) > 1 else None)
    for name in ("about", "my"):
        p = out / name / "index.html"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(env.get_template(f"{name}.html").render(page=name, **shared), encoding="utf-8")
    write_pwa(out, done)
    (out / ".nojekyll").write_text("")
    print(f"built {sum(e['sargas'] for d in done for e in d['eds'])} sarga/adhyāya pages -> {out}")


def build_dict(out: Path) -> None:
    """The Śabdārtha Kaustubha dictionary app (vendor/kosha, copied from hms-cap/VedaAlokana by etl/sync_kosha.sh)
    goes to dist/dict/ unchanged, except for a link back to Itihāsa in its top bar."""
    src = ROOT / "vendor" / "kosha"
    if not src.exists():
        return
    shutil.copytree(src, out / "dict")
    (out / "dict" / "SOURCE.txt").unlink(missing_ok=True)
    page = out / "dict" / "kosha" / "index.html"
    html = page.read_text(encoding="utf-8")
    assert '<span class="sp"></span>' in html and "</head>" in html
    html = html.replace('<span class="sp"></span>', '<span class="sp"></span><a class="itihasa-back" href="../../" lang="kn">\u0c87\u0ca4\u0cbf\u0cb9\u0cbe\u0cb8</a>', 1)
    html = html.replace("</head>", '<link rel="stylesheet" href="itihasa.css">\n</head>', 1)
    page.write_text(html, encoding="utf-8")
    (out / "dict" / "kosha" / "itihasa.css").write_text(
        ".itihasa-back{font-size:.9rem;font-weight:700;text-decoration:none;color:inherit;border:1px solid currentColor;border-radius:999px;padding:.25rem .8rem;opacity:.85}\n"
        ".itihasa-back:hover{opacity:1}\n", encoding="utf-8")


def build_daily(out: Path, editions, titles: dict) -> dict:
    """365 automatic verse-of-the-day cards (etl/daily.py) -> dist/data/daily/. Returns the fallback card."""
    ed = next(e for e in editions if e["id"] == "ce")
    recs = [json.loads(l) for l in open(ROOT / "data" / "normalized" / "ce.jsonl", encoding="utf-8")]
    cur = json.loads((ROOT / "data" / "daily" / "curated.json").read_text(encoding="utf-8"))
    cur.pop("_comment", None)
    sizes = defaultdict(int)
    for r in recs:
        sizes[(r["k"], r["s"])] += 1
    def metre_of(r):
        return r.get("meter")

    def has_match(r):
        cw = crosswalk_for(r, ed)
        return bool(cw) and cw["status"] == "match" and len(cw["links"]) == 1

    chosen = daily.select(recs, WORDS, metre_of, has_match)

    def card(r):
        v = render_verse(r, ed)
        k = kanda_info(r["k"])
        units = []
        for u in WORDS[r["uid"]]:
            g = GLOSS.get(u["l"][-1], "")          # the head word of a compound carries the grammar
            g = re.sub(r"^(?:p\. ?p\. ?\d*\s*|pass\. ?\d*\s*|Ved\.\s*|[PAU]\.,?\s*)", "", g.split(" | ")[0]).strip()
            if len(g) > 70:
                g = g[:70].rsplit(",", 1)[0].rsplit(" ", 1)[0] if "," in g[:70] else g[:70].rsplit(" ", 1)[0]
            if g and u["t"].get("pos") != "i" and len(units) < 8:
                d = {"f": u["f"], "l": u["l"], "t": u["t"], "g": g}
                if GLOSS_KN.get(u["l"][-1]):
                    d["k"] = GLOSS_KN[u["l"][-1]]
                units.append(d)
        cw = v["crosswalk"]
        c = {"uid": r["uid"], "ref": v["ref"], "path": f'ce/{r["k"]}/{r["s"]}/#v{r["v"]}',
             "slp": v["slp1"].split(" / "), "meter": v["meter"], "scan": v["scan"],
             "ctx": {"k": r["k"], "kn": k["kn"], "deva": k["deva"], "iast": k["iast"], "en": k["en"], "s": r["s"], "v": r["v"],
                     "of": sizes[(r["k"], r["s"])], "title": (titles.get((r["k"], r["s"])) or {}).get("title_iast", "")},
             "w": units}
        if cw:
            c["cw"] = {"status": cw["status"], "refs": [l["ref"] for l in cw["links"]], "paths": [l["path"] for l in cw["links"]]}
        if r["uid"] in cur:
            c.update({kk: vv for kk, vv in cur[r["uid"]].items() if kk in ("m", "u")})
        return c

    cards = [card(r) for r in chosen]
    assert len(cards) == daily.N, len(cards)
    daily.write(out, cards)
    first = next(r for r in recs if r["uid"] == "CE-1-001-001")
    return card(first)


def build_daily_mbh(wdir: Path, W: dict, editions) -> dict:
    """365 verse-of-the-day cards for the Mahābhārata, from the Traditional Text (the default reading text).
    Only verses that match a Pune verse exactly are eligible, so the word-by-word card (taken from that Pune
    verse, DCS) is right for the verse shown. Same deterministic rule as the Rāmāyaṇa (etl/daily.py)."""
    import gzip
    ed_vu = next(e for e in editions if e["id"] == "vu")
    recs = [json.loads(l) for l in open(norm_path(W, "vu"), encoding="utf-8")]
    sizes = defaultdict(int)
    for r in recs:
        sizes[(r["k"], r["s"])] += 1

    def target(r):
        cw = crosswalk_for(r, ed_vu, W)
        if not cw or cw["status"] != "match" or len(cw["links"]) != 1:
            return None
        tid = cw_target_uid(cw)
        e, tk, ts, tv = uid_ref(tid)
        uid = f"CE-{tk}-{ts:03d}-{tv:03d}"
        return (uid, cw) if uid in MBH_WORD_UIDS else None

    ok = {r["uid"]: target(r) for r in recs}
    elig_words = {u: range(8) for u, t in ok.items() if t}          # daily.select only checks membership and a size range
    def accept(r):
        return r["v"] >= 1 and sum(len(" ".join(l)) for l in r["lines"]) <= 130

    chosen = daily.select(recs, elig_words, lambda r: r.get("meter"), accept)
    want = {ok[r["uid"]][0] for r in chosen}
    units_of = {}
    for line in gzip.open(ROOT / "data" / "normalized" / "mbh" / "words.jsonl.gz", "rt", encoding="utf-8"):
        r = json.loads(line)
        if r["uid"] in want:
            units_of[r["uid"]] = r["units"]

    def card(r):
        v = lean_verse(r)
        k = unit_info(W, r["k"])
        cuid, cw = ok[r["uid"]]
        units = []
        for u in units_of[cuid]:
            g = GLOSS.get(u["l"][-1], "")          # the head word of a compound carries the grammar
            g = re.sub(r"^(?:p\. ?p\. ?\d*\s*|pass\. ?\d*\s*|Ved\.\s*|[PAU]\.,?\s*)", "", g.split(" | ")[0]).strip()
            if len(g) > 70:
                g = g[:70].rsplit(",", 1)[0].rsplit(" ", 1)[0] if "," in g[:70] else g[:70].rsplit(" ", 1)[0]
            if g and u["t"].get("pos") != "i" and len(units) < 8:
                d = {"f": u["f"], "l": u["l"], "t": u["t"], "g": g}
                kn = GLOSS_KN.get(u["l"][-1])
                if kn:
                    d["k"] = kn
                units.append(d)
        return {"uid": r["uid"], "ref": v["ref"], "ed": "vu", "path": f'vu/{r["k"]}/{r["s"]}/#v{r["v"]}',
                "slp": v["slp1"].split(" / "), "meter": v["meter"], "scan": v["scan"],
                "ctx": {"k": r["k"], "kn": k["kn"], "deva": k["deva"], "iast": k["iast"], "en": k["en"], "s": r["s"], "v": r["v"],
                        "of": sizes[(r["k"], r["s"])], "title": ""},
                "w": units,
                "cw": {"status": "match", "refs": [l["ref"] for l in cw["links"]], "paths": [l["path"] for l in cw["links"]],
                       "other": cw["other_label"], "other_kn": "ಪುಣೆ ಪರಿಷ್ಕೃತ ಪಾಠ"}}

    cards = [card(r) for r in chosen]
    assert len(cards) == daily.N, len(cards)
    daily.write(wdir, cards)
    return cards[0]


def write_pwa(out: Path, done: list) -> None:
    """Service worker (with its shell list), manifest, and the offline download packs."""
    shell = ["", "about/", "my/"]
    for d in done:
        pre = d["W"]["prefix"]
        nu = len(d["W"]["units"])
        shell += [pre, f"{pre}read/", f"{pre}search/"] if pre else ["read/", "search/"]
        for e in d["eds"]:
            shell.append(f'{pre}{e["id"]}/')
            shell += [f'{pre}{e["id"]}/{k}/' for k in range(1, nu + 1)]
        shell += [f"{pre}data/daily/index.json"]
    shell += ["data/grammar.json", "manifest.webmanifest"]
    shell += sorted(str(p.relative_to(out)) for p in (out / "static").rglob("*") if p.is_file() and p.suffix != ".txt")
    sw = (ROOT / "site" / "sw.js").read_text(encoding="utf-8").replace("/*SHELL_FILES*/[]", json.dumps(shell))
    (out / "sw.js").write_text(sw, encoding="utf-8")
    shutil.copy(ROOT / "site" / "manifest.webmanifest", out / "manifest.webmanifest")
    packs = []

    def size(paths):
        return sum((out / p.rstrip("/") / "index.html").stat().st_size if p.endswith("/") else (out / p).stat().st_size for p in paths)

    for d in done:
        W, pre = d["W"], d["W"]["prefix"]
        for e in d["eds"]:
            for k in range(1, len(W["units"]) + 1):
                urls = []
                for sd in sorted((out / pre / e["id"] / str(k)).iterdir(), key=lambda x: int(x.name) if x.name.isdigit() else 0):
                    if sd.is_dir():
                        urls.append(f'{pre}{e["id"]}/{k}/{sd.name}/')
                        if (sd / "words.json").exists():
                            urls.append(f'{pre}{e["id"]}/{k}/{sd.name}/words.json')
                kn = unit_info(W, k)
                label = f'{e["short"]}: {kn["en"]}' if not pre else f'{W["short_en"]}, {e["short"]}: {kn["en"]}'
                packs.append({"id": f'{pre.strip("/")}{"-" if pre else ""}{e["id"]}-{k}', "label": label, "urls": urls, "bytes": size(urls)})
        core = [f"{pre}data/search-{e['id']}.json" for e in d["eds"]] + [f"{pre}data/daily/c{i}.json" for i in range(8)]
        packs.append({"id": f'{pre.strip("/") or "ram"}-core', "label": ("Search index and verse-of-the-day cards" if not pre else f'{W["short_en"]}: search index and verse-of-the-day cards'),
                      "urls": core, "bytes": size(core)})
    (out / "data" / "offline.json").write_text(json.dumps({"version": json.loads((ROOT / "data" / "changes.json").read_text())[0][0], "packs": packs},
                                                         ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def alt_edition_href(ed, editions, k, s, W=None):
    """Link to the same sarga in the other edition, when the sarga cross-walk knows it."""
    wid = W["id"] if W else "ram"
    if wid not in _SARGA_CW:
        cw_path = ROOT / "data" / "crosswalk" / ("mbh" if wid == "mbh" else "") / "sargas.json"
        _SARGA_CW[wid] = json.loads(cw_path.read_text(encoding="utf-8")) if cw_path.exists() else {}
    tgt = _SARGA_CW[wid].get(f"{ed['id']}:{k}.{s}")
    if not tgt:
        return None
    other, ks = tgt.split(":")
    kk, ss = ks.split(".")
    label = next((e["short"] for e in editions if e["id"] == other), other)
    return {"href": f"../../../{other}/{kk}/{ss}/", "label": label, "ref": ks}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "dist"))
    ap.add_argument("--only", choices=list(WORKS), help="build one work only (faster while developing)")
    a = ap.parse_args()
    build(Path(a.out), a.only)
