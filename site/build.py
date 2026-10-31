"""Stage 2+4: normalized JSONL -> static site in dist/

    python site/build.py [--out dist]

Pre-renders every verse in Kannada script, Devanāgarī and IAST (plus the
para-savarṇa nasal variant where it differs), writes one HTML page per
sarga, per-sarga JSON, and a compact per-edition search index.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections import defaultdict
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "etl"))
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
        "uid": rec["uid"], "k": rec["k"], "s": rec["s"], "v": rec["v"], "ref": ref,
        "v_knda": to_digits(rec["v"], "knda"), "v_deva": to_digits(rec["v"], "deva"),
        "text": out, "meter": rec.get("meter"), "scan": scan,
        "slp1": " / ".join(slp_lines),
        "ids": rec_ids(rec, ed),
        "crosswalk": rec.get("crosswalk"),
    }


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
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(ROOT / "site" / "static", out / "static")
    sources = json.loads((ROOT / "etl" / "sources.json").read_text(encoding="utf-8"))

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

        index_rows = []
        for i, (k, s) in enumerate(sarga_keys):
            verses = [render_verse(r, ed) for r in by_sarga[(k, s)]]
            prev_key = sarga_keys[i - 1] if i > 0 else None
            next_key = sarga_keys[i + 1] if i + 1 < len(sarga_keys) else None
            page = out / ed["id"] / str(k) / str(s) / "index.html"
            page.parent.mkdir(parents=True, exist_ok=True)
            page.write_text(env.get_template("sarga.html").render(
                root="../../../", ed=summary, editions=editions, kanda=kanda_info(k), s=s,
                title=titles.get((k, s)), verses=verses, prev=prev_key, next=next_key,
                total_in_kanda=kandas[k - 1]["sargas"], page="sarga",
                alt_href=alt_edition_href(ed, editions, k, s),
            ), encoding="utf-8")
            (page.parent / "sarga.json").write_text(json.dumps(
                {"edition": ed["id"], "kanda": k, "sarga": s,
                 "verses": [{key: v[key] for key in ("uid", "ref", "text", "meter", "ids", "crosswalk")}
                            for v in verses]},
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

    common = dict(editions=editions, eds=edition_summaries, ed=edition_summaries[0], sources=sources)
    (out / "index.html").write_text(env.get_template("home.html").render(root="", page="home", **common), encoding="utf-8")
    for name in ("search", "about"):
        p = out / name / "index.html"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(env.get_template(f"{name}.html").render(root="../", page=name, **common), encoding="utf-8")
    for ed in edition_summaries:  # /ce/ -> list of kāṇḍas
        p = out / ed["id"] / "index.html"
        p.write_text(env.get_template("edition.html").render(root="../", page="edition",
                                                             **{**common, "ed": ed}), encoding="utf-8")
    (out / ".nojekyll").write_text("")
    print(f"built {sum(e['sargas'] for e in edition_summaries)} sarga pages "
          f"for {', '.join(e['id'] for e in edition_summaries)} -> {out}")


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
