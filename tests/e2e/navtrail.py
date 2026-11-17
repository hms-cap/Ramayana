"""In-app Back / Forward (nav.js, v0.23): ‹ goes one step back on the trail of pages this tab has shown, sideways moves
(Previous/Next, crumbs, works switch, jump sheet) replace instead of stacking, › appears after going back, and a page
opened from outside goes up with ‹ without growing history."""
import os
from playwright.sync_api import sync_playwright
B = os.environ.get("BASE", "http://localhost:8765")
def path(pg): return pg.url.replace(B, "").split("#")[0].split("?")[0]
def back_to(pg): return pg.inner_text("a.back .back-to") if pg.locator("a.back:visible").count() else None
def go(pg, sel): pg.locator(sel).first.click(); pg.wait_for_timeout(700)
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 390, "height": 844}, service_workers="block"); pg = ctx.new_page()
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    # 1. Home → sarga → Next → ‹ lands on Home in one step; › returns to the verse
    pg.goto(B + "/"); pg.wait_for_timeout(600)
    assert not pg.locator("a.back:visible").count()
    go(pg, ".kcell >> nth=4"); pg.locator("#ksheet a:visible").nth(14).click(); pg.wait_for_timeout(800)
    s0 = path(pg); assert s0.startswith("/vu/5/") and back_to(pg) == "Home", (s0, back_to(pg))
    go(pg, "a[rel=next]"); s1 = path(pg); assert s1 != s0 and s1.startswith("/vu/5/") and back_to(pg) == "Home"
    go(pg, "a.back"); assert path(pg) == "/", path(pg)
    assert pg.is_visible("button.fwd"); go(pg, "button.fwd"); assert path(pg) == s1
    go(pg, "a.back"); assert path(pg) == "/"
    # 2. Read → kāṇḍa → sarga, then ‹ ‹ walks back the same way
    go(pg, "a[href$='read/']:visible"); assert path(pg) == "/read/"
    go(pg, ".kcard >> nth=1"); pg.locator("#ksheet a:visible").nth(3).click(); pg.wait_for_timeout(800)
    sarga = path(pg); assert sarga.startswith("/vu/2/"), sarga
    assert back_to(pg) == "Read", back_to(pg)
    go(pg, "a.back"); assert path(pg) == "/read/"
    go(pg, "a.back"); assert path(pg) == "/"
    # 3. crumbs replace: sarga → crumb (kāṇḍa) → ‹ goes to where the sarga came from, not back to the sarga
    pg.goto(B + "/"); pg.wait_for_timeout(500)
    go(pg, ".kcell >> nth=1"); pg.locator("#ksheet a:visible").nth(5).click(); pg.wait_for_timeout(800)
    go(pg, ".crumbs a >> nth=-1"); assert path(pg) == "/vu/2/", path(pg)
    assert back_to(pg) == "Home", back_to(pg)
    # 4. Mahābhārata: works switch replaces; sarga ‹ → its home
    pg.goto(B + "/"); pg.wait_for_timeout(500)
    go(pg, ".workchips a[data-work-pick=mbh]"); assert path(pg) == "/mbh/"
    assert not pg.locator("a.back:visible").count()   # replaced Home, nothing behind
    go(pg, ".kcell >> nth=5"); pg.locator("#ksheet a:visible").nth(24).click(); pg.wait_for_timeout(800)
    assert path(pg).startswith("/mbh/vu/6/"), path(pg)
    go(pg, "a.back"); assert path(pg) == "/mbh/", path(pg)
    # 5. stotra from the Pariśiṣṭa: ‹ returns to the list
    pg.goto(B + "/appendix/stotras/#adityahrdayam"); pg.wait_for_timeout(600)
    go(pg, "#adityahrdayam [data-st-read].stb"); assert "/vu/6/" in path(pg), path(pg)
    go(pg, "a.back"); assert path(pg) == "/appendix/stotras/", path(pg)
    # 6. a link from outside: ‹ goes up and does not add history
    pg2 = b.new_context(viewport={"width": 390, "height": 844}, service_workers="block").new_page()
    pg2.goto(B + "/vu/2/10/"); pg2.wait_for_timeout(700)
    n0 = pg2.evaluate("history.length"); assert back_to(pg2) == "ಅಯೋಧ್ಯಾಕಾಂಡ", back_to(pg2)
    go(pg2, "a.back"); assert path(pg2) == "/vu/2/" and pg2.evaluate("history.length") == n0
    # 7. long-press menu lists earlier places
    pg.goto(B + "/?work=ram"); pg.wait_for_timeout(400); go(pg, ".kcell >> nth=0"); pg.locator("#ksheet a:visible").nth(1).click(); pg.wait_for_timeout(700)
    go(pg, "a[rel=next]"); pg.locator("a.back").dispatch_event("contextmenu"); pg.wait_for_timeout(200)
    assert pg.locator(".trail-menu button").count() >= 1
    pg.keyboard.press("Escape"); assert not pg.locator(".trail-menu").count()
    # 8. crumbs and the works switch replace for real (history does not grow); jump sheet then ‹ ‹ keeps labels right
    pg3 = b.new_context(viewport={"width": 390, "height": 844}, service_workers="block").new_page()
    pg3.goto(B + "/?work=ram"); pg3.wait_for_timeout(500)
    n = pg3.evaluate("history.length"); go(pg3, ".workchips a[data-work-pick=mbh]"); assert pg3.evaluate("history.length") == n
    go(pg3, ".workchips a[data-work-pick=ram]"); go(pg3, ".kcell >> nth=0"); pg3.locator("#ksheet a:visible").nth(1).click(); pg3.wait_for_timeout(700)
    n = pg3.evaluate("history.length"); go(pg3, ".crumbs a >> nth=-1"); assert pg3.evaluate("history.length") == n and path(pg3) == "/vu/1/"
    pg3.goto(B + "/?work=ram"); pg3.wait_for_timeout(400)
    go(pg3, "a[href$='read/']:visible"); go(pg3, ".kcard >> nth=0"); pg3.locator("#ksheet a:visible").nth(2).click(); pg3.wait_for_timeout(700)
    go(pg3, ".jump-open"); go(pg3, ".jp-grid a >> nth=6"); assert back_to(pg3) == "Read", back_to(pg3)
    go(pg3, "a.back"); assert path(pg3) == "/read/"; go(pg3, "a.back"); assert path(pg3) == "/"
    go(pg3, ".kcell >> nth=0"); pg3.locator("#ksheet a:visible").nth(3).click(); pg3.wait_for_timeout(700)
    assert back_to(pg3) == "Home", back_to(pg3)
    print("errors:", errs); assert not errs
    print("OK")
