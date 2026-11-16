"""Stotras appendix: list, tabs, a link opens the reader with the range marked (Rāmāyaṇa and lean MBH pages), search shows stotras."""
from playwright.sync_api import sync_playwright
B = "http://localhost:8765"
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 390, "height": 800}, service_workers="block"); pg = ctx.new_page()
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(B + "/appendix/"); pg.click("a[href='stotras/']"); pg.wait_for_selector(".st")
    n = {w: pg.locator(f"[data-cw-sec={w}] .st").count() for w in ("ram", "mbh")}; print("stotras:", n); assert n["ram"] >= 5 and n["mbh"] >= 15
    pg.click("[data-cw-tab=ram]"); assert pg.is_visible("#adityahrdayam") and not pg.is_visible("#vishnu-sahasranama")
    assert "Only in the" in pg.inner_text("#adityahrdayam")
    pg.click("#adityahrdayam .st-main"); pg.wait_for_selector(".verse.st-hl")
    hl = pg.locator(".verse.st-hl").count(); print("ādityahṛdayam marked:", hl, pg.url); assert hl == 27
    assert pg.evaluate("document.querySelector('.verse.st-first').getBoundingClientRect().top < innerHeight")
    pg.goto(B + "/appendix/stotras/#vishnu-sahasranama"); assert pg.is_visible("#vishnu-sahasranama")
    pg.click("#vishnu-sahasranama .st-loc a >> nth=1"); pg.wait_for_selector(".verse.st-hl")
    print("vsn ce marked:", pg.locator(".verse.st-hl").count(), pg.url); assert "/mbh/ce/13/135/" in pg.url
    pg.goto(B + "/appendix/stotras/#gita-arjuna-vishvarupa-stuti"); pg.click("#gita-arjuna-vishvarupa-stuti .st-loc a:has-text('Gītā')")
    pg.wait_for_selector(".verse.st-hl"); assert pg.locator(".verse.st-hl").count() == 32
    pg.goto(B + "/search/?q=sahasran"); pg.wait_for_selector(".st-hit"); print("search:", pg.inner_text("#st-hits").replace("\n", " | "))
    pg.click(".st-hit >> nth=0"); pg.wait_for_selector(".st-now")
    assert pg.evaluate("document.documentElement.scrollWidth <= innerWidth"), "overflow"
    print("errors:", errs); assert not errs
    b.close()
