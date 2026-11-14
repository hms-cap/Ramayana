"""Find verses that name someone, to choose citations for data/characters/.

    python etl/find_verses.py ram vu vibhīṣaṇa            # all verses naming him (first 40)
    python etl/find_verses.py mbh vu karṇa --k 8 --all     # only in parva 8, no limit
    python etl/find_verses.py mbh vu "karṇa+arjuna"        # verses naming both
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_characters import NORM, stem  # noqa: E402
from translit import iast_to_slp1, loose_for_index  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("work", choices=["ram", "mbh"])
ap.add_argument("ed", choices=["vu", "ce"])
ap.add_argument("names", help="IAST name(s), several joined with +")
ap.add_argument("--k", type=int, help="only this kāṇḍa / parvan")
ap.add_argument("--s", type=int, help="only this sarga / adhyāya")
ap.add_argument("--all", action="store_true")
a = ap.parse_args()
keys = [stem(n) for n in a.names.split("+")]
n = 0
with open(NORM[a.work] / f"{a.ed}.jsonl", encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        if (a.k and r["k"] != a.k) or (a.s and r["s"] != a.s):
            continue
        text = " / ".join(p for ln in r["lines"] for p in ln)
        t = loose_for_index(iast_to_slp1(text.lower()))
        if all(k in t for k in keys):
            print(f'{r["k"]}.{r["s"]}.{r["v"]}\t{text}')
            n += 1
            if n >= 40 and not a.all:
                print("… (more; use --all or --k/--s)")
                break
