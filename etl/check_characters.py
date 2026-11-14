"""Check the character data in data/characters/ against the text.

    python etl/check_characters.py            # all files
    python etl/check_characters.py ram        # one work (ram | mbh)

Every character in seed_<work>.json must be present with the required fields; every relation must point
to a known id; and every verse cited (moments and relations with a "ref") must exist in that edition and
must contain a name or epithet of the character it is about (or of a character listed in the moment's
"with"). A citation whose verse names the person only by pronoun may carry "check": "skip" with a "why".
Exit code 1 when anything fails.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "etl"))
from translit import iast_to_slp1, loose_for_index  # noqa: E402

DIR = ROOT / "data" / "characters"
NORM = {"ram": ROOT / "data" / "normalized", "mbh": ROOT / "data" / "normalized" / "mbh"}
REL_TYPES = {"parent", "spouse", "sibling", "teacher", "ally", "enemy", "friend", "serves", "killed_by", "other"}
REQ = ("id", "name", "group", "gender", "rank", "role_en", "role_kn", "desc_en", "desc_kn", "epithets", "relations", "moments")
REF = re.compile(r"^\d+\.\d+\.\d+$")


def stem(name: str) -> str:
    """Loose key of a name with its final vowel dropped, so inflected forms match (rāma -> ram: rāmaḥ, rāmeṇa)."""
    k = loose_for_index(iast_to_slp1(name.lower().replace("-", "")))
    k = re.sub(r"(an|in|at|as|is|us|[aiu])$", "", k) if len(k) > 4 else k
    return k


def verses(work: str, ed: str) -> dict:
    out = {}
    with open(NORM[work] / f"{ed}.jsonl", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            text = " ".join(p for ln in r["lines"] for p in ln)
            out[f'{r["k"]}.{r["s"]}.{r["v"]}'] = loose_for_index(iast_to_slp1(text.lower()))
    return out


def load(work: str) -> tuple[dict, list]:
    seed = json.loads((DIR / f"seed_{work}.json").read_text(encoding="utf-8"))
    chars = []
    for p in sorted(DIR.glob(f"{work}*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        chars += [dict(c, _file=p.name) for c in d.get("characters", [])]
    return seed, chars


def check(work: str) -> list[str]:
    errs = []
    seed, chars = load(work)
    ids = {c["id"] for c in seed["characters"]}
    groups = {g["id"] for g in seed["groups"]}
    by = {}
    for c in chars:
        if c["id"] in by:
            errs.append(f'{work}: {c["id"]} defined twice ({by[c["id"]]["_file"]}, {c["_file"]})')
        by[c["id"]] = c
    for i in sorted(ids - set(by)):
        errs.append(f"{work}: {i} missing")
    for i in sorted(set(by) - ids):
        errs.append(f"{work}: {i} is not in seed_{work}.json")
    texts = {}

    def names_of(cid):
        c = by.get(cid) or {}
        return [n for n in [c.get("name", "")] + c.get("epithets", []) + c.get("match", []) if n]

    def verse_has(ed, ref, who):
        if ed not in texts:
            texts[ed] = verses(work, ed)
        t = texts[ed].get(ref)
        if t is None:
            return None
        return any(stem(n) and stem(n) in t for w in who for n in names_of(w))

    for cid, c in sorted(by.items()):
        for f in REQ:
            if f not in c or c[f] in ("", None):
                errs.append(f"{work}/{cid}: field {f} missing")
        if c.get("group") not in groups:
            errs.append(f'{work}/{cid}: unknown group {c.get("group")}')
        for r in c.get("relations", []):
            if r.get("type") not in REL_TYPES:
                errs.append(f'{work}/{cid}: relation type {r.get("type")}')
            if r.get("to") not in ids:
                errs.append(f'{work}/{cid}: relation to unknown id {r.get("to")}')
            if r.get("type") == "other" and not r.get("note_en"):
                errs.append(f'{work}/{cid}: relation "other" to {r.get("to")} needs note_en')
        cited = [("moment", m, [cid] + m.get("with", [])) for m in c.get("moments", [])]
        cited += [("relation", r, [cid, r.get("to")]) for r in c.get("relations", []) if r.get("ref")]
        if len(c.get("moments", [])) < 2:
            errs.append(f"{work}/{cid}: fewer than 2 moments")
        for kind, m, who in cited:
            ref, ed = m.get("ref", ""), m.get("ed", "vu")
            if not REF.match(ref) or ed not in ("vu", "ce"):
                errs.append(f"{work}/{cid}: {kind} bad ref {ed}:{ref}")
                continue
            if kind == "moment" and not (m.get("en") and m.get("kn")):
                errs.append(f"{work}/{cid}: moment {ref} needs en and kn")
            ok = verse_has(ed, ref, who)
            if ok is None:
                errs.append(f"{work}/{cid}: {kind} {ed}:{ref} no such verse")
            elif not ok and m.get("check") != "skip":
                errs.append(f"{work}/{cid}: {kind} {ed}:{ref} does not name {'/'.join(who)}")
            elif m.get("check") == "skip" and not m.get("why"):
                errs.append(f"{work}/{cid}: {kind} {ed}:{ref} skip needs why")
    return errs


if __name__ == "__main__":
    works = sys.argv[1:] or ["ram", "mbh"]
    allerr = []
    for w in works:
        e = check(w)
        allerr += e
        print(f"{w}: {len(e)} problems")
    for e in allerr:
        print("  " + e)
    sys.exit(1 if allerr else 0)
