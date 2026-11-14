"""Bottom bar without Read; grouped settings; Settings > Downloads saves and removes one chip."""
from playwright.sync_api import sync_playwright
B = "http://localhost:8765"
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 390, "height": 800}, service_workers="block"); pg = ctx.new_page()
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(B + "/")
    labs = pg.eval_on_selector_all(".tabbar a", "a => a.map(x => x.getAttribute('aria-label'))")
    print("tabbar:", labs); assert labs == ["Home", "Search", "Saved", "Dictionary: Sanskrit to Kannada (Śabdārtha Kaustubha)"], labs
    pg.click("[data-open-sheet=settings]")
    assert pg.is_visible("#settings .set-prev"), "preview"
    assert not pg.is_visible("#settings [data-pref=savarna]"), "pañcama is under Advanced"
    pg.click("#settings .acc-d summary"); assert pg.is_visible("#settings [data-pref=savarna]")
    pg.click("[data-set-script=deva]"); assert "धर्मक्षेत्रे" in pg.inner_text("#settings .set-prev")
    pg.click("[data-open-sheet=dlsheet]"); pg.wait_for_selector("#dl-list .dl")
    assert not pg.is_visible("#settings")
    pg.click("[data-dl-work=gita]"); pg.wait_for_selector("#dl-list [data-dl]")
    pg.click("#dl-list [data-dl]").__class__
    pg.wait_for_selector("#dl-list [data-dl-remove]", timeout=60000)
    print("saved:", pg.inner_text("#dl-list .dl >> nth=0").replace("\n", " "))
    print("used:", pg.inner_text("#dl-used"), "| summary:", pg.evaluate("document.getElementById('dl-sum').textContent"))
    pg.click("#dl-list [data-dl-remove]"); pg.wait_for_selector("#dl-list [data-dl]")
    pg.click("#dlsheet [data-open-sheet=settings]"); assert pg.is_visible("#settings")
    ov = pg.evaluate("document.documentElement.scrollWidth > innerWidth"); assert not ov
    print("errors:", errs); assert not errs
    b.close()
