"""Read page unit cells (Rāmāyaṇa, Mahābhārata, Gītā), kāṇḍa page cards and pinned Continue card, no overflow at 390px (light, dark).
    BASE=http://localhost:8765 python tests/e2e/pages2.py       screenshots go to $SHOTS or /tmp."""
import json
import os
from playwright.sync_api import sync_playwright

B = os.environ.get("BASE", "http://localhost:8765").rstrip("/")
SP = os.environ.get("SHOTS", "/tmp")


def noscroll(pg, what):
    d = pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
    assert d <= 0, f"{what}: horizontal scroll {d}px"


with sync_playwright() as p:
    b = p.chromium.launch()
    for theme in ("light", "dark"):
        ctx = b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        ctx.add_init_script("try{ if(!localStorage.getItem('vr-prefs')) localStorage.setItem('vr-prefs', JSON.stringify({theme:'%s'})) }catch(e){}" % theme)
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))

        # ---- Read pages: cells, counts, sheet ----
        for path, n_min, n_max, sheet in (("/read/", 6, 7, True), ("/mbh/read/", 18, 18, True), ("/gita/read/", 18, 19, False)):
            pg.goto(B + path); pg.wait_for_selector(".kcell")
            n = pg.locator(".kcell").count()
            assert n_min <= n <= n_max, (path, n)
            assert pg.locator(".kgrid, .kcard svg:visible").count() == 0
            assert pg.locator(".kcell .kl-c").first.inner_text().strip(), path
            noscroll(pg, path + " " + theme)
            if sheet:
                pg.locator("button.kcell.kcard").first.click()
                pg.wait_for_selector("#ksheet.open, #ksheet[aria-hidden=false], #ks-chips a", state="visible")
                assert pg.locator("#ks-chips a").count() > 10, path
                pg.keyboard.press("Escape"); pg.wait_for_timeout(300)
            else:
                assert pg.locator("a.kcell").count() >= 18
        # seeded place tints the unit
        ctx.add_init_script("try{localStorage.setItem('vr.last', JSON.stringify({href:'/vu/5/15/', ts:Date.now()}))}catch(e){}")
        pg.goto(B + "/read/"); pg.wait_for_selector(".kcell.now")
        assert pg.locator(".kcell.now").get_attribute("data-k") == "5"
        assert "reading now" in pg.locator(".kcell.now").inner_text()
        pg.screenshot(path=f"{SP}/read_{theme}.png", full_page=True)
        pg.goto(B + "/mbh/read/"); pg.wait_for_selector(".kcell")
        pg.screenshot(path=f"{SP}/read_mbh_{theme}.png")

        # ---- kāṇḍa page ----
        pg.goto(B + "/vu/5/"); pg.wait_for_selector(".sargas li")
        rows = pg.locator(".sargas li")
        assert rows.count() > 20
        r = rows.first
        assert r.locator(".sn").inner_text().strip() and r.locator(".first").inner_text().strip() and "verses" in r.locator(".meta").inner_text()
        assert pg.locator("#kcont:visible").count() == 1
        pin = pg.locator("#kcont .kc-pin"); assert "Continue here" in pin.inner_text() and "15" in pin.inner_text()
        assert pin.get_attribute("href") == "15/"
        assert pg.locator(".sargas li.now").get_attribute("data-s") == "15"
        assert pg.locator(".chant-list").is_visible()
        noscroll(pg, "kanda " + theme)
        pg.screenshot(path=f"{SP}/kanda_{theme}.png")
        pg.goto(B + "/vu/4/"); pg.wait_for_selector(".sargas li")   # other kāṇḍa: no pin
        assert not pg.is_visible("#kcont") and pg.locator(".sargas li.now").count() == 0
        pg.goto(B + "/mbh/vu/6/"); pg.wait_for_selector(".sargas li")
        assert pg.locator(".sargas li").count() > 5 and not pg.is_visible("#kcont")
        noscroll(pg, "mbh kanda " + theme)
        assert not errs, errs
        ctx.close()
    print("pages2 ok")
