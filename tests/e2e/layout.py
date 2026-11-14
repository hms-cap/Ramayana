"""Phone layout: no horizontal overflow on the main pages at 360 and 390 px, the B1 verse header (reference pill, no side column),
the two-by-two work chips, and the verse-of-the-day card for the longest Mahābhārata cards.
    python site/build.py && python -m http.server 8765 --directory dist &
    python tests/e2e/layout.py
"""
import json
import sys
import urllib.request
from playwright.sync_api import sync_playwright

B = "http://localhost:8765/"
PAGES = ["", "mbh/", "gita/", "appendix/", "appendix/chandas/", "ce/1/1/", "vu/2/10/", "mbh/vu/2/10/", "mbh/vu/3/159/", "mbh/ce/2/10/", "gita/vu/1/2/", "gita/ce/1/18/"]
SIZES = [(360, 780), (390, 844)]
SCRIPTS = ["knda", "deva", "iast", "all"]


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        check.bad += 1


check.bad = 0


def get(path):
    return json.load(urllib.request.urlopen(B + path))


def widest_cards(n):
    """Indices of the Mahābhārata daily cards with the longest half-lines (they are the ones that can overflow)."""
    ix = get("mbh/data/daily/index.json")
    cards = []
    for c in range((ix["n"] + ix["chunk"] - 1) // ix["chunk"]):
        cards += get(f"mbh/data/daily/c{c}.json")
    worst = sorted(range(len(cards)), key=lambda i: -max(len(l) for l in cards[i]["slp"]))
    return ix["n"], worst[:n]


def overflow(pg):
    return pg.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")


with sync_playwright() as p:
    b = p.chromium.launch()
    for w, h in SIZES:
        ctx = b.new_context(viewport={"width": w, "height": h}, service_workers="block", timezone_id="UTC")
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        for path in PAGES:
            for sc in SCRIPTS if path.count("/") >= 3 or path in ("", "mbh/", "gita/") else ["knda"]:
                pg.goto(B)
                pg.evaluate("p => localStorage.setItem('vr-prefs', JSON.stringify({script: p, offMbh: [], offGita: [], off: []}))", sc)
                pg.goto(B + path)
                pg.wait_for_timeout(500 if "/" in path.rstrip("/") or path == "" else 300)
                sw, cw = overflow(pg)
                check(sw <= cw, f"{w}px /{path} [{sc}] scrollWidth {sw} <= {cw}")

        # work chips: 2 x 2, full names
        pg.goto(B)
        pg.evaluate("localStorage.setItem('vr-prefs', JSON.stringify({script: 'knda'}))")
        for path in ("", "mbh/", "gita/", "appendix/"):
            pg.goto(B + path)
            chips = pg.evaluate("""[...document.querySelectorAll('.wchip')].map(c => { const r = c.getBoundingClientRect(), t = c.querySelector('.wtx b');
                return {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), clipped: t.scrollWidth > t.clientWidth + 1} })""")
            check(len(chips) == 4, f"{w}px /{path}: four chips")
            ys = sorted({c["y"] for c in chips})
            check(len(ys) == 2, f"{w}px /{path}: chips in two rows ({ys})")
            check(not any(c["clipped"] for c in chips), f"{w}px /{path}: no chip name is cut")
        ctx.close()

    # B1 header on a Mahābhārata page (lean.js) and on a Rāmāyaṇa page (build.py)
    ctx = b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
    pg = ctx.new_page()
    for path, ref in (("mbh/vu/2/10/", "2.10."), ("vu/1/1/", "1.1."), ("gita/vu/1/2/", "2.")):
        pg.goto(B)
        pg.evaluate("localStorage.setItem('vr-prefs', JSON.stringify({script: 'knda', offMbh: [], offGita: []}))")
        pg.goto(B + path)
        pg.wait_for_selector(".verses > .verse .vh .vnum")
        n = pg.locator(".verses > .verse").count()
        check(n > 3, f"/{path}: {n} verses")
        check(pg.locator(".verses > .verse .vh .vnum").count() == n, f"/{path}: every verse has the reference pill")
        check(pg.locator(".verses > .verse .vh .wbw-ic").count() == n, f"/{path}: every verse has the word icon in the header")
        check(pg.locator(".side").count() == 0, f"/{path}: no .side column")
        first = pg.locator(".verses > .verse").first
        pill = first.locator(".vnum .n-knda").inner_text()
        check(pill.startswith("೨.") or pill.startswith("೧.") or pill[0] in "೦೧೨೩೪೫೬೭೮೯", f"/{path}: pill shows Kannada digits ({pill})")
        pg.evaluate("document.documentElement.dataset.script = 'iast'")
        check(first.locator(".vnum").inner_text().startswith(ref), f"/{path}: IAST pill {first.locator('.vnum').inner_text()}")
        pg.evaluate("document.documentElement.dataset.script = 'deva'")
        check(first.locator(".vnum").inner_text()[0] in "०१२३४५६७८९", f"/{path}: Devanāgarī pill {first.locator('.vnum').inner_text()}")
        pg.evaluate("document.documentElement.dataset.script = 'knda'")
        ends = pg.evaluate("""[...document.querySelectorAll('.verses > .verse .t-knda p:first-child, .verses > .verse .t-iast p:first-child')].map(p => { const l = p.querySelectorAll('.ln'); return l[l.length-1].textContent.replace(/\\u00a0/g, ' ').trim() })""")
        check(all(e.endswith("॥") or e.endswith("||") for e in ends) and not any(any(c.isdigit() or c in "೦೧೨೩೪೫೬೭೮೯" for c in e[-8:]) for e in ends), f"/{path}: verses end with a plain danda, no number")
        # the pill opens the details; keyboard works
        pill_btn = first.locator(".vnum")
        pill_btn.focus()
        pg.keyboard.press("Enter")
        check(pill_btn.get_attribute("aria-expanded") == "true" and first.locator(".details").is_visible(), f"/{path}: pill (Enter) opens the details")
        check(pill_btn.get_attribute("aria-controls") == first.locator(".details").get_attribute("id"), f"/{path}: aria-controls matches")
        ln = first.locator(".t-knda .ln").evaluate_all("l => l.map(x => getComputedStyle(x).paddingLeft)")
        check(ln[0] == "0px" and ln[1] != "0px", f"/{path}: second line indented, first not ({ln})")
    ctx.close()

    # verse-of-the-day card on the Mahābhārata home: the widest cards, in every script, at both widths
    total, worst = widest_cards(10)
    n_days = 6
    days = list(worst) + list(range(n_days))
    for w, h in SIZES:
        for sc in ("knda", "deva", "iast"):
            ctx = b.new_context(viewport={"width": w, "height": h}, service_workers="block", timezone_id="UTC")
            pg = ctx.new_page()
            bad = 0
            for idx in days:
                day = next(d for d in range(total * 2) if (d * 7919) % total == idx)
                pg.add_init_script(f"Date.now = () => {day * 86400000 + 3600000};")
                pg.goto(B)
                pg.evaluate("p => localStorage.setItem('vr-prefs', JSON.stringify({script: p}))", sc)
                pg.goto(B + "mbh/")
                pg.wait_for_selector(".votd .vc-verse")
                pg.wait_for_timeout(150)
                sw, cw = overflow(pg)
                lines = pg.locator(".votd .vc-verse .ln").count()
                if sw > cw or lines < 2:
                    bad += 1
                    print(f"     card {idx} [{sc}] {w}px: scrollWidth {sw} > {cw}, {lines} lines")
            check(bad == 0, f"{w}px MBH home [{sc}]: {len(days)} daily cards fit")
            ctx.close()
    # the card itself: left aligned, one rule above and below, no per-line rules
    ctx = b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
    pg = ctx.new_page()
    pg.goto(B + "mbh/")
    pg.wait_for_selector(".votd .vc-verse")
    st = pg.evaluate("""(() => { const v = document.querySelector('.votd .vc-verse'), c = getComputedStyle(v), l = v.querySelectorAll('.ln');
        return {align: c.textAlign, top: c.borderTopWidth, bottom: c.borderBottomWidth, img: c.backgroundImage, pad2: l.length > 1 ? getComputedStyle(l[1]).paddingLeft : null, wrap: getComputedStyle(l[0]).overflowWrap} })()""")
    check(st["align"] in ("left", "start") and st["top"] == "1px" and st["bottom"] == "1px" and st["img"] == "none" and st["wrap"] == "anywhere" and st["pad2"] not in (None, "0px"), f"verse card: {st}")
    ctx.close()
    b.close()

sys.exit(1 if check.bad else 0)
