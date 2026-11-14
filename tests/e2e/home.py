from playwright.sync_api import sync_playwright
SP="/tmp"; B="http://localhost:8765"
with sync_playwright() as p:
    b=p.chromium.launch(); errs=[]
    ctx=b.new_context(viewport={"width":1280,"height":900},accept_downloads=True); pg=ctx.new_page()
    pg.on("console",lambda m:errs.append(m.text) if m.type=="error" else None); pg.on("pageerror",lambda e:errs.append(str(e)))
    # make a last-read place first
    pg.goto(B+"/ce/2/5/"); pg.evaluate("window.scrollTo(0,1500)"); pg.wait_for_timeout(700)
    pg.goto(B+"/"); pg.wait_for_selector(".votd-slide .vc-verse"); pg.wait_for_timeout(400)
    print("name:",pg.inner_text(".votd-name"), "| cont:",pg.inner_text("#cont-where"))
    pg.screenshot(path=SP+"/home_d.png")
    for i in range(5):
        pg.click(".votd-slide"); pg.wait_for_timeout(300); print(i, pg.inner_text(".votd-name"))
    pg.click("#votd-more"); pg.click("#votd-another"); pg.wait_for_timeout(500); print("another:",pg.inner_text(".votd-kind"), pg.is_visible("#votd-today"))
    pg.click("#votd-more"); pg.click("#votd-save"); print("saved:",pg.get_attribute("#votd-save","aria-pressed"))
    pg.click(".kcard >> nth=0"); pg.wait_for_selector("#ksheet:not([hidden])"); print("chips:",pg.locator("#ks-chips a").count()); pg.keyboard.press("Escape"); pg.click("#script-cycle"); print("letter:",pg.inner_text("[data-script-letter]"))
    with pg.expect_download() as d: pg.click("#votd-share")
    d.value.save_as(SP+"/share.png"); print("share:",d.value.suggested_filename)
    pg.goto(B+"/my/"); pg.wait_for_timeout(300); print("my:",pg.inner_text("#my-saved")[:80].replace("\n"," "))
    print("errors:",errs)
    m=b.new_context(viewport={"width":390,"height":800},has_touch=True,is_mobile=True).new_page(); m.goto(B+"/"); m.wait_for_selector(".vc-verse"); m.wait_for_timeout(400)
    print("hscroll:",m.evaluate("document.documentElement.scrollWidth>innerWidth")); m.screenshot(path=SP+"/home_m.png",full_page=False)
    m.goto(B+"/ce/1/1/"); m.screenshot(path=SP+"/sarga_m.png")
    b.close()
