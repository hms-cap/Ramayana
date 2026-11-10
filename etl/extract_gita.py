"""Extract the Bhagavadgītā from the two Mahābhārata editions into a standalone dataset.

    python etl/extract_gita.py

Reads  data/normalized/mbh/{ce,vu}.jsonl
Writes data/normalized/gita/{ce,vu}.jsonl     one record per verse, chapter/verse order
       data/crosswalk/gita/{verses,sargas,report}.json   Gītā-only Pune<->Kumbakonam crosswalk
       data/gita/gretil_appendix_18_78.txt    raw junk GRETIL appends to Pune 18.78 (see below)
Stdlib plus the repo's own etl/meter.py and translit.py.

Record: {"uid":"BG-CE-02-047","ch":2,"v":47,"speaker":null|"śrībhagavān uvāca",
         "lines":[["pāda"],...],"meter":...,"mbh_uid":"CE-6-024-047"[,"colophon":...][,"speaker_inline":true]}
"lines" is the source structure minus speaker lines and junk. "meter" follows the ingest convention
(meter.identify on the cleaned lines, only for 2- or 4-line verses, else null).

Sources
-------
Pune (CE):       k=6, adhyāyas 23-40 = Gītā chapters 1-18 (ch = s - 22); 700 verses.
Kumbakonam (VU): k=6, adhyāyas 25-42 = Gītā chapters 1-18 (ch = s - 24); 700 records.
Verse numbers are each edition's own, as printed. The familiar "700" numbering follows Pune; the VU numbering
differs only in chapter 13 (below).

Speakers
--------
Pune prints the speaker line first in the verse it introduces. Kumbakonam prints it as the LAST line of the
PRECEDING verse (across chapter boundaries too); that trailing line is moved to the next verse. Two VU verses
(1.21 = VU-6-025-021, 1.28 = VU-6-025-028) have the speaker line in the middle of the record (the VU verse
break falls inside a sentence); the line is removed and used as that verse's speaker, flagged
"speaker_inline": true. VU-6-026-001 has its own leading "sañjaya uvāca" and a trailing "śrībhagavānuvāca":
the leading one is its speaker, the trailing one goes to 2.2. Speaker strings are kept as in the source
(incl. "śrībhagavānuvāca" and the VU typo "śrībhagavanuvāca", which gives BG-VU-10-019 its speaker).
Only whole lines equal to "<name> uvāca" count; pādas that merely contain "uvāca" are verse text.

Junk (non-verse text in the Gītā range)
---------------------------------------
1. CE-6-023-001: the GRETIL preface (nyāsa formulas, dhyāna ślokas (1)-(5)); removed from the MBH file by
   etl/fix_mbh_gita_preface.py, raw text in data/gita/gretil_preface.txt. This script also truncates such a
   block itself (first line with "namaḥ |", "(Gītā", "atha dhyānaṃ") so it works on either state of the file.
2. CE-6-040-078 (18.78): after the two real lines (yatra yogeśvaraḥ ... matir mama) GRETIL appends a
   246-line apocryphal text (a "Gītā" dialogue "arjuna uvāca / yad etan niṣkalaṃ brahma ...", numbered
   (1)-(51), then a second, variant copy numbered (1)-(57), with "...." gaps). Not Mahābhārata; it is
   cut (for Pune any speaker line after the first line is the cut point) and saved to
   data/gita/gretil_appendix_18_78.txt. NOT removed from data/normalized/mbh/ce.jsonl (outside the task scope).
3. No colophons ("iti śrīmadbhagavadgītāsu ...") or "(Gītā" runs exist elsewhere in the 6.23-40 / 6.25-42
   ranges of either edition. Colophon detection is implemented anyway ("iti ... gītā..." / "oṃ tat sat" as a
   last line): the line is stripped and stored as "colophon" on the chapter's last verse.
4. Kumbakonam keeps "- -" and a stray "a" in one record (see chapter 13). Left as is, not invented away.

Chapter 13 reconciliation
-------------------------
Pune 13 has 34 verses (adhyāya 35, v=1..34); Kumbakonam 13 has 34 records (adhyāya 37) but numbered 1..35
with number 27 absent. Differences:
 * VU 13.1 "arjuna uvāca / prakṛtiṃ puruṣaṃ caiva ..." is the extra Arjuna question absent from Pune (the
   vulgate's verse 13.1; Pune's 13.1 is "idaṃ śarīraṃ kaunteya"). So VU v = Pune v + 1 up to 25.
 * VU 13.26 (VU-6-037-026) is a single line holding two verses run together, separated by " - - ":
   "anye tvevamajānantaḥ ... śrutiparāyaṇāḥ - - ayāvatsaṃjāyate ... bharatarṣabha". These are Pune 13.25
   ("anye tv evam ajānantaḥ") and Pune 13.26 ("yāvat saṃjāyate"); the second begins with a stray "a" for the
   avagraha ('yāvat). VU has no record numbered 27, so the pair of verses occupies numbers 26 and 27 of its
   own numbering and the count returns to 34 (+1 extra verse -1 merged verse). From VU 28 on, VU v = Pune v + 2.
   So VU 13.28..35 = Pune 13.27..34. Text is not split here (that would mean inventing a boundary in a
   single printed line); the crosswalk records both Pune verses against the merged record where the MBH
   crosswalk does.
"""
from __future__ import annotations

