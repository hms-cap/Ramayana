"""Stage 1b: verse and sarga cross-walk between the Vulgate (vu) and the
Baroda Critical Edition (ce).

    python etl/crosswalk.py [--work mbh]

With --work mbh the Kumbakonam (vu) text is walked onto the Pune critical
edition (ce), parvan by parvan, and written to data/crosswalk/mbh/.

Method
------
1. Every verse (and every line) gets a phonetic "loose" key (see
   translit.loose_for_index): vowel length, aspiration, retroflexion,
   sibilants and word breaks are ignored. This matters because the Vulgate
   source writes many verses with sandhi dissolved (जनः च शूद्रो अपि) while
   the CE keeps it (janaś ca śūdro 'pi).
2. Candidate CE verses for a Vulgate verse are retrieved through its
   rarest character trigrams (same kāṇḍa only) and scored with the Dice
   coefficient on trigram sets.
3. Sargas are mapped by majority vote of confident verse matches.
4. Within each Vulgate sarga, confident matches must run in CE order
   (longest increasing subsequence); out-of-order weak matches are dropped.
5. Unmatched verses get a second, line-level pass so that verses whose
   lines are grouped differently in the two editions are recognised.

Output: data/crosswalk/{verses.json, sargas.json, review.tsv, report.json}
"""
from __future__ import annotations

import bisect
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from translit import iast_to_slp1, loose_for_index  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
NORM = ROOT / "data" / "normalized"
OUT = ROOT / "data" / "crosswalk"
if "--work" in sys.argv and sys.argv[sys.argv.index("--work") + 1] == "mbh":
    NORM, OUT = NORM / "mbh", OUT / "mbh"

MATCH, VARIANT, LINE_MATCH = 0.55, 0.38, 0.7
RARE = 12


def load(name):
    recs = [json.loads(l) for l in open(NORM / f"{name}.jsonl", encoding="utf-8")]
    for i, r in enumerate(recs):
        r["i"] = i
        r["line_keys"] = [loose_for_index(iast_to_slp1(" ".join(l))) for l in r["lines"]]
        r["key"] = "".join(r["line_keys"])
        r["tri"] = trigrams(r["key"])
    return recs


def trigrams(s: str) -> set[str]:
    return {s[i:i + 3] for i in range(len(s) - 2)}


def dice(a: set, b: set) -> float:
    return 2 * len(a & b) / (len(a) + len(b)) if a and b else 0.0


class Index:
    def __init__(self, recs, key="tri"):
        self.post = collections.defaultdict(list)
        for r in recs:
            for t in r[key]:
                self.post[(r["k"], t)].append(r["i"])

    def candidates(self, k, tri):
        rare = sorted(tri, key=lambda t: len(self.post.get((k, t), ())) or 10**9)[:RARE]
        c = collections.Counter()
        for t in rare:
            for i in self.post.get((k, t), ()):
                c[i] += 1
        return [i for i, _ in c.most_common(40)]


def containment(a: set, b: set) -> float:
    """Share of a's trigrams found in b (a line may be half of the other's line)."""
    return len(a & b) / len(a) if a else 0.0


def best_line(line_key: str, pool) -> tuple[float, int | None]:
    lt = trigrams(line_key)
    best = (0.0, None)
    for c in pool:
        for i, cl in enumerate(c["line_keys"]):
            sc = containment(lt, trigrams(cl))
            # also try the CE line joined with the next one (VU half-lines can straddle)
            if i + 1 < len(c["line_keys"]):
                sc = max(sc, containment(lt, trigrams(cl + c["line_keys"][i + 1])))
            if sc > best[0]:
                best = (sc, c["i"])
    return best


def line_coverage(r, pool) -> float:
    lines = [lk for lk in r["line_keys"] if len(lk) >= 8]
    if not lines:
        return 1.0
    return sum(1 for lk in lines if best_line(lk, pool)[0] >= LINE_MATCH) / len(lines)


def lis_indices(seq):
    """Indices of a longest strictly increasing subsequence of seq."""
    tails, tails_i, prev = [], [], [-1] * len(seq)
    for i, x in enumerate(seq):
        j = bisect.bisect_left(tails, x)
        if j == len(tails):
            tails.append(x); tails_i.append(i)
        else:
            tails[j] = x; tails_i[j] = i
        prev[i] = tails_i[j - 1] if j else -1
    out, i = [], tails_i[-1] if tails_i else -1
    while i != -1:
        out.append(i); i = prev[i]
    return set(out)


def ref(r):
    return f'{r["k"]}.{r["s"]}.{r["v"]}'


