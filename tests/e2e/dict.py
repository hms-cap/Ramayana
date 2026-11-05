"""Dictionary: bottom-bar link, the Dictionary app at dict/kosha/, and word look-up from the word-by-word panel.
    python site/build.py && python -m http.server 8765 --directory dist &
    python tests/e2e/dict.py
"""
import asyncio

from playwright.async_api import async_playwright

B = "http://localhost:8765/"


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        pg = await ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: m.type == "error" and errs.append(m.text))

        # 1. the bottom bar links to the in-app Dictionary
        await pg.goto(B + "ce/1/1/")
        href = await pg.get_attribute(".tabbar a.ext", "href")
        print("tab link:", href)
        assert href.endswith("dict/kosha/") and "http" not in href

        # 2. tap a word in the word-by-word panel (Rāmāyaṇa)
        await pg.click("#v1 .wbw-ic")
        await pg.wait_for_selector("#v1 .wbw-list > li")
        n = await pg.locator("#v1 .wbw-list > li").count()
        entries = absent = 0
        for i in range(n):
            li = pg.locator("#v1 .wbw-list > li").nth(i)
            await li.locator(".w").click()
            await li.locator(".dcard .dc-c").wait_for(timeout=15000)
            txt = await li.locator(".dcard").inner_text()
            assert "Could not load" not in txt, txt
            entries += await li.locator(".dc-e").count() > 0
            absent += await li.locator(".dc-no").count() > 0 and await li.locator(".dc-e").count() == 0
        print("verse 1.1.1: words", n, "with entry", entries, "without", absent)
        assert entries >= n // 2
        kn = await pg.locator("#v1 .dcard .dc-s [lang=kn]").first.inner_text()
        print("first Kannada meaning:", kn[:50])
        assert any("ಀ" <= c <= "೿" for c in kn)
        # tapping again closes the card
        await pg.locator("#v1 .wbw-list > li").first.locator(".w").click()
        assert await pg.locator("#v1 .wbw-list > li").first.locator(".dcard").count() == 0

        # 3. the same on a Mahābhārata page
        await pg.evaluate("localStorage.setItem('vr-prefs', JSON.stringify({offMbh: []}))")
        await pg.goto(B + "mbh/ce/1/1/")
        await pg.click("#v1 .wbw-ic")
        await pg.wait_for_selector("#v1 .wbw-list > li")
        li = pg.locator("#v1 .wbw-list > li").first
        await li.locator(".w").click()
        await li.locator(".dcard .dc-c").wait_for(timeout=15000)
        assert await li.locator(".dc-e").count() >= 1
        link = await li.locator(".dc-h a").first.get_attribute("href")
        print("full-entry link:", link)
        assert "/dict/kosha/#/kosha/" in link

        # 4. the Dictionary app itself, and the way back
        await pg.goto(B + "dict/kosha/")
        await pg.wait_for_selector("#kq")
        await pg.fill("#kq", "agni")
        await pg.wait_for_selector("#kSug a", timeout=15000)
        assert await pg.locator("#kSug a").count() >= 1
        back = await pg.get_attribute(".itihasa-back", "href")
        assert back == "../../"
        await pg.click("#kSug a")
        await pg.wait_for_selector(".k-senses")
        print("entry:", (await pg.inner_text(".k-head")))

        print("console errors:", errs)
        assert not errs
        await b.close()
        print("OK")


asyncio.run(main())
