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
    var w = e.target.closest(".wbw-btn");
    if (w) { toggleWords(w); return; }
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

  // ---- Word by word (Critical Edition only) --------------------------------
  var wordsData = null, grammarData = null;
  function loadJSON(url) { return fetch(url).then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); }); }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function lab(table, key, en) { var o = grammarData[table] && grammarData[table][key]; return o ? (en ? o.en : o.kn) : key; }
  function scriptNow() { var s = root.dataset.script || "knda"; return /^(knda|deva|iast)$/.test(s) ? s : (s === "knda-deva" ? "knda" : "knda"); }

  function describe(t, en) {
    var parts = [];
    if (t.pos) parts.push(lab("pos", t.pos, en));
    if (t.f) parts.push(lab("f", t.f, en));
    if (t.g) parts.push(lab("g", t.g, en));
    if (t.c) parts.push(lab("c", t.c, en));
    if (t.n) parts.push(lab("n", t.n, en));
    if (t.p) parts.push(lab("p", t.p, en));
    if (t.l) parts.push(lab("l", t.l, en));
    if (t.comp) parts.push(grammarData.comp[en ? "en" : "kn"]);
    return parts.join(" · ");
  }
  function renderWords(box, units) {
    var T = window.Translit, sc = scriptNow(), en = sc === "iast", sav = !!prefs.savarna;
    var h = '<ol class="wbw-list">';
    units.forEach(function (u) {
      var word = u.f.map(function (f) { return T.render(f, sc, sav); }).join("-");
      var lem = u.l.map(function (l) { return T.render(l, "deva", false); }).join("-");
      var gl = u.l.map(function (l) { return wordsData.gloss[l]; }).filter(Boolean);
      h += '<li><span class="w">' + esc(word) + '</span>' +
        '<span class="lem" lang="sa-Deva">' + esc(lem) + '</span>' +
        '<span class="gr">' + esc(describe(u.t, en)) + '</span>' +
        (gl.length ? '<span class="mean" lang="en">' + gl.map(esc).join(" + ") + '</span>' : "") + '</li>';
    });
    box.innerHTML = h + '</ol>' +
      '<p class="wbw-note">Analysis: Digital Corpus of Sanskrit. Meanings are dictionary senses of each base word, chosen automatically (Apte, 1890, and project notes); they are not a translation of this verse. ' +
      '<a href="' + root_href() + 'about/#words">About this data</a></p>';
    box.dataset.script = sc;
  }
  function root_href() { return document.querySelector(".reader").dataset.root || "../../../"; }
  function toggleWords(btn) {
    var box = btn.parentNode.querySelector(".wbw"), open = btn.getAttribute("aria-expanded") === "true";
    btn.setAttribute("aria-expanded", open ? "false" : "true");
    box.hidden = open;
    if (open) return;
    var vnum = btn.closest(".verse").id.slice(1);
    Promise.all([wordsData || loadJSON("words.json"), grammarData || loadJSON(root_href() + "data/grammar.json")]).then(function (r) {
      wordsData = r[0]; grammarData = r[1];
      var units = wordsData.verses[vnum];
      if (units) renderWords(box, units); else box.textContent = "No word analysis for this verse.";
    }, function () { box.textContent = "Could not load the word analysis."; });
  }
  document.addEventListener("prefs-changed", function () {
    if (!wordsData) return;
    document.querySelectorAll(".wbw:not([hidden])").forEach(function (box) {
      var units = wordsData.verses[box.closest(".verse").id.slice(1)];
      if (units) renderWords(box, units);
    });
  });

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
