"""Gītās inside the Mahābhārata: list, multi-adhyāya reading part by part (bar, Next part, chant through parts),
overlapping passages (Brāhmaṇagītā inside the Anugītā), Back to the list, Gītā home link, search."""
from playwright.sync_api import sync_playwright
B = "http://localhost:8765"
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 390, "height": 800}, service_workers="block"); pg = ctx.new_page()
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(B + "/gita/"); pg.click(".gitas-link a"); pg.wait_for_selector(".st")
    n = pg.locator(".st").count(); print("gītās:", n); assert n >= 15
    assert pg.locator("[data-st-tab]").count() == 0 and pg.is_visible("#anugita")
    # Anugītā: part 1, Next part, part 2
    pg.click("#anugita [data-st-read].stb"); pg.wait_for_selector(".stbar")
    pos = pg.inner_text(".stbar-pos"); print("anugītā:", pos); assert "Part" in pos
    shown = pg.evaluate("[...document.querySelectorAll('.verses > .verse')].filter(l => l.offsetParent).length"); assert shown == pg.locator(".verse.st-hl").count()
    u1 = pg.url; pg.click(".st-endli a.dk"); pg.wait_for_selector(".stbar"); print("next part:", pg.inner_text(".stbar-pos"), pg.url); assert pg.url != u1
    pg.go_back(); pg.wait_for_timeout(300); print("phone Back:", pg.url); assert "/appendix/gitas/" in pg.url
    # chant through: from part 1, Next part inside chant reopens chant on part 2
    pg.goto(B + "/appendix/gitas/#anugita"); pg.click("#anugita [data-st-chant]"); pg.wait_for_selector(".chant")
    pg.click(".ch-seg [data-l=book]"); pg.click("[data-rep-act=next]"); pg.wait_for_timeout(1500); pg.wait_for_selector(".chant")
    print("chant part:", pg.inner_text(".ch-title")); assert "2/" in pg.inner_text(".ch-title")
    pg.click(".ch-x"); pg.wait_for_timeout(500); print("✕ from chant:", pg.url); assert "/appendix/gitas/" in pg.url
    # Brāhmaṇagītā shares adhyāyas with the Anugītā but keeps its own name
    if pg.query_selector("#brahmanagita"):
        pg.goto(B + "/appendix/gitas/#brahmanagita"); pg.click("#brahmanagita [data-st-read].stb"); pg.wait_for_selector(".stbar")
        pg.click(".st-endli a.dk"); pg.wait_for_selector(".stbar"); nm = pg.inner_text(".stbar-nm b"); print("brāhmaṇagītā part 2:", nm, pg.inner_text(".stbar-pos"))
        assert "ಬ್ರಾಹ್ಮಣ" in nm
    # a one-adhyāya gītā and Back to the list
    pg.goto(B + "/appendix/gitas/#hamsagita"); pg.click("#hamsagita [data-st-read].stb"); pg.wait_for_selector(".stbar")
    assert "Part" not in pg.inner_text(".stbar-pos"); pg.click(".stbar-bk"); pg.wait_for_url("**/appendix/gitas/**"); assert pg.url.endswith("#hamsagita")
    pg.goto(B + "/search/?q=anug"); pg.wait_for_selector(".st-hit"); assert "Gītā" in pg.inner_text("#st-hits")
    assert pg.evaluate("document.documentElement.scrollWidth <= innerWidth")
    print("errors:", errs); assert not errs
    b.close()
