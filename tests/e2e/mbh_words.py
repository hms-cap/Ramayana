"""Mahābhārata word-by-word, cross-walk links and Kannada meanings.
    python site/build.py && python -m http.server 8765 --directory dist &
    python tests/e2e/mbh_words.py
"""
import asyncio
import sys

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

        # 1. Pune text: open the word panel of the first verse
        await pg.goto(B + "mbh/ce/1/1/")
        await pg.evaluate("localStorage.setItem('vr-prefs', JSON.stringify({offMbh: []}))")
        await pg.goto(B + "mbh/ce/1/1/")
        await pg.wait_for_selector("#v1 .wbw-ic")
        assert await pg.get_attribute("#v1 .wbw-ic", "aria-disabled") is None
        await pg.click("#v1 .wbw-ic")
        await pg.wait_for_selector("#v1 .wbw-list li")
        n = await pg.locator("#v1 .wbw-list li").count()
        kn = await pg.locator("#v1 .wbw-list .mean-kn").count()
        print("Pune 1.1.1 words:", n, "with Kannada:", kn)
        assert n >= 6 and kn >= 1
        note = await pg.inner_text("#v1 .wbw-note")
        assert "not yet been reviewed" in note, note
        # in IAST the Kannada meanings are not shown
        await pg.evaluate("document.documentElement.dataset.script='iast'; document.dispatchEvent(new Event('prefs-changed'))")
        await pg.wait_for_timeout(400)
        assert await pg.locator("#v1 .wbw-list .mean-kn").count() == 0
        await pg.evaluate("document.documentElement.dataset.script='knda'")

        # 2. Traditional text: a matched verse borrows the Pune verse's words, an unmatched verse has a dimmed icon
        await pg.goto(B + "mbh/vu/1/2/")
        await pg.wait_for_selector(".verses .verse")
        res = await pg.evaluate("""(() => { const l=[...document.querySelectorAll('.verses > .verse')];
            return {on: l.filter(x=>x.querySelector('.wbw-ic:not([aria-disabled])')).length, off: l.filter(x=>x.querySelector('.wbw-ic[aria-disabled]')).length, n: l.length}})()""")
        print("Traditional 1.2 icons:", res)
        assert res["on"] > 0 and res["on"] + res["off"] == res["n"]
        first = pg.locator(".verses > .verse:has(.wbw-ic:not([aria-disabled]))").first
        await first.locator(".wbw-ic").click()
        await first.locator(".wbw-list li").first.wait_for()
        assert await first.locator(".wbw-list li").count() >= 3

        # 3. cross-walk: details row links to the Pune verse; filter hides verses not in Pune
        await first.locator(".vnum").click()
        links = await first.locator(".details a").evaluate_all("els => els.map(e => e.getAttribute('href'))")
        print("details links:", links)
        assert any("/ce/" in x or x.startswith("../") and "ce/" in x for x in links), links
        rec = await pg.inner_text(".recension")
        print("recension:", rec.replace("\n", " | ")[:140])
        assert "Pune Text" in rec
        if await pg.locator('[data-set-filter="shared"]').count():
            await pg.click('[data-set-filter="shared"]')
            hidden = await pg.evaluate("[...document.querySelectorAll('.v-absent')].every(x => getComputedStyle(x).display === 'none')")
            assert hidden

        # 4. Bhagavadgītā pages: a note, and no active word icons
        await pg.goto(B + "mbh/ce/6/30/")
        txt = await pg.inner_text(".sarga-head")
        assert "Bhagavadgītā" in txt, txt
        assert await pg.locator(".wbw-ic:not([aria-disabled])").count() == 0

        # 5. the Rāmāyaṇa panel still works and now shows Kannada for names
        await pg.goto(B + "ce/1/1/")
        await pg.click("#v1 .wbw-ic")
        await pg.wait_for_selector("#v1 .wbw-list li")
        assert await pg.locator("#v1 .wbw-list .mean-kn").count() >= 1

        # 6. daily card: the Mahābhārata card has a words section
        await pg.goto(B + "mbh/")
        await pg.wait_for_selector("#votd-words")
        assert await pg.get_attribute("#votd-words", "aria-disabled") == "false"
        await pg.click("#votd-words")
        await pg.wait_for_timeout(300)
        dl = await pg.locator(".vc-dl dt").count()
        print("daily card words:", dl)
        assert dl >= 3

        print("console errors:", errs)
        assert not errs
        await b.close()
        print("OK")


asyncio.run(main())
