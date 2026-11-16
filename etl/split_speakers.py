"""Take speaker lines ("dhṛtarāṣṭra uvāca") and Pune appendix passages out of the Mahābhārata verse lines.

    python etl/split_speakers.py [--src-ce <GRETIL mbh dir>] [--src-vu <SARIT xml>] [--dry]

Both sources mark speaker lines; the ingest kept them as ordinary verse lines:
  * Kumbakonam (SARIT): <l rend="speak" xml:id="bhisma-6-25-2x"> — the id names the verse the line introduces,
    which is usually the NEXT verse (the source prints it as the last line of the previous <lg>).
  * Pune (GRETIL): a line whose reference has no pāda letter ("06,023.001\tdhṛtarāṣṭra uvāca").
Pune lines marked "@" (e.g. "01,019.017d@012_0001") are passages printed in the Pune Appendix I, not part of
the critical text; the ingest appended them to the verse after which they occur. Inside them "=" marks a speaker.

Result, per record of data/normalized/mbh/{ce,vu}.jsonl:
  lines   only the verse (or prose) lines
  spk     [{"at": i, "t": "sañjaya uvāca"[, "from": uid]}]  the speaker stands before lines[i] (0 = above the
          verse); "from" = the record that held it before (Kumbakonam trailing speakers), so the old layout can
          be rebuilt (raw_lines below; etl/extract_gita.py uses it)
  app     [{"id": "012", "at": i, "lines": [[pāda], …], "spk": [{"at": j, "t": …}]}]  Pune appendix passages, in order (CE
          only); "at" as for spk (the passage stands before lines[i]; = len(lines) after the verse)
  meter   recomputed by the ingest rule for records whose lines changed
Idempotent: a file that already has spk/app fields is left as it is. Pipeline after a re-ingest:
ingest_mbh.py → (vu: apply_errata.py | ce: fix_mbh_gita_preface.py, fix_pada_markers.py) → split_speakers.py → extract_gita.py.
"""
from __future__ import annotations

import collections
import json
import re
import sys
from pathlib import Path

from lxml import etree

sys.path.insert(0, str(Path(__file__).parent))
from ingest_mbh import LINE, PARVA_NO, TEI, XMLID, clean, deva_to_iast, meter_of, split_padas  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "normalized" / "mbh"
# where etl/fetch_sources.sh puts them (sources/ in the repo), else an older scratch checkout
_GR = "gretil/gretil.sub.uni-goettingen.de/gretil/1_sanskr/2_epic/mbh"
SRC_CE = next((p for p in (ROOT / "sources" / _GR, Path("/tmp/claude-0/src") / _GR) if p.exists()), ROOT / "sources" / _GR)
SRC_VU = next((p for p in (ROOT / "sources/sarit/mahabharata-devanagari.xml", Path("/tmp/claude-0/src/sarit/mahabharata-devanagari.xml"))
               if p.exists()), ROOT / "sources/sarit/mahabharata-devanagari.xml")


SPK_WORD = re.compile(r"(uvāca|ūcuḥ|ūcatuḥ)$")
# a handful of speaker lines carry no mark in the source ("bṛhadaśva uvāca" numbered as a pāda): name + verb alone
UNMARKED = re.compile(r"(?!(?:sa|sā|tam|taṃ|te|tān|tāṃ|tāḥ|tau|ca|punar|punaḥ|idam|idaṃ|tato|tataḥ) )\S+ (?:uvāca|ūcuḥ|ūcatuḥ)")


def is_header(t: str) -> bool:
    """'saṃjaya uvāca', 'ṛṣaya ūcuḥ', 'brahmovāca', 'sautiruvāca' — not 'provāca' or 'tam uvāca'."""
    w = t.split()
    if len(w) == 2:
        return bool(UNMARKED.fullmatch(t))
    return len(w) == 1 and len(t) >= 7 and bool(re.search(r"(uvāca|ovāca|ūcuḥ|ūcatuḥ)$", t)) \
        and not re.match(r"(prat[iy]|pro|abhy|samud|upo)", t)


def key(s: str) -> str:
    return re.sub(r"[^a-zāīūṛṝḷṃḥṅñṭḍṇśṣ]", "", s.lower())


def raw_lines(rec: dict, by_uid: dict | None = None) -> list:
    """The record's lines as the ingest wrote them: speakers back in place (a speaker taken from a previous
    record is NOT put back here; raw_layout() does that across records)."""
    out, own = [], [s for s in rec.get("spk", []) if not s.get("from")]
    for i, l in enumerate(rec["lines"]):
        out += [[s["t"]] for s in own if s["at"] == i]
        out.append(l)
    out += [[s["t"]] for s in own if s["at"] >= len(rec["lines"])]
    return out


