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


def load_editions():
    return json.loads((ROOT / "data" / "editions.json").read_text(encoding="utf-8"))


def kanda_info(k: int) -> dict:
    iast, kn, en = KANDAS[k - 1]
    return {"n": k, "iast": iast, "kn": kn, "en": en,
            "deva": slp1_to_brahmic(iast_to_slp1(iast), "deva"),
            "n_knda": to_digits(k, "knda")}


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


_CW = None
WORDS: dict[str, list] = {}
GLOSS: dict[str, str] = {}


def load_words() -> None:
    """Word-by-word analysis (DCS) and lemma glosses, keyed by Critical Edition verse uid."""
    wp = ROOT / "data" / "normalized" / "words.jsonl"
    gp = ROOT / "data" / "lexicon" / "gloss.json"
    if wp.exists():
        for line in open(wp, encoding="utf-8"):
            r = json.loads(line)
            WORDS[r["uid"]] = r["units"]
    if gp.exists():
        GLOSS.update(json.loads(gp.read_text(encoding="utf-8")))
_EDITION_LABEL = {"ce": "Critical Edition", "vu": "Vulgate"}
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


def crosswalk_for(rec: dict, ed: dict):
    """Per-verse link to the other edition, from data/crosswalk/verses.json."""
    global _CW
    if _CW is None:
        p = ROOT / "data" / "crosswalk" / "verses.json"
        _CW = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    entry = _CW.get(ed["id"], {}).get(rec["uid"])
    if not entry:
        return None
    other = "ce" if ed["id"] == "vu" else "vu"
    links = []
    for t in entry.get("targets", []):
        oe, k, s, v = uid_ref(t)
        links.append({"ref": f"{k}.{s}.{v}", "path": f"{oe}/{k}/{s}/#v{v}"})
    return {"status": entry["status"], "other": other, "other_label": _EDITION_LABEL[other],
            "links": links, "score": entry.get("score")}


def rec_ids(rec: dict, ed: dict) -> list[dict]:
    ids = []
    if rec.get("gretil_id"):
        ids.append({"label": "GRETIL", "value": rec["gretil_id"]})
    if rec.get("source_ref"):
        ids.append({"label": ed.get("source_label", "Source"), "value": rec["source_ref"]})
    return ids


