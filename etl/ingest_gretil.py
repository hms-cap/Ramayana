"""Stage 1 (CE): GRETIL TEI-XML -> data/normalized/ce.jsonl

Usage:
    python etl/ingest_gretil.py path/to/sa_rAmAyaNa.xml

The XML comes from INDOLOGY/GRETIL-mirror (see etl/sources.json for the
pinned commit). Output is one JSON object per verse, IAST exactly as in the
source (NFC-normalised), plus a report of structural anomalies.
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
from translit import iast_to_slp1  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "normalized"
TEI = "{http://www.tei-c.org/ns/1.0}"
XMLID = "{http://www.w3.org/XML/1998/namespace}id"
ID_RE = re.compile(r"^R_(\d)\.(\d{3})\.(\d{3})$")


def clean(s: str) -> str:
    s = unicodedata.normalize("NFC", s)
    return re.sub(r"\s+", " ", s).strip()


def main(xml_path: str) -> None:
    parser = etree.XMLParser(collect_ids=False, huge_tree=True)  # source has a few duplicate xml:ids
    root = etree.parse(xml_path, parser).getroot()
    body = root.find(f".//{TEI}body")
    records, anomalies = [], []
    line_ids = collections.Counter()

    for lg in body.iter(f"{TEI}lg"):
        gid = lg.get(XMLID)
        m = ID_RE.match(gid or "")
        if not m:
            anomalies.append({"type": "bad_id", "id": gid})
            continue
        k, s, v = map(int, m.groups())
        lines = []
        for l in lg.findall(f"{TEI}l"):
            line_ids[l.get(XMLID)] += 1
            segs = l.findall(f"{TEI}seg")
            if segs:
                lines.append([clean("".join(sg.itertext())) for sg in segs])
            else:
                lines.append([clean("".join(l.itertext()))])
        if len(lines) != 2:
            anomalies.append({"type": f"lines_{len(lines)}", "id": gid})
        met = meter.identify([[iast_to_slp1(p) for p in line] for line in lines])
        records.append({
            "uid": f"CE-{k}-{s:03d}-{v:03d}",
            "gretil_id": gid,
            "k": k, "s": s, "v": v,
            "lines": lines,
            "meter": met["name"],
        })

    for lid, n in line_ids.items():
        if n > 1:
            anomalies.append({"type": "duplicate_line_id", "id": lid, "count": n})

    # numbering continuity
    by_ks = collections.defaultdict(list)
    for r in records:
        by_ks[(r["k"], r["s"])].append(r["v"])
    for k in range(1, 8):
        sargas = sorted(s for (kk, s) in by_ks if kk == k)
        if sargas != list(range(1, len(sargas) + 1)):
            anomalies.append({"type": "sarga_gap", "kanda": k})
    for (k, s), vs in by_ks.items():
        if vs != list(range(1, len(vs) + 1)):
            anomalies.append({"type": "verse_gap", "kanda": k, "sarga": s,
                              "missing": sorted(set(range(1, max(vs) + 1)) - set(vs))})

    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "ce.jsonl", "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")
    meters = collections.Counter(r["meter"] or "unidentified" for r in records)
    report = {
        "verses": len(records),
        "sargas": len(by_ks),
        "sargas_per_kanda": {k: len([1 for (kk, _) in by_ks if kk == k]) for k in range(1, 8)},
        "meters": dict(meters.most_common()),
        "anomalies": anomalies,
    }
    (OUT / "ce_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "anomalies"}, ensure_ascii=False, indent=1))
    print("anomalies:", collections.Counter(a["type"] for a in anomalies))


if __name__ == "__main__":
    main(sys.argv[1])
