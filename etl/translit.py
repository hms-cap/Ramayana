"""Deterministic Sanskrit transliteration via SLP1.

Pipeline:  IAST / Devanāgarī / Kannada  ->  SLP1  ->  Devanāgarī / Kannada / IAST

SLP1 is used internally because every Sanskrit phoneme is exactly one ASCII
character, which makes conversion, scansion and search normalisation simple
and lossless. The same tables are mirrored in site/static/translit.js; the
test-suite checks that both implementations agree.
"""
from __future__ import annotations

import re
import unicodedata

# --------------------------------------------------------------------------
# SLP1 inventory
# --------------------------------------------------------------------------
VOWELS = "aAiIuUfFxXeEoO"
LONG_VOWELS = set("AIUFXeEoO")
CONSONANTS = "kKgGNcCjJYwWqQRtTdDnpPbBmyrlvSzshL"
STOPS = {  # class nasal for para-savarṇa
    **{c: "N" for c in "kKgG"},
    **{c: "Y" for c in "cCjJ"},
    **{c: "R" for c in "wWqQ"},
    **{c: "n" for c in "tTdD"},
    **{c: "m" for c in "pPbB"},
}

# --------------------------------------------------------------------------
# IAST <-> SLP1
# --------------------------------------------------------------------------
_IAST_TO_SLP1 = {
    "ai": "E", "au": "O",
    "kh": "K", "gh": "G", "ch": "C", "jh": "J", "ṭh": "W", "ḍh": "Q",
    "th": "T", "dh": "D", "ph": "P", "bh": "B",
    "ā": "A", "ī": "I", "ū": "U", "ṛ": "f", "ṝ": "F", "ḷ": "x", "ḹ": "X",
    "ṅ": "N", "ñ": "Y", "ṭ": "w", "ḍ": "q", "ṇ": "R", "ś": "S", "ṣ": "z",
    "ṃ": "M", "ṁ": "M", "ḥ": "H", "m̐": "~",
}
_IAST_RE = re.compile("|".join(sorted(map(re.escape, _IAST_TO_SLP1), key=len, reverse=True)))
_SLP1_TO_IAST = {v: k for k, v in _IAST_TO_SLP1.items() if k not in ("ṁ",)}
_SLP1_TO_IAST["L"] = "ḻ"


def iast_to_slp1(text: str) -> str:
    text = unicodedata.normalize("NFC", text).lower()
    return _IAST_RE.sub(lambda m: _IAST_TO_SLP1[m.group(0)], text)


def slp1_to_iast(text: str) -> str:
    return "".join(_SLP1_TO_IAST.get(ch, ch) for ch in text)


# --------------------------------------------------------------------------
# SLP1 <-> Brahmic (Devanāgarī, Kannada)
# --------------------------------------------------------------------------
_SCRIPTS = {
    "deva": {
        "vowels": dict(zip(VOWELS, "अआइईउऊऋॠऌॡएऐओऔ")),
        "signs": dict(zip("AiIuUfFxXeEoO", "ािीुूृॄॢॣेैोौ")),
        "cons": dict(zip(CONSONANTS, "कखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसहळ")),
        "virama": "्", "M": "ं", "H": "ः", "~": "ँ", "'": "ऽ",
        "digits": "०१२३४५६७८९",
    },
    "knda": {
        "vowels": dict(zip(VOWELS, "ಅಆಇಈಉಊಋೠಌೡಏಐಓಔ")),
        "signs": dict(zip("AiIuUfFxXeEoO", "ಾಿೀುೂೃೄೢೣೇೈೋೌ")),
        "cons": dict(zip(CONSONANTS, "ಕಖಗಘಙಚಛಜಝಞಟಠಡಢಣತಥದಧನಪಫಬಭಮಯರಲವಶಷಸಹಳ")),
        "virama": "್", "M": "ಂ", "H": "ಃ", "~": "ಁ", "'": "ಽ",
        "digits": "೦೧೨೩೪೫೬೭೮೯",
    },
}
DANDA, DOUBLE_DANDA = "।", "॥"


def slp1_to_brahmic(text: str, script: str) -> str:
    t = _SCRIPTS[script]
    out: list[str] = []
    pending = False  # last char was a consonant still carrying implicit 'a'
    for ch in text:
        if ch in t["cons"]:
            if pending:
                out.append(t["virama"])
            out.append(t["cons"][ch])
            pending = True
        elif ch in t["vowels"]:
            if pending:
                if ch != "a":
                    out.append(t["signs"][ch])
                pending = False
            else:
                out.append(t["vowels"][ch])
        else:
            if pending:
                out.append(t["virama"])
                pending = False
            if ch in ("M", "H", "~", "'"):
                out.append(t[ch])
            elif ch.isdigit():
                out.append(t["digits"][int(ch)])
            else:
                out.append(ch)
    if pending:
        out.append(t["virama"])
    return "".join(out)


def _reverse(script: str):
    t = _SCRIPTS[script]
    rev = {}
    for k, v in t["vowels"].items():
        rev[v] = ("V", k)
    for k, v in t["signs"].items():
        rev[v] = ("S", k)
    for k, v in t["cons"].items():
        rev[v] = ("C", k)
    rev[t["virama"]] = ("X", "")
    for k in ("M", "H", "~", "'"):
        rev[t[k]] = ("O", k)
    for i, d in enumerate(t["digits"]):
        rev[d] = ("O", str(i))
    return rev


_REV = {s: _reverse(s) for s in _SCRIPTS}
_NUKTA = {"़", "಼"}
_ZW = {"‌", "‍"}