def build(out: Path) -> None:
    editions = load_editions()
    env = Environment(loader=FileSystemLoader(ROOT / "site" / "templates"),
                      autoescape=select_autoescape(["html"]), trim_blocks=True, lstrip_blocks=True)
    env.filters["knda"] = lambda n: to_digits(n, "knda")
    env.filters["deva"] = lambda n: to_digits(n, "deva")
    env.globals["rail_kandas"] = [kanda_info(k) for k in range(1, 8)]
    env.globals["rail_eds"] = editions
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(ROOT / "site" / "static", out / "static")
    sources = json.loads((ROOT / "etl" / "sources.json").read_text(encoding="utf-8"))
    load_words()
    (out / "data").mkdir(exist_ok=True)
    (out / "data" / "grammar.json").write_text(
        json.dumps(grammar.as_json(), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    edition_summaries = []
    for ed in editions:
        recs = [json.loads(l) for l in open(ROOT / "data" / "normalized" / f'{ed["id"]}.jsonl', encoding="utf-8")]
        by_sarga = defaultdict(list)
        for r in recs:
            by_sarga[(r["k"], r["s"])].append(r)
        sarga_keys = sorted(by_sarga)
        titles = {}
        tpath = ROOT / "data" / "normalized" / f'{ed["id"]}_sargas.json'
        if tpath.exists():
            for t in json.loads(tpath.read_text(encoding="utf-8")):
                titles[(t["k"], t["s"])] = t
        kandas = []
        for k in range(1, 8):
            ks = [s for (kk, s) in sarga_keys if kk == k]
            kandas.append({**kanda_info(k), "sargas": len(ks),
                           "verses": sum(len(by_sarga[(k, s)]) for s in ks)})
        summary = {**ed, "kandas": kandas, "verses": len(recs), "sargas": len(sarga_keys)}
        edition_summaries.append(summary)
        if ed["id"] == "ce":
            ce_titles = titles

        index_rows = []
        for i, (k, s) in enumerate(sarga_keys):
            verses = [render_verse(r, ed) for r in by_sarga[(k, s)]]
            words = {}
            if ed["id"] == "ce":
                for v in verses:
                    if v["uid"] in WORDS:
                        words[v["v"]] = WORDS[v["uid"]]
                for v in verses:
                    v["has_words"] = v["v"] in words
            prev_key = sarga_keys[i - 1] if i > 0 else None
            next_key = sarga_keys[i + 1] if i + 1 < len(sarga_keys) else None
            page = out / ed["id"] / str(k) / str(s) / "index.html"
            page.parent.mkdir(parents=True, exist_ok=True)
            page.write_text(env.get_template("sarga.html").render(
                root="../../../", ed=summary, editions=editions, kanda=kanda_info(k), s=s,
                title=titles.get((k, s)), verses=verses, prev=prev_key, next=next_key,
                total_in_kanda=kandas[k - 1]["sargas"], page="sarga",
                alt_href=alt_edition_href(ed, editions, k, s),
                shared=sum(1 for v in verses if v["crosswalk"] and v["crosswalk"]["status"] != "absent"),
                has_cw=any(v["crosswalk"] for v in verses),
                other_label="Critical Edition" if ed["id"] == "vu" else "Vulgate",
                iitk=any("iitk_restored" in v["flags"] for v in verses),
            ), encoding="utf-8")
            (page.parent / "sarga.json").write_text(json.dumps(
                {"edition": ed["id"], "kanda": k, "sarga": s,
                 "verses": [{key: v[key] for key in ("uid", "ref", "lines", "meter", "ids", "crosswalk", "flags")}
                            for v in verses]},
                ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
            if words:
                lemmas = {l for us in words.values() for u in us for l in u["l"]}
                (page.parent / "words.json").write_text(json.dumps(
                    {"verses": words, "gloss": {l: GLOSS[l] for l in sorted(lemmas) if l in GLOSS}},
                    ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
            for v in verses:
                index_rows.append([k, s, v["v"], v["slp1"]])

        for k in range(1, 8):
            ks = [s for (kk, s) in sarga_keys if kk == k]
            items = []
            for s in ks:
                first = render_verse(by_sarga[(k, s)][0], ed)
                items.append({"s": s, "count": len(by_sarga[(k, s)]), "first": first,
                              "title": titles.get((k, s))})
            page = out / ed["id"] / str(k) / "index.html"
            page.write_text(env.get_template("kanda.html").render(
                root="../../", ed=summary, editions=editions, kanda=kandas[k - 1], items=items,
                page="kanda"), encoding="utf-8")

        (out / "data").mkdir(exist_ok=True)
        (out / "data" / f'search-{ed["id"]}.json').write_text(
            json.dumps(index_rows, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    fallback = build_daily(out, editions, ce_titles)
    cw_report = ROOT / "data" / "crosswalk" / "report.json"
    changes = json.loads((ROOT / "data" / "changes.json").read_text(encoding="utf-8"))
    common = dict(changes=changes, fallback=json.dumps(fallback, ensure_ascii=False), editions=editions, eds=edition_summaries, ed=edition_summaries[0], sources=sources,
                  crosswalk=json.loads(cw_report.read_text()) if cw_report.exists() and len(edition_summaries) > 1 else None)
    (out / "index.html").write_text(env.get_template("home.html").render(root="", page="home", **common), encoding="utf-8")
    for name in ("search", "about", "my"):
        p = out / name / "index.html"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(env.get_template(f"{name}.html").render(root="../", page=name, **common), encoding="utf-8")
    for ed in edition_summaries:  # /ce/ -> list of kāṇḍas
        p = out / ed["id"] / "index.html"
        p.write_text(env.get_template("edition.html").render(root="../", page="edition",
                                                             **{**common, "ed": ed}), encoding="utf-8")
    write_pwa(out, edition_summaries)
    (out / ".nojekyll").write_text("")
    print(f"built {sum(e['sargas'] for e in edition_summaries)} sarga pages "
          f"for {', '.join(e['id'] for e in edition_summaries)} -> {out}")


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

    chosen = daily.select(recs, WORDS, metre_of)

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
                units.append({"f": u["f"], "l": u["l"], "t": u["t"], "g": g})
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


def write_pwa(out: Path, eds) -> None:
    """Service worker (with its shell list), manifest, and the offline download packs."""
    shell = ["", "search/", "about/", "my/"]
    for e in eds:
        shell.append(f'{e["id"]}/')
        shell += [f'{e["id"]}/{k}/' for k in range(1, 8)]
    shell += ["data/grammar.json", "data/daily/index.json", "manifest.webmanifest"]
    shell += sorted(str(p.relative_to(out)) for p in (out / "static").rglob("*") if p.is_file() and p.suffix != ".txt")
    sw = (ROOT / "site" / "sw.js").read_text(encoding="utf-8").replace("/*SHELL_FILES*/[]", json.dumps(shell))
    (out / "sw.js").write_text(sw, encoding="utf-8")
    shutil.copy(ROOT / "site" / "manifest.webmanifest", out / "manifest.webmanifest")
    packs = []

    def size(paths):
        return sum((out / p.rstrip("/") / "index.html").stat().st_size if p.endswith("/") else (out / p).stat().st_size for p in paths)

    for e in eds:
        for k in range(1, 8):
            urls = []
            for d in sorted((out / e["id"] / str(k)).iterdir(), key=lambda x: int(x.name) if x.name.isdigit() else 0):
                if d.is_dir():
                    urls.append(f'{e["id"]}/{k}/{d.name}/')
                    if (d / "words.json").exists():
                        urls.append(f'{e["id"]}/{k}/{d.name}/words.json')
            kn = kanda_info(k)
            packs.append({"id": f'{e["id"]}-{k}', "label": f'{e["short"]}: {kn["en"]}', "urls": urls, "bytes": size(urls)})
    core = [f"data/search-{e['id']}.json" for e in eds] + [f"data/daily/c{i}.json" for i in range(8)]
    packs.append({"id": "core", "label": "Search index and verse-of-the-day cards", "urls": core, "bytes": size(core)})
    (out / "data" / "offline.json").write_text(json.dumps({"version": json.loads((ROOT / "data" / "changes.json").read_text())[0][0], "packs": packs},
                                                         ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def alt_edition_href(ed, editions, k, s):
    """Link to the same sarga in the other edition, when the sarga cross-walk knows it."""
    cw_path = ROOT / "data" / "crosswalk" / "sargas.json"
    if not cw_path.exists():
        return None
    global _SARGA_CW
    try:
        _SARGA_CW
    except NameError:
        _SARGA_CW = json.loads(cw_path.read_text(encoding="utf-8"))
    key = f"{ed['id']}:{k}.{s}"
    tgt = _SARGA_CW.get(key)
    if not tgt:
        return None
    other, ks = tgt.split(":")
    kk, ss = ks.split(".")
    label = next((e["short"] for e in editions if e["id"] == other), other)
    return {"href": f"../../../{other}/{kk}/{ss}/", "label": label, "ref": ks}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "dist"))
    build(Path(ap.parse_args().out))
