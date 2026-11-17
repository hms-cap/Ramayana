"""Settings A: script, size stepper, text to show, theme, place, version check, no overflow. BASE env var picks the server."""
import os, re
from playwright.sync_api import sync_playwright
B = os.environ.get("BASE", "http://localhost:8765")
SHOT = os.environ.get("SHOTS", "/tmp")
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 390, "height": 844}, service_workers="block", timezone_id="Asia/Kolkata"); pg = ctx.new_page()
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    html = lambda a: pg.evaluate("a => document.documentElement.getAttribute(a)", a)
    pg.goto(B + "/"); pg.click("[data-open-sheet=settings]"); assert pg.is_visible("#settings")
    # script
    pg.click("[data-set-script=deva]"); assert html("data-script") == "deva" and "धर्मक्षेत्रे" in pg.inner_text("#settings .set-prev")
    assert not pg.is_visible("#settings .kn-row")
    pg.click("[data-set-script=iast]"); assert not pg.is_visible("#settings .kn-row")
    pg.click("[data-set-script=knda-deva]"); assert pg.is_visible("#settings .kn-row")
    pg.click("[data-set-script=knda]"); assert pg.is_visible("#settings .kn-row")
    pg.click("[data-set-knfont=sans]"); assert html("data-knfont") == "sans"
    pg.click("[data-set-knfont=serif]"); assert html("data-knfont") is None
    # size
    pg.click("[data-size-step='1']"); assert html("data-size") == "l" and pg.is_disabled("[data-size-step='1']")
    pg.click("[data-size-step='-1']"); pg.click("[data-size-step='-1']"); assert html("data-size") == "s" and pg.is_disabled("[data-size-step='-1']")
    pg.click("[data-size-step='1']"); assert not html("data-size")
    # text to show
    assert pg.get_attribute("[data-ed-show=vu]", "aria-checked") == "true" and html("data-off") == "ce"
    pg.click("[data-ed-show=both]"); assert (html("data-off") or "") == "" and pg.get_attribute("[data-ed-show=both]", "aria-checked") == "true"
    pg.click("[data-ed-show=ce]"); assert html("data-off") == "vu"
    pg.click("[data-ed-show=vu]"); assert html("data-off") == "ce"
    assert pg.locator("[data-ed-show]").count() == 3
    # theme
    pg.click("[data-set-theme=dark]"); assert html("data-theme") == "dark"
    pg.click("[data-set-theme=system]"); assert html("data-theme") == "system"
    pg.click("[data-set-theme=light]"); assert html("data-theme") == "light"
    # switches
    pg.click("#settings [data-pref=scan] ~ i"); assert html("data-scan") == "1"
    pg.click("#settings [data-pref=scan] ~ i"); assert html("data-scan") is None
    pg.click("#settings [data-pref=savarna] ~ i"); assert html("data-savarna") == "1"
    pg.click("#settings [data-pref=savarna] ~ i")
    # place
    assert pg.inner_text("#set-place") == "Bengaluru"
    pg.evaluate("window.__pc = 0; document.addEventListener('place-changed', () => window.__pc++)")
    pg.click("[data-open-sheet=placesheet]"); assert pg.is_visible("#placesheet") and not pg.is_visible("#settings")
    pg.click("[data-place=Varanasi]")
    assert pg.evaluate("window.__pc") == 1
    pl = pg.evaluate("JSON.parse(localStorage.getItem('vr.place'))"); print("place:", pl); assert pl["name"] == "Varanasi" and abs(pl["lat"] - 25.3176) < 1e-6
    pg.click("#placesheet [data-open-sheet=settings]"); assert pg.inner_text("#set-place") == "Varanasi"
    # offline row opens the downloads sheet
    pg.click("#settings [data-open-sheet=dlsheet]"); assert pg.is_visible("#dlsheet"); pg.click("#dlsheet [data-open-sheet=settings]")
    # version
    v = pg.evaluate("self.VRAMAYANA.version"); assert v in pg.inner_text(".set-ver-r")
    pg.click("#set-chk"); pg.wait_for_function("document.getElementById('set-ver-msg').textContent.includes('latest')")
    print("msg:", pg.inner_text("#set-ver-msg"))
    pg.route("**/static/version.js*", lambda r: r.fulfill(status=200, content_type="application/javascript", body="self.VRAMAYANA = { version: '99.0.0', released: '2030-01-01' };"))
    pg.click("#set-chk"); pg.wait_for_selector("#set-upd"); assert "99.0.0" in pg.inner_text("#set-ver-msg")
    pg.unroute("**/static/version.js*")
    pg.route("**/static/version.js*", lambda r: r.abort())
    pg.click("#set-chk"); pg.wait_for_function("document.getElementById('set-ver-msg').textContent.includes('Could not check')")
    pg.unroute("**/static/version.js*")
    # screenshots and overflow in light and dark
    for th in ("light", "dark"):
        pg.click(f"[data-set-theme={th}]")
        pg.evaluate("document.getElementById('set-ver-msg').textContent = ''; var u = document.getElementById('set-upd'); if (u) u.remove()")
        assert pg.evaluate("document.documentElement.scrollWidth <= innerWidth"), th
        assert pg.evaluate("(() => { var s = document.querySelector('#settings'); return s.scrollWidth <= s.clientWidth; })()"), th
        pg.screenshot(path=f"{SHOT}/settings_{th}.png")
        print(th, "sheet scroll", pg.evaluate("(() => { var s = document.querySelector('#settings .sheet-body'); return [s.scrollHeight, s.clientHeight]; })()"))
    # Escape closes
    pg.keyboard.press("Escape"); assert not pg.is_visible("#settings")
    # Mahābhārata: its own texts setting
    pg.goto(B + "/mbh/"); pg.click("[data-open-sheet=settings]"); pg.click("[data-ed-show=both]")
    assert (pg.evaluate("document.documentElement.getAttribute('data-off')") or "") == ""
    print("errors:", errs); assert not errs
    b.close()
