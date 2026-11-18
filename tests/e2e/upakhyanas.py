"""Pariśiṣṭa → Upākhyānas (v0.24): the row on the Pariśiṣṭa home, the list with frame lines and twin links,
a long tale's adhyāya list, reading a part with the bar, Back to the list, search hits."""
import os
from playwright.sync_api import sync_playwright
B = os.environ.get("BASE", "http://localhost:8765")
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_context(viewport={"width": 390, "height": 844}, service_workers="block").new_page()
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(B + "/appendix/"); pg.wait_for_timeout(500)
    row = pg.locator(".achip:has(a[href='upakhyanas/'])"); assert row.count() == 1
    assert "65 tales" in row.inner_text() and row.locator(".ach").count() >= 8
    pg.goto(B + "/appendix/upakhyanas/#nala"); pg.wait_for_timeout(700)
    assert pg.locator(".st").count() == 65
    nala = pg.locator("#nala"); assert nala.is_visible() and "Bṛhadaśva" in nala.inner_text() or "ಬೃಹದಶ್ವ" in nala.inner_text()
    assert nala.locator(".st-frame").count() == 1
    # a twin link to the other epic
    pg.goto(B + "/appendix/upakhyanas/#rishyashringa-mbh"); pg.wait_for_timeout(600)
    tw = pg.locator("#rishyashringa-mbh .st-rel a"); assert tw.count() >= 1 and "Rāmāyaṇa" in tw.first.inner_text()
    # Nala: adhyāya list → a part → Back
    pg.goto(B + "/appendix/upakhyanas/#nala"); pg.wait_for_timeout(500)
    pg.click("#nala .stb.dk"); pg.wait_for_selector(".pt-row"); n = pg.locator(".pt-row:visible").count(); assert n >= 25, n
    pg.locator(".pt-row:visible").nth(2).click(); pg.wait_for_selector(".stbar"); txt = pg.inner_text(".stbar")
    assert "Part" in txt, txt
    pg.click("a.back"); pg.wait_for_timeout(600); assert pg.url.rstrip("/").endswith("/appendix/upakhyanas/nala"), pg.url
    # search finds a tale
    pg.goto(B + "/search/"); pg.wait_for_timeout(500); pg.fill("input[type=search]", "sāvitry"); pg.wait_for_timeout(1500)
    hits = pg.locator(".st-hit"); assert hits.count() >= 1 and "Upākhyāna" in hits.first.inner_text(), hits.count()
    assert pg.evaluate("document.documentElement.scrollWidth") <= 390
    print("errors:", errs); assert not errs; print("OK")
