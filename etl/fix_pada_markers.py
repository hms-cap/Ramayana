"""Turn GRETIL's ';' pāda separator into real pāda breaks in the Pune Mahābhārata data.

    python etl/fix_pada_markers.py

GRETIL writes a long-metre half-verse as one line with ';' between its two pādas
("gurūn ahatvā hi mahānubhāvāñ; śreyo bhoktuṃ …"). The ';' reached the page as a
character. Each such line becomes a list of pādas (the record shape already allows
that: lines = [[pāda, …], …]); the page joins pādas with a space, and scansion reads
them as pādas. The metre is recomputed for changed records by the ingest rule
(ingest_mbh.meter_of, only for 2- or 4-line records). etl/ingest_mbh.py now does the
same on a fresh ingest (split_padas). Idempotent; other records are left byte for byte.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from ingest_mbh import meter_of, split_padas  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CE = ROOT / "data" / "normalized" / "mbh" / "ce.jsonl"


def main() -> None:
    raw = CE.read_bytes().decode("utf-8").split("\n")
    out, changed, metre = [], 0, {}
    for line in raw:
        if ";" in line and line.startswith("{"):
            rec = json.loads(line)
            new = [[p for part in l for p in split_padas(part)] for l in rec["lines"]]
            if new != rec["lines"]:
                rec["lines"] = new
                m = meter_of(new) if len(new) in (2, 4) else None
                if m != rec.get("meter"):
                    metre[rec["uid"]] = (rec.get("meter"), m)
                rec["meter"] = m
                line = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
                changed += 1
        out.append(line)
    if changed:
        CE.write_bytes("\n".join(out).encode("utf-8"))
    print(f"{changed} records split into pādas; metre changed for {len(metre)}")
    for uid, (a, b) in list(metre.items())[:20]:
        print(f"  {uid}: {a} -> {b}")


if __name__ == "__main__":
    main()
