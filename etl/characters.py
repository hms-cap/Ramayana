"""Characters (Pariśiṣṭa): load the data, derive relations, find lemmas, lay out circles and family trees.

Everything here is plain Python (no templates) so that site/build.py and the tests can share it.
Data: data/characters/seed_<work>.json (the list) and every data/characters/<work>*.json other than the seed
(characters with their relations and moments). Characters without an entry yet are kept, with their name only.
Set the environment variable CHARACTERS_DIR to read another folder (tests, previews).
"""
from __future__ import annotations

import json
import math
import os
import re
from collections import OrderedDict
from html import escape
from pathlib import Path

from translit import iast_to_slp1, render, slp1_to_brahmic

ROOT = Path(__file__).resolve().parent.parent
WORKS = ("ram", "mbh")


def data_dir() -> Path:
    return Path(os.environ.get("CHARACTERS_DIR") or ROOT / "data" / "characters")


# ---------------------------------------------------------------- loading

def load(work: str) -> dict:
    """{'work', 'groups': [...], 'chars': OrderedDict id -> char} in seed order. A char is the seed entry
    merged with its data entry; char['has'] says whether the data entry exists."""
    d = data_dir()
    seed = json.loads((d / f"seed_{work}.json").read_text(encoding="utf-8"))
    data = {}
    for p in sorted(d.glob(f"{work}*.json")):
        if p.name.startswith("seed_"):
            continue
        for c in json.loads(p.read_text(encoding="utf-8")).get("characters", []):
            data.setdefault(c["id"], c)
    chars = OrderedDict()
    for i, s in enumerate(seed["characters"]):
        c = {"epithets": [], "relations": [], "moments": [], "match": [], **s, "idx": i}
        if s["id"] in data:
            c.update({k: v for k, v in data[s["id"]].items() if v is not None})
            c["has"] = True
        else:
            c["has"] = False
        c.setdefault("gender", guess_gender(c["name"]))
        c.setdefault("rank", 3)
        chars[s["id"]] = c
    return {"work": work, "groups": seed["groups"], "chars": chars}


def guess_gender(name: str) -> str:
    return "f" if re.search(r"[āī]$", name.strip()) else "m"


# ---------------------------------------------------------------- names in the three scripts

def kn_name(name: str, gender: str | None = None) -> str:
    """A name in Kannada script the way it is usually written: Sītā -> ಸೀತೆ, Draupadī -> ದ್ರೌಪದಿ, Hanumat -> ಹನುಮಂತ,
    Śikhaṇḍin -> ಶಿಖಂಡಿ. Only the final syllable is adjusted; everything else is the plain transliteration."""
    s = iast_to_slp1(name.strip())
    g = gender or guess_gender(name)
    if s.endswith("H"):
        s = s[:-1]
    if re.search(r"[mv]at$", s):
        s = s[:-3] + s[-3] + "aMta"
    elif s.endswith("in"):
        s = s[:-2] + "i"
    elif s.endswith("as") and len(s) > 4:
        s = s[:-1]
    elif s.endswith("I"):
        s = s[:-1] + "i"
    out = render(s, "knda")
    if s.endswith("A") and g == "f":
        out = out[:-1] + "\u0cc6"            # ಾ -> ೆ  (Sītā -> ಸೀತೆ)
    return out


def names3(name: str, gender: str | None = None) -> tuple[str, str, str]:
    """(kannada, devanagari, iast) of a name."""
    return kn_name(name, gender), render(iast_to_slp1(name.strip()), "deva"), name.strip()


# ---------------------------------------------------------------- relations

