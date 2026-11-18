"""Source numbering slips in the Kumbakonam (SARIT) text, fixed after ingest (idempotent).

    python etl/fix_vu_numbering.py

vana-3-161-180 is verse 80 (it stands between 79 and 81: Maṇimān hurls his spear at Bhīma); the source typed 180.
Moves the record, keeps the file in verse order, and renames the uid in the Mahābhārata cross-walk.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIX = {"VU-3-161-180": 80}


def main():
    p = ROOT / "data" / "normalized" / "mbh" / "vu.jsonl"
    recs = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    ren = {}
    for r in recs:
        if r["uid"] in FIX:
            new = f'VU-{r["k"]}-{r["s"]:03d}-{FIX[r["uid"]]:03d}'
            ren[r["uid"]] = new
            r["uid"], r["v"] = new, FIX[r["uid"]]
    if not ren:
        print("nothing to fix"); return
    order = {}
    for i, r in enumerate(recs):
        order.setdefault((r["k"], r["s"]), i)
    recs.sort(key=lambda r: (order[(r["k"], r["s"])], r["v"]))
    p.write_text("".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in recs), encoding="utf-8")
    cw = ROOT / "data" / "crosswalk" / "mbh" / "verses.json"
    if cw.exists():
        t = cw.read_text(encoding="utf-8")
        for a, b in ren.items():
            t = t.replace(f'"{a}"', f'"{b}"')
        cw.write_text(t, encoding="utf-8")
    print("renumbered", ren)


if __name__ == "__main__":
    main()
