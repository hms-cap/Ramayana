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
  function marks(sc, ref, n) {
    if (sc === "iast") return null;
    return { mid: NB + "।", last: NB + "॥" + NB + T.digits(ref, sc) + NB + "॥" };
  }
  function script(slp, sc, ref, sav) {
    var m = marks(sc, ref);
    return slp.map(function (l, i) { return T.render(l, sc, sav) + (i === slp.length - 1 ? m.last : m.mid); });
  }
  function block(sc, lang, slp, ref) {
    var d = el("div", "t t-" + sc, { lang: lang });
    var base = script(slp, sc, ref, false), alt = script(slp, sc, ref, true), same = base.join("|") === alt.join("|");
    function para(lines, cls) {
      var p = el("p", cls || ""); if (!cls) p.removeAttribute("class");
      lines.forEach(function (t) { var s = el("span", "ln"); s.textContent = t; p.appendChild(s); });
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
    host.insertBefore(block("knda", "sa-Knda", slp, ref), iast);
    host.insertBefore(block("deva", "sa-Deva", slp, ref), iast);

    var side = el("div", "side"), b = el("button", "vnum", { type: "button", "aria-expanded": "false", "aria-controls": "d" + n, title: "Verse details" });
    [["knda", T.digits(n, "knda")], ["deva", T.digits(n, "deva")], ["iast", n]].forEach(function (x) {
      var s = el("span", "n-" + x[0]); s.textContent = x[1]; b.appendChild(s);
    });
    side.appendChild(b); li.insertBefore(side, li.firstChild);

    var d = el("div", "details", { id: "d" + n, hidden: "" }), dl = el("dl");
    function row(k, v, code) {
      var dt = el("dt"); dt.textContent = k; var dd = el("dd");
      if (code) { var c = el("code"); c.textContent = v; dd.appendChild(c); } else dd.textContent = v;
      dl.appendChild(dt); dl.appendChild(dd);
    }
    row("Verse", ref);
    if (li.dataset.meter) row("Metre", li.dataset.meter);
    (li.dataset.ids || "").split("; ").filter(Boolean).forEach(function (x) { var i = x.indexOf(" "); row(x.slice(0, i), x.slice(i + 1), true); });
    d.appendChild(dl);
    [["chant-here", "Chant from here"], ["cite", "Copy citation"]].forEach(function (x) {
      var bt = el("button", x[0], { type: "button" }); bt.textContent = x[1]; d.appendChild(bt);
    });
    d.appendChild(el("span", "cite-ok", { role: "status" }));
    li.querySelector(".body").appendChild(d);
  });
})();
