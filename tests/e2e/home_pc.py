"""Home: today's pañcāṅga readout (folds, follows the script) and the foldable śloka of the day (remembered)."""
from playwright.sync_api import sync_playwright
import os
B = os.environ.get("BASE", "http://localhost:8765").rstrip("/")
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 390, "height": 800}, service_workers="block", timezone_id="Asia/Kolkata", locale="en-IN"); pg = ctx.new_page()
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(B + "/"); pg.wait_for_selector(".votd .vc-verse"); pg.wait_for_selector(".pc-main")
    main = pg.inner_text(".pc-main"); print("pañcāṅga:", main); assert "ಶುಕ್ಲ" in main or "ಕೃಷ್ಣ" in main
    assert not pg.is_visible(".pc-grid")                       # folded to one line at first
    pg.click("#pc-tog"); pg.wait_for_selector(".pc-grid", state="visible")
    assert pg.locator(".pc-grid > div").count() == 5 and "Bengaluru" in pg.inner_text(".pc-loc")
    pg.click("#pc-tog"); pg.wait_for_timeout(400); assert not pg.is_visible(".pc-grid")
    # the śloka folds to its title and first line; the choice is remembered
    assert pg.is_visible(".votd-view")
    pg.click("#votd-fold"); assert not pg.is_visible(".votd-view") and pg.inner_text("#votd-peek").strip()
    assert pg.get_attribute("#votd-fold", "aria-expanded") == "false"
    pg.reload(); pg.wait_for_selector("#votd-peek"); assert not pg.is_visible(".votd-view")
    pg.click("#votd-fold"); assert pg.is_visible(".votd-view") and pg.get_attribute("#votd-fold", "aria-expanded") == "true"
    # script follows the setting
    pg.evaluate("localStorage.setItem('vr-prefs', JSON.stringify({script:'iast'}))"); pg.reload(); pg.wait_for_selector(".pc-main")
    assert "Śukla" in pg.inner_text(".pc-main") or "Kṛṣṇa" in pg.inner_text(".pc-main")
    assert pg.evaluate("document.documentElement.scrollWidth") <= 390
    print("errors:", errs); assert not errs