# key -> (English, Kannada) label for the circle; {m,f} variants are picked by the other person's gender
LAB = {
    "parent": {"m": ("father", "ತಂದೆ"), "f": ("mother", "ತಾಯಿ"), "n": ("parent", "ಪೋಷಕ")},
    "child": {"m": ("son", "ಮಗ"), "f": ("daughter", "ಮಗಳು"), "n": ("child", "ಮಗು")},
    "spouse": {"m": ("husband", "ಗಂಡ"), "f": ("wife", "ಹೆಂಡತಿ"), "n": ("spouse", "ಸಂಗಾತಿ")},
    "sibling": {"m": ("brother", "ಸಹೋದರ"), "f": ("sister", "ಸಹೋದರಿ"), "n": ("sibling", "ಸಹೋದರ")},
    "teacher": {"*": ("teacher", "ಗುರು")},
    "student": {"*": ("student", "ಶಿಷ್ಯ")},
    "master": {"*": ("master", "ಒಡೆಯ")},
    "servant": {"*": ("serves him", "ಸೇವಕ")},
    "ally": {"*": ("ally", "ಮಿತ್ರ")},
    "friend": {"*": ("friend", "ಸ್ನೇಹಿತ")},
    "enemy": {"*": ("opposed", "ವಿರೋಧಿ")},
    "killed_by": {"*": ("killed by", "ಕೊಂದವನು")},
    "killed": {"*": ("killed", "ಇವನಿಂದ ಹತ")},
    "other": {"*": ("related", "ಸಂಬಂಧ")},
}
KIND_OF = {"parent": "fam", "child": "fam", "spouse": "fam", "sibling": "fam", "teacher": "tea", "student": "tea",
           "master": "ally", "servant": "ally", "ally": "ally", "friend": "ally", "enemy": "foe",
           "killed_by": "kill", "killed": "kill", "other": "oth"}
KIND_PRIO = ["kill", "fam", "tea", "ally", "foe", "oth"]            # colour of an edge that has several kinds
KEY_ORDER = ["parent", "spouse", "sibling", "child", "teacher", "student", "master", "servant", "ally", "friend",
             "killed_by", "killed", "enemy", "other"]               # order around the circle
INVERSE = {"parent": "child", "teacher": "student", "serves": "servant", "killed_by": "killed"}
SYMMETRIC = {"spouse": "spouse", "sibling": "sibling", "ally": "ally", "friend": "friend", "enemy": "enemy", "other": "other"}


def facts(W: dict) -> dict:
    """{id: {other_id: {'keys': [...], 'refs': {key: (ref, ed)}, 'note': (en, kn)}}}: what each person's page shows
    about each other person, with inverses derived (parent -> child, teacher -> student, shared parent -> siblings)."""
    ch = W["chars"]
    out: dict = {i: {} for i in ch}

    def add(a, b, key, r=None):
        if a == b or a not in ch or b not in ch:
            return
        e = out[a].setdefault(b, {"keys": [], "refs": {}, "note": None})
        if key not in e["keys"]:
            e["keys"].append(key)
        if r and r.get("ref"):
            e["refs"].setdefault(key, (r["ref"], r.get("ed", "vu")))
        if r and key == "other" and r.get("note_en"):
            e["note"] = (r["note_en"], r.get("note_kn") or r["note_en"])

    parents: dict = {i: [] for i in ch}
    for i, c in ch.items():
        for r in c["relations"]:
            t, to = r.get("type"), r.get("to")
            if to not in ch:
                continue
            if t == "parent":
                add(i, to, "parent", r)
                add(to, i, "child", r)
                parents[i].append(to)
            elif t == "serves":
                add(i, to, "master", r)
                add(to, i, "servant", r)
            elif t == "teacher":
                add(i, to, "teacher", r)
                add(to, i, "student", r)
            elif t == "killed_by":
                add(i, to, "killed_by", r)
                add(to, i, "killed", r)
            elif t in SYMMETRIC:
                add(i, to, t, r)
                add(to, i, t, r)
    kids: dict = {}
    for c, ps in parents.items():
        for p in ps:
            kids.setdefault(p, []).append(c)
    for p, cs in kids.items():
        for a in cs:
            for b in cs:
                if a != b:
                    add(a, b, "sibling")
    return out


def label(key: str, other_gender: str) -> tuple[str, str]:
    d = LAB[key]
    return d.get(other_gender) or d.get("*") or d["n"]


