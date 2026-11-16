"""Tools for data/stotras.json (the Stotras appendix).

    python etl/stotras.py find ram vu "tato yuddhapariśrāntaṃ"     # verses containing these words in order (loose spelling)
    python etl/stotras.py find mbh ce "viśvaṃ viṣṇur" --k 13
    python etl/stotras.py show ram vu 6 107 1 31                   # print verses 1–31 of 6.107 (omit range for the whole chapter)
    python etl/stotras.py heads mbh vu 13 149                      # first words of every verse in a chapter (to spot where a hymn starts/ends)
    python etl/stotras.py check [data/stotras.json]                # every entry: each edition's start verse contains its opening words
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from translit import iast_to_slp1, loose_for_index  # noqa: E402

NORM = {"ram": ROOT / "data" / "normalized", "mbh": ROOT / "data" / "normalized" / "mbh"}
_cache = {}


def recs(work, ed):
    if (work, ed) not in _cache:
        _cache[(work, ed)] = [json.loads(l) for l in open(NORM[work] / f"{ed}.jsonl", encoding="utf-8")]
    return _cache[(work, ed)]


def text(r):
    return " / ".join(p for ln in r["lines"] for p in ln)


def loose(s):
    # spelling-tolerant, space-free key: anusvāra/nasal, v/b, sandhi spacing, punctuation and digits ignored
    t = loose_for_index(iast_to_slp1(s.lower().replace("'", "a")))
    return re.sub(r"[^a-zA-Z]", "", t).replace("M", "m")


def contains(r, words):
    return loose(words) in loose(text(r))


def find(work, ed, words, k=None, s=None, limit=30):
    out = []
    rs = recs(work, ed)
    for i, r in enumerate(rs):
        if (k and r["k"] != k) or (s and r["s"] != s):
            continue
        # also try across the join with the next verse, for words split over a verse boundary
        if contains(r, words):
            out.append(r)
        if len(out) >= limit:
            break
    return out


def chapter(work, ed, k, s):
    return [r for r in recs(work, ed) if r["k"] == k and r["s"] == s]


def check(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    bad = 0
    for st in data["stotras"]:
        for ed in ("vu", "ce"):
            loc = st["loc"].get(ed)
            if not loc:
                continue
            ch = {r["v"]: r for r in chapter(st["work"], ed, loc["k"], loc["s"])}
            a, b = loc["v"]
            if a not in ch or b not in ch:
                print(f"BAD  {st['id']} {ed}: verse range {loc['k']}.{loc['s']}.{a}-{b} not in chapter (has {min(ch) if ch else '-'}–{max(ch) if ch else '-'})")
                bad += 1
                continue
            op = st.get("opening", {}).get(ed) or st.get("opening", {}).get("vu") or st.get("opening", {}).get("ce")
            if op and not contains(ch[a], op):
                print(f"BAD  {st['id']} {ed}: {loc['k']}.{loc['s']}.{a} does not contain opening {op!r}: {text(ch[a])}")
                bad += 1
            else:
                print(f"ok   {st['id']} {ed} {loc['k']}.{loc['s']}.{a}-{b} ({b - a + 1} vv)")
    print(f"{len(data['stotras'])} entries, {bad} problems")
    return bad


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print(__doc__); sys.exit(0)
    cmd = a[0]
    if cmd == "find":
        work, ed, words = a[1], a[2], a[3]
        k = int(a[a.index("--k") + 1]) if "--k" in a else None
        for r in find(work, ed, words, k):
            print(f'{r["k"]}.{r["s"]}.{r["v"]}\t{text(r)}')
    elif cmd == "show":
        work, ed, k, s = a[1], a[2], int(a[3]), int(a[4])
        lo, hi = (int(a[5]), int(a[6])) if len(a) > 6 else (-1, 10**6)
        for r in chapter(work, ed, k, s):
            if lo <= r["v"] <= hi:
                print(f'{r["v"]}\t{text(r)}')
    elif cmd == "heads":
        work, ed, k, s = a[1], a[2], int(a[3]), int(a[4])
        for r in chapter(work, ed, k, s):
            print(f'{r["v"]}\t{text(r)[:70]}')
    elif cmd == "check":
        sys.exit(1 if check(a[1] if len(a) > 1 else ROOT / "data" / "stotras.json") else 0)
