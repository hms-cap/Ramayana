"""Apply data/gita/errata_vu.json to the Kumbakonam Mahābhārata text.

    python etl/apply_errata.py && python etl/extract_gita.py

Each erratum replaces its exact 'from' text, which must lie within one line of the record (mbh_uid) of
data/normalized/mbh/vu.jsonl, by 'to'; ' / ' in 'to' splits that line into separate lines (used where the
source runs two half-verses, or two verses, into one line). The record gets "corrected": [[from, to], …] and
its metre is recomputed by the ingest rule. Idempotent: an erratum whose 'to' is already in place is skipped;
one that matches neither way stops the script, so a re-ingest that changes the text cannot be patched blindly.
After a fresh ingest (etl/ingest_mbh.py vu …) run this script again.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from ingest_mbh import meter_of  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
VU = ROOT / "data" / "normalized" / "mbh" / "vu.jsonl"
ERRATA = ROOT / "data" / "gita" / "errata_vu.json"
SPEAKER = re.compile(r"\buvāca$")


def apply(rec: dict, e: dict) -> str:
    """'applied', 'present' (already applied) or raises."""
    lines = [" ".join(l) for l in rec["lines"]]
    if [e["from"], e["to"]] in rec.get("corrected", []):     # checked first: 'to' may contain 'from' (…anvitā -> …anvitāḥ)
        return "present"
    hits = [i for i, l in enumerate(lines) if e["from"] in l]
    if len(hits) == 1 and lines[hits[0]].count(e["from"]) == 1:
        i = hits[0]
        new = lines[i].replace(e["from"], e["to"])
        parts = [p.strip() for p in new.split(" / ")]
        rec["lines"] = [[l] for l in lines[:i]] + [[p] for p in parts] + [[l] for l in lines[i + 1:]]
        rec.setdefault("corrected", []).append([e["from"], e["to"]])
        return "applied"
    whole = " / ".join(lines)
    raise SystemExit(f"{e['ref']} ({e['mbh_uid']}): {e['from']!r} not found once in {whole!r}")


def main() -> None:
    errata = json.loads(ERRATA.read_text(encoding="utf-8"))["errata"]
    by = {}
    for e in errata:
        by.setdefault(e["mbh_uid"], []).append(e)
    raw = VU.read_bytes().decode("utf-8").split("\n")
    out, n_app, n_pre, touched = [], 0, 0, 0
    for line in raw:
        uid = line[8:20] if line.startswith('{"uid":"') else ""
        if uid in by:
            rec = json.loads(line)
            before = json.dumps(rec, ensure_ascii=False)
            for e in by.pop(uid):
                r = apply(rec, e)
                n_app += r == "applied"
                n_pre += r == "present"
            if json.dumps(rec, ensure_ascii=False) != before:
                speaker = any(SPEAKER.search(" ".join(l)) for l in rec["lines"])
                rec["meter"] = meter_of(rec["lines"]) if len(rec["lines"]) in (2, 4) and not speaker else None
                line = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
                touched += 1
        out.append(line)
    if by:
        raise SystemExit(f"records not found: {sorted(by)}")
    if touched:
        VU.write_bytes("\n".join(out).encode("utf-8"))
    print(f"{n_app} errata applied, {n_pre} already in place, {touched} records rewritten")


if __name__ == "__main__":
    main()