def edges_for(W: dict, F: dict, cid: str) -> list[dict]:
    """The people directly related to cid, as dicts: id, kind, keys, label (en, kn), ref."""
    ch = W["chars"]
    rows = []
    for o, e in F[cid].items():
        keys = sorted(e["keys"], key=KEY_ORDER.index)
        kind = min((KIND_OF[k] for k in keys), key=KIND_PRIO.index)
        labs = []
        for k in keys:
            en, kn = (e["note"] if k == "other" and e["note"] else label(k, ch[o]["gender"]))
            if (en, kn) not in labs:
                labs.append((en, kn))
        labs = labs[:2]
        ref = next(iter(e["refs"].values()), None)
        rows.append({"id": o, "kind": kind, "keys": keys, "en": " · ".join(x[0] for x in labs),
                     "kn": " · ".join(x[1] for x in labs), "ref": ref, "rank": ch[o]["rank"], "idx": ch[o]["idx"],
                     "order": KEY_ORDER.index(keys[0])})
    return rows


def pick_circle(rows: list[dict], limit: int = 14) -> tuple[list[dict], list[dict]]:
    """At most `limit` people for the circle (family and rank-1 first); the rest are listed as text."""
    pri = sorted(rows, key=lambda r: (0 if (r["kind"] == "fam" or r["rank"] == 1) else 1, 0 if r["kind"] == "fam" else 1, r["rank"], r["idx"]))
    top, rest = pri[:limit], pri[limit:]
    top.sort(key=lambda r: (r["order"], r["idx"]))
    rest.sort(key=lambda r: (r["order"], r["idx"]))
    return top, rest


# ---------------------------------------------------------------- lemmas and mention counts

def lemma_forms(text: str) -> set[str]:
    """Lemma spellings (SLP1) a name may have in the word analysis: Hanumat -> hanumat, Karṇa -> karRa, Aśvins -> aSvin.
    A name of several words or a hyphenated one is the lemmas written together."""
    s = iast_to_slp1(text.strip())
    s = re.sub(r"[\s\-]+", "", s)
    if s.endswith("H"):
        s = s[:-1]
    if len(s) < 3:
        return set()
    out = {s}
    if re.search(r"[mv]An$", s):
        out.add(s[:-2] + "t")
    if s.endswith("ins"):
        out.add(s[:-1])
    return out


def lemma_owners(W: dict) -> dict[str, set[str]]:
    """lemma -> ids of the characters that carry it as a name or epithet (the optional 'match' stems are not used)."""
    own: dict = {}
    for i, c in W["chars"].items():
        for t in [c["name"]] + list(c.get("epithets", [])):
            for f in lemma_forms(t):
                own.setdefault(f, set()).add(i)
    return own


def unique_lemmas(W: dict) -> dict[str, str]:
    """lemma -> character id, for lemmas that belong to exactly one character of the work."""
    return {l: next(iter(s)) for l, s in lemma_owners(W).items() if len(s) == 1}


def count_mentions(W: dict, lemma_count: dict, n_units: int) -> dict[str, list[int]]:
    """id -> mentions per kāṇḍa/parva, from lemma_count {lemma: [n per unit]} (see build.py: load_words)."""
    out = {i: [0] * n_units for i in W["chars"]}
    for l, cid in unique_lemmas(W).items():
        row = lemma_count.get(l)
        if row:
            for k, n in enumerate(row[:n_units]):
                out[cid][k] += n
    return out


# ---------------------------------------------------------------- SVG helpers

def _fit(text: str, avail: float, size: float, floor: float = 8.0) -> float:
    return max(floor, min(size, avail / (0.56 * max(1, len(text)))))


def _sx_text(x: float, y: float, names: tuple[str, str, str], avail: float, size: float, cls: str = "", weight: int = 600,
             anchor: str = "middle") -> str:
    """The same label three times (Kannada, Devanāgarī, IAST); style.css shows the one that matches the script setting."""
    out = []
    for sc, txt, lang in zip(("kn", "deva", "iast"), names, ("kn", "sa", "sa-Latn")):
        fs = _fit(txt, avail, size)
        out.append(f'<text class="sx sx-{sc} {cls}" lang="{lang}" x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" font-size="{fs:.1f}" '
                   f'font-weight="{weight}">{escape(txt)}</text>')
    return "".join(out)


def _lab_text(x: float, y: float, en: str, kn: str, avail: float) -> str:
    out = [f'<text class="sx sx-kn lab" lang="kn" x="{x:.1f}" y="{y:.1f}" text-anchor="middle" font-size="{_fit(kn, avail, 9.5, 7):.1f}">{escape(kn)}</text>']
    for sc in ("deva", "iast"):
        out.append(f'<text class="sx sx-{sc} lab" lang="en" x="{x:.1f}" y="{y:.1f}" text-anchor="middle" font-size="{_fit(en, avail, 9.5, 7):.1f}">{escape(en)}</text>')
    return "".join(out)


