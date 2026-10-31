"""Syllable weight (laghu/guru) scansion and basic metre identification.

Only the metres that make up practically all of the Rāmāyaṇa are named:
Anuṣṭubh (śloka) and the Triṣṭubh / Jagatī families. Anything else is
reported with its syllable counts so nothing is silently mislabelled.
"""
from __future__ import annotations

from translit import CONSONANTS, LONG_VOWELS, VOWELS

L, G = "L", "G"

# Pāda patterns (the final syllable is anceps and ignored when matching).
PADA = {
    "GGLGGLLGLGG": "Indravajrā",
    "LGLGGLLGLGG": "Upendravajrā",
    "GLGLLLGLLGG": "Rathoddhatā",
    "GGGGLGGLGGG": "Śālinī",
    "LGLGGLLGLGLG": "Vaṃśastha",
    "GGLGGLLGLGLG": "Indravaṃśā",
    "LLLGLLGLLGLG": "Drutavilambita",
    "GGGLLLLGLGLGG": "Praharṣiṇī",
    "LGLGLLLLGLGLG": "Rucirā",
    "GGLGLLLGLLGLGG": "Vasantatilakā",
}
# Ardhasama metres: (odd pāda, even pāda)
ARDHASAMA = {
    ("LLLLLLGLGLGG", "LLLLGLLGLGLGG"): "Puṣpitāgrā",
    ("LLLLLLGLGLG", "LLLLGLLGLGLG"): "Aparavaktra",
}
UPAJATI_T = {"Indravajrā", "Upendravajrā"}
UPAJATI_J = {"Vaṃśastha", "Indravaṃśā"}


def _same(a: str, b: str) -> bool:
    return len(a) == len(b) and a[:-1] == b[:-1]


def _pada_name(p: str) -> str | None:
    for target, name in PADA.items():
        if _same(p, target):
            return name
    return None


def scan(slp1_pada: str) -> str:
    """Return a string of L/G, one per syllable. The final syllable of the
    pāda is treated as heavy (anceps) only by the metre matcher, not here."""
    s = "".join(ch for ch in slp1_pada if ch in VOWELS or ch in CONSONANTS or ch in "MH~")
    weights = []
    i, n = 0, len(s)
    while i < n:
        if s[i] in VOWELS:
            v = s[i]
            j = i + 1
            heavy = v in LONG_VOWELS
            if j < n and s[j] in "MH~":
                heavy = heavy or s[j] in "MH"
                j += 1
            k = j
            while k < n and s[k] in CONSONANTS:
                k += 1
            if k - j >= 2 and k < n:  # conjunct before the next vowel
                heavy = True
            weights.append(G if heavy else L)
            i = j
        else:
            i += 1
    return "".join(weights)


def identify(lines_slp1: list[list[str]]) -> dict:
    """lines_slp1: list of lines, each a list of pādas (SLP1).
    Returns {'name': str, 'family': str, 'scansion': [[str,...],...]}"""
    scans = []
    for line in lines_slp1:
        sc = [scan(p) for p in line]
        if len(sc) == 1 and len(sc[0]) in (16, 22, 24):  # split unmarked half-verse into pādas
            h = len(sc[0]) // 2
            sc = [sc[0][:h], sc[0][h:]]
        scans.append(sc)
    line_lengths = [sum(len(p) for p in line) for line in scans]
    padas = [p for line in scans for p in line]
    if line_lengths and all(n == 16 for n in line_lengths):
        return {"name": "Anuṣṭubh", "family": "anustubh", "scansion": scans}
    names = [_pada_name(p) for p in padas]
    name = None
    if padas and all(names):
        kinds = set(names)
        if len(kinds) == 1:
            name = names[0]
        elif kinds <= UPAJATI_T:
            name = "Upajāti"
        elif kinds <= UPAJATI_J:
            name = "Upajāti (Jagatī)"
        elif kinds <= UPAJATI_T | UPAJATI_J:
            name = "Upajāti (mixed)"
    if name is None and len(padas) >= 2 and len(padas) % 2 == 0:
        for (odd, even), nm in ARDHASAMA.items():
            if all(_same(p, odd if i % 2 == 0 else even) for i, p in enumerate(padas)):
                name = nm
    if name is None and padas:
        lens = {len(p) for p in padas}
        name = {frozenset({11}): "Triṣṭubh", frozenset({12}): "Jagatī",
                frozenset({11, 12}): "Upajāti (mixed)"}.get(frozenset(lens))
    family = "anustubh" if name == "Anuṣṭubh" else ("other" if name is None else "vrtta")
    return {"name": name, "family": family, "scansion": scans}
