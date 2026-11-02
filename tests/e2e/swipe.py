"""Swipe between sargas: one finger in the reading view, two fingers in the chant view."""
from playwright.sync_api import sync_playwright
B = "http://localhost:8765"
def swipe(cdp, pts0, pts1, steps=6):
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y, "id": i} for i, (x, y) in enumerate(pts0)]})
    for s in range(1, steps + 1):
        pts = [(a[0] + (b[0] - a[0]) * s / steps, a[1] + (b[1] - a[1]) * s / steps) for a, b in zip(pts0, pts1)]
        cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x, "y": y, "id": i} for i, (x, y) in enumerate(pts)]})
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    ctx = b.new_context(viewport={"width": 390, "height": 800}, has_touch=True, is_mobile=True); pg = ctx.new_page()
    pg.on("pageerror", lambda e: errs.append(str(e)))
    cdp = ctx.new_cdp_session(pg)
    pg.goto(B + "/vu/1/3/"); pg.wait_for_timeout(500)
    swipe(cdp, [(300, 400)], [(100, 405)]); pg.wait_for_timeout(600); print("swipe left :", pg.url)
    swipe(cdp, [(100, 400)], [(300, 405)]); pg.wait_for_timeout(600); print("swipe right:", pg.url)
    swipe(cdp, [(300, 400)], [(280, 700)]); pg.wait_for_timeout(400); print("vertical   :", pg.url)
    # chant, one verse layout: one finger = verse, two fingers = sarga
    pg.evaluate("localStorage.setItem('vr-prefs', JSON.stringify({chantLayout:'one'}))"); pg.reload(); pg.wait_for_timeout(400)
    pg.click(".chant-open"); pg.wait_for_selector(".chant"); pg.wait_for_timeout(300)
    c0 = pg.inner_text(".ch-count")
    swipe(cdp, [(300, 400)], [(100, 400)]); pg.wait_for_timeout(300); print("one finger :", c0, "->", pg.inner_text(".ch-count"), pg.url)
    swipe(cdp, [(300, 400), (320, 420)], [(100, 400), (120, 420)]); pg.wait_for_timeout(700)
    print("two fingers:", pg.url, pg.inner_text(".ch-title")[:30])
    print("errors:", errs); b.close()
