"""Bookmarks: verse star, strip under the title, list sheet, Read page bar, MBH lean pages."""
from playwright.sync_api import sync_playwright
B = "http://localhost:8765"
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 390, "height": 800}, service_workers="block"); pg = ctx.new_page()
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(B + "/vu/1/1/"); pg.wait_for_selector(".bm-ic")
    pg.evaluate("localStorage.removeItem('vr.saved')"); pg.reload(); pg.wait_for_selector(".bm-ic")
    pg.click(".verse >> nth=2 >> .bm-ic"); pg.click(".verse >> nth=4 >> .bm-ic")
    assert pg.locator(".bm-ic[aria-pressed=true]").count() == 2
    pg.wait_for_selector("[data-bmbar] .bm-chip"); assert pg.locator("[data-bmbar] .bm-chip").count() == 2
    pg.click("[data-save]"); assert "Bookmarked" in pg.inner_text("[data-save]")
    pg.click("[data-bmbar] .bm-all"); pg.wait_for_selector("#bm-list .bm-it")
    print("sheet:", pg.inner_text("#bm-list").replace("\n", " | "))
    assert pg.locator("#bm-list .bm-it").count() == 3
    pg.click("#bm-list .bm-x >> nth=0"); assert pg.locator("#bm-list .bm-it").count() == 2
    pg.click("[data-bm-work=mbh]"); assert pg.is_visible("#bm-empty")
    pg.click("#bmsheet [data-close-sheet]")
    pg.goto(B + "/mbh/vu/1/1/"); pg.wait_for_selector(".bm-ic"); pg.click(".verse >> nth=1 >> .bm-ic")
    pg.wait_for_selector("[data-bmbar] .bm-chip"); assert pg.locator("[data-bmbar] .bm-chip").count() == 1
    pg.goto(B + "/mbh/read/"); pg.wait_for_selector("[data-bmbar] .bm-chip")
    pg.goto(B + "/read/"); pg.wait_for_selector("[data-bmbar] .bm-chip")
    assert pg.evaluate("document.documentElement.scrollWidth <= innerWidth"), "overflow"
    print("errors:", errs); assert not errs
    b.close()

# export / import
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 390, "height": 800}, accept_downloads=True, service_workers="block"); pg = ctx.new_page()
    pg.goto(B + "/vu/1/1/"); pg.wait_for_selector(".bm-ic"); pg.click(".verse >> nth=2 >> .bm-ic"); pg.click(".verse >> nth=3 >> .bm-ic")
    pg.click("[data-bmbar] .bm-all"); pg.wait_for_selector("#bm-list .bm-it")
    with pg.expect_download() as dl: pg.click("#bm-export")
    path = dl.value.path(); import json; d = json.load(open(path)); assert len(d["items"]) == 2, d
    pg.evaluate("localStorage.removeItem('vr.saved')"); pg.reload(); pg.click(".verse >> nth=0 >> .bm-ic")
    pg.click("[data-bmbar] .bm-all"); pg.set_input_files("#bm-file", path); pg.wait_for_function("document.getElementById('bm-msg').textContent.startsWith('Added')")
    assert pg.locator("#bm-list .bm-it").count() == 3
    pg.set_input_files("#bm-file", path); pg.wait_for_function("document.getElementById('bm-msg').textContent.startsWith('Nothing new')")
    assert pg.locator("#bm-list .bm-it").count() == 3
    open("/tmp/bad.json", "w").write("{}"); pg.set_input_files("#bm-file", "/tmp/bad.json"); pg.wait_for_function("document.getElementById('bm-msg').textContent.startsWith('That file')")
    print("export/import ok"); b.close()
