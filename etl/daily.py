"""Verse-of-the-day cards.

365 Critical Edition verses are chosen deterministically (same set on every
build) and written as chunked JSON for the home page. The cards are
*automatic*: the verse, its metre and scansion, its place in the epic, the
word-by-word analysis with dictionary glosses, and the Vulgate cross-walk.

Hand-written notes (meaning `m`, use and significance `u`, as
[English, Kannada] pairs) are read from data/daily/curated.json, keyed by
verse uid, and appear as extra cards when present. The file ships empty:
Kannada notes should be written or reviewed by a Kannada reader.

The daily pick is  k = (day * 7919) % 365  on the local day number; 7919 is
prime, so 365 consecutive days visit 365 different cards.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

N = 365
CHUNK = 50
STRIDE = 7919


def digest(s: str) -> str:
    return hashlib.sha1(s.encode()).hexdigest()


def select(records: list[dict], words: dict, metre_of) -> list[dict]:
    """records: CE verse records (uid, k, s, v, lines, flags). Returns N chosen, in card order."""
    elig = []
    for r in records:
        if r["uid"] not in words or len(r["lines"]) != 2 or r.get("flags"):
            continue
        if not 6 <= len(words[r["uid"]]) <= 22:
            continue
        if not metre_of(r):
            continue
        elig.append(r)
    by_k: dict[int, list[dict]] = {}
    for r in elig:
        by_k.setdefault(r["k"], []).append(r)
    total = len(elig)
    quota = {k: max(1, round(N * len(v) / total)) for k, v in by_k.items()}
    while sum(quota.values()) > N:                       # rounding drift
        quota[max(quota, key=quota.get)] -= 1
    while sum(quota.values()) < N:
        quota[min(quota, key=quota.get)] += 1
    chosen = []
    for k, vs in by_k.items():
        vs = sorted(vs, key=lambda r: digest("pick" + r["uid"]))
        chosen += vs[:quota[k]]
    return sorted(chosen, key=lambda r: digest("order" + r["uid"]))


def day_index(day: int) -> int:
    return (day * STRIDE) % N


def write(out: Path, cards: list[dict]) -> None:
    d = out / "data" / "daily"
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.json").write_text(json.dumps({"n": len(cards), "chunk": CHUNK}), encoding="utf-8")
    for i in range(0, len(cards), CHUNK):
        (d / f"c{i // CHUNK}.json").write_text(
            json.dumps(cards[i:i + CHUNK], ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
