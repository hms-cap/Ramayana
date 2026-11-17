/* In-app Back / Forward (v0.23).
   The tab keeps a trail of the app pages it has shown (sessionStorage "vr.trail": {e: [{id, u, t}], i}), one per
   browser history entry; history.state.vrn holds the entry's id, so Back/Forward through the browser land on the
   right place in the trail. Moves that replace the page (Previous/Next, jump sheet, edition switch, crumbs, the
   works switch) replace the trail entry too, so the trail never fills up with sideways steps.
   ‹ = one step back on the trail (history.back) — or, with nothing behind it (a shared link, a fresh launch), the
   parent page, replacing this one. › = forward, shown only when there is somewhere to go. Long-press ‹ (or
   right-click) lists the last few places.  window.VRNav: {replace(url), canBack(), canFwd(), back(), trail()}. */
(function () {
  "use strict";
  var KEY = "vr.trail", RKEY = "vr.trail.rep", LKEY = "vr.trail.len", MAX = 40;
  var H = window.history, origReplace = H.replaceState, origPush = H.pushState;
  function load() { try { var t = JSON.parse(sessionStorage.getItem(KEY) || "null"); if (t && Array.isArray(t.e)) return t; } catch (e) { /* ignore */ } return { e: [], i: -1 }; }
  function save(t) { try { sessionStorage.setItem(KEY, JSON.stringify(t)); } catch (e) { /* ignore */ } }
  function here() { return location.pathname + location.search; }
  function label() {
    var b = document.body;
    if (b.classList.contains("page-home")) return "Home";
    var t = (document.title || "").split(" — ")[0].split(" · ")[0].trim();
    return t.length > 28 ? t.slice(0, 27) + "…" : t;
  }
  function newId() { return Date.now().toString(36) + Math.random().toString(36).slice(2, 6); }
  var st = H.state && typeof H.state === "object" ? H.state : null;
  var trail = load(), id = st && st.vrn, pos = -1, k;
  if (id) for (k = 0; k < trail.e.length; k++) if (trail.e[k].id === id) { pos = k; break; }
  if (pos >= 0) {                                   // back / forward / reload onto a known entry
    trail.i = pos; trail.e[pos].u = here(); trail.e[pos].t = label();
  } else {
    var rep = false; try { rep = sessionStorage.getItem(RKEY) === "1"; sessionStorage.removeItem(RKEY); } catch (e) { /* ignore */ }
    if (!rep) {                                     // a replace we were not told about: history did not grow
      var lastLen = 0; try { lastLen = +sessionStorage.getItem(LKEY) || 0; } catch (e) { /* ignore */ }
      var ref = ""; try { ref = document.referrer && new URL(document.referrer).origin === location.origin ? 1 : ""; } catch (e) { /* ignore */ }
      rep = !!ref && trail.i === trail.e.length - 1 && trail.i >= 0 && lastLen && H.length === lastLen;
    }
    id = newId();
    var entry = { id: id, u: here(), t: label() };
    var fromApp = false; try { fromApp = !!document.referrer && new URL(document.referrer).origin === location.origin; } catch (e) { /* ignore */ }
    if (!fromApp && !rep) trail = { e: [], i: -1 };  // came from outside: a new trail
    if (rep && trail.i >= 0) trail.e[trail.i] = entry;
    else { trail.e = trail.e.slice(0, trail.i + 1); trail.e.push(entry); trail.i = trail.e.length - 1; }
    if (trail.e.length > MAX) { var cut = trail.e.length - MAX; trail.e = trail.e.slice(cut); trail.i -= cut; }
    try { origReplace.call(H, Object.assign({}, st || {}, { vrn: id }), ""); } catch (e) { /* ignore */ }
  }
  save(trail);
  // keep the entry id when other scripts replace or push state on this page
  H.replaceState = function (s, t, u) { if (s == null || typeof s === "object") s = Object.assign({}, s || {}, { vrn: id }); return origReplace.call(H, s, t, u); };
  H.pushState = function (s, t, u) { if (s == null || typeof s === "object") s = Object.assign({}, s || {}, { vrn: id }); return origPush.call(H, s, t, u); };
  window.addEventListener("pagehide", function () { try { sessionStorage.setItem(LKEY, String(H.length)); } catch (e) { /* ignore */ } });

  function canBack() { return trail.i > 0; }
  function canFwd() { return trail.i < trail.e.length - 1; }
  function replace(url) { try { sessionStorage.setItem(RKEY, "1"); } catch (e) { /* ignore */ } location.replace(url); }
  var backA = document.querySelector("a.back[data-back]"), fwdB = document.querySelector("button.fwd");
  function back() {
    if (canBack()) H.back();
    else if (backA) replace(backA.dataset.up || backA.href);
  }
  function upLabel() {   // with nothing behind us, ‹ goes up: name the parent page
    var u = backA.getAttribute("data-up") || "", wr = document.body.dataset.wroot || "";
    if (/(^|\/)read\/$/.test(u)) return "Read";
    if (u === wr || u === "" || /^(\.\.\/)+$/.test(u) && !document.querySelector(".crumbs a")) return "Home";
    var c = document.querySelectorAll(".crumbs a"); return c.length ? (c[c.length - 1].innerText || c[c.length - 1].textContent).trim() : "";
  }
  function paint() {
    if (backA && document.body.classList.contains("page-home")) backA.hidden = !canBack();
    if (backA) {
      var prev = canBack() ? trail.e[trail.i - 1] : null, to = backA.querySelector(".back-to");
      var name = prev ? prev.t : (backA.dataset.upLabel || upLabel());
      if (to) to.textContent = name;
      backA.setAttribute("aria-label", name ? "Back to " + name : "Back");
    }
    if (fwdB) { fwdB.hidden = !canFwd(); if (canFwd()) fwdB.setAttribute("aria-label", "Forward to " + trail.e[trail.i + 1].t); }
  }
  paint();
  // restored from the back/forward cache: this page's place in the trail is where the user is now
  window.addEventListener("pageshow", function (e) {
    if (!e.persisted) return;
    trail = load();
    for (var j = 0; j < trail.e.length; j++) if (trail.e[j].id === id) { trail.i = j; break; }
    save(trail); paint();
  });

  // ‹ and ›; others (the stotra bar) may handle ‹ first and stop the event
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("a.back[data-back]");
    if (a && !e.defaultPrevented && e.button === 0 && !e.metaKey && !e.ctrlKey && !e.shiftKey) {
      if (held) { e.preventDefault(); held = false; return; }
      e.preventDefault(); back(); return;
    }
    if (e.target.closest && e.target.closest("button.fwd")) { e.preventDefault(); if (canFwd()) H.forward(); return; }
    var m = e.target.closest && e.target.closest("[data-trail-go]");
    if (m) { e.preventDefault(); var n = +m.dataset.trailGo - trail.i; closeMenu(); if (n) H.go(n); return; }
    // sideways moves replace the page: crumbs and the works switch (Previous/Next and the jump sheet already do)
    var r = e.target.closest && e.target.closest(".crumbs a[href], .workchips a[href]");
    if (r && !e.defaultPrevented && e.button === 0 && !e.metaKey && !e.ctrlKey && !e.shiftKey && !r.target) {
      e.preventDefault(); replace(r.href); return;
    }
    var dr = e.target.closest && e.target.closest("a[data-replace]");
    if (dr) { try { sessionStorage.setItem(RKEY, "1"); } catch (x) { /* ignore */ } }
  }, false);

  // long-press / right-click on ‹: the last few places
  var timer = null, held = false, menu = null;
  function closeMenu() { if (menu) { menu.remove(); menu = null; } }
  function openMenu() {
    closeMenu();
    if (!backA || trail.i < 1) return;
    var items = [];
    for (var j = trail.i - 1; j >= 0 && items.length < 6; j--) items.push('<button type="button" role="menuitem" data-trail-go="' + j + '">' + esc(trail.e[j].t) + "</button>");
    menu = document.createElement("div");
    menu.className = "trail-menu"; menu.setAttribute("role", "menu"); menu.setAttribute("aria-label", "Recent places");
    menu.innerHTML = items.join("");
    document.body.appendChild(menu);
    var r = backA.getBoundingClientRect();
    menu.style.top = Math.round(r.bottom + 6) + "px"; menu.style.left = Math.max(8, Math.round(r.left)) + "px";
    var f = menu.querySelector("button"); if (f) f.focus();
  }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  if (backA) {
    backA.addEventListener("pointerdown", function () { held = false; clearTimeout(timer); timer = setTimeout(function () { held = true; openMenu(); }, 550); });
    ["pointerup", "pointerleave", "pointercancel"].forEach(function (ev) { backA.addEventListener(ev, function () { clearTimeout(timer); }); });
    backA.addEventListener("contextmenu", function (e) { if (trail.i > 0) { e.preventDefault(); openMenu(); } });
  }
  document.addEventListener("pointerdown", function (e) { if (menu && !menu.contains(e.target) && !(backA && backA.contains(e.target))) closeMenu(); });
  document.addEventListener("keydown", function (e) { if (menu && e.key === "Escape") { closeMenu(); if (backA) backA.focus(); } });

  window.VRNav = { replace: replace, canBack: canBack, canFwd: canFwd, back: back, trail: function () { return trail; } };
})();
