"""Stage 1 (Vulgate): Ramayana_Book san/*_all.json -> data/normalized/vu.jsonl

Usage:
    python etl/ingest_vulgate.py path/to/Ramayana_Book/san

The source is Sanskrit Wikisource's text of the traditional (vulgate /
southern) recension as packaged by svenkatreddy/Ramayana_Book. It is noisy:
mixed verse-end markers, ':' typed for visarga, word-final 'ह्' for visarga,
leftover ITRANS fragments (ऋष्यश्R^ङ्ग), HTML <br>, and sarga colophons
stored as verses. This script repairs only what can be repaired
mechanically and without ambiguity, records every repair, and flags verses
that still contain noise so the reader can show it.
"""
from __future__ import annotations

import collections
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import meter  # noqa: E402
from translit import brahmic_to_slp1, slp1_to_iast  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "normalized"

FILES = ["balakanda_all.json", "ayodhyakanda_all.json", "aranyakanda_all.json", "kishkindhakanda_all.json",
         "sundarakanda_all.json", "yudhhakanda_all.json", "uttarakanda_all.json"]
# Sargas the upstream repo restored from IIT Kanpur's site (see its README / issue #31)
IITK_RESTORED = {(4, 11), (6, 25), (6, 31)}

DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
MARK = re.compile(r"[\s।॥|]*([०-९0-9]+)\s*[-.]\s*([०-९0-9]+)\s*[-.]\s*([०-९0-9]+)\s*[\s।॥|]*$")
TAIL = re.compile(r"[\s।॥|]*(?:[०-९0-9]+\s*)?[\s।॥|]*$")
COLOPHON = re.compile(r"^[\s।॥|]*इति(?=\s).*(सर्गः|सर्ग:|काण्डे|काण्डः)")
DEVA = r"[ऀ-ॿ]"
SIGNS = dict(zip("ािीुूृॄेैोौ", "AiIuUfFeEoO"))
VOWEL_LETTER_TO_SIGN = {"अ": "", "आ": "ा", "इ": "ि", "ई": "ी", "उ": "ु", "ऊ": "ू", "ए": "े", "ऐ": "ै", "ओ": "ो", "औ": "ौ"}


def repair(s: str, log: collections.Counter) -> str:
    s = unicodedata.normalize("NFC", s)
    # editorial alternatives in parentheses, e.g. "महोरसि (पात्यमानो)" or "(?)"
    s, n = re.subn(r"\s*\([^)]*\)", "", s)
    log["parenthetical_removed"] += n
    n = len(re.findall(r"<br\s*/?>", s, flags=re.I))
    if n:
        s = re.sub(r"\s*<br\s*/?>\s*", " । ", s, flags=re.I)
        log["html_br"] += n
    # ':' typed instead of visarga
    s, n = re.subn(rf"(?<={DEVA}):", "ः", s)
    log["colon_visarga"] += n
    # word-final ह् typed for visarga (no Sanskrit word ends in h)
    s, n = re.subn(r"ह्(?=[\s।॥|]|$)", "ः", s)
    log["h_visarga"] += n
    # ITRANS 'R^i' / 'R' after a virama is vocalic ṛ: श्R^ङ्ग -> शृङ्ग, व्Rत -> वृत
    s, n = re.subn(r"्R\^?(?:i|इ|ि)?", "ृ", s)
    log["itrans_r"] += n
    # ITRANS 'L' + vowel letter is la + vowel: पाताLअतल -> पातालतल is ambiguous, but ताLआ -> ताला is safe
    def _l(m):
        log["itrans_l"] += 1
        return "ल" + VOWEL_LETTER_TO_SIGN[m.group(1)]
    s = re.sub(r"L([अआइईउऊएऐओऔ])", _l, s)
    # stray vowel sign U+093A, nukta-r
    s, n = re.subn("ऺ", "", s)
    log["stray_093a"] += n
    s, n = re.subn("ऱ", "र", s)
    log["eyelash_ra"] += n
    return s