import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).parent))
import meter  # noqa: E402
from translit import iast_to_slp1, loose_for_index  # noqa: E402

NORM = ROOT / "data" / "normalized"
OUT = NORM / "gita"
CW_OUT = ROOT / "data" / "crosswalk" / "gita"
GITA = ROOT / "data" / "gita"

FIRST_S = {"ce": 23, "vu": 25}
EXPECTED = [47, 72, 43, 42, 29, 47, 30, 28, 34, 42, 55, 20, 34, 27, 20, 24, 28, 78]
EXPECTED_ED = {"ce": EXPECTED, "vu": EXPECTED[:12] + [35] + EXPECTED[13:]}
# Kumbakonam records holding two printed verses (after etl/apply_errata.py has split their lines): mbh uid -> lines
# in the first verse. VU-6-037-026 is print 13.26 + 13.27 (the source keys no 13.27), so chapter 13 runs 1–35.
SPLIT = {"VU-6-037-026": 2}

SPEAKER = re.compile(r"^(dhṛtarāṣṭra|saṃjaya|sañjaya|arjuna|śrībhagavān|śrībhagavan) ?uvāca$")
JUNK = re.compile(r"namaḥ \||\(Gītā|atha dhyānaṃ|\|\| \(\d+\)\s*$|\.\.\.\.")
COLOPHON = re.compile(r"^(iti\b.*(gītā|upaniṣa)|oṃ tat sat)", re.I)


def load(ed):
    return [json.loads(l) for l in open(NORM / "mbh" / f"{ed}.jsonl", encoding="utf-8")]


def meter_of(lines):
    if len(lines) not in (2, 4):
        return None
    try:
        return meter.identify([[iast_to_slp1(p) for p in l] for l in lines])["name"]
    except Exception:
        return None


def is_speaker(line):
    return len(line) == 1 and bool(SPEAKER.match(line[0].strip()))


