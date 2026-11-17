/* Jump sheet: tap the sarga title to go to any kāṇḍa / sarga of this text without going back up.
   Data: data/units.json (unit names in three scripts) and data/nav.json (sarga numbers per edition and unit).
   The jump replaces the current page in history (like Previous / Next). */
(function () {
  "use strict";
  var btn = document.querySelector(".jump-open");
  var rd = document.querySelector(".reader");
  if (!btn || !rd) return;
  var T = window.Translit, P = window.VRPrefs;
  var B = document.body.dataset, ROOT = B.root || "", WROOT = B.wroot || "", W = B.work || "ram";
  var ED = rd.dataset.edition, K = +rd.dataset.k, S = +(location.pathname.replace(/\/(index\.html)?$/, "").split("/").pop());
  var data = null, el = null, selK = K, opener = null, pushed = false, pending = null;

  function sc() { var s = (P && P.get().script) || "knda"; return s === "deva" || s === "iast" ? s : "knda"; }
  function dig(n) { return sc() === "iast" ? String(n) : T.digits(String(n), sc()); }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function load() {
    if (!data) data = Promise.all([fetch(ROOT + "data/units.json").then(function (r) { return r.json(); }), fetch(ROOT + "data/nav.json").then(function (r) { return r.json(); })])
      .then(function (x) { return { units: x[0][W] || {}, nav: ((x[1][W] || {})[ED]) || {} }; })
      .catch(function (e) { data = null; throw e; });
    return data;
  }
  function list(v) { if (!v) return []; if (v.length === 2 && v[1] - v[0] > 1) { var o = []; for (var i = v[0]; i <= v[1]; i++) o.push(i); return o; } return v; }
  function lastRead() {
    var key = { mbh: "vr.last.mbh", gita: "vr.last.gita" }[W] || "vr.last";
    try { var l = JSON.parse(localStorage.getItem(key) || "null"); return l && l.href; } catch (e) { return null; }
  }

  function paint(d) {
    var si = sc() === "knda" ? 0 : sc() === "deva" ? 1 : 2, keys = Object.keys(d.nav).map(Number).sort(function (a, b) { return a - b; });
    var chips = keys.length > 1 ? '<div class="jp-ks" role="group" aria-label="' + (W === "mbh" ? "Parva" : "Kāṇḍa") + '">' + keys.map(function (k) {
      var u = d.units[k] || [String(k), String(k), String(k)];
      return '<button type="button" data-jk="' + k + '" aria-pressed="' + (k === selK) + '" lang="' + (si === 2 ? "sa-Latn" : "sa") + '">' + esc(u[si]) + "</button>";
    }).join("") + "</div>" : "";
    var last = lastRead();
    var grid = list(d.nav[selK]).map(function (s) {
      var href = WROOT + ED + "/" + selK + "/" + s + "/", cur = selK === K && s === S;
      var lr = last && last.indexOf("/" + ED + "/" + selK + "/" + s + "/") >= 0;
      return '<a href="' + href + '" data-replace' + (cur ? ' aria-current="page"' : "") + (lr ? ' class="lr" title="Last read"' : "") + ">" + (W === "gita" && s === 0 ? "ॐ" : dig(s)) + "</a>";
    }).join("");
    el.querySelector(".jp-body").innerHTML = chips + '<div class="jp-grid">' + grid + "</div>";
    var on = el.querySelector(".jp-ks [aria-pressed=true]"); if (on) on.scrollIntoView({ block: "nearest", inline: "center" });
    var cur = el.querySelector(".jp-grid [aria-current]"); if (cur) cur.scrollIntoView({ block: "center" });
  }
  function open() {
    if (el) return;
    opener = document.activeElement; selK = K;
    el = document.createElement("div");
    el.className = "jp-wrap";
    el.innerHTML = '<div class="jp-dim"></div><section class="jp" role="dialog" aria-modal="true" aria-labelledby="jp-t">' +
      '<div class="jp-grab" aria-hidden="true"></div><header class="jp-h"><h2 id="jp-t">Go to</h2><button type="button" class="jp-x" aria-label="Close">✕</button></header>' +
      '<div class="jp-body"><p class="hint">Loading…</p></div></section>';
    document.body.appendChild(el);
    btn.setAttribute("aria-expanded", "true");
    try { history.pushState({ jump: 1 }, ""); pushed = true; } catch (e) { pushed = false; }
    el.querySelector(".jp-x").focus();
    load().then(paint, function () { el.querySelector(".jp-body").innerHTML = '<p class="hint">Could not load the list. Check your connection.</p>'; });
  }
  function close(fromPop) {
    if (!el) return;
    el.remove(); el = null; btn.setAttribute("aria-expanded", "false");
    if (pushed && !fromPop) { pushed = false; history.back(); }
    pushed = false;
    if (opener && opener.focus) opener.focus();
  }
  btn.addEventListener("click", open);
  document.addEventListener("click", function (e) {
    if (!el) return;
    if (e.target.closest(".jp-x") || e.target.classList.contains("jp-dim")) { close(false); return; }
    var k = e.target.closest("[data-jk]");
    if (k) { selK = +k.dataset.jk; load().then(paint); return; }
    var a = e.target.closest(".jp-grid a");
    if (a) {   // drop the sheet's history entry first, then replace this page: Back still leaves reading in one step
      e.preventDefault(); e.stopPropagation();
      var h = a.href; el.remove(); el = null;
      if (pushed) { pushed = false; pending = h; history.back(); } else (window.VRNav ? VRNav.replace(h) : location.replace(h));
    }
  }, true);
  document.addEventListener("keydown", function (e) { if (el && e.key === "Escape") { e.preventDefault(); close(false); } });
  window.addEventListener("popstate", function () {
    if (pending) { var h = pending; pending = null; (window.VRNav ? VRNav.replace(h) : location.replace(h)); return; }
    if (el) close(true);
  });
})();
