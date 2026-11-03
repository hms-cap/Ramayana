"""Stage 1 (lexicon): short English glosses for every DCS lemma.

Usage:
    python etl/build_lexicon.py path/to/apte-1890.babylon

Writes data/lexicon/gloss.json  {lemma_slp1: gloss}  and
data/lexicon/gloss_report.json.

Sources, in order of priority:
 1. etl/gloss_overrides.json — glosses written for this project (pronouns,
    particles, the epic's proper names). Needed because dictionary headwords
    mislead for these: DCS lemmatises "aham, me" under `mad`, which in a
    dictionary is "intoxication"; "rAma" first means "pleasing".
 2. Apte, The Practical Sanskrit-English Dictionary (1890), Cologne digital
    edition, CC BY-NC-SA 3.0 (credit: "Copyright 2014 The Sanskrit Library and
    Thomas Malten"). Each gloss is the first few senses of the entry with
    quotations, citations and compounds removed.

The Kannada dictionary Shabdarthakaustubha is NOT used here: its upstream
repository states no licence, so it is linked to rather than redistributed.
Kannada meanings come only from etl/gloss_kn.json: about 500 lemmas (names,
epithets, pronouns, particles and the commonest small words of both epics),
written for this project by Claude and awaiting review by a Kannada reader.
They are copied to data/lexicon/gloss_kn.json; the panel shows them first when
the script is Kannada, with the English underneath.

A dictionary gloss describes the lemma in general. It is not a translation
of the word as used in a particular verse, and the reader says so.
"""
from __future__ import annotations

import collections
import gzip
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from translit import brahmic_to_slp1, slp1_to_brahmic, slp1_to_iast  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "lexicon"
DEVA = re.compile(r"[ऀ-ॿ]")
MAX_LEN = 150


def read_babylon(path: str) -> dict[str, list[str]]:
    """headword (Devanagari) -> list of definition strings."""
    entries = collections.defaultdict(list)
    block = []
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("#"):
            continue
        if line == "":
            if len(block) >= 2:
                for hw in block[0].split("|"):
                    entries[hw.strip()].append(" ".join(block[1:]))
            block = []
        else:
            block.append(line)
    if len(block) >= 2:
        for hw in block[0].split("|"):
            entries[hw.strip()].append(" ".join(block[1:]))
    return entries


CITATION = re.compile(r"\b[A-ZŚṢ][A-Za-zāīūṛṇṣś]{0,4}\.(?:\s*\d+\.?)+")   # "Ś. 4", "R. 14. 67"
SEE = re.compile(r"See\s+(?:under|also)?\s*([\u0900-\u097F]+)")


def clean_entry(entry: str) -> str:
    t = re.sub(r"<a [^>]*>.*?</a>", " ", entry, flags=re.S)
    t = re.sub(r"<BR\s*/?>", " ", t, flags=re.I)
    t = html.unescape(re.sub(r"<[^>]+>", "", t))
    return re.sub(r"\s+", " ", t).strip()


def short_gloss(entry: str) -> str:
    t = clean_entry(entry)
    t = re.split(r"--\s*Comp\.", t)[0]                       # compounds section
    t = re.sub(r"\[[^\]]*\]", " ", t)                       # etymology brackets
    t = re.sub(r"^\S+\s+", "", t, count=1)                   # the headword itself
    segs = [x.strip() for x in t.split("--") if x.strip()]
    keep = []
    for seg in segs[:8]:
        seg = re.sub(r"\{[^}]*\}", " ", seg)                   # {c1c} {vI.v} class markers
        seg = re.sub(r"^(?:[IVX]+\.\s*)?(?:[PAU]\.\s*\(?\s*)?", "", seg)  # "I. P. (" verb-class lead-ins
        seg = re.sub(r"^(?:(?:m|f|n|a|ind|pron|adv|pp|s|pr)\.\s*)+", "", seg)   # part-of-speech abbreviations
        seg = re.sub(r"^[PAU]\.\s+", "", seg)                  # voice letters ("P. To ask")
        seg = re.sub(r"^\d+\s+", "", seg)                      # sense numbers
        seg = DEVA.split(seg)[0]                               # drop quotations from first Devanagari char
        seg = CITATION.sub("", seg)
        seg = re.sub(r"\([^)]*$", "", seg)                     # a parenthesis cut off by the above
        seg = re.sub(r"\s+", " ", seg).strip(" ;,:.")
        seg = re.sub(r"\s+[PAU]\.?$", "", seg)                # stray verb-class letter at the end
        seg = trim_dangling(seg)
        if len(seg) >= 3 and not re.fullmatch(r"(?:Caus|Desid|Pass|Intens|Den|Ved|Comp)\.?", seg) and seg not in keep:
            keep.append(seg)
    g = ""
    for seg in keep:                                          # whole senses only, up to MAX_LEN
        cand = f"{g} | {seg}" if g else seg
        if len(cand) <= MAX_LEN:
            g = cand
        else:
            if not g:
                cut = seg[:MAX_LEN]
                pos = max(cut.rfind(","), cut.rfind(";"))
                cut = cut[:pos] if pos > 20 else cut.rsplit(" ", 1)[0]
                g = trim_dangling(cut) + "…"
            break
    return g if len(g.rstrip("…")) >= 4 else ""