def _name3(c: dict) -> tuple[str, str, str]:
    return names3(c["name"], c.get("gender"))


# ---------------------------------------------------------------- relationship circle

def circle_svg(W: dict, cid: str, rows: list[dict], hrefs: dict[str, str]) -> str:
    """The person in the middle, the given related people around (an ellipse, staggered when there are many), each a link
    to that person's page when hrefs has it. Edges are coloured by kind (CSS classes e-fam, e-tea, e-ally, e-foe, e-kill, e-oth)."""
    ch = W["chars"]
    Wd, H = 360, 340
    cx, cy = Wd / 2, H / 2
    n = len(rows)
    rx, ry = 134, 124
    pos = []
    for i, r in enumerate(rows):
        a = -math.pi / 2 + i * 2 * math.pi / max(n, 1)
        k = 0.74 if (n > 9 and i % 2) else 1.0
        pos.append((cx + rx * k * math.cos(a), cy + ry * k * math.sin(a)))
    s = [f'<svg viewBox="0 0 {Wd} {H}" class="circ" role="img" aria-label="Relations of {escape(ch[cid]["name"])}" xmlns="http://www.w3.org/2000/svg">']
    for r, (x, y) in zip(rows, pos):
        s.append(f'<line class="e e-{r["kind"]}" x1="{cx:.1f}" y1="{cy:.1f}" x2="{x:.1f}" y2="{y:.1f}"/>')
    for r, (x, y) in zip(rows, pos):
        o = ch[r["id"]]
        pw, ph = 82, 24
        body = (f'<rect class="pill p-{r["kind"]}" x="{x - pw / 2:.1f}" y="{y - ph / 2:.1f}" width="{pw}" height="{ph}" rx="12"/>'
                + _sx_text(x, y + 4.5, _name3(o), pw - 10, 12.5, "nm") + _lab_text(x, y + ph / 2 + 10, r["en"], r["kn"], 90))
        if r["id"] in hrefs:
            s.append(f'<a class="node" href="{escape(hrefs[r["id"]])}" data-id="{r["id"]}">{body}</a>')
        else:
            s.append(f'<g class="node dim" data-id="{r["id"]}">{body}</g>')
    me = ch[cid]
    s.append(f'<ellipse class="me" cx="{cx}" cy="{cy}" rx="50" ry="27"/>' + _sx_text(cx, cy + 5, _name3(me), 86, 15, "me-t", 700) + "</svg>")
    return "".join(s)


# ---------------------------------------------------------------- family trees

LINES = {
    "ram": [
        dict(id="ikshvaku", kn="ಇಕ್ಷ್ವಾಕು ವಂಶ", en="Ikṣvāku", full="The Ikṣvāku line", roots=["dasharatha"], side=[],
             note="Daśaratha's family down to Lava and Kuśa."),
        dict(id="mithila", kn="ಮಿಥಿಲೆ", en="Mithilā", full="The family of Mithilā", roots=["janaka"], side=[],
             note="Janaka, his daughters Sītā and Ūrmilā, and their husbands."),
        dict(id="vanara", kn="ವಾನರರು", en="Vānaras", full="The vānara kings of Kiṣkindhā", roots=["valin"], side=["sugriva"],
             note="Vālin and Sugrīva, Tārā and Aṅgada."),
        dict(id="rakshasa", kn="ರಾಕ್ಷಸರು", en="Rākṣasas", full="Rāvaṇa's family", roots=["ravana"],
             side=["shurpanakha", "vibhishana", "kumbhakarna"], note="Rāvaṇa and his brothers and sister, Mandodarī and Indrajit."),
    ],
    "mbh": [
        dict(id="kuru", kn="ಕುರು", en="Kuru", full="The Kuru line", roots=["shantanu"], side=[],
             note="From Śantanu to Parikṣit."),
        dict(id="panchala", kn="ಪಾಂಚಾಲ", en="Pāñcāla", full="The Pāñcāla line", roots=["drupada"], side=[],
             note="Drupada and his children."),
        dict(id="yadava", kn="ಯಾದವ", en="Yādava", full="The Yādava line", roots=["vasudeva"], side=["kunti"],
             note="Vasudeva, Kṛṣṇa, Balarāma and Subhadrā."),
    ],
}
# parent -> child links drawn dashed besides those whose parent is a god (group "gods"): birth by niyoga or from a god
DASHED = {("vyasa", "dhritarashtra"), ("vyasa", "pandu"), ("vyasa", "vidura"), ("satyavati", "vyasa"), ("kunti", "karna")}