def raw_layout(recs: list) -> dict:
    """uid -> lines in the old layout (moved speakers back at the end of the record they came from)."""
    out = {r["uid"]: raw_lines(r) for r in recs}
    for r in recs:
        for s in r.get("spk", []):
            if s.get("from") in out:
                out[s["from"]].append([s["t"]])
    return out


# ---------------- sources: per record, the kind of every line, in order ----------------

def src_vu(path: Path) -> dict:
    """uid -> [(text, target_uid or None)] ; target set for speaker lines."""
    root = etree.parse(str(path), etree.XMLParser(huge_tree=True, collect_ids=False)).getroot()
    body = root.find(f".//{TEI}body")
    out, pend = {}, []
    for pdiv in body.findall(f"{TEI}div"):
        k = PARVA_NO[(pdiv.get(XMLID) or "").removesuffix("parva")]
        for adiv in pdiv.findall(f"{TEI}div"):
            if not (adiv.get(XMLID) or adiv.get("n")):
                continue
            for lg in adiv.iter(f"{TEI}lg"):
                ls = []
                for l in lg.findall(f"{TEI}l"):
                    segs = l.findall(f"{TEI}seg")
                    t = deva_to_iast(" ".join("".join(sg.itertext()) for sg in segs) if segs else "".join(l.itertext()))
                    if not t:
                        continue
                    lid = l.get(XMLID) or ""
                    mx = re.search(r"-(\d+)-(\d+)-(\d+)x$", lid)
                    if mx:
                        ls.append((t, f"VU-{k}-{int(mx[2]):03d}-{int(mx[3]):03d}"))
                    elif l.get("rend") == "speak":
                        ls.append((t, "self"))
                    elif UNMARKED.fullmatch(t):
                        ls.append((t, "self"))
                    else:
                        ls.append((t, None))
                m = re.search(r"-(\d+)-(\d+)-(\d+)(x?)$", lg.get(XMLID) or "")
                if not ls or not m:
                    continue
                s_, v = int(m[2]), int(m[3])
                uid = f"VU-{k}-{s_:03d}-{v:03d}"
                if m[4] or v == 0:
                    # a separate speaker <lg> (or verse 0): the ingest put it in front of the next verse
                    pend.extend((t, "self" if (tg or m[4]) else None) for t, tg in ls)
                    continue
                ls = pend + ls; pend = []
                out.setdefault(uid, ls)
            pend = []
    return out


def src_ce(folder: Path) -> dict:
    """uid -> [(kind, passage_id, text)] ; kind in txt / spk / app / appspk."""
    out = collections.OrderedDict()
    for p in range(1, 19):
        for raw in (folder / f"mbh_{p:02d}_u.htm").read_text(encoding="utf-8").splitlines():
            m = LINE.match(raw.strip())
            if not m:
                continue
            k, s, v, suf, body = int(m[1]), int(m[2]), int(m[3]), m[4], m[5]
            if "*" in suf or not body.strip():
                continue
            uid = f"CE-{k}-{s:03d}-{v:03d}"
            if "@" in suf:
                pa = re.match(r"@([0-9]+[A-Z]?)([_=])(\d+)", suf[suf.index("@"):])
                kind, pid = ("appspk" if pa and pa[2] == "=" else "app"), ((pa[1], int(pa[3])) if pa else (suf, 0))
            else:
                kind, pid = ("spk" if suf == "" or UNMARKED.fullmatch(clean(body)) else "txt"), None
            out.setdefault(uid, []).append((kind, pid, clean(body)))
    # inside a passage a speaker line is sometimes numbered like the line after it ("@041_0003 vaiśaṃpāyana uvāca",
    # "@041_0003 dhṛtarāṣṭrasya …"), not marked "="
    # or numbered as an ordinary line ("@006_0000 vaiśaṃpāyana uvāca"): a bare speaker header is a speaker
    for uid, ls in out.items():
        for i, (kind, pid, t) in enumerate(ls):
            if kind == "app" and is_header(t):
                ls[i] = ("appspk", (pid[0], sum(1 for x in ls[:i] if x[0] == "app" and x[1][0] == pid[0])), t)
    return out


# ---------------- split ----------------