DANGLING = re.compile(r"(?:\s+|^)(?:of|to|or|and|in|with|a|an|the|by|for|at|as|from|esp|i\.\s*e|e\.\s*g|&c|oft|usually|also|etc)\.?$", re.I)


def trim_dangling(t: str) -> str:
    """Drop trailing connective words left over when a sentence was cut short."""
    prev = None
    while prev != t:
        prev = t
        t = DANGLING.sub("", t).rstrip(" ;,:.-")
    return t


def lookup(entries, hw: str) -> str:
    """Gloss for a Devanagari headword. Follows one 'See under X' cross-reference
    and says so, since the root's meaning is not the derived word's meaning."""
    defs = entries.get(hw)
    if not defs:
        return ""
    g = short_gloss(defs[0])
    if g and not g.lower().startswith("see "):
        return g
    m = SEE.search(clean_entry(defs[0]))
    if not m or m.group(1) == hw:
        return ""
    root_defs = entries.get(m.group(1))
    if not root_defs:
        return ""
    rg = short_gloss(root_defs[0])
    if not rg or rg.lower().startswith("see "):
        return ""
    root = slp1_to_iast(brahmic_to_slp1(m.group(1)))
    return f"from {root}: {rg}"


def main(babylon: str) -> None:
    """Lemmas of both epics: the Rāmāyaṇa file and the Mahābhārata file (gzipped)."""
    freq = collections.Counter()
    srcs = [open(ROOT / "data" / "normalized" / "words.jsonl", encoding="utf-8")]
    mb = ROOT / "data" / "normalized" / "mbh" / "words.jsonl.gz"
    if mb.exists():
        srcs.append(gzip.open(mb, "rt", encoding="utf-8"))
    for src in srcs:
        for line in src:
            for u in json.loads(line)["units"]:
                freq.update(u["l"])
    entries = read_babylon(babylon)
    overrides = json.loads((Path(__file__).parent / "gloss_overrides.json").read_text(encoding="utf-8"))
    overrides.pop("_comment", None)

    gloss, source = {}, collections.Counter()
    missing = []
    for lemma, n in freq.items():
        if lemma in overrides:
            gloss[lemma] = overrides[lemma]
            source["override"] += 1
            continue
        if len(lemma) <= 2:           # short words are where dictionary homonyms mislead most
            source["short_skipped"] += 1
            missing.append((n, lemma))
            continue
        g = lookup(entries, slp1_to_brahmic(lemma, "deva"))
        if g:
            gloss[lemma] = g
            source["apte"] += 1
            continue
        missing.append((n, lemma))

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "gloss.json").write_text(json.dumps(gloss, ensure_ascii=False, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    kn = json.loads((Path(__file__).parent / "gloss_kn.json").read_text(encoding="utf-8"))
    kn = {l: g for l, g in kn.items() if l in gloss}
    (OUT / "gloss_kn.json").write_text(json.dumps(kn, ensure_ascii=False, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    tok_cov = sum(freq[l] for l in gloss) / sum(freq.values())
    missing.sort(reverse=True)
    report = {
        "lemmas": len(freq), "with_gloss": len(gloss), "sources": dict(source),
        "token_coverage": round(tok_cov, 4),
        "kannada_lemmas": len(kn), "kannada_token_coverage": round(sum(freq[l] for l in kn) / sum(freq.values()), 4),
        "top_missing": [[l, n] for n, l in missing[:60]],
    }
    (OUT / "gloss_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items()}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
