"""Stage 1 (words): ambuda-dcs ramayanam.txt / mahabharatam.txt -> words.jsonl

Usage:
    python etl/ingest_dcs.py path/to/ambuda-dcs/ramayanam.txt
    python etl/ingest_dcs.py path/to/ambuda-dcs/mahabharatam.txt --work mbh

The Mahābhārata run writes data/normalized/mbh/words.jsonl.gz (ids M.k.s.v
follow the Pune critical edition, so they map onto the CE uids of that work).

Source: Oliver Hellwig, Digital Corpus of Sanskrit (DCS), as corrected in
ambuda-org/dcs. CC BY 4.0. Verse ids (R.k.s.v) follow the Baroda Critical
Edition, so they map directly onto the CE verse uids used elsewhere.

File format (SLP1, sandhi already split):
    # id = R.1.1.1
    tapaH<TAB>tapas<TAB>pos=n,comp=y
    ...
A token tagged comp=y is the first or middle member of a compound whose last
member is the next token without comp=y. We group those into one "unit" so a
compound like tapaH+svADyAya+niratam is shown as one word with its members.

Output, one JSON object per verse:
    {"uid":"CE-1-001-001",
     "units":[ {"f":["tapaH","svADyAya","niratam"],
                "l":["tapas","svADyAya","niram"],
                "t":{"pos":"va","g":"m","c":"2","n":"s","f":"part"}} , ...]}
`t` carries the grammar of the unit (taken from its last member).
"""
from __future__ import annotations

import collections
import gzip
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import grammar  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "normalized"
ID = re.compile(r"^# id = [RM]\.(\d+)\.(\d+)\.(\d+)\s*$")


def parse_tags(raw: str) -> dict[str, str]:
    d = {}
    for part in raw.split(","):
        if "=" in part:
            k, v = part.split("=", 1)
            d[k.strip()] = v.strip()
        elif part.strip():
            d[part.strip()] = ""
    return d


UD = {"Case": ("c", {"Nom": "1", "Acc": "2", "Ins": "3", "Dat": "4", "Abl": "5", "Gen": "6", "Loc": "7", "Voc": "8"}),
      "Gender": ("g", {"Masc": "m", "Fem": "f", "Neut": "n"}),
      "Number": ("n", {"Sing": "s", "Dual": "d", "Plur": "p"})}


def salvage(raw: str) -> dict[str, str]:
    m = re.match(r"ERR:\s*(\w+)\s*,\s*(.*)$", raw)
    pos = m.group(1) if m and m.group(1) in grammar.POS else "n"
    tags = {"pos": pos}
    if "Part" in raw:
        tags["f"] = "part"
    for kv in (m.group(2).split("|") if m else []):
        k, _, v = kv.partition("=")
        if k in UD and v in UD[k][1]:
            tags[UD[k][0]] = UD[k][1][v]
    return tags


def main(path: str, work: str = "ram") -> None:
    out_dir = OUT if work == "ram" else OUT / work
    ce_uids = {json.loads(l)["uid"] for l in open(out_dir / "ce.jsonl", encoding="utf-8")}
    verses: dict[str, list] = {}
    cur = None
    problems = collections.Counter()
    unlabelled = collections.Counter()
    examples = {}

    for lineno, line in enumerate(open(path, encoding="utf-8"), 1):
        line = line.rstrip("\n")
        m = ID.match(line)
        if m:
            k, s, v = map(int, m.groups())
            cur = f"CE-{k}-{s:03d}-{v:03d}"
            verses[cur] = []
            continue
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 3 or cur is None:
            problems["malformed_line"] += 1
            examples.setdefault("malformed_line", f"{lineno}: {line[:80]}")
            continue
        form, lemma, raw = parts
        tags = parse_tags(raw)
        if "pos" not in tags:
            # A few source lines read "ERR: va, Case=Nom|Gender=Masc|Number=Sing" (or "ERR: n, ").
            # Keep what they say: the part of speech, and the case/gender/number when given.
            problems["no_pos"] += 1
            examples.setdefault("no_pos", f"{lineno}: {line[:80]}")
            tags = salvage(raw)
        for miss in grammar.check_tags(tags):
            unlabelled[miss] += 1
        verses[cur].append((form, lemma, tags))

    records, n_units, n_tokens, dangling = [], 0, 0, 0
    for uid, toks in verses.items():
        if uid not in ce_uids:
            problems["unknown_verse"] += 1
            continue
        units, group = [], []
        for form, lemma, tags in toks:
            group.append((form, lemma, tags))
            n_tokens += 1
            if "comp" not in tags:
                units.append(group)
                group = []
        if group:  # compound continues into the next verse
            dangling += 1
            units.append(group)
        out = []
        for g in units:
            last = g[-1][2]
            t = {k: v for k, v in last.items() if k in ("pos", "g", "c", "n", "p", "l", "f") and v != ""}
            if "comp" in last:
                t["comp"] = "y"
            out.append({"f": [x[0] for x in g], "l": [x[1] for x in g], "t": t})
        n_units += len(out)
        records.append({"uid": uid, "units": out})

    opener = (lambda: gzip.open(out_dir / "words.jsonl.gz", "wt", encoding="utf-8", compresslevel=9)) if work == "mbh" \
        else (lambda: open(out_dir / "words.jsonl", "w", encoding="utf-8"))
    with opener() as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")

    lemmas = collections.Counter(l for r in records for u in r["units"] for l in u["l"])
    report = {
        "verses_with_words": len(records),
        "ce_verses_without_words": len(ce_uids) - len(records),
        "tokens": n_tokens, "units": n_units, "distinct_lemmas": len(lemmas),
        "compounds_running_into_next_verse": dangling,
        "problems": dict(problems), "problem_examples": examples,
        "unlabelled_tags": dict(unlabelled),
        "missing_uids": sorted(ce_uids - {r["uid"] for r in records}),
    }
    (out_dir / "words_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "missing_uids"}, ensure_ascii=False, indent=1))
    if unlabelled:
        sys.exit("ERROR: tags without a Kannada/English label: " + ", ".join(unlabelled))


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], a[a.index("--work") + 1] if "--work" in a else "ram")
