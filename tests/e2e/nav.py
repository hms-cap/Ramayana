"""Navigation (v0.17): ‹ is always up (sarga → kāṇḍa → Read → Home), Previous/Next and swipes replace history,
edition switch, jump sheet, other-text peek sheet, Back-to-verse pill. Rāmāyaṇa, Mahābhārata (lean) and Gītā."""
from playwright.sync_api import sync_playwright
B = __import__("os").environ.get("BASE", "http://localhost:8765").rstrip("/") + ""
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 390, "height": 800}, service_workers="block"); pg = ctx.new_page()
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    # up chain
    pg.goto(B + "/vu/2/10/"); pg.click("header [data-back]"); assert pg.url.endswith("/vu/2/"), pg.url
    pg.click("header [data-back]"); assert pg.url.endswith("/read/"), pg.url
    pg.click("header [data-back]"); assert pg.url == B + "/", pg.url
    crumbs = pg.goto(B + "/vu/2/10/") and pg.inner_text(".crumbs"); print("crumbs:", crumbs.replace("\n", " ")); assert "Traditional" not in crumbs
    # Next x3 replaces: one Back leaves reading
    pg.goto(B + "/read/"); pg.goto(B + "/vu/2/10/")
    for _ in range(3): pg.click(".pager a[rel=next]"); pg.wait_for_load_state()
    assert pg.url.endswith("/vu/2/13/"), pg.url
    pg.go_back(); print("phone Back after 3× Next:", pg.url); assert pg.url.endswith("/read/")
    # ‹ after Next still goes up, not to the previous sarga
    pg.goto(B + "/vu/2/10/"); pg.click(".pager a[rel=next]"); pg.wait_for_load_state(); pg.click("header [data-back]"); assert pg.url.endswith("/vu/2/"), pg.url
    # edition switch hidden while the Critical text is off; shown and replacing when on
    pg.goto(B + "/vu/2/10/"); assert not pg.is_visible(".edsw-go")
    pg.evaluate("localStorage.setItem('vr-prefs', JSON.stringify({off: [], offMbh: []}))")
    pg.goto(B + "/read/"); pg.goto(B + "/vu/2/10/"); assert pg.is_visible(".edsw-go"); print("switch:", pg.inner_text(".edsw"))
    pg.click(".edsw-go"); pg.wait_for_load_state(); assert "/ce/2/" in pg.url, pg.url
    pg.go_back(); assert pg.url.endswith("/read/"), pg.url
    # peek: badge opens a sheet, stays on the page, Back closes it
    pg.goto(B + "/vu/2/10/"); u = pg.url
    pg.click(".verse .badge a >> nth=0"); pg.wait_for_selector(".pk-sheet"); pg.wait_for_function("!document.querySelector('.pk-sheet').textContent.includes('Loading')")
    print("peek:", pg.inner_text(".pk-sheet").replace("\n", " | ")[:160]); assert pg.url.split("#")[0] == u
    pg.go_back(); pg.wait_for_timeout(200); assert not pg.query_selector(".pk-sheet") or not pg.is_visible(".pk-sheet"); assert pg.url.split("#")[0] == u
    pg.evaluate("localStorage.removeItem('vr-prefs')")
    # jump sheet: kāṇḍa chips + grid; jumping replaces
    pg.goto(B + "/read/"); pg.goto(B + "/vu/2/10/"); pg.click(".jump-open"); pg.wait_for_selector(".jp-grid a")
    assert pg.get_attribute(".jp-grid a[aria-current]", "href").endswith("/vu/2/10/")
    pg.click(".jp-ks [data-jk='5']"); pg.wait_for_selector(".jp-grid a"); print("sundara sargas:", pg.locator(".jp-grid a").count())
    pg.click(".jp-grid a >> nth=11"); pg.wait_for_url("**/vu/5/12/"); pg.go_back(); pg.wait_for_timeout(300); print("Back after jump:", pg.url); assert pg.url.endswith("/read/")
    pg.goto(B + "/vu/2/10/"); pg.click(".jump-open"); pg.wait_for_selector(".jp-x"); pg.keyboard.press("Escape"); assert not pg.query_selector(".jp"); assert pg.url.endswith("/vu/2/10/")
    # MBH lean and Gītā
    pg.goto(B + "/mbh/vu/5/3/"); pg.click(".jump-open"); pg.wait_for_selector(".jp-grid a"); print("mbh parva chips:", pg.locator(".jp-ks button").count()); assert pg.locator(".jp-ks button").count() == 18
    pg.goto(B + "/gita/vu/1/2/"); pg.click(".jump-open"); pg.wait_for_selector(".jp-grid a"); assert pg.locator(".jp-ks button").count() == 0; print("gītā grid:", pg.locator(".jp-grid a").count())
    pg.keyboard.press("Escape"); pg.click("header [data-back]"); assert pg.url.endswith("/gita/vu/1/"), pg.url
    # Back-to-verse pill
    pg.goto(B + "/vu/2/10/#v4"); pg.wait_for_timeout(200)
    pg.evaluate("document.getElementById('v4').scrollIntoView()"); pg.click(".tabbar a[href*='search']")
    pg.wait_for_selector(".retpill"); print("pill:", pg.inner_text(".retpill").replace("\n", " ")); pg.click(".retpill a"); pg.wait_for_url("**/vu/2/10/#v4")
    pg.goto(B + "/appendix/"); assert not pg.query_selector(".retpill"), "cleared after returning"
    pg.goto(B + "/appendix/"); assert pg.evaluate("document.documentElement.scrollWidth <= innerWidth")
    print("errors:", errs); assert not errs
    b.close()