def brahmic_to_slp1(text: str) -> str:
    """Convert Devanāgarī and/or Kannada text (may be mixed) to SLP1."""
    text = unicodedata.normalize("NFC", text)
    out: list[str] = []
    pending = False
    for ch in text:
        if ch in _NUKTA or ch in _ZW:
            continue
        kind = None
        for rev in _REV.values():
            if ch in rev:
                kind, val = rev[ch]
                break
        if kind == "C":
            if pending:
                out.append("a")
            out.append(val)
            pending = True
            continue
        if kind == "S":
            out.append(val)
            pending = False
            continue
        if kind == "X":
            pending = False
            continue
        if pending:
            out.append("a")
            pending = False
        if kind in ("V", "O"):
            out.append(val)
        elif ch in (DANDA, DOUBLE_DANDA):
            out.append("|")
        else:
            out.append(ch)
    if pending:
        out.append("a")
    return "".join(out)


# --------------------------------------------------------------------------
# Display helpers
# --------------------------------------------------------------------------
_CONS_CLASS = re.escape(CONSONANTS)


def join_for_display(slp1: str) -> str:
    """Traditional Brahmic printing: a word ending in a bare consonant is
    written together with the next word (vālmīkir munipuṃgavam ->
    वाल्मीकिर्मुनिपुंगवम्), and avagraha attaches to the preceding word."""
    s = re.sub(rf"([{_CONS_CLASS}]) +(?=\S)", r"\1", slp1)
    s = re.sub(r" +'", "'", s)
    return s


def para_savarna(slp1: str) -> str:
    """Replace anusvāra before a stop (within a written word) with the
    homorganic nasal: puMgava -> puNgava (ಪುಙ್ಗವ)."""
    out = []
    for i, ch in enumerate(slp1):
        if ch == "M" and i + 1 < len(slp1) and slp1[i + 1] in STOPS:
            out.append(STOPS[slp1[i + 1]])
        else:
            out.append(ch)
    return "".join(out)



def to_digits(n: str | int, script: str) -> str:
    if script == "iast":
        return str(n)
    d = _SCRIPTS[script]["digits"]
    return "".join(d[int(c)] if c.isdigit() else c for c in str(n))


def anusvara_before_stops(slp1: str) -> str:
    """Kannada print usage: a class nasal before a stop of its own class is written as anusvāra
    (saNga -> saMga ಸಂಗ, paYca -> paMca ಪಂಚ, anta -> aMta ಅಂತ). Only inside a written word: it runs
    before join_for_display, so it never reaches across a space."""
    return re.sub(r"[NYRnm](?=[kKgGcCjJwWqQtTdDpPbB])",
                  lambda m: "M" if STOPS[slp1[m.end()]] == m.group(0) else m.group(0), slp1)


def render(slp1: str, script: str, *, savarna: bool = False) -> str:
    """Render one SLP1 line for display in 'deva', 'knda' or 'iast'.
    Kannada shows anusvāra before a stop of the same class (anusvara_before_stops) unless savarna asks
    for class nasals everywhere (para_savarna); Devanāgarī keeps the source spelling unless savarna."""
    if script == "iast":
        return slp1_to_iast(slp1)
    if script == "knda" and not savarna:
        slp1 = anusvara_before_stops(slp1)
    s = join_for_display(slp1)
    if savarna:
        s = para_savarna(s)
    return slp1_to_brahmic(s, script)


# --------------------------------------------------------------------------
# Search normalisation ("loose" key) — mirrored in translit.js
# --------------------------------------------------------------------------
_LOOSE = {
    "A": "a", "I": "i", "U": "u", "f": "ri", "F": "ri", "x": "li", "X": "li",
    "E": "ai", "O": "au",
    "K": "k", "G": "g", "N": "n", "C": "c", "J": "j", "Y": "n",
    "w": "t", "W": "t", "q": "d", "Q": "d", "R": "n",
    "T": "t", "D": "d", "P": "p", "B": "b",
    "S": "s", "z": "s", "L": "l", "H": "", "~": "n", "'": "",
}
_LABIAL_OR_FRICATIVE = set("pPbBmyrlvSzsh")


def loose_key(slp1: str) -> str:
    """Lossy, phonetic key so that ಮಾರೀಚ, मारीच, mārīca and maricha all
    reduce to the same string ('marica'). Spaces are removed so matches work
    across sandhi word boundaries."""
    s = re.sub(r"[^A-Za-z'~]", "", slp1)
    out = []
    for i, ch in enumerate(s):
        if ch == "M":
            nxt = s[i + 1] if i + 1 < len(s) else ""
            out.append("m" if (not nxt or nxt in _LABIAL_OR_FRICATIVE or nxt in VOWELS) else "n")
        else:
            out.append(_LOOSE.get(ch, ch))
    return "".join(out)


def ascii_query_to_loose(q: str) -> str:
    """Loose key for a plain-ASCII query typed the way people usually
    romanise Indian words (maricha, seetha, krishna, hanuman)."""
    q = q.lower()
    q = re.sub(r"[^a-z]", "", q)
    q = q.replace("ee", "i").replace("oo", "u").replace("aa", "a")
    q = q.replace("ou", "au").replace("w", "v")
    # drop aspiration / sh / ch digraph 'h' after a consonant
    q = re.sub(r"([bcdgjkptsr])h", r"\1", q)
    q = re.sub(r"h$", "", q)  # final visarga typed as h
    q = q.replace("ksh", "ks").replace("x", "ks")
    q = re.sub(r"(.)\1", r"\1", q)  # collapse doubled letters
    return q


def loose_for_index(slp1: str) -> str:
    """Index key: loose key with doubled letters collapsed (so 'putra' and
    'puttra' style typing both match)."""
    return re.sub(r"(.)\1", r"\1", loose_key(slp1))
