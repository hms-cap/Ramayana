"""Pariśiṣṭa chip and the Chandas pages.
    python site/build.py && python -m http.server 8765 --directory dist &
    python tests/e2e/chandas.py
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

        await pg.goto(B)
        assert await pg.locator(".wchip").count() == 4   # Rāmāyaṇa, Mahābhārata, Bhagavadgītā, Pariśiṣṭa
        await pg.click(".wchip[data-work-pick=app]")
        await pg.wait_for_url("**/appendix/")
        assert await pg.evaluate("localStorage.getItem('vr.work')") != "app"   # the appendix is not a work
        await pg.click(".appx-list a")
        await pg.wait_for_url("**/appendix/chandas/")
        assert await pg.locator(".ctable tbody tr").count() >= 15
        await pg.click(".ctable tbody th a >> nth=0")
        await pg.wait_for_selector(".ex")
        assert await pg.locator(".ex").count() >= 8

        # names and verses follow the script choice
        for sc, rx in (("deva", "अनुष्टुभ्"), ("iast", "Anuṣṭubh"), ("knda", "ಅನುಷ್ಟುಭ್")):
            await pg.evaluate(f"localStorage.setItem('vr-prefs', JSON.stringify({{script: '{sc}'}}))")
            await pg.reload()
            h1 = (await pg.inner_text("h1")).strip()
            assert rx in h1, (sc, h1)
            assert await pg.locator(f".ex .t-{sc}").first.is_visible()
            chip = (await pg.inner_text(".wchip[data-work-pick=ram] b")).strip()
            print(sc, h1, chip)

        # an example links into the reader at the verse
        href = await pg.locator(".ex-ref").first.get_attribute("href")
        await pg.locator(".ex-ref").first.click()
        await pg.wait_for_load_state()
        assert pg.url.endswith(href.split("../")[-1]) and await pg.locator(":target").count() == 1, pg.url
        # Mahābhārata examples link under mbh/
        await pg.goto(B + "appendix/chandas/triṣṭubh/".replace("ṣ", "sh") if False else B + "appendix/chandas/trishtubh/")
        assert "/mbh/" in (await pg.locator(".m-sec >> nth=1 >> .ex-ref >> nth=0").get_attribute("href"))
        assert not errs, errs
        print("OK")
        await b.close()


asyncio.run(main())