NW, NH, SPOUSE_GAP, SIB_GAP, KID_GAP, SX_, SY_, PAD = 90, 30, 22, 22, 14, 0, 82, 16


def _dashed(W: dict, p: str, c: str, par_rel: dict) -> bool:
    if (p, c) in DASHED:
        return True
    r = par_rel.get((c, p), {})
    if r.get("niyoga") or r.get("dashed") or r.get("birth") in ("niyoga", "divine"):
        return True
    return W["chars"][p].get("group") == "gods"


def tree_layout(W: dict, F: dict, line: dict) -> dict:
    """Place the people of one line. Returns {'members', 'rows', 'units', 'pos': {id: (x, y)}, 'links', 'kids', 'w', 'h', 'missing'}.

    Members: the roots, everyone below them by parent links (children of in-law spouses too), and the spouses of the roots
    and of everyone below them. A woman takes at most her first husband; a man all his wives (up to four), the first wife
    next to him, the others alternating to the left and right. Each person is drawn once. A person's row is one below the
    lowest of his parents shown. Children sit under their parents, in the order of their parent's position and then seed
    order; a couple's children hang from the middle of the marriage."""
    ch = W["chars"]
    idx = {i: c["idx"] for i, c in ch.items()}
    parents = {i: [o for o, e in F[i].items() if "parent" in e["keys"]] for i in ch}
    children = {i: sorted((o for o, e in F[i].items() if "child" in e["keys"]), key=idx.get) for i in ch}
    spouses = {i: sorted((o for o, e in F[i].items() if "spouse" in e["keys"]), key=idx.get) for i in ch}
    sibs = {i: {o for o, e in F[i].items() if "sibling" in e["keys"]} for i in ch}
    roots = [r for r in line["roots"] if r in ch]
    missing = []
    side = []
    for sid in line.get("side", []):
        if sid in ch and any(sid in sibs[r] for r in roots):
            side.append(sid)
        else:
            missing.append(f'{sid} is not linked as a sibling of {line["roots"][0]}')
    # who is below: roots, side siblings, and children of anyone in the set; spouses of non-married-in people
    member, core, order = set(roots) | set(side), set(roots) | set(side), list(roots) + list(side)
    claim: dict = {}                                    # married-in person -> the person they are placed beside
    changed = True
    done_sp: set = set()
    while changed:
        changed = False
        for p in sorted(list(member), key=idx.get):
            if p in side:                               # a sibling is shown beside the root and brings nothing else
                continue
            if p not in claim and p not in done_sp:     # married-in people do not bring their other spouses
                done_sp.add(p)
                sp = [s for s in spouses[p] if s not in core]
                if ch[p]["gender"] == "f":
                    sp = sp[:1]
                for s in sp[:4]:
                    if s not in claim:
                        claim[s] = p
                        member.add(s)
                        changed = True
            for c in children[p]:
                if c not in member:
                    member.add(c)
                    core.add(c)
                    changed = True
    # a claimed person may also be a descendant (cousin marriage): descendants stay where their parents put them
    for s in list(claim):
        if s in core:
            del claim[s]
    # a person claimed twice by different people keeps the first (lowest seed index) claimant only
    rows: dict = {}

    def row(p, depth=0):
        if p in rows:
            return rows[p]
        if depth > 40:
            return 0
        if p in claim:
            rows[p] = row(claim[p], depth + 1)
        else:
            ps = [x for x in parents[p] if x in member and x != p]
            rows[p] = 0 if (p in roots or p in side or not ps) else 1 + max(row(x, depth + 1) for x in ps)
        return rows[p]

    for p in sorted(member, key=idx.get):
        row(p)
    # units: a core person with his claimed spouses (and side siblings for the root)
    units: dict = {}
    unit_of: dict = {}
    for p in sorted(core - set(side), key=lambda x: (rows[x], idx[x])):
        mine = [s for s in sorted(claim, key=idx.get) if claim[s] == p]
        arr = mine[1::2][::-1] + [p] + mine[0::2] if len(mine) > 1 else [p] + mine
        units[p] = {"head": p, "members": arr, "links": [("mar", p, s) for s in mine], "kids": []}
        for m in arr:
            unit_of[m] = p
    if side and roots:
        u = units[roots[0]]
        chain = side + [roots[0]]
        u["members"] = side + u["members"]
        u["links"] += [("sib", chain[i], chain[i + 1]) for i in range(len(chain) - 1)]
        for m in side:
            unit_of[m] = roots[0]
    # attach each core person (not a root) to the unit of his lowest parent shown
    top = []
    for p in sorted(core - set(side), key=lambda x: (rows[x], idx[x])):
        ps = [x for x in parents[p] if x in member and x in unit_of and unit_of[x] != p]
        if p in roots or not ps:
            top.append(p)
            continue
        best = max(ps, key=lambda x: (rows[x], -idx[x]))
        units[unit_of[best]]["kids"].append(p)
    # horizontal layout
    def uw(u):
        return len(u["members"]) * NW + (len(u["members"]) - 1) * SPOUSE_GAP

    def anchor_local(u, c):
        xs = [u["members"].index(x) * (NW + SPOUSE_GAP) + NW / 2 for x in parents[c] if x in u["members"]]
        return sum(xs) / len(xs) if xs else 0

    for u in units.values():
        u["kids"].sort(key=lambda c: (anchor_local(u, c), idx[c]))
    sub: dict = {}

    def width(p):
        u = units[p]
        kw = sum(width(c) for c in u["kids"]) + KID_GAP * max(0, len(u["kids"]) - 1)
        sub[p] = max(uw(u), kw)
        return sub[p]

    pos: dict = {}

    def place(p, x0):
        u = units[p]
        kw = sum(sub[c] for c in u["kids"]) + KID_GAP * max(0, len(u["kids"]) - 1)
        kx = x0 + (sub[p] - kw) / 2
        centres = []
        for c in u["kids"]:
            place(c, kx)
            centres.append(pos[c][0])
            kx += sub[c] + KID_GAP
        centre = (centres[0] + centres[-1]) / 2 if centres else x0 + sub[p] / 2
        left = min(max(centre - uw(u) / 2, x0), x0 + sub[p] - uw(u))
        y = PAD + rows[p] * SY_
        for i, m in enumerate(u["members"]):
            pos[m] = (PAD + left + i * (NW + SPOUSE_GAP) + NW / 2, y + NH / 2)
        u["left"] = left

    x = 0.0
    for p in top:
        width(p)
    for p in top:
        place(p, x)
        x += sub[p] + 2 * KID_GAP
    if not pos:
        return {"members": [], "pos": {}, "w": 0, "h": 0, "units": units, "missing": missing, "rows": rows, "line": line}
    maxrow = max(rows[m] for m in pos)
    return {"members": list(pos), "pos": pos, "rows": rows, "units": units, "missing": missing, "line": line,
            "parents": parents, "w": PAD * 2 + x, "h": PAD * 2 + maxrow * SY_ + NH + 14}


