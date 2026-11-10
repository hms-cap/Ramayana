"""Mahābhārata ingest -> data/normalized/mbh/{ce,vu}.jsonl

    python etl/ingest_mbh.py ce  path/to/gretil/.../mbh/        # Pune critical text, mbh_01_u.htm ... mbh_18_u.htm
    python etl/ingest_mbh.py vu  path/to/mahabharata-devanagari.xml   # Kumbakonam (southern recension), SARIT

Same record shape as the Rāmāyaṇa files: k = parva, s = adhyāya, v = verse.
CE: lines carrying a "*" in their id are variant insertions in the apparatus and are left out. GRETIL's ";"
between the pādas of a long line becomes a pāda break (the line's list gets one entry per pāda).
VU: speaker lines ("X uvāca", xml:id ending in x) are kept as the first line of the verse that follows.
A word that the print splits across two pādas ("jijīviṣāma- ste…") is joined; nukta letters (ऩ ऱ, a typing slip in
the source) are read without the nukta.
"""
from __future__ import annotations

import collections
import json
import re
import sys
import unicodedata
from pathlib import Path

from lxml import etree

sys.path.insert(0, str(Path(__file__).parent))
import meter  # noqa: E402
from translit import brahmic_to_slp1, iast_to_slp1, slp1_to_iast  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "normalized" / "mbh"
TEI = "{http://www.tei-c.org/ns/1.0}"
XMLID = "{http://www.w3.org/XML/1998/namespace}id"


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", s)).strip()


def meter_of(lines):
    try:
        return meter.identify([[iast_to_slp1(p) for p in line] for line in lines])["name"]
    except Exception:  # prose or irregular lines
        return None


LINE = re.compile(r"^(\d\d),(\d{3})\.(\d{3})([^\t<]*)(?:\t|<>)(.*?)(?:<BR>)?\s*$")


def ingest_ce(folder: str) -> list[dict]:
    recs: dict[tuple, list[str]] = collections.OrderedDict()
    for p in range(1, 19):
        text = (Path(folder) / f"mbh_{p:02d}_u.htm").read_text(encoding="utf-8")
        for raw in text.splitlines():
            m = LINE.match(raw.strip())
            if not m:
                continue
            k, s, v, suf, body = int(m[1]), int(m[2]), int(m[3]), m[4], m[5]
            if "*" in suf or not body.strip():
                continue
            recs.setdefault((k, s, v), []).append(clean(body))
    out = []
    for (k, s, v), ls in recs.items():
        lines = [split_padas(l) for l in ls]
        out.append({"uid": f"CE-{k}-{s:03d}-{v:03d}", "gretil_id": f"{k:02d},{s:03d}.{v:03d}", "k": k, "s": s, "v": v,
                    "lines": lines, "meter": meter_of(lines) if len(lines) in (2, 4) else None})
    return out


def split_padas(line: str) -> list[str]:
    """GRETIL marks the break between the pādas of a long-metre line with ';'."""
    return [p.strip() for p in line.split(";") if p.strip()] or [line]


def join_split_words(t: str) -> str:
    """'jijīviṣāma- ste'vasthitāḥ' -> 'jijīviṣāmaste'vasthitāḥ' (a word split at a pāda break in the print);
    a single '-' closing the line (the word goes on in the next line) is dropped. Runs of dashes (lacunae) stay."""
    t = re.sub(r"(?<=[^\s-])- (?=[^\s-])", "", t)
    return re.sub(r"(?<=[^\s-])-$", "", t)


def deva_to_iast(t: str) -> str:
    t = unicodedata.normalize("NFC", t).replace("\u0929", "\u0928").replace("\u0931", "\u0930")   # ऩ -> न, ऱ -> र (nukta slips)
    t = t.replace("`", "").replace("'", "").replace("’", "").replace("‘", "")
    t = re.sub(r"[॥।|]+", " ", t)
    t = re.sub(r"\([^)]*\)", " ", t)           # editorial words in brackets, e.g. (व्यासं)
    t = re.sub(r"[0-9०-९]+", " ", t)
    slp = brahmic_to_slp1(t)
    return join_split_words(clean(slp1_to_iast(slp)))


PARVA_NO = {"ādi": 1, "sabhā": 2, "araṇya": 3, "vana": 3, "virāṭa": 4, "udyoga": 5, "bhīṣma": 6, "droṇa": 7, "karṇa": 8, "śalya": 9,
            "sauptika": 10, "strī": 11, "śānti": 12, "anuśāsana": 13, "āśvamedhika": 14, "āśramavāsika": 15, "mausala": 16,
            "mahāprasthānika": 17, "svargārohaṇa": 18}


def ingest_vu(path: str) -> list[dict]:
    root = etree.parse(path, etree.XMLParser(huge_tree=True, collect_ids=False)).getroot()
    body = root.find(f".//{TEI}body")
    out, pend, anomalies = [], [], collections.Counter()
    for pdiv in body.findall(f"{TEI}div"):
        k = PARVA_NO[(pdiv.get(XMLID) or "").removesuffix("parva")]   # the file's own n= puts Mausala before Āśramavāsika
        for adiv in pdiv.findall(f"{TEI}div"):
            if not (adiv.get(XMLID) or adiv.get("n")):
                continue                                                  # closing colophon
            for lg in adiv.iter(f"{TEI}lg"):
                ls, speaker = [], False
                for l in lg.findall(f"{TEI}l"):
                    segs = l.findall(f"{TEI}seg")
                    t = " ".join("".join(sg.itertext()) for sg in segs) if segs else "".join(l.itertext())
                    t = deva_to_iast(t)
                    if t:
                        ls.append([t])
                    speaker = speaker or l.get("rend") == "speak" or (l.get(XMLID) or "").endswith("x")
                m = re.search(r"-(\d+)-(\d+)-(\d+)(x?)$", lg.get(XMLID) or "")
                if not ls or not m:
                    anomalies["unparsed"] += 1
                    continue
                s_, v = int(m[2]), int(m[3])      # numbers come from the id: some divs also hold a second run (karnaB-8-2-…)
                if m[4] or v == 0:
                    pend.extend(ls); anomalies["speaker_or_0"] += 1
                    continue
                ls = pend + ls; pend = []
                out.append({"uid": f"VU-{k}-{s_:03d}-{v:03d}", "source_ref": lg.get(XMLID), "k": k, "s": s_, "v": v, "lines": ls,
                            "meter": meter_of(ls) if len(ls) in (2, 4) and not speaker else None})
            pend = []
    out.sort(key=lambda r: (r["k"], r["s"], r["v"]))
    print("notes:", dict(anomalies))
    return out


def main(kind: str, src: str) -> None:
    recs = ingest_ce(src) if kind == "ce" else ingest_vu(src)
    OUT.mkdir(parents=True, exist_ok=True)
    seen, dups = set(), 0
    with open(OUT / f"{kind}.jsonl", "w", encoding="utf-8") as f:
        for r in recs:
            if r["uid"] in seen:
                dups += 1; continue
            seen.add(r["uid"])
            f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")
    by = collections.defaultdict(set)
    for r in recs:
        by[r["k"]].add(r["s"])
    print(kind, "verses", len(seen), "duplicates dropped", dups, "adhyayas per parva", {k: len(v) for k, v in sorted(by.items())})
    gaps = {k: sorted(set(range(1, max(v) + 1)) - v) for k, v in by.items() if set(range(1, max(v) + 1)) - v}
    print("adhyaya gaps:", gaps)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
