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

        # 5. from a card to the dictionary and back: the same word's card is reopened (link and Back button)
        for how in ("pill", "back"):
            await pg.goto(B + "ce/1/1/")
            await pg.evaluate("sessionStorage.clear()")
            await pg.click("#v1 .wbw-ic")
            await pg.wait_for_selector("#v1 .wbw-list > li")
            li = pg.locator("#v1 .wbw-list > li").nth(2)
            await li.locator(".w").click()
            await li.locator(".dcard .dc-h a").first.wait_for(timeout=15000)
            await li.locator(".dcard .dc-h a").first.click()
            await pg.wait_for_selector(".k-senses")
            assert "?from=" in pg.url and "/dict/kosha/" in pg.url, pg.url
            label = (await pg.inner_text(".itihasa-back")).strip()
            print(how, "pill:", label)
            assert label.endswith("1.1.1"), label
            if how == "pill":
                await pg.click(".itihasa-back")
            else:
                await pg.go_back()
            await pg.wait_for_url("**/ce/1/1/**")
            await pg.locator("#v1 .wbw-list > li").nth(2).locator(".dcard .dc-c").wait_for(timeout=15000)
            assert await pg.locator("#v1 .wbw-list > li").count() > 2
            print(how, "restored the card")

        # 6. the dictionary follows Itihāsa's light/dark setting, also while it is open
        await pg.goto(B + "ce/1/1/")
        await pg.evaluate("localStorage.setItem('vr-prefs', JSON.stringify({theme: 'dark'}))")
        k = await ctx.new_page()
        await k.goto(B + "dict/kosha/")
        await k.wait_for_selector("#kq")
        assert await k.evaluate("document.documentElement.dataset.theme") == "dark"
        await pg.evaluate("localStorage.setItem('vr-prefs', JSON.stringify({theme: ''}))")
        await k.wait_for_function("document.documentElement.dataset.theme === 'light'", timeout=5000)
        await k.goto(B + "dict/kosha/#/about")
        await k.wait_for_selector("#abTheme")
        assert "follows" in (await k.inner_text("#abTheme"))
        await k.close()

        print("console errors:", errs)
        assert not errs
        await b.close()
        print("OK")


asyncio.run(main())
