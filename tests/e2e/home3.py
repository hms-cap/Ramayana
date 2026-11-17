"""Home "layout 3": date strip, Continue reading (hero + chips from the saved places), unit cells, no overflow (light, dark).
    BASE=http://localhost:8765 python tests/e2e/home3.py
Reader visits make the real localStorage entries (vr.last, vr.last.mbh, vr.last.gita, vr.last.st); screenshots go to $SHOTS or /tmp."""
import json
import os
from playwright.sync_api import sync_playwright

B = os.environ.get("BASE", "http://localhost:8765").rstrip("/")
SP = os.environ.get("SHOTS", "/tmp")


def read(pg, path, wait=".verse"):
    pg.goto(B + path)
    pg.wait_for_selector(wait, state="attached")
    pg.evaluate("window.scrollTo(0,1200)")
    pg.wait_for_timeout(900)


with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 390, "height": 844}, service_workers="block", timezone_id="Asia/Kolkata", locale="en-IN")
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: m.type == "error" and errs.append(m.text))

    # ---- nothing saved: the Begin card ----
    pg.goto(B + "/"); pg.wait_for_selector(".kcell")
    assert pg.inner_text("#cont-label").strip() == "Begin", pg.inner_text("#cont-label")
    assert "Start" in pg.inner_text("#cont-go-t") and pg.locator(".cchip").count() == 0

    # ---- date strip ----
    pg.wait_for_selector(".pc-main")
    strip = pg.inner_text("#pc-tog"); print("strip:", strip.replace("\n", " "))
    assert pg.locator("#pc-tog .pc-date").inner_text().split()[0].isalpha() and "ಶುಕ್ಲ" in strip or "ಕೃಷ್ಣ" in strip
    assert pg.get_attribute("#pc-tog", "aria-expanded") == "false" and not pg.is_visible(".pc-grid")
    pg.click("#pc-tog"); pg.wait_for_selector(".pc-grid", state="visible")
    assert pg.get_attribute("#pc-tog", "aria-expanded") == "true" and pg.locator(".pc-grid > div").count() == 5
    pg.click("#pc-tog"); pg.wait_for_timeout(400); assert not pg.is_visible(".pc-grid")
    # the settings sheet's place change repaints the strip
    pg.evaluate("localStorage.setItem('vr.place', JSON.stringify({lat:28.61,lon:77.2,name:'Delhi'})); document.dispatchEvent(new Event('place-changed'))")
    pg.click("#pc-tog"); pg.wait_for_selector(".pc-grid", state="visible")
    assert "Delhi" in pg.inner_text(".pc-loc"); pg.click("#pc-tog")

    # ---- real reader visits seed the saved places (oldest first) ----
    idx = pg.evaluate("fetch('/data/stotras.json').then(r=>r.json())")
    st = next(x for x in idx if x["t"] == "s" and "vu" in x["parts"])
    k, s, a, z = st["parts"]["vu"][0]
    read(pg, "/vu/%d/%d/#v%d-%d" % (k, s, a, z))      # a stotra inside the Rāmāyaṇa: also sets vr.last
    read(pg, "/vu/5/15/")
    read(pg, "/mbh/vu/5/33/")
    read(pg, "/gita/vu/1/6/")
    saved = pg.evaluate("({r:localStorage.getItem('vr.last'),m:localStorage.getItem('vr.last.mbh'),g:localStorage.getItem('vr.last.gita'),s:localStorage.getItem('vr.last.st')})")
    print("seeded:", {x: (y or "")[:90] for x, y in saved.items()})
    assert all(saved.values()), saved
    sst = json.loads(saved["s"]); assert sst["list"] == "stotras" and sst["title"]["knda"] and sst["href"].endswith("#v%d-%d" % (a, z)) and sst["ts"]

    # ---- Continue reading from each home: hero = newest work (Gītā), chips by recency, hues, working links ----
    for home in ("/", "/mbh/", "/gita/"):
        pg.goto(B + home); pg.wait_for_selector(".cchip")
        assert pg.inner_text("#cont-label").strip() == "Continue reading"
        cls = pg.get_attribute("#cont-go", "class"); assert "w-gita" in cls, cls
        assert "6" in pg.inner_text("#cont-where") or "೬" in pg.inner_text("#cont-where")
        chips = pg.locator(".cchip"); n = chips.count()
        hues = [("w-app" if "w-app" in c else "w-mbh" if "w-mbh" in c else "w-ram" if "w-ram" in c else "?") for c in [chips.nth(i).get_attribute("class") for i in range(n)]]
        print(home, "chips:", hues, [chips.nth(i).inner_text() for i in range(n)])
        assert hues == ["w-mbh", "w-ram", "w-app"], hues
        for i in range(-1, n):
            href = pg.evaluate("(i)=>(i<0?document.querySelector('#cont-go'):document.querySelectorAll('.cchip')[i]).href", i)
            r = ctx.request.get(href); assert r.status == 200, (home, href, r.status)
        # chip text is in the chosen script; the Rāmāyaṇa chip names the kāṇḍa and the sarga number
        assert "·" in chips.nth(1).inner_text()
    # click through: the Rāmāyaṇa chip opens sarga 5.15, the stotra chip opens its range
    pg.goto(B + "/mbh/"); pg.wait_for_selector(".cchip.w-ram"); pg.click(".cchip.w-ram"); pg.wait_for_url("**/vu/5/15/**")
    pg.goto(B + "/gita/"); pg.wait_for_selector(".cchip.w-app"); pg.click(".cchip.w-app"); pg.wait_for_url("**#v%d-%d" % (a, z))
    # script follows the setting
    pg.evaluate("localStorage.setItem('vr-prefs', JSON.stringify({script:'iast'}))"); pg.goto(B + "/"); pg.wait_for_selector(".cchip")
    assert not any(0x0C80 <= ord(c) <= 0x0CFF for c in pg.inner_text("#continue")), pg.inner_text("#continue")
    pg.evaluate("localStorage.setItem('vr-prefs', JSON.stringify({script:'knda'}))")

    # ---- unit cells ----
    pg.goto(B + "/"); pg.wait_for_selector(".kcell.now")
    assert pg.locator(".kcell").count() == 7 and pg.locator(".kcell.now").count() == 1
    assert pg.get_attribute(".kcell.now", "data-k") == "5" and "reading now" in pg.inner_text(".kcell.now")
    assert not pg.is_visible(".kcell:not(.now) .kl-now") and "77" in pg.inner_text(".kcell >> nth=0")
    pg.click(".kcell >> nth=0"); pg.wait_for_selector("#ksheet:not([hidden])"); assert pg.locator("#ks-chips a").count() >= 70; pg.keyboard.press("Escape")
    pg.goto(B + "/mbh/"); pg.wait_for_selector(".kcell"); assert pg.locator(".kcell").count() == 18 and pg.get_attribute(".kcell.now", "data-k") == "5"
    pg.goto(B + "/gita/"); pg.wait_for_selector(".kcell"); assert pg.locator(".kcell").count() >= 18 and pg.get_attribute(".kcell.now", "data-k") == "6"
    pg.click(".kcell.now"); pg.wait_for_url("**/gita/vu/1/6/**")

    # ---- no horizontal scroll, light and dark; screenshots ----
    for theme in ("", "dark"):
        pg.evaluate("localStorage.setItem('vr-prefs', JSON.stringify({script:'knda', theme:'%s'}))" % theme)
        for home in ("/", "/mbh/", "/gita/"):
            for w in (360, 390, 430):
                pg.set_viewport_size({"width": w, "height": 900}); pg.goto(B + home); pg.wait_for_selector(".cchip"); pg.wait_for_selector(".votd-slide .vc-verse"); pg.wait_for_timeout(300)
                assert pg.evaluate("document.documentElement.scrollWidth") <= w, (home, w, theme)
                assert pg.evaluate("document.documentElement.dataset.theme") == (theme or "light")
        pg.set_viewport_size({"width": 390, "height": 900}); pg.goto(B + "/"); pg.wait_for_selector(".cchip"); pg.wait_for_timeout(400)
        pg.click("#pc-tog"); pg.wait_for_timeout(400)
        pg.screenshot(path="%s/home3_390_%s.png" % (SP, theme or "light"), full_page=True)
        pg.set_viewport_size({"width": 1100, "height": 900}); pg.goto(B + "/"); pg.wait_for_selector(".cchip"); pg.wait_for_timeout(400)
        assert pg.evaluate("document.documentElement.scrollWidth") <= 1100
        pg.screenshot(path="%s/home3_1100_%s.png" % (SP, theme or "light"), full_page=True)
    print("errors:", errs); assert not errs
    b.close(); print("OK")
