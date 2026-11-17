"""Mahābhārata speaker lines ("sañjaya uvāca") stand above the verse they introduce, not inside the one before;
Pune Appendix I passages sit in a fold under the verse; the "appendix" cross-walk badge; chant skips speakers."""
from playwright.sync_api import sync_playwright
B = __import__("os").environ.get("BASE", "http://localhost:8765").rstrip("/") + ""
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 390, "height": 800}, service_workers="block"); pg = ctx.new_page()
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    for ed in ("vu/6/25", "ce/6/23"):
        pg.goto(f"{B}/mbh/{ed}/"); pg.wait_for_selector("#v1 .t-knda .ln")
        lines1 = pg.locator("#v1 .t-knda > p:first-child .ln").all_inner_texts()
        print(ed, "v1:", len(lines1), "lines; speaker:", pg.inner_text("#v1 .speaker .sx-kn"), "| v2 speaker:", pg.inner_text("#v2 .speaker .sx-kn"))
        assert len(lines1) == 2 and "ಉವಾಚ" not in "".join(lines1), lines1
        assert "ಸಂಜಯ" in pg.inner_text("#v2 .speaker .sx-kn")
        assert pg.get_attribute("#v1", "data-meter") == "Anuṣṭubh"
        assert pg.evaluate("document.documentElement.scrollWidth") <= 390
    # inline speaker inside a verse (Kumbakonam, source puts it mid-record) renders in every script
    pg.goto(f"{B}/mbh/ce/1/19/#v17"); pg.wait_for_selector("#v17 .apx")
    assert pg.locator("#v17 .t-knda > p:first-child .ln").count() == 2
    pg.click("#v17 .apx summary"); pg.wait_for_selector("#v17 .ax-knda .al")
    print("appendix fold:", pg.inner_text("#v17 .apx summary"), "|", pg.locator("#v17 .ax-knda .al").count(), "lines,", pg.locator("#v17 .ax-knda .spk").count(), "speaker")
    assert pg.locator("#v17 .ax-knda .spk").count() >= 1 and pg.is_visible("#v17 .ax-knda")
    # a Kumbakonam verse found only in an appendix passage of the Pune text
    pg.goto(f"{B}/mbh/vu/1/68/#v104"); pg.wait_for_selector("#v104 .badge", state="attached")
    t = pg.text_content("#v104 .badge"); print("badge:", t); assert "Appendix I" in t
    # chant view: the verse lines only
    pg.goto(f"{B}/mbh/vu/6/25/"); pg.wait_for_selector("#v1 .t-knda .ln"); pg.click(".chant-open"); pg.wait_for_selector(".chant")
    pg.click('[data-l=one]'); pg.wait_for_timeout(300); v = pg.inner_text(".ch-verse"); print("chant v1:", v.replace("\n", " / ")[:120])
    assert "ಉವಾಚ" not in v
    print("errors:", errs); assert not errs