def tree_svg(W: dict, F: dict, lay: dict, hrefs: dict[str, str], par_rel: dict) -> str:
    ch = W["chars"]
    pos = lay["pos"]
    if not pos:
        return ""
    w = max(lay["w"], max(x for x, _ in pos.values()) + NW / 2 + PAD)
    h = lay["h"]
    out = [f'<svg class="tree-svg" width="{w:.0f}" height="{h:.0f}" viewBox="0 0 {w:.0f} {h:.0f}" role="img" aria-label="{escape(lay["line"]["full"])}" xmlns="http://www.w3.org/2000/svg">']
    members = set(pos)
    bracket: dict = {}
    anchors: dict = {}                       # (parent pair) -> (x, y) where children hang
    for u in lay["units"].values():
        mem = u["members"]
        if not mem or mem[0] not in pos:
            continue
        for kind, a, b in u["links"]:
            if a not in pos or b not in pos:
                continue
            (xa, ya), (xb, yb) = pos[a], pos[b]
            lo, hi = sorted((xa, xb))
            between = [m for m in mem if lo < pos[m][0] < hi]
            if kind == "sib":
                if not between:
                    out.append(f'<line class="t-sib" x1="{lo + NW / 2:.1f}" y1="{ya:.1f}" x2="{hi - NW / 2:.1f}" y2="{ya:.1f}"/>')
                continue
            if not between:
                for dy in (-3, 3):
                    out.append(f'<line class="t-mar" x1="{lo + NW / 2:.1f}" y1="{ya + dy:.1f}" x2="{hi - NW / 2:.1f}" y2="{ya + dy:.1f}"/>')
                anchors[frozenset((a, b))] = ((xa + xb) / 2, ya)
            else:
                lvl = 1 + len(bracket.setdefault(u["head"], []))
                bracket[u["head"]].append(1)
                yb2 = ya + NH / 2 + 5 * lvl
                out.append(f'<path class="t-mar" d="M{xa:.1f} {ya + NH / 2:.1f} V{yb2:.1f} H{xb:.1f} V{yb + NH / 2:.1f}"/>')
                anchors[frozenset((a, b))] = ((xa + xb) / 2, yb2)
    # child connectors
    for c in members:
        ps = [p for p in lay["parents"][c] if p in members and p != c]
        if not ps:
            continue
        cx, cy = pos[c]
        top_y = cy - NH / 2
        done = set()
        groups = []
        for p in ps:
            if p in done:
                continue
            pair = next((q for q in ps if q != p and q not in done and frozenset((p, q)) in anchors), None)
            if pair:
                done |= {p, pair}
                groups.append(([p, pair], anchors[frozenset((p, pair))]))
            else:
                done.add(p)
                groups.append(([p], (pos[p][0], pos[p][1] + NH / 2)))
        for gp, (ax, ay) in groups:
            if ay >= top_y - 4:
                continue
            my = top_y - 14
            dash = all(_dashed(W, p, c, par_rel) for p in gp)
            out.append(f'<path class="t-kid{" t-dash" if dash else ""}" d="M{ax:.1f} {ay:.1f} V{my:.1f} H{cx:.1f} V{top_y:.1f}"/>')
    for m, (x, y) in pos.items():
        c = ch[m]
        body = (f'<rect class="t-node" x="{x - NW / 2:.1f}" y="{y - NH / 2:.1f}" width="{NW}" height="{NH}" rx="8"/>'
                + _sx_text(x, y + 4.5, _name3(c), NW - 10, 12.5, "nm"))
        if m in hrefs:
            out.append(f'<a class="node" href="{escape(hrefs[m])}" data-id="{m}">{body}</a>')
        else:
            out.append(f'<g class="node dim" data-id="{m}">{body}</g>')
    out.append("</svg>")
    return "".join(out)


