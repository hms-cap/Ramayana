"""Pariśiṣṭa -> Characters: index, character page (circle, moments, chart), family trees, word-panel link, scripts, no overflow.
    python site/build.py && python -m http.server 8765 --directory dist &
    python tests/e2e/characters.py
"""
import asyncio

from playwright.async_api import async_playwright

B = "http://localhost:8765/"
CH = "appendix/characters/"


async def no_overflow(pg, what):
    w = await pg.evaluate("[document.documentElement.scrollWidth, window.innerWidth]")
    assert w[0] <= w[1], (what, w)


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        pg = await ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: m.type == "error" and errs.append(m.text))

        # hub and index
        await pg.goto(B + "appendix/")
        assert await pg.locator(".appx-list li").count() == 2
        await pg.click(".appx-list a[href='characters/']")
        await pg.wait_for_url("**/appendix/characters/")
        n_ram = await pg.locator("[data-cw-sec=ram] .crow").count()
        n_mbh = await pg.locator("[data-cw-sec=mbh] .crow").count()
        print("index rows:", n_ram, n_mbh)
        assert n_ram == 42 and n_mbh == 81
        await pg.click("[data-cw-tab=mbh]")
        assert await pg.locator("[data-cw-sec=mbh]").is_visible() and not await pg.locator("[data-cw-sec=ram]").is_visible()
        assert await pg.locator("[data-cw-sec=mbh] .cbars i").count() >= 18
        await no_overflow(pg, "index")
        # names follow the script
        for sc, rx in (("deva", "कर्ण"), ("iast", "Karṇa"), ("knda", "ಕರ್ಣ")):
            await pg.evaluate(f"localStorage.setItem('vr-prefs', JSON.stringify({{script: '{sc}'}}))")
            await pg.reload()
            await pg.click("[data-cw-tab=mbh]")
            txt = await pg.locator("[data-cw-sec=mbh] .crow[data-id=karna] .cn").inner_text()
            assert rx in txt, (sc, txt)
        await pg.evaluate("localStorage.removeItem('vr-prefs')")

        # character page
        await pg.goto(B + CH + "mbh/karna/")
        assert "ಕರ್ಣ" in await pg.inner_text("h1")
        assert await pg.locator(".circle svg a.node").count() >= 3
        assert await pg.locator(".legend i").count() >= 2
        assert await pg.locator(".mchart .cb").count() == 18
        assert await pg.locator(".mom li").count() >= 2
        await no_overflow(pg, "character")
        await pg.set_viewport_size({"width": 360, "height": 800})
        await pg.reload()
        await no_overflow(pg, "character 360")
        await pg.set_viewport_size({"width": 390, "height": 844})
        # a moment opens the reader at the verse
        href = await pg.locator(".mom .r").first.get_attribute("href")
        await pg.locator(".mom .r").first.click()
        await pg.wait_for_load_state()
        assert "/mbh/" in pg.url and "#v" in pg.url and await pg.locator(":target").count() == 1, pg.url
        # a circle node opens that person's page
        await pg.goto(B + CH + "mbh/karna/")
        await pg.locator(".circle svg a.node").first.click()
        await pg.wait_for_url("**/appendix/characters/mbh/*/")
        assert await pg.locator("h1.pt").count() == 1
        # script switch changes the name on a page
        for sc, rx in (("deva", "कर्ण"), ("iast", "Karṇa")):
            await pg.goto(B + CH + "mbh/karna/")
            await pg.evaluate(f"localStorage.setItem('vr-prefs', JSON.stringify({{script: '{sc}'}}))")
            await pg.reload()
            assert rx in await pg.locator("h1.pt").inner_text(), sc
        await pg.evaluate("localStorage.removeItem('vr-prefs')")
        # dark mode keeps the circle readable (tokens applied)
        await pg.evaluate("localStorage.setItem('vr-prefs', JSON.stringify({theme: 'dark'}))")
        await pg.goto(B + CH + "mbh/karna/")
        fill = await pg.evaluate("getComputedStyle(document.querySelector('.circ .me')).fill")
        assert fill != "rgb(168, 106, 18)", fill
        await pg.evaluate("localStorage.removeItem('vr-prefs')")

        # family trees
        for work, first in (("mbh", "kuru"), ("ram", "ikshvaku")):
            await pg.goto(B + CH + f"{work}/family/")
            assert await pg.locator("[data-tr-tab]").count() >= 3
            assert await pg.locator(f"[data-tr-sec={first}]").is_visible()
            await pg.wait_for_selector(f"[data-tr-sec={first}] .tree-svg")
            assert await pg.locator(f"[data-tr-sec={first}] .tree-svg a.node").count() >= 3
            await no_overflow(pg, f"tree {work}")
            tabs = await pg.locator("[data-tr-tab]").count()
            for i in range(tabs):
                await pg.locator("[data-tr-tab]").nth(i).click()
                assert await pg.locator("[data-tr-sec]:not([hidden])").count() == 1
        await pg.goto(B + CH + "mbh/family/")
        await pg.locator("[data-tr-sec=kuru] .tree-svg a.node").first.click()
        await pg.wait_for_url("**/appendix/characters/mbh/*/")

        # word panel: Pune 1.1.65 names Karṇa
        await pg.goto(B + "mbh/ce/1/1/")
        await pg.evaluate("localStorage.setItem('vr-prefs', JSON.stringify({offMbh: []}))")
        await pg.goto(B + "mbh/ce/1/1/")
        await pg.wait_for_selector("#v65 .wbw-ic")
        await pg.click("#v65 .wbw-ic")
        await pg.wait_for_selector("#v65 .wbw-list > li")
        await pg.wait_for_selector("#v65 .wbw-char")
        link = pg.locator("#v65 .wbw-char[href$='/mbh/karna/']")
        txt = await link.first.inner_text()
        print("word panel link:", txt)
        assert "ಕರ್ಣ" in txt
        await link.first.click()
        await pg.wait_for_url("**/appendix/characters/mbh/karna/")
        assert not errs, errs
        print("OK")
        await b.close()


asyncio.run(main())