def extract(ed, report):
    s0 = FIRST_S[ed]
    recs = [r for r in load(ed) if r["k"] == 6 and s0 <= r["s"] < s0 + 18]
    out, pending = [], None
    for r in recs:
        ch = r["s"] - s0 + 1
        lines = list(r["lines"])
        speaker, inline, colophon = None, False, None
        junk = []
        if ed == "ce":  # speaker is always first; anything after a later speaker/junk marker is appended text
            cut = None
            for i, l in enumerate(lines):
                if i > 0 and (is_speaker(l) or JUNK.search(" ".join(l))):
                    cut = i
                    break
            if cut is not None:
                junk = lines[cut:]
                lines = lines[:cut]
                report["junk"].append((r["uid"], len(junk)))
                if r["uid"] == "CE-6-040-078":
                    GITA.mkdir(parents=True, exist_ok=True)
                    (GITA / "gretil_appendix_18_78.txt").write_text(
                        "\n".join(" ".join(l) for l in junk) + "\n", encoding="utf-8")
        if lines and COLOPHON.search(" ".join(lines[-1])):
            colophon = " ".join(lines.pop())
        body, trailing, speaker_at = [], None, None
        for i, l in enumerate(lines):
            if is_speaker(l):
                name = l[0].strip()
                if i == 0:
                    speaker = name
                elif i == len(lines) - 1 and ed == "vu":
                    trailing = name
                else:
                    if speaker is not None:
                        report["conflicts"].append(r["uid"])
                    speaker, inline, speaker_at = name, True, len(body)
            else:
                body.append(l)
        if pending:
            if speaker is not None:
                report["conflicts"].append(r["uid"])
            else:
                speaker = pending
        pending = trailing
        rec = {"uid": f"BG-{ed.upper()}-{ch:02d}-{r['v']:03d}", "ch": ch, "v": r["v"], "speaker": speaker,
               "lines": body, "meter": meter_of(body), "mbh_uid": r["uid"]}
        if inline:
            rec["speaker_inline"] = True
            rec["speaker_at"] = speaker_at          # the speaker line stands before this line of the verse
        if colophon:
            rec["colophon"] = colophon
        if r.get("corrected"):
            rec["corrected"] = r["corrected"]
        if r["uid"] in SPLIT and len(body) > SPLIT[r["uid"]]:
            n = SPLIT[r["uid"]]
            rec2 = {**rec, "uid": f"BG-{ed.upper()}-{ch:02d}-{r['v'] + 1:03d}", "v": r["v"] + 1, "speaker": None,
                    "lines": body[n:], "meter": meter_of(body[n:]), "split_from": r["uid"]}
            rec.update(lines=body[:n], meter=meter_of(body[:n]), split_from=r["uid"])
            out += [rec, rec2]
            report["split"].append(r["uid"])
            continue
        out.append(rec)
    if pending:
        report["conflicts"].append(f"{ed}: trailing speaker {pending!r} after last verse")
    return out


def _key(rec):
    return loose_for_index(iast_to_slp1(" ".join(" ".join(l) for l in rec["lines"])))


def _tri(k):
    return {k[i:i + 3] for i in range(len(k) - 2)}


