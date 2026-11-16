"""Stotras: list (tabs, one-line openings, deity chips, search, daily), reader bar (Back to the list item, progress,
end card), chant of just the stotra with repetitions, Back from chant to the list, search page hits."""
from playwright.sync_api import sync_playwright
B = "http://localhost:8765"
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 390, "height": 800}, service_workers="block"); pg = ctx.new_page()
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(B + "/appendix/"); pg.click("a[href='stotras/']"); pg.wait_for_selector(".st")
    n = {w: pg.locator(f"[data-st-sec={w}] .st").count() for w in ("ram", "mbh")}; print("stotras:", n); assert n["ram"] >= 5 and n["mbh"] >= 15
    # every card is short: one-line opening (Nārada's hymn used to be ~1,650px tall)
    pg.click("[data-st-tab=mbh]"); h = pg.evaluate("document.getElementById('narada-narayana-stuti').offsetHeight"); print("nārada card:", h); assert h < 420
    # deity chips and search
    pg.click("[data-st-sec=mbh] [data-deity=shiva]"); vis = pg.locator("[data-st-sec=mbh] .st:visible").count(); print("śiva:", vis); assert 4 <= vis <= 8
    pg.click("[data-st-sec=mbh] [data-deity='']")
    pg.fill("#st-q", "aditya"); assert pg.is_visible("#adityahrdayam"), "search switches work"; pg.fill("#st-q", "")
    pg.fill("#st-q", "ವಿಷ್ಣು"); assert pg.is_visible("#devas-stuti-of-vishnu") and not pg.is_visible("#adityahrdayam"); pg.fill("#st-q", "")
    # Read -> reader bar -> Back lands on the item
    pg.click("[data-st-tab=ram]"); pg.click("#adityahrdayam [data-st-read].stb")
    pg.wait_for_selector(".stbar"); assert pg.locator(".verse.st-hl").count() == 27
    print("bar:", pg.inner_text(".stbar").replace("\n", " | "))
    assert pg.locator(".st-endli").count() == 1
    pg.click(".stbar-bk"); pg.wait_for_url("**/appendix/stotras/**"); print("back to:", pg.url); assert pg.url.endswith("#adityahrdayam")
    assert pg.is_visible("#adityahrdayam")
    # daily: add, chant from the list with 1 repetition, ✕ returns to the list, ticked
    pg.evaluate("localStorage.setItem('vr.reps','1'); localStorage.removeItem('vr.daily')"); pg.reload(); pg.wait_for_selector("#adityahrdayam")
    pg.click("#adityahrdayam [data-st-daily]"); pg.wait_for_selector("#st-daily:not([hidden])")
    pg.click("#adityahrdayam [data-st-chant]"); pg.wait_for_selector(".chant .ch-title")
    print("chant title:", pg.inner_text(".chant .ch-title"))
    nv = pg.evaluate("document.querySelectorAll('.chant .cv').length"); print("chant verses:", nv); assert nv in (0, 27)
    if nv == 0:  # one-verse layout
        assert "/ " in pg.inner_text(".ch-count")
    pg.click(".ch-seg [data-l=book]"); assert pg.evaluate("document.querySelectorAll('.chant .cv').length") == 27
    pg.click("[data-rep='3']"); assert "1 of 3" in pg.inner_text(".ch-tally")
    pg.click("[data-rep='1']"); pg.click("[data-rep-act=done]"); assert "Done" in pg.inner_text(".ch-tally")
    pg.click(".ch-x"); pg.wait_for_url("**/appendix/stotras/**"); pg.wait_for_selector("#st-daily .st-tick[aria-pressed=true]")
    print("daily ticked:", pg.inner_text("#st-dlist").replace("\n", " "))
    # MBH lean page and a Gītā link
    pg.goto(B + "/appendix/stotras/#vishnu-sahasranama"); pg.click("#vishnu-sahasranama [data-st-read].stb"); pg.wait_for_selector(".stbar")
    assert pg.locator(".verse.st-hl").count() == 143
    pg.mouse.wheel(0, 3000); pg.wait_for_timeout(300); print("progress:", pg.inner_text(".stbar-pos"))
    pg.click(".stbar-go"); pg.wait_for_selector(".chant"); pg.click(".ch-x"); pg.wait_for_timeout(200); assert "/mbh/vu/13/254/" in pg.url, pg.url
    pg.goto(B + "/appendix/stotras/#gita-arjuna-vishvarupa-stuti"); pg.click("#gita-arjuna-vishvarupa-stuti .st-loc a:has-text('Gītā')")
    pg.wait_for_selector(".stbar"); assert pg.locator(".verse.st-hl").count() == 32
    # Nārada (Pune): no editors' numbers in the text
    pg.goto(B + "/mbh/ce/12/325/#v4-4"); pg.wait_for_selector(".stbar"); assert "[1]" not in pg.inner_text("#v4")
    pg.goto(B + "/search/?q=sahasran"); pg.wait_for_selector(".st-hit"); pg.click(".st-hit >> nth=0"); pg.wait_for_selector(".st-now")
    assert pg.evaluate("document.documentElement.scrollWidth <= innerWidth"), "overflow"
    print("errors:", errs); assert not errs
    b.close()