def split_ce(recs: list, src: dict, rep: collections.Counter, notes: list) -> None:
    for r in recs:
        if "spk" in r or "app" in r:
            rep["already"] += 1; continue
        sl = src.get(r["uid"])
        if not sl:
            rep["no_source"] += 1; continue
        n = len(r["lines"])
        if n > len(sl) or any(key(" ".join(r["lines"][i])) != key(sl[i][2]) for i in range(n)):
            rep["mismatch"] += 1; notes.append(f"CE mismatch {r['uid']}"); continue
        kinds = [x[0] for x in sl[:n]]
        if all(k == "txt" for k in kinds):
            continue
        lines, spk, app = [], [], []
        for l, (kind, pid, _) in zip(r["lines"], sl[:n]):
            if kind == "spk":
                spk.append({"at": len(lines), "t": " ".join(l)})
            elif kind in ("app", "appspk"):
                if not app or app[-1]["id"] != pid[0] or app[-1]["at"] != len(lines):
                    app.append({"id": pid[0], "at": len(lines), "lines": [], "spk": []})
                if kind == "appspk":   # "=0015": the speaker stands after line 15 of the passage
                    app[-1]["spk"].append({"at": pid[1], "t": " ".join(l)})
                else:
                    app[-1]["lines"].append(l)
            else:
                if app and app[-1]["at"] == len(lines):
                    rep["app_inside"] += 1   # the verse goes on after the passage: the fold stands before lines[at]
                lines.append(l)
        r["lines"] = lines
        if spk:
            r["spk"] = spk; rep["spk"] += len(spk)
        if app:
            r["app"] = app; rep["app_passages"] += len(app); rep["app_lines"] += sum(len(a["lines"]) + len(a["spk"]) for a in app)
        r["meter"] = meter_of(lines) if len(lines) in (2, 4) else None


def split_vu(recs: list, src: dict, rep: collections.Counter, notes: list) -> None:
    by = {r["uid"]: r for r in recs}
    nxt = {a["uid"]: b["uid"] for a, b in zip(recs, recs[1:]) if (a["k"], a["s"]) == (b["k"], b["s"])}
    moves = []
    for r in recs:
        if "spk" in r:
            rep["already"] += 1; continue
        sl = src.get(r["uid"])
        if not sl:
            rep["no_source"] += 1; continue
        sp = [(t, tg) for t, tg in sl if tg and len(t.split()) <= 3]   # 6 long verse lines are mis-marked "speak"
        if not sp:
            continue
        # find each speaker line in the record by its text (errata may have split other lines)
        flags, used = [None] * len(r["lines"]), set()
        for t, tg in sp:
            hit = next((i for i, l in enumerate(r["lines"]) if i not in used and len(l) == 1 and key(l[0]) == key(t)), None)
            if hit is None:
                rep["spk_not_found"] += 1; notes.append(f"VU speaker not found {r['uid']} {t!r}"); continue
            used.add(hit); flags[hit] = (t, tg)
        lines, spk = [], []
        for i, l in enumerate(r["lines"]):
            if flags[i] is None:
                lines.append(l); continue
            tg = flags[i][1]
            trailing = lines and all(f is not None for f in flags[i:])
            if trailing and (tg == "self" or tg == r["uid"] or tg not in by) and r["uid"] in nxt:
                tg = nxt[r["uid"]]; rep["trailing_to_next"] += 1   # no id, or an id with a typo: the next verse
            if tg == "self" or tg == r["uid"]:
                spk.append({"at": len(lines), "t": l[0]})
            elif tg in by and trailing:   # trailing: belongs to a later verse
                moves.append((tg, l[0], r["uid"]))
            else:
                spk.append({"at": len(lines), "t": l[0]})
                notes.append(f"VU speaker for {tg} kept in {r['uid']} (line {i})"); rep["kept_inline"] += 1
        r["lines"] = lines
        r["_spk"] = spk
    for tg, t, frm in moves:
        by[tg].setdefault("_in", []).append({"at": 0, "t": t, "from": frm})
        rep["moved"] += 1
    for r in recs:
        if "_spk" in r or "_in" in r:
            spk = r.pop("_in", []) + r.pop("_spk", [])
            if spk:
                r["spk"] = spk; rep["spk"] += len(spk)
            r["meter"] = meter_of(r["lines"]) if len(r["lines"]) in (2, 4) else None


def main() -> None:
    a = sys.argv[1:]
    dry = "--dry" in a
    for ed in ("ce", "vu"):
        path = OUT / f"{ed}.jsonl"
        recs = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
        if any("spk" in r or "app" in r for r in recs):
            print(ed, "already split; nothing to do"); continue
        before = sum(1 for r in recs if r.get("meter"))
        rep, notes = collections.Counter(), []
        if ed == "ce":
            split_ce(recs, src_ce(Path(a[a.index("--src-ce") + 1]) if "--src-ce" in a else SRC_CE), rep, notes)
        else:
            split_vu(recs, src_vu(Path(a[a.index("--src-vu") + 1]) if "--src-vu" in a else SRC_VU), rep, notes)
        after = sum(1 for r in recs if r.get("meter"))
        print(ed, dict(rep), f"metre {before} -> {after}")
        for n in notes[:20]:
            print("  ", n)
        if len(notes) > 20:
            print(f"   … {len(notes) - 20} more notes")
        if not dry:
            path.write_text("".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in recs), encoding="utf-8")


if __name__ == "__main__":
    main()