def main():
    ce, vu = load("ce"), load("vu")
    idx = Index(ce)

    # --- pass 1: verse-level best match -------------------------------------
    best = {}
    for r in vu:
        scored = [(dice(r["tri"], ce[i]["tri"]), i) for i in idx.candidates(r["k"], r["tri"])]
        if scored:
            best[r["i"]] = max(scored)

    # --- pass 2: sarga mapping by majority of confident matches ---------------
    votes = collections.defaultdict(collections.Counter)
    for vi, (sc, ci) in best.items():
        if sc >= MATCH:
            votes[(vu[vi]["k"], vu[vi]["s"])][(ce[ci]["k"], ce[ci]["s"])] += 1
    vu_sarga_count = collections.Counter((r["k"], r["s"]) for r in vu)
    sarga_map = {}
    for key, c in votes.items():
        (tk, ts), n = c.most_common(1)[0]
        sarga_map[key] = {"ce": (tk, ts), "share": round(n / vu_sarga_count[key], 3)}

    # --- pass 3: whole-verse matches, kept only if in order and in the right sarga
    by_vs = collections.defaultdict(list)
    for r in vu:
        by_vs[(r["k"], r["s"])].append(r["i"])
    status = {}
    for key, vis in by_vs.items():
        m = sarga_map.get(key)
        near = set()
        if m:
            tk, ts = m["ce"]
            near = {(tk, ts + d) for d in (-1, 0, 1)}
        cand = [(vi, best[vi]) for vi in vis if vi in best and best[vi][0] >= VARIANT]
        keep = lis_indices([ci for _, (_, ci) in cand])
        for j, (vi, (sc, ci)) in enumerate(cand):
            c = ce[ci]
            if sc < 0.8 and ((c["k"], c["s"]) not in near or j not in keep):
                continue
            frac = line_coverage(vu[vi], [c])
            if sc >= 0.75 or (sc >= MATCH and frac == 1):
                status[vi] = ("match", [ci], round(sc, 3))
            elif frac == 0:
                status[vi] = ("variant", [ci], round(sc, 3))
            # otherwise some lines match and some don't: resolved line by line below

    # --- pass 4: line-level pass for the rest ---------------------------------
    ce_by_sarga = collections.defaultdict(list)
    for r in ce:
        ce_by_sarga[(r["k"], r["s"])].append(r)
    for r in vu:
        if r["i"] in status:
            continue
        m = sarga_map.get((r["k"], r["s"]))
        if not m:
            continue
        tk, ts = m["ce"]
        pool = [c for d in (-1, 0, 1) for c in ce_by_sarga.get((tk, ts + d), [])]
        hits, scores, n = [], [], 0
        for lk in r["line_keys"]:
            if len(lk) < 8:
                continue
            n += 1
            sc, tgt = best_line(lk, pool)
            if sc >= LINE_MATCH:
                hits.append(tgt); scores.append(sc)
        if hits:
            status[r["i"]] = ("regrouped" if len(hits) == n else "partial", sorted(set(hits)),
                              round(sum(scores) / len(scores), 3))

    # --- assemble -------------------------------------------------------------
    vu_out, ce_out = {}, {}
    ce_hits = collections.defaultdict(list)
    for r in vu:
        st = status.get(r["i"])
        if not st:
            vu_out[r["uid"]] = {"status": "absent"}
            continue
        kind, targets, sc = st
        vu_out[r["uid"]] = {"status": kind, "targets": [ce[t]["uid"] for t in targets], "score": sc}
        for t in targets:
            ce_hits[t].append((kind, r["i"], sc))
    for c in ce:
        h = ce_hits.get(c["i"])
        if not h:
            ce_out[c["uid"]] = {"status": "absent"}
            continue
        order = {"match": 0, "variant": 1, "regrouped": 2, "partial": 3}
        kind, vi, sc = min(h, key=lambda x: (order[x[0]], -x[2]))
        ce_out[c["uid"]] = {"status": kind, "targets": [vu[x[1]]["uid"] for x in sorted(h, key=lambda x: x[1])], "score": sc}

    sargas = {}
    for (k, s), m in sarga_map.items():
        sargas[f"vu:{k}.{s}"] = f'ce:{m["ce"][0]}.{m["ce"][1]}'
    rev = collections.defaultdict(collections.Counter)
    for c in ce:
        st = ce_out[c["uid"]]
        if st["status"] != "absent":
            t = st["targets"][0].split("-")
            rev[(c["k"], c["s"])][(int(t[1]), int(t[2]))] += 1
    for (k, s), cnt in rev.items():
        (vk, vs), _ = cnt.most_common(1)[0]
        sargas[f"ce:{k}.{s}"] = f"vu:{vk}.{vs}"

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "verses.json").write_text(json.dumps({"vu": vu_out, "ce": ce_out}, ensure_ascii=False,
                                                separators=(",", ":")), encoding="utf-8")
    (OUT / "sargas.json").write_text(json.dumps(sargas, indent=0, sort_keys=True), encoding="utf-8")

    ce_by_uid = {c["uid"]: c for c in ce}
    with open(OUT / "review.tsv", "w", encoding="utf-8") as f:
        f.write("vulgate\tstatus\tscore\tce\tvulgate_text\tce_text\n")
        for r in vu:
            st = vu_out[r["uid"]]
            if st["status"] in ("variant", "partial"):
                t = ce_by_uid[st["targets"][0]]
                f.write(f'{ref(r)}\t{st["status"]}\t{st["score"]}\t{ref(t)}\t'
                        f'{" / ".join(" ".join(l) for l in r["lines"])}\t{" / ".join(" ".join(l) for l in t["lines"])}\n')

    vc = collections.Counter(v["status"] for v in vu_out.values())
    cc = collections.Counter(v["status"] for v in ce_out.values())
    unmapped = sorted(f"{k}.{s}" for (k, s) in vu_sarga_count if (k, s) not in sarga_map)
    report = {
        "vulgate_verses": dict(vc), "ce_verses": dict(cc),
        "vulgate_sargas_mapped": len(sarga_map), "vulgate_sargas_total": len(vu_sarga_count),
        "vulgate_sargas_unmapped": unmapped,
        "ce_sargas_mapped": len(rev),
        "thresholds": {"match": MATCH, "variant": VARIANT, "line": LINE_MATCH},
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
