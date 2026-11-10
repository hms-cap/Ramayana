"""Remove GRETIL's non-Mahābhārata Gītā additions from two Pune records.

    python etl/fix_mbh_gita_preface.py

GRETIL's Bhīṣmaparvan file prints, right after Gītā 1.1 (the speaker line
"dhṛtarāṣṭra uvāca" and the two lines "dharmakṣetre kurukṣetre ... kim akurvata
saṃjaya"), a liturgical preface that is not Mahābhārata text: the nyāsa
formulas ("śrīrāmacandrāya namaḥ ... mālāmantra, karanyāsa, aṅganyāsa") and the
dhyāna ślokas (1)-(5). It sits inside the same record (46 lines in all).

This script keeps the first three lines of that record, saves the raw preface
lines to data/gita/gretil_preface.txt (one per original line; only written if
the block is still present, so a later run never overwrites it), sets meter by
the ingest convention (identified only for 2- or 4-line records, so None here:
the speaker line is part of the record) and rewrites
data/normalized/mbh/ce.jsonl touching no other line (byte for byte).
Idempotent: a second run finds nothing to remove and writes nothing.

The same is done for CE-6-040-078 (Gītā 18.78): GRETIL appends to it a
246-line "arjuna uvāca / yad etan niṣkalaṃ brahma ..." dialogue (with gaps
marked "...."), which is not part of the Pune text. The record keeps its first
two lines (the verse) and the removed lines go to data/gita/gretil_appendix_18_78.txt
(written only if that file does not exist yet).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).parent))
from translit import iast_to_slp1  # noqa: E402
import meter  # noqa: E402

CE = ROOT / "data" / "normalized" / "mbh" / "ce.jsonl"
# record uid -> (lines to keep, where the removed lines are saved)
TARGETS = {"CE-6-023-001": (3, ROOT / "data" / "gita" / "gretil_preface.txt"),
           "CE-6-040-078": (2, ROOT / "data" / "gita" / "gretil_appendix_18_78.txt")}


def main():
    raw = CE.read_bytes().decode("utf-8").split("\n")
    out, changed = [], False
    for line in raw:
        uid = line[8:20] if line.startswith('{"uid":"') else ""
        if uid in TARGETS:
            KEEP, save = TARGETS[uid]
            rec = json.loads(line)
            if len(rec["lines"]) > KEEP:
                save.parent.mkdir(parents=True, exist_ok=True)
                if not save.exists():
                    save.write_text("\n".join(" ".join(l) for l in rec["lines"][KEEP:]) + "\n", encoding="utf-8")
                rec["lines"] = rec["lines"][:KEEP]
                try:
                    rec["meter"] = (meter.identify([[iast_to_slp1(p) for p in l] for l in rec["lines"]])["name"]
                                    if len(rec["lines"]) in (2, 4) else None)
                except Exception:
                    rec["meter"] = None
                line = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
                changed = True
        out.append(line)
    if changed:
        CE.write_bytes("\n".join(out).encode("utf-8"))
    print("removed GRETIL additions" if changed else "nothing to do")


if __name__ == "__main__":
    main()