INNER = re.compile(r"[०-९0-9]+\s*[-.]\s*[०-९0-9]+\s*[-.]\s*[०-९0-9]+\s*[।॥|]*")


def split_merged(raw: str, log: collections.Counter) -> list[str]:
    """Some source entries hold two verses, each with its own number
    (… क्षितौ ॥६-९७-३१॥ दीप्तं …). Split them so each keeps its marker."""
    pieces, start = [], 0
    for m in INNER.finditer(raw):
        pieces.append(raw[start:m.end()])
        start = m.end()
    rest = raw[start:]
    if re.search(r"[\u0900-\u097F]{2}", re.sub(r"[।॥०-९]", "", rest)):
        pieces.append(rest)
    elif pieces:
        pieces[-1] += rest
    else:
        pieces = [raw]
    if len(pieces) > 1:
        log["merged_verses_split"] += len(pieces) - 1
    return pieces


NOISE = re.compile(r"[A-Za-z\^~\\\[\]{}<>!?*;,/()]")


def main(san_dir: str) -> None:
    san = Path(san_dir)
    records, log, issues = [], collections.Counter(), []
    sargas = collections.Counter()
    for k, fname in enumerate(FILES, 1):
        data = json.loads((san / fname).read_text(encoding="utf-8"))
        chapters = next(iter(data.values()))["chapters"]
        for ch in chapters:
            s = ch["chapter_number"]
            v = 0
            for raw in (piece for r0 in ch["slokas"] for piece in split_merged(r0, log)):
                if COLOPHON.search(raw):
                    log["colophon_dropped"] += 1
                    continue
                m = MARK.search(raw)
                source_ref = None
                if m:
                    mk, ms, mv = (int(x.translate(DIGITS)) for x in m.groups())
                    source_ref = f"{mk}.{ms}.{mv}"
                    body = raw[:m.start()]
                else:
                    body = TAIL.sub("", raw)
                text = repair(body, log)
                parts = [p.strip() for p in re.split(r"[।॥|]+", text)]
                parts = [p for p in parts if p]
                if not parts:
                    log["empty_dropped"] += 1
                    continue
                v += 1
                flags = []
                if NOISE.search(text):
                    flags.append("source_noise")
                    issues.append({"ref": f"{k}.{s}.{v}", "type": "source_noise", "text": text[:120]})
                if source_ref and source_ref != f"{k}.{s}.{v}":
                    flags.append("renumbered")
                if (k, s) in IITK_RESTORED:
                    flags.append("iitk_restored")
                lines = []
                for p in parts:
                    p = NOISE.sub("", p).strip() if "source_noise" in flags else p
                    lines.append([slp1_to_iast(re.sub(r"\s+", " ", brahmic_to_slp1(p)).strip())])
                leftover = [l[0] for l in lines if re.search(r"[ऀ-ॿ]", l[0])]
                if leftover:
                    issues.append({"ref": f"{k}.{s}.{v}", "type": "unconverted", "text": leftover[0][:80]})
                met = meter.identify([[brahmic_to_slp1(p)] for p in parts])
                rec = {"uid": f"VU-{k}-{s:03d}-{v:03d}", "k": k, "s": s, "v": v, "lines": lines,
                       "meter": met["name"]}
                if source_ref and source_ref != f"{k}.{s}.{v}":
                    rec["source_ref"] = source_ref
                if flags:
                    rec["flags"] = flags
                if "source_noise" in flags:
                    rec["raw"] = raw
                records.append(rec)
                sargas[(k, s)] += 1

    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "vu.jsonl", "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")
    report = {
        "verses": len(records), "sargas": len(sargas),
        "sargas_per_kanda": {k: sum(1 for (kk, _) in sargas if kk == k) for k in range(1, 8)},
        "meters": dict(collections.Counter(r["meter"] or "unidentified" for r in records).most_common()),
        "repairs": dict(log),
        "flags": dict(collections.Counter(f for r in records for f in r.get("flags", []))),
        "issues": issues,
    }
    (OUT / "vu_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "issues"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
