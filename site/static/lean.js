/* Mahābhārata pages ship only the IAST text of each verse (to keep the site small).
   This builds the Kannada and Devanāgarī versions, the verse number buttons and the
   details panel in the browser, before app.js and chant.js read the page. */
(function () {
  "use strict";
  var T = window.Translit;
  if (!T) return;
  var NB = "\u00a0";
  function el(tag, cls, attrs) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (attrs) Object.keys(attrs).forEach(function (k) { e.setAttribute(k, attrs[k]); });
    return e;
  }
  function marks(sc) {                                     // the reference is in the verse's pill, so the verse ends with a plain ॥
    return { mid: NB + "।", last: NB + "॥" };
  }
  function script(slp, sc, sav) {
    var m = marks(sc);
    return slp.map(function (l, i) { return [T.render(l, sc, sav), i === slp.length - 1 ? m.last : m.mid]; });
  }
  function block(sc, lang, slp) {
    var d = el("div", "t t-" + sc, { lang: lang });
    var base = script(slp, sc, false);
    // the Kannada-only "classical pañcama" variant (.ps1); Devanāgarī has no variant
    var alt = sc === "knda" ? script(slp, sc, true) : null;
    var same = !alt || base.map(function (x) { return x[0]; }).join("|") === alt.map(function (x) { return x[0]; }).join("|");
    function para(lines, cls) {
      var p = el("p", cls || ""); if (!cls) p.removeAttribute("class");
      lines.forEach(function (t) {
        var s = el("span", "ln"), dm = el("span", "d");
        s.appendChild(document.createTextNode(t[0])); dm.textContent = t[1]; s.appendChild(dm); p.appendChild(s);
      });
      return p;
    }
    if (same) d.appendChild(para(base));
    else { d.appendChild(para(base, "ps0")); d.appendChild(para(alt, "ps1")); }
    return d;
  }

  [].forEach.call(document.querySelectorAll(".verses > .verse[data-ref]"), function (li) {
    var iast = li.querySelector(".t-iast"); if (!iast) return;
    var ref = li.dataset.ref, n = li.id.slice(1);
    var slp = [].map.call(iast.querySelectorAll(".ln"), function (x) {
      return T.iastToSlp1(x.textContent.replace(/\u00a0\|.*$/, "").trim());
    });
    var host = iast.parentNode;
    host.insertBefore(block("knda", "sa-Knda", slp), iast);
    host.insertBefore(block("deva", "sa-Deva", slp), iast);

    // header row: reference pill (opens the details), metre, word-by-word icon
    var vh = el("div", "vh"), b = el("button", "vnum", { type: "button", "aria-expanded": "false", "aria-controls": "d" + n, title: "Verse details" });
    [["knda", T.digits(ref, "knda")], ["deva", T.digits(ref, "deva")], ["iast", ref]].forEach(function (x) {
      var s = el("span", "n-" + x[0]); s.textContent = x[1]; b.appendChild(s);
    });
    vh.appendChild(b);
    if (li.dataset.meter) { var mt = el("span", "vmeter"); mt.textContent = li.dataset.meter; vh.appendChild(mt); }
    var wi = el("button", "wbw-ic", { type: "button", "aria-expanded": "false" });
    wi.innerHTML = '<svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><path d="M3 5h14M3 10h8M3 15h14"/><path d="M14 8.5l2 2 2-2" stroke-width="1.4"/></svg>';
    if (li.dataset.w) { wi.title = "Word-by-word meaning"; wi.setAttribute("aria-label", "Word-by-word meaning"); }
    else { wi.setAttribute("aria-disabled", "true"); wi.title = "No word-by-word meaning for this verse"; wi.setAttribute("aria-label", "No word-by-word meaning for this verse"); }
    vh.appendChild(wi);
    var body = li.querySelector(".body"); body.insertBefore(vh, body.firstChild);

    var d = el("div", "details", { id: "d" + n, hidden: "" }), dl = el("dl");
    function row(k, v, code) {
      var dt = el("dt"); dt.textContent = k; var dd = el("dd");
      if (code) { var c = el("code"); c.textContent = v; dd.appendChild(c); } else dd.textContent = v;
      dl.appendChild(dt); dl.appendChild(dd);
    }
    row("Verse", ref);
    if (li.dataset.meter) row("Metre", li.dataset.meter);
    (li.dataset.ids || "").split("; ").filter(Boolean).forEach(function (x) { var i = x.indexOf(" "); row(x.slice(0, i), x.slice(i + 1), true); });
    if (li.dataset.cwl) {                                  // link to the same verse in the other text
      var parts = li.dataset.cwl.split("|"), root = (document.querySelector(".reader") || {}).dataset.wroot || "";
      var dtc = el("dt"); dtc.textContent = parts[0]; dtc.setAttribute("data-ed", li.dataset.cwo);
      var ddc = el("dd"); ddc.setAttribute("data-ed", li.dataset.cwo);
      parts[1].split(";").forEach(function (x, i) {
        var kv = x.split("="), a = el("a"); a.textContent = kv[0]; a.href = root + kv[1];
        if (i) ddc.appendChild(document.createTextNode(", ")); ddc.appendChild(a);
      });
      dl.appendChild(dtc); dl.appendChild(ddc);
    }
    d.appendChild(dl);
    if (li.dataset.w) { var wb = el("button", "wbw-btn", { type: "button", "aria-expanded": "false" }); wb.textContent = "Word by word"; d.appendChild(wb); }
    [["chant-here", "Chant from here"], ["cite", "Copy citation"]].forEach(function (x) {
      var bt = el("button", x[0], { type: "button" }); bt.textContent = x[1]; d.appendChild(bt);
    });
    d.appendChild(el("span", "cite-ok", { role: "status" }));
    body.appendChild(d);
  });
})();
