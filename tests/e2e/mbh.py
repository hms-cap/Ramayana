"""Mahābhārata as a second work: lean rendering parity, work switch, per-work state, launch redirect, offline shell.
    python site/build.py && python -m http.server 8765 --directory dist &
    python tests/e2e/mbh.py
"""
import asyncio
import json
import sys
from pathlib import Path

from playwright.async_api import async_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "etl"))
from translit import iast_to_slp1, render  # noqa: E402

B = "http://localhost:8765/"


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        pg = await ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: m.type == "error" and errs.append(m.text))

        # 1. the browser's Kannada/Devanāgarī (built from IAST) equals the build-time transliteration
        await pg.goto(B + "mbh/vu/1/2/")
        rows = await pg.evaluate("""[...document.querySelectorAll('.verses > .verse')].slice(0, 60).map(li => ({
            iast: [...li.querySelectorAll('.t-iast .ln')].map(x => x.textContent.replace(/\\u00a0\\|.*$/, '')),
            knda: [...li.querySelectorAll('.t-knda p:first-child .ln')].map(x => x.textContent.replace(/\\u00a0[।॥].*$/, '')),
            deva: [...li.querySelectorAll('.t-deva p:first-child .ln')].map(x => x.textContent.replace(/\\u00a0[।॥].*$/, ''))}))""")
        bad = 0
        for r in rows:
            for sc, key in (("knda", "knda"), ("deva", "deva")):
                want = [render(iast_to_slp1(l), sc) for l in r["iast"]]
                if want != r[key]:
                    bad += 1
        print("lean parity: mismatches", bad, "of", len(rows) * 2)
        assert bad == 0

        # 2. work switch and per-work state
        await pg.goto(B)
        await pg.evaluate("localStorage.clear(); sessionStorage.clear()")
        await pg.goto(B + "ce/1/1/")
        await pg.goto(B + "mbh/vu/1/3/#v4")
        await pg.wait_for_timeout(300)
        await pg.click(".chant-open")
        await pg.wait_for_timeout(500)
        await pg.keyboard.press("Escape")
        keys = await pg.evaluate("Object.keys(localStorage).sort()")
        print("keys:", keys)
        assert "vr.last.mbh" in keys and "vr.work" in keys
        await pg.goto(B + "mbh/")
        await pg.wait_for_timeout(900)
        txt = await pg.inner_text("#continue")
        print("mbh continue:", txt.replace("\n", " | "))
        assert "continue" in txt.lower() and "ಆದಿಪರ್ವ" in txt
        # texts switched on are per work: turn the Pune text on in the Mahābhārata only
        await pg.click('[data-open-sheet="settings"]')
        await pg.click('label.sw:has([data-ed-toggle="ce"])')
        await pg.keyboard.press("Escape")
        prefs = await pg.evaluate("JSON.parse(localStorage.getItem('vr-prefs'))")
        print("prefs:", prefs)
        assert prefs.get("offMbh") == [] or prefs.get("offMbh") == ["vu"] or "ce" not in prefs["offMbh"]
        assert "off" not in prefs or "ce" in prefs["off"]
        # switch to the Rāmāyaṇa from the sheet
        await pg.click('.wchip[data-work-pick="ram"]')
        await pg.wait_for_timeout(900)
        print("after switch:", pg.url)
        assert pg.url.rstrip("/") == B.rstrip("/")
        txt = await pg.inner_text("#continue")
        print("ram continue:", txt.replace("\n", " | "))
        assert "begin" in txt.lower() and "ಆದಿಪರ್ವ" not in txt   # the Rāmāyaṇa has its own place
        assert await pg.evaluate("document.documentElement.dataset.off") == "ce"

        # 3. fresh launch returns to the last-used work (no referrer); a link inside the site does not
        await pg.goto(B + "mbh/")
        await pg.goto("about:blank")
        await pg.goto(B)
        await pg.wait_for_timeout(600)
        print("fresh launch:", pg.url, await pg.evaluate("localStorage.getItem(\"vr.work\")"), repr(await pg.evaluate("document.referrer")))
        assert pg.url == B + "mbh/"
        # About and Saved follow the work
        await pg.goto(B + "about/")
        await pg.wait_for_timeout(300)
        hrefs = await pg.evaluate("[...document.querySelectorAll('.tabbar a')].map(a => a.getAttribute('href'))")
        print("about tabbar:", hrefs)
        assert hrefs[0].endswith("mbh/") and hrefs[1].endswith("mbh/search/")

        # 4. search and the daily śloka
        await pg.goto(B + "mbh/search/?q=dharmaksetre")
        await pg.wait_for_function("document.getElementById('status').textContent.includes('match')", timeout=20000)
        print("search:", await pg.inner_text("#status"))
        await pg.goto(B + "mbh/")
        await pg.wait_for_selector("#votd .vc-verse")
        print("votd ctx:", (await pg.evaluate("[...document.querySelectorAll('#votd [data-card]')].length")), "cards")
        print("errors:", errs)
        assert not errs
        await b.close()


asyncio.run(main())
