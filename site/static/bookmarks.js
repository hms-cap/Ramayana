/* Bookmarks: a ☆ on every verse, a strip of this text's bookmarks at the top of reading pages, and a list sheet.
   Stored in the same list as "Saved" (VRSaved, localStorage "vr.saved"); a bookmark belongs to the text its address starts with
   ("mbh/", "gita/", otherwise the Rāmāyaṇa). Kinds: "verse" (address ends #vN) and "sarga" (the whole page). */
(function () {
  "use strict";
  var T = window.Translit, P = window.VRPrefs, S = window.VRSaved;
  if (!S || !T) return;
  var B = document.body.dataset, ROOT = B.root || "", WORK = B.work;
  var SCR = ["knda", "deva", "iast"];
  var WORKS = {
    ram: { en: "Rāmāyaṇa", sub: ["ಸರ್ಗ", "सर्गः", "Sarga"] },
    mbh: { en: "Mahābhārata", sub: ["ಅಧ್ಯಾಯ", "अध्यायः", "Adhyāya"] },
    gita: { en: "Gītā", sub: ["ಅಧ್ಯಾಯ", "अध्यायः", "Adhyāya"] }
  };
  var ED = { vu: "Traditional text", ce: "Critical text" };
  function sc() { var s = (P.get().script) || "knda"; return SCR.indexOf(s) >= 0 ? s : "knda"; }
  function si() { var s = sc(); return s === "knda" ? 0 : s === "deva" ? 1 : 2; }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function langOf(x) { return x === "knda" ? "sa-Knda" : x === "deva" ? "sa-Deva" : "sa-Latn"; }
  function digits(n) { return sc() === "iast" ? String(n) : T.digits(String(n), sc()); }

  // ---- what a bookmark is ----
  var HREF = /^(?:(mbh|gita)\/)?(vu|ce)\/(\d+)\/(\d+)\/(?:#v(\d+))?$/;
  function info(it) {
    var m = HREF.exec(it.href || ""); if (!m) return null;
    return { w: m[1] || "ram", ed: m[2], k: +m[3], s: +m[4], v: m[5] ? +m[5] : 0 };
  }
  function all(w) {
    return S.list().map(function (it) { var i = info(it); return i ? { it: it, i: i } : null; })
      .filter(function (x) { return x && x.i.w === w; });
  }
  var units = null;
  function loadUnits() {
    if (!units) units = fetch(ROOT + "data/units.json").then(function (r) { return r.json(); }).catch(function () { return {}; });
    return units;
  }
  function unitName(U, w, k) { var u = U[w] && U[w][k]; return u ? u[si()] : ""; }

  // ---- ☆ on each verse ----
  var base = (document.querySelector("[data-save]") || {}).dataset;
  base = base && base.save;
  function verseItem(li) {
    var n = li.id.slice(1), ln = li.querySelector(".t-iast .ln"), m = HREF.exec(base + "#v" + n);
    var slp = ln ? T.iastToSlp1(ln.textContent.replace(/ \|.*$/, "").trim()) : "";
    return { id: base + "#v" + n, href: base + "#v" + n, kind: "verse", slp: [slp], label: WORKS[m[1] || "ram"].en + " " + li.dataset.ref };
  }
  function addButtons() {
    if (!base) return;
    document.querySelectorAll(".verses > .verse .vh").forEach(function (vh) {
      if (vh.querySelector(".bm-ic")) return;
      var b = document.createElement("button"); b.type = "button"; b.className = "bm-ic"; b.innerHTML = "☆";
      b.title = "Bookmark this verse"; b.setAttribute("aria-label", "Bookmark this verse"); b.setAttribute("aria-pressed", "false");
      vh.appendChild(b);
    });
    paintButtons();
  }
  function paintButtons() {
    document.querySelectorAll(".bm-ic").forEach(function (b) {
      var li = b.closest(".verse"), on = S.has(base + "#" + li.id);
      b.setAttribute("aria-pressed", on ? "true" : "false"); b.textContent = on ? "★" : "☆";
      b.title = on ? "Remove bookmark" : "Bookmark this verse";
    });
  }
  document.addEventListener("click", function (e) {
    var b = e.target.closest(".bm-ic"); if (!b) return;
    var li = b.closest(".verse"); S.toggle(verseItem(li));
  });

  // ---- the strip ----
  function here(x) {
    if (!base) return false;
    var m = info({ href: base });
    if (!m || x.i.w !== m.w || x.i.ed !== m.ed || x.i.k !== m.k || x.i.s !== m.s) return false;
    return x.i.v ? location.hash === "#v" + x.i.v : true;
  }
  function chipText(U, x, curK) {
    var i = x.i, t = i.v ? digits(i.s) + "." + digits(i.v) : WORKS[i.w].sub[si()] + " " + digits(i.s);
    return (i.w !== "gita" && i.k !== curK ? unitName(U, i.w, i.k) + " " : "") + t;
  }
  function lastOf(w) {
    var key = { mbh: "vr.last.mbh", gita: "vr.last.gita" }[w] || "vr.last", l = null;
    try { l = JSON.parse(localStorage.getItem(key) || "null"); } catch (e) { /* ignore */ }
    return l && l.href ? l : null;
  }
  function paintBars() {
    var bars = document.querySelectorAll("[data-bmbar]"); if (!bars.length) return;
    var list = WORK ? all(WORK).sort(function (a, b) { return (b.it.ts || 0) - (a.it.ts || 0); }) : [];
    var cur = base ? (info({ href: base }) || {}).k : 0;
    loadUnits().then(function (U) {
      bars.forEach(function (bar) {
        var cont = bar.hasAttribute("data-continue"), last = cont ? lastOf(WORK) : null, html = "";
        if (last) {
          var tt = (last.titles && last.titles[sc()]) || last.src;
          html += '<a class="bm-cont" href="' + ROOT + esc(last.href.replace(/^\/[^/]*\//, "").replace(/^\//, "")) + '"><span aria-hidden="true">▶</span><span><b lang="' + langOf(sc()) + '">Continue · ' + esc(tt) + '</b><small>' + esc(last.src) + ' ' + esc(last.v || "") + '</small></span></a>';
        }
        if (list.length) {
          html += '<div class="bm-box"><div class="bm-t"><b aria-hidden="true">★</b> Bookmarks <span class="bm-n">' + list.length + '</span><button type="button" class="bm-all" data-open-sheet="bmsheet" aria-haspopup="dialog">See all ›</button></div><div class="bm-chips">' +
            list.slice(0, cont ? 8 : 5).map(function (x) {
              return '<a class="bm-chip' + (here(x) ? " now" : "") + '" href="' + ROOT + esc(x.it.href) + '" lang="' + langOf(sc()) + '"' + (here(x) ? ' aria-current="true"' : "") + ">" + esc(chipText(U, x, cur)) + "</a>";
            }).join("") + "</div></div>";
        }
        bar.innerHTML = html; bar.hidden = !html;
      });
    });
  }
  function badge() {
    var n = S.list().length;
    document.querySelectorAll(".badge-n").forEach(function (b) { b.hidden = !n; b.textContent = n; });
  }

  // ---- the list sheet ----
  var sheet = document.getElementById("bmsheet"), tab = WORKS[WORK] ? WORK : "ram";
  function paintSheet() {
    if (!sheet) return;
    var list = document.getElementById("bm-list");
    sheet.querySelectorAll("[data-bm-work]").forEach(function (b) {
      var n = all(b.dataset.bmWork).length;
      b.setAttribute("aria-selected", b.dataset.bmWork === tab ? "true" : "false"); b.querySelector("b").textContent = n || "";
    });
    var items = all(tab).sort(function (a, b) { return a.i.k - b.i.k || a.i.s - b.i.s || a.i.v - b.i.v || (a.i.ed < b.i.ed ? -1 : 1); });
    document.getElementById("bm-empty").hidden = items.length > 0;
    loadUnits().then(function (U) {
      var out = "", prev = null;
      items.forEach(function (x) {
        var i = x.i, it = x.it;
        if (tab !== "gita" && i.k !== prev) { out += '<div class="bm-g" lang="' + langOf(sc()) + '">' + esc(unitName(U, tab, i.k)) + "</div>"; prev = i.k; }
        var main = i.v
          ? '<span class="t-' + sc() + '" lang="' + langOf(sc()) + '">' + esc(T.render((it.slp || [""])[0], sc(), !!P.get().savarna)) + "</span>"
          : '<span lang="' + langOf(sc()) + '">' + esc((it.titles && it.titles[sc()]) || (WORKS[tab].sub[si()] + " " + digits(i.s))) + "</span>";
        var small = (i.v ? "Verse " + i.s + "." + i.v : WORKS[tab].sub[2] + " " + i.s + " (whole)") + " · " + ED[i.ed];
        out += '<div class="bm-it"><a href="' + ROOT + esc(it.href) + '" data-bm-go><span class="bm-tx">' + main + "<small>" + esc(small) + '</small></span></a><button type="button" class="bm-x" data-bm-del="' + esc(it.id) + '" aria-label="Remove bookmark">✕</button></div>';
      });
      list.innerHTML = out;
    });
  }
  document.addEventListener("click", function (e) {
    var t;
    if ((t = e.target.closest("[data-open-sheet=bmsheet]"))) { tab = WORKS[WORK] ? WORK : tab; paintSheet(); return; }
    if (!sheet || sheet.hidden) return;
    if ((t = e.target.closest("[data-bm-work]"))) { tab = t.dataset.bmWork; paintSheet(); return; }
    if ((t = e.target.closest("[data-bm-del]"))) {
      var it = S.list().filter(function (x) { return x.id === t.dataset.bmDel; })[0]; if (it) S.toggle(it); return;
    }
    if (e.target.closest("[data-bm-go]") && window.VRSheet) window.VRSheet.close();
  });
  function all_() { paintButtons(); paintBars(); paintSheet(); badge(); }
  document.addEventListener("saved-changed", all_);
  document.addEventListener("prefs-changed", function () { paintBars(); paintSheet(); });
  window.addEventListener("hashchange", paintBars);
  window.addEventListener("storage", function (e) { if (e.key === "vr.saved") all_(); });
  addButtons(); paintBars(); badge();
})();
