"""Render site/static/icons/icon.svg to the PNG sizes the app needs (needs Playwright + Chromium)."""
from pathlib import Path
from playwright.sync_api import sync_playwright

D = Path(__file__).resolve().parent.parent / "site" / "static" / "icons"
svg = (D / "icon.svg").read_text(encoding="utf-8")
with sync_playwright() as p:
    b = p.chromium.launch()
    for name, size in (("icon-192.png", 192), ("icon-512.png", 512), ("apple-touch-icon.png", 180)):
        pg = b.new_page(viewport={"width": size, "height": size})
        pg.set_content(f'<body style="margin:0">{svg.replace("<svg ", f"<svg width={size} height={size} ", 1)}</body>')
        pg.screenshot(path=str(D / name), clip={"x": 0, "y": 0, "width": size, "height": size})
    b.close()
print("icons written to", D)