def crosswalk(ce, vu):
    """Translate data/crosswalk/mbh/verses.json through mbh_uid, then repair two known weaknesses:
    (a) targets outside the same Gītā chapter are dropped (both editions have the same 18 chapters, and the
        MBH walk links e.g. VU 1.15-16 to the identical conch verses at Pune 6.47.25-26 and the extra VU 13.1
        to Pune 12.1-2); (b) a verse left without target is searched for in the same chapter of the other
        edition: Dice on loose trigram sets >= 0.55 gives "match", containment >= 0.8 of the shorter in the
        longer (a merged record, VU 13.26) gives "partial". Repaired entries carry "repaired": true; a status changed from the MBH one keeps it as "mbh_status"."""
    mbh = json.load(open(ROOT / "data" / "crosswalk" / "mbh" / "verses.json", encoding="utf-8"))
    recs = {"ce": ce, "vu": vu}
    g = {sd: {r["mbh_uid"]: r["uid"] for r in recs[sd]} for sd in recs}
    chap = lambda u: int(u.split("-")[2])
    other = {"ce": "vu", "vu": "ce"}
    res, stats = {}, {}
    for side in ("vu", "ce"):
        res[side], outside, xch = {}, 0, 0
        for mu, gu in g[side].items():
            e = mbh[side][mu]
            all_t = [g[other[side]][t] for t in e.get("targets", []) if t in g[other[side]]]
            outside += len(e.get("targets", [])) - len(all_t)
            tg = [t for t in all_t if chap(t) == chap(gu)]
            xch += len(all_t) - len(tg)
            ne = {"status": e["status"] if tg or e["status"] == "absent" else "absent"}
            if tg:
                ne.update(targets=tg, score=e["score"])
            if ne["status"] != e["status"]:
                ne["mbh_status"] = e["status"]
            res[side][gu] = ne
        stats[side + "_targets_outside_gita_dropped"] = outside
        stats[side + "_targets_other_chapter_dropped"] = xch
    split = {r["uid"] for sd in recs for r in recs[sd] if r.get("split_from")}
    for side in ("vu", "ce"):
        for r in recs[side]:
            e = res[side].get(r["uid"])
            if r["uid"] in split or e is None or any(t in split for t in (e or {}).get("targets", [])):
                res[side][r["uid"]] = {"status": "absent"}
    tri = {sd: {r["uid"]: _tri(_key(r)) for r in recs[sd]} for sd in recs}
    byc = {sd: collections.defaultdict(list) for sd in recs}
    for sd in recs:
        for r in recs[sd]:
            byc[sd][r["ch"]].append(r["uid"])
    repaired = 0
    for side in ("ce", "vu"):
        for gu, e in res[side].items():
            if e["status"] != "absent":
                continue
            best = None
            for cand in byc[other[side]][chap(gu)]:
                a, b = tri[side][gu], tri[other[side]][cand]
                if not a or not b:
                    continue
                dice = 2 * len(a & b) / (len(a) + len(b))
                cont = len(a & b) / min(len(a), len(b))
                lopsided = max(len(a), len(b)) > 1.6 * min(len(a), len(b))
                st = "match" if dice >= 0.55 and not lopsided else "partial" if cont >= 0.8 else None
                if st and (best is None or dice > best[0]):
                    best = (dice, cand, st)
            if best:
                e.clear()
                e.update(status=best[2], targets=[best[1]], score=round(best[0], 3), repaired=True)
                back = res[other[side]][best[1]]
                if back["status"] == "absent":
                    back.clear()
                    back.update(status=best[2], targets=[gu], score=round(best[0], 3), repaired=True)
                elif gu not in back.get("targets", []):
                    back["targets"].append(gu)
                repaired += 1
    # "regrouped" at 1.1 and 18.78 was an effect of the junk in the Pune record; re-score on the cleaned text
    rescored = 0
    for side in ("ce", "vu"):
        for gu, e in res[side].items():
            if e["status"] == "regrouped" and len(e["targets"]) == 1:
                a, b = tri[side][gu], tri[other[side]][e["targets"][0]]
                dice = 2 * len(a & b) / (len(a) + len(b))
                if dice >= 0.55:
                    e.update(mbh_status="regrouped", status="match", score=round(dice, 3))
                    rescored += 1
    stats["rescored_regrouped_to_match"] = rescored
    stats["repaired_entries"] = repaired
    for side in ("vu", "ce"):
        stats[side + "_verses"] = dict(collections.Counter(e["status"] for e in res[side].values()))
        stats[side + "_absent"] = [u for u, e in res[side].items() if e["status"] == "absent"]
    sargas = {f"ce:{c}": f"vu:{c}" for c in range(1, 19)}
    sargas.update({f"vu:{c}": f"ce:{c}" for c in range(1, 19)})
    return res, sargas, stats


def write(path, recs):
    with open(path, "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    CW_OUT.mkdir(parents=True, exist_ok=True)
    report = {"junk": [], "conflicts": [], "split": []}
    res = {ed: extract(ed, report) for ed in ("ce", "vu")}
    for ed, recs in res.items():
        counts = [sum(1 for r in recs if r["ch"] == c) for c in range(1, 19)]
        assert counts == EXPECTED_ED[ed], (ed, counts)
        write(OUT / f"{ed}.jsonl", recs)
        print(ed, len(recs), "verses;", sum(1 for r in recs if r["speaker"]), "with speaker;",
              sum(1 for r in recs if r["meter"]), "with meter;", sum(1 for r in recs if "colophon" in r), "colophons")
    cw, sargas, stats = crosswalk(res["ce"], res["vu"])
    (CW_OUT / "verses.json").write_text(json.dumps(cw, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (CW_OUT / "sargas.json").write_text(json.dumps(sargas, ensure_ascii=False, indent=0), encoding="utf-8")
    (CW_OUT / "report.json").write_text(json.dumps(stats, ensure_ascii=False, indent=1), encoding="utf-8")
    print("junk blocks cut:", report["junk"], "| speaker conflicts:", report["conflicts"])
    print(json.dumps(stats, ensure_ascii=False))


if __name__ == "__main__":
    main()
