from playwright.sync_api import sync_playwright
SP="/tmp"
B="http://localhost:8765"
with sync_playwright() as p:
    b=p.chromium.launch(); ctx=b.new_context(viewport={"width":1000,"height":800}, accept_downloads=True); pg=ctx.new_page()
    errs=[]; pg.on("console",lambda m:errs.append(m.text) if m.type=="error" else None); pg.on("pageerror",lambda e:errs.append(str(e)))
    pg.goto(B+"/ce/1/1/"); pg.wait_for_timeout(300)
    pg.click(".chant-open"); pg.wait_for_selector(".chant")
    print("title:",pg.inner_text(".ch-title"))
    print("p1:",pg.inner_text(".ch-page p").replace("\xa0"," ")[:120])
    pg.screenshot(path=SP+"/chant_book.png")
    pg.click('[data-l=one]'); pg.wait_for_timeout(300); pg.screenshot(path=SP+"/chant_one.png")
    print("count:",pg.inner_text(".ch-count"))
    pg.keyboard.press("ArrowRight"); print("after right:",pg.inner_text(".ch-count"))
    pg.click('[data-s=deva]'); print(pg.inner_text(".ch-verse")[:60].replace("\n"," / "))
    # next work x2 then close
    pg.click('[data-l=book]')
    for _ in range(2):
        pg.click('[data-nav=next]'); pg.wait_for_selector(".chant"); pg.wait_for_timeout(300); print("now:",pg.url, pg.inner_text(".ch-title"))
    pg.click(".ch-x"); pg.wait_for_timeout(600); print("after close:",pg.url, "chant open:",pg.locator(".chant").count())
    # system back test
    pg.click(".chant-open"); pg.click('[data-nav=next]'); pg.wait_for_selector(".chant"); pg.wait_for_timeout(300)
    pg.go_back(); pg.wait_for_timeout(600); print("after back:",pg.url,"chant:",pg.locator(".chant").count())
    # PDF
    pg.goto(B+"/ce/1/1/"); pg.click(".chant-open"); pg.click('[data-s=knda]')
    with pg.expect_download(timeout=60000) as d: pg.click(".ch-pdf")
    dl=d.value; print("pdf:",dl.suggested_filename); dl.save_as(SP+"/out.pdf")
    # print doc
    pg.evaluate("() => { window.print = function(){ window.__p = document.getElementById('printDoc').innerText } }")
    pg.click(".ch-dots"); pg.click('[data-m=print]'); pg.wait_for_timeout(300); print("print:",(pg.evaluate("window.__p")or"")[:80].replace("\n"," | "))
    print("errors:",errs)
    # mobile
    m=b.new_context(viewport={"width":360,"height":740},has_touch=True).new_page(); m.goto(B+"/ce/1/1/"); m.click(".chant-open"); m.wait_for_timeout(300)
    print("hscroll:",m.evaluate("document.documentElement.scrollWidth>innerWidth")); m.screenshot(path=SP+"/chant_m.png")
    b.close()
