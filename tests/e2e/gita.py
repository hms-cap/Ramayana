"""Bhagavadgītā as the third work: chips, home, Dhyāna, reader, links to the Mahābhārata, Pune edition, search, verse of the day.
    python site/build.py && python -m http.server 8765 --directory dist &
    python tests/e2e/gita.py
"""
import json
import sys
from playwright.sync_api import sync_playwright

B = "http://localhost:8765/"


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        check.bad += 1


check.bad = 0

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: m.type == "error" and errs.append(m.text))

    # work chips: three works, the Gītā chip goes to gita/
    pg.goto(B)
    picks = pg.eval_on_selector_all(".workchips .wchip", "els => els.map(e => [e.dataset.workPick, e.getAttribute('href')])")
    works = [x for x in picks if x[0] != "app"]
    check(len(works) == 3 and [w[0] for w in works] == ["ram", "mbh", "gita"], f"home chip row has three works {picks}")
    pg.click('.wchip[data-work-pick="gita"]')
    pg.wait_for_url("**/gita/")
    check(pg.url == B + "gita/", f"Gītā chip goes to gita/ ({pg.url})")

    # Gītā home: 18 cards, adhyāya 2 -> vu/1/2/, verse of the day
    pg.wait_for_selector(".votd-slide .vc-verse")
    check(pg.locator(".kcard").count() == 18, "gita/ shows 18 adhyāya cards")
    check(pg.get_attribute('.kcard[data-k="2"]', "href") == "vu/1/2/", "card for adhyāya 2 links to vu/1/2/")
    vt = pg.inner_text(".votd-slide .vc-verse").strip()
    check(len(vt) > 10, f"verse of the day renders: {vt[:40]!r}")
    check(not pg.evaluate("document.documentElement.scrollWidth > innerWidth"), "gita/ has no horizontal scroll at 390px")

    # script: IAST via prefs
    pg.evaluate("localStorage.setItem('vr-prefs', JSON.stringify({script: 'iast'}))")

    # Dhyāna
    pg.goto(B + "gita/vu/1/0/")
    check(pg.locator(".verses > .verse").count() == 9, "Dhyāna page shows 9 verses")
    h1 = pg.inner_text("h1")
    check("gītādhyānam" in h1, f"Dhyāna heading: {h1!r}")

    # adhyāya 2
    pg.goto(B + "gita/vu/1/2/")
    check(pg.locator(".verses > .verse").count() == 72, "gita/vu/1/2/ shows 72 verses")
    t47 = pg.inner_text("#v47 .t-iast")
    check("karmaṇy" in t47, f"2.47 in IAST: {t47[:30]!r}")
    sp = pg.eval_on_selector_all(".speaker", "els => els.map(e => e.textContent)")
    check(any("śrībhagavān" in s for s in sp), f"speaker line śrībhagavān present ({len(sp)} speaker lines)")
    pg.click("#v47 .vnum")
    link = pg.locator("#d47 a", has_text="Bhīṣma")
    check(link.count() == 1 and link.get_attribute("href").endswith("mbh/vu/6/26/#v47"), "2.47 details link to the Mahābhārata adhyāya")
    link.click()
    pg.wait_for_url("**/mbh/vu/6/26/**")
    check("/mbh/vu/6/26/" in pg.url, f"link works ({pg.url})")
    gl = pg.locator("a[href*='gita/vu/1/2/']")
    check(gl.count() >= 1, "mbh/vu/6/26/ has a Gītā link to gita/vu/1/2/")
    check("Gītā" in pg.inner_text("main"), "Mahābhārata page names the Gītā")

    # Pune
    pg.goto(B + "gita/ce/1/18/")
    check(pg.locator(".verses > .verse").count() == 78, "gita/ce/1/18/ has 78 verses")

    # adhyāya list
    pg.goto(B + "gita/vu/1/")
    check(pg.locator("a[href^='0/'], a[href='0/']").count() >= 1, "adhyāya list links to the Dhyāna")

    # search
    pg.goto(B + "gita/search/?q=karmanyevadhikaraste")
    pg.wait_for_selector("#results li", timeout=20000)
    res = pg.inner_text("#results")
    check("2.47" in res, f"search finds 2.47: {res[:60]!r}".replace("\n", " "))

    check(not errs, f"no console errors {errs}")
    b.close()
print("FAILED" if check.bad else "all passed")
sys.exit(1 if check.bad else 0)
