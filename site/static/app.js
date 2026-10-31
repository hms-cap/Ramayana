(function () {
  "use strict";
  var root = document.documentElement;
  var KEY = "vr-prefs";

  function load() { try { return JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) { return {}; } }
  function save(p) { try { localStorage.setItem(KEY, JSON.stringify(p)); } catch (e) { /* storage unavailable */ } }
  var prefs = load();
  // Shareable overrides, e.g. ?script=deva&savarna=1 (applied, not saved)
  try {
    var qp = new URLSearchParams(location.search);
    if (/^(knda|deva|iast|knda-deva|all)$/.test(qp.get("script") || "")) prefs.script = qp.get("script");
    ["savarna", "scan"].forEach(function (k) { if (qp.has(k)) prefs[k] = qp.get(k) === "1"; });
  } catch (e) { /* old browser */ }

  function apply() {
    root.dataset.script = prefs.script || "knda";
    if (prefs.savarna) root.dataset.savarna = "1"; else delete root.dataset.savarna;
    if (prefs.scan) root.dataset.scan = "1"; else delete root.dataset.scan;
    if (prefs.size) root.dataset.size = prefs.size; else delete root.dataset.size;
    if (prefs.filter) root.dataset.filter = prefs.filter; else delete root.dataset.filter;
    document.querySelectorAll("[data-set-script]").forEach(function (b) {
      b.setAttribute("aria-checked", b.dataset.setScript === root.dataset.script ? "true" : "false");
    });
    document.querySelectorAll("[data-pref]").forEach(function (i) { i.checked = !!prefs[i.dataset.pref]; });
    document.querySelectorAll("[data-pref-size]").forEach(function (i) { i.checked = (prefs.size || "m") === i.value; });
    document.querySelectorAll("[data-set-filter]").forEach(function (b) {
      b.setAttribute("aria-checked", (prefs.filter || "all") === b.dataset.setFilter ? "true" : "false");
    });
    document.dispatchEvent(new CustomEvent("prefs-changed", { detail: prefs }));
  }
  window.VRPrefs = { get: function () { return prefs; } };

  document.addEventListener("click", function (e) {
    var b = e.target.closest("[data-set-script]");
    if (b) { prefs.script = b.dataset.setScript; save(prefs); apply(); return; }
    var f = e.target.closest("[data-set-filter]");
    if (f) { prefs.filter = f.dataset.setFilter === "all" ? "" : f.dataset.setFilter; save(prefs); apply(); return; }
    var v = e.target.closest(".vnum");
    if (v) {
      var d = document.getElementById(v.getAttribute("aria-controls"));
      var open = v.getAttribute("aria-expanded") === "true";
      v.setAttribute("aria-expanded", open ? "false" : "true");
      d.hidden = open;
      if (!open && history.replaceState) history.replaceState(null, "", "#" + v.closest(".verse").id);
      return;
    }
    var c = e.target.closest(".cite");
    if (c) { copyCitation(c); return; }
    var opts = document.querySelector(".opts[open]");
    if (opts && !e.target.closest(".opts")) opts.open = false;
  });
  document.addEventListener("change", function (e) {
    var t = e.target;
    if (t.dataset.pref) { prefs[t.dataset.pref] = t.checked; save(prefs); apply(); }
    if (t.hasAttribute("data-pref-size")) { prefs.size = t.value === "m" ? "" : t.value; save(prefs); apply(); }
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") { var o = document.querySelector(".opts[open]"); if (o) o.open = false; }
  });

  function copyCitation(btn) {
    var verse = btn.closest(".verse"), reader = btn.closest(".reader");
    var url = location.origin + location.pathname + "#" + verse.id;
    var text = reader.dataset.citation + " " + verse.dataset.ref +
      (verse.dataset.ids ? " (" + verse.dataset.ids + ")" : "") + ". " + url;
    var ok = btn.parentNode.querySelector(".cite-ok");
    function done(msg) { ok.textContent = msg; setTimeout(function () { ok.textContent = ""; }, 2500); }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () { done("Copied"); }, function () { done(text); });
    } else { done(text); }
  }

  // Open the details of a verse linked by anchor.
  function openFromHash() {
    var m = /^#v(\d+)$/.exec(location.hash);
    if (!m) return;
    var el = document.getElementById("v" + m[1]);
    if (el && root.dataset.filter === "shared" && el.classList.contains("v-absent")) { prefs.filter = ""; apply(); }
  }
  apply();
  openFromHash();
  window.addEventListener("hashchange", openFromHash);
})();