def parent_rels(W: dict) -> dict:
    return {(i, r["to"]): r for i, c in W["chars"].items() for r in c["relations"] if r.get("type") == "parent"}


def line_members(W: dict, F: dict) -> dict[str, list[str]]:
    """character id -> ids of the family lines it appears in (needs the layout, so it is built on demand)."""
    out: dict = {}
    for line in LINES[W["work"]]:
        for m in tree_layout(W, F, line)["members"]:
            out.setdefault(m, []).append(line["id"])
    return out


# ---------------------------------------------------------------- the name files used by the word panel and search

def names_json(W: dict) -> dict:
    """{'c': {id: [iast, kannada, devanagari]}, 'l': {lemma: id}, 's': [[id, 'slp1 slp1 ...']]} for the characters that
    have a page: the word panel links a lemma to its character, and search finds a character by any of its names."""
    ch = W["chars"]
    uniq = unique_lemmas(W)
    c = {i: [x["name"], _name3(x)[0], _name3(x)[1]] for i, x in ch.items() if x["has"]}
    lem = {l: i for l, i in uniq.items() if i in c}
    s = []
    for i, x in ch.items():
        if not x["has"]:
            continue
        names = [x["name"]] + list(x.get("epithets", []))
        s.append([i, " ".join(iast_to_slp1(n) for n in names)])
    return {"c": c, "l": lem, "s": s}
