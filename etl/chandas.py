"""Chandas (metre) index: what each metre is, and a census of the metre labels already stored with every verse.

The labels come from `meter.identify` (run when the texts were ingested). Only the metres that actually occur
in the two epics are listed; verses that could not be named are counted as "not identified", never guessed.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# order = order on the index page. slug is ASCII for URLs. syl = syllables per pāda. gana = the traditional gaṇa formula.
CATALOGUE = [
    dict(name="Anuṣṭubh", slug="anushtubh", syl="8", family="śloka",
         gana="",
         text="The śloka, the common metre of both epics: four pādas of eight syllables, 32 in all. In the usual form the fifth syllable of each pāda is short and the sixth long. "
              "The app names a verse Anuṣṭubh when each half-verse has 16 syllables; it does not check the fifth to seventh syllables."),
    dict(name="Triṣṭubh", slug="trishtubh", syl="11", family="triṣṭubh",
         gana="",
         text="Four pādas of eleven syllables, 44 in all. The epics use it with freedom, so pādas do not all follow one pattern. "
              "Here a verse is called Triṣṭubh when every pāda has eleven syllables but the pattern is none of the named ones below."),
    dict(name="Jagatī", slug="jagati", syl="12", family="jagatī",
         gana="",
         text="Four pādas of twelve syllables, 48 in all. Used here for verses whose pādas all have twelve syllables but follow no named pattern below."),
    dict(name="Upajāti", slug="upajati", syl="11", family="triṣṭubh",
         gana="Indravajrā + Upendravajrā",
         text="A verse that mixes Indravajrā and Upendravajrā pādas. They differ only in the first syllable (long in Indravajrā, short in Upendravajrā), so poets mix them freely."),
    dict(name="Upajāti (Jagatī)", slug="upajati-jagati", syl="12", family="jagatī",
         gana="Vaṃśastha + Indravaṃśā",
         text="The same idea in twelve-syllable pādas: Vaṃśastha and Indravaṃśā mixed in one verse."),
    dict(name="Upajāti (mixed)", slug="upajati-mixed", syl="11 / 12", family="mixed",
         gana="",
         text="Pādas of eleven and twelve syllables in one verse, or a mix of the named patterns of both lengths."),
    dict(name="Indravajrā", slug="indravajra", syl="11", family="triṣṭubh", gana="ta ta ja ga ga",
         text="Eleven syllables, all four pādas the same: two long, one short, two long, two short, one long, one short, two long."),
    dict(name="Upendravajrā", slug="upendravajra", syl="11", family="triṣṭubh", gana="ja ta ja ga ga",
         text="Like Indravajrā but the first syllable is short."),
    dict(name="Vaṃśastha", slug="vamshastha", syl="12", family="jagatī", gana="ja ta ja ra",
         text="Twelve syllables, all four pādas the same. Also called Vaṃśasthavila."),
    dict(name="Indravaṃśā", slug="indravamsha", syl="12", family="jagatī", gana="ta ta ja ra",
         text="Like Vaṃśastha but the first syllable is long."),
    dict(name="Puṣpitāgrā", slug="pushpitagra", syl="12 / 13", family="ardhasama", gana="na na ra ya  /  na ja ja ra ga",
         text="A half-equal metre: the first and third pādas have twelve syllables, the second and fourth thirteen. The epics use it to close a chapter."),
    dict(name="Aparavaktra", slug="aparavaktra", syl="11 / 12", family="ardhasama", gana="na ra na la ga  /  na ja ja ra",
         text="A half-equal metre: eleven syllables in the first and third pādas, twelve in the second and fourth."),
    dict(name="Rucirā", slug="rucira", syl="13", family="vṛtta", gana="ja bha sa ja ga",
         text="Thirteen syllables in every pāda."),
    dict(name="Praharṣiṇī", slug="praharshini", syl="13", family="vṛtta", gana="ma na ja ra ga",
         text="Thirteen syllables in every pāda."),
    dict(name="Vasantatilakā", slug="vasantatilaka", syl="14", family="vṛtta", gana="ta bha ja ja ga ga",
         text="Fourteen syllables in every pāda."),
    dict(name="Drutavilambita", slug="drutavilambita", syl="12", family="vṛtta", gana="na bha bha ra",
         text="Twelve syllables in every pāda, a quick, lilting rhythm."),
]
BY_NAME = {m["name"]: m for m in CATALOGUE}
WORKS = {"ram": ("", "Rāmāyaṇa"), "mbh": ("mbh", "Mahābhārata")}
EDS = ("ce", "vu")


def census() -> dict:
    """{work: {ed: {"total": n, "none": n, "by": {metre: {k: n}}, "refs": {metre: [(k, s, v), ...]}}}}"""
    out = {}
    for w, (sub, _) in WORKS.items():
        out[w] = {}
        for ed in EDS:
            path = ROOT / "data" / "normalized" / sub / f"{ed}.jsonl"
            by, refs, total, none = defaultdict(lambda: defaultdict(int)), defaultdict(list), 0, 0
            with open(path, encoding="utf-8") as f:
                for line in f:
                    r = json.loads(line)
                    total += 1
                    m = r.get("meter")
                    if not m:
                        none += 1
                        continue
                    by[m][r["k"]] += 1
                    refs[m].append((r["k"], r["s"], r["v"]))
            out[w][ed] = dict(total=total, none=none, by={m: dict(c) for m, c in by.items()}, refs=dict(refs))
    return out


def spread(items: list, n: int) -> list:
    """n items taken evenly across the list (all of them when there are no more than n)."""
    if len(items) <= n:
        return list(items)
    return [items[int((i + 0.5) * len(items) / n)] for i in range(n)]
