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

  function offList() { return Array.isArray(prefs.off) ? prefs.off : ["ce"]; }   // Baroda text is optional, off until chosen
  function apply() {
    root.dataset.script = prefs.script || "knda";
    if (prefs.savarna) root.dataset.savarna = "1"; else delete root.dataset.savarna;
    if (prefs.scan) root.dataset.scan = "1"; else delete root.dataset.scan;
    if (prefs.size) root.dataset.size = prefs.size; else delete root.dataset.size;
    root.dataset.off = offList().join(" ");
    document.querySelectorAll("[data-ed-toggle]").forEach(function (i) { i.checked = offList().indexOf(i.dataset.edToggle) < 0; });
    var note = document.getElementById("off-note");
    if (note) note.hidden = offList().indexOf(document.body.dataset.ed) < 0 || !document.body.dataset.ed;
    // search: pick an enabled edition
    var es = document.getElementById("ed");
    if (es && offList().indexOf(es.value) >= 0) { var ok = [].filter.call(es.options, function (o) { return offList().indexOf(o.value) < 0; })[0]; if (ok) es.value = ok.value; }
    root.dataset.theme = prefs.theme || "light";
    document.querySelectorAll("[data-pref-theme]").forEach(function (i) { i.checked = (prefs.theme || "light") === i.value; });
    var tc = document.querySelector('meta[name=theme-color]');
    if (tc) tc.content = (prefs.theme === "dark" || (prefs.theme === "system" && window.matchMedia && matchMedia("(prefers-color-scheme: dark)").matches)) ? "#14171E" : "#1B2358";
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
  window.VRPrefs = {
    off: function () { return Array.isArray(prefs.off) ? prefs.off : ["ce"]; },
    get: function () { return prefs; },
    set: function (k, v) { prefs[k] = v; save(prefs); apply(); }
  };

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
    if (e.target.closest("[data-ed-on]")) { prefs.off = offList().filter(function (x) { return x !== document.body.dataset.ed; }); save(prefs); apply(); return; }
    var w = e.target.closest(".wbw-btn");
    if (w) { toggleWords(w.closest(".verse")); return; }
    var c = e.target.closest(".cite");
    if (c) { copyCitation(c); return; }
    var opts = document.querySelector(".opts[open]");
    if (opts && !e.target.closest(".opts")) opts.open = false;
  });
  document.addEventListener("change", function (e) {
    var t = e.target;
    if (t.dataset.edToggle) {
      var off = offList().filter(function (x) { return x !== t.dataset.edToggle; });
      if (!t.checked) off.push(t.dataset.edToggle);
      if (off.length >= document.querySelectorAll("[data-ed-toggle]").length) { t.checked = true; return; }   // keep at least one text
      prefs.off = off; save(prefs); apply(); return;
    }
    if (t.dataset.pref) { prefs[t.dataset.pref] = t.checked; save(prefs); apply(); }
    if (t.hasAttribute("data-pref-theme")) { prefs.theme = t.value === "light" ? "" : t.value; save(prefs); apply(); }
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
      '<a href="' + root_href() + 'about/#words">About this data</a></p>' +
      (box.dataset.note ? '<p class="wbw-note wbw-warn">' + esc(NOTES[box.dataset.note]) + '</p>' : "");
    box.dataset.script = sc;
  }
  function root_href() { return document.querySelector(".reader").dataset.root || "../../../"; }
  var wordsCache = {};
  function loadWords(u) { return wordsCache[u] || (wordsCache[u] = loadJSON(u)); }
  var NOTES = {
    variant: "This verse reads differently from the Baroda verse analysed here, so some words may not match.",
    partial: "Only part of this verse is in the Baroda verse analysed here, so some words may not match.",
    regrouped: "The lines of this verse are grouped differently in the Baroda text, so some words may not match."
  };
  function toggleWords(li) {
    var src = li.querySelector(".vtext"), box = li.querySelector(".wbw"), btn = li.querySelector(".wbw-btn");
    if (!src || !src.dataset.words || !box) return;
    var open = !box.hidden;
    box.hidden = open; src.setAttribute("aria-expanded", open ? "false" : "true");
    if (btn) btn.setAttribute("aria-expanded", open ? "false" : "true");
    li.classList.toggle("wbw-on", !open);
    if (open) return;
    var wurl = src.dataset.words === "words.json" ? "words.json" : root_href() + src.dataset.words;
    var vnum = src.dataset.vn;
    box.dataset.words = wurl; box.dataset.vn = vnum; box.dataset.note = src.dataset.wnote || "";
    Promise.all([loadWords(wurl), grammarData || loadJSON(root_href() + "data/grammar.json")]).then(function (r) {
      wordsData = r[0]; grammarData = r[1];
      var units = wordsData.verses[vnum];
      if (units) renderWords(box, units); else box.textContent = "No word analysis for this verse.";
    }, function () { box.textContent = "Could not load the word analysis."; });
  }
  // click the verse text (not while selecting text, not on links) or press Enter / Space on it
  document.addEventListener("click", function (e) {
    var src = e.target.closest(".vtext[data-words]");
    if (!src || e.target.closest("a")) return;
    var sel = window.getSelection && String(window.getSelection());
    if (sel && sel.length > 0) return;
    toggleWords(src.closest(".verse"));
  });
  document.addEventListener("keydown", function (e) {
    var src = e.target.closest && e.target.closest(".vtext[data-words]");
    if (src && e.target === src && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); toggleWords(src.closest(".verse")); }
  });
  document.addEventListener("prefs-changed", function () {
    document.querySelectorAll(".wbw:not([hidden])").forEach(function (box) {
      if (!box.dataset.words) return;
      loadWords(box.dataset.words).then(function (w) {
        wordsData = w; var units = w.verses[box.dataset.vn];
        if (units) renderWords(box, units);
      });
    });
  });

  // Open the details of a verse linked by anchor.
  function openFromHash() {
    var m = /^#v(\d+)$/.exec(location.hash);
    if (!m) return;
    var el = document.getElementById("v" + m[1]);
    if (el && root.dataset.filter === "shared" && el.classList.contains("v-absent")) { prefs.filter = ""; apply(); }
  }
  // ---- Saved list ("My"): sargas and single verses, kept on this device ----
  var SAVED = "vr.saved";
  function savedList() { try { return JSON.parse(localStorage.getItem(SAVED) || "[]"); } catch (e) { return []; } }
  function setSaved(l) { try { localStorage.setItem(SAVED, JSON.stringify(l)); } catch (e) { /* storage unavailable */ } }
  window.VRSaved = {
    list: savedList,
    has: function (id) { return savedList().some(function (x) { return x.id === id; }); },
    toggle: function (item) {
      var l = savedList(), i = l.findIndex(function (x) { return x.id === item.id; });
      if (i >= 0) l.splice(i, 1); else { item.ts = Date.now(); l.unshift(item); }
      setSaved(l); return i < 0;
    }
  };
  function paintSave() {
    document.querySelectorAll("[data-save]").forEach(function (b) {
      var on = window.VRSaved.has(b.dataset.save);
      b.setAttribute("aria-pressed", on ? "true" : "false");
      b.firstChild.nodeValue = on ? "★ " : "☆ ";
      b.querySelector("span").textContent = on ? "Saved" : "Save";
    });
  }
  document.addEventListener("click", function (e) {
    var b = e.target.closest("[data-save]");
    if (!b) return;
    var rd = document.querySelector(".reader");
    window.VRSaved.toggle({ id: b.dataset.save, href: b.dataset.save, kind: "sarga",
      titles: rd ? { knda: rd.dataset.titleKnda, deva: rd.dataset.titleDeva, iast: rd.dataset.titleIast } : {},
      label: rd ? rd.dataset.src : b.dataset.save });
    paintSave();
  });
  paintSave();
  // ---- offline app: service worker and the reload prompt ----
  var ROOT = document.body.dataset.root || "";
  window.VRToast = function (msg, actions) {
    var t = document.querySelector(".toast") || document.body.appendChild(Object.assign(document.createElement("div"), { className: "toast", role: "status" }));
    t.textContent = msg + " ";
    (actions || []).forEach(function (x) { var b = document.createElement("button"); b.type = "button"; b.textContent = x[0]; b.addEventListener("click", function () { t.remove(); x[1](); }); t.appendChild(b); });
    return t;
  };
  if ("serviceWorker" in navigator && (location.protocol === "https:" || location.hostname === "localhost")) {
    var hadController = !!navigator.serviceWorker.controller;
    navigator.serviceWorker.register(ROOT + "sw.js", { updateViaCache: "none" }).catch(function () { /* offline use unavailable */ });
    navigator.serviceWorker.addEventListener("controllerchange", function () {
      if (hadController) window.VRToast("A new version is ready.", [["Reload", function () { location.reload(); }]]);
      hadController = true;
    });
  }
  apply();
  openFromHash();
  window.addEventListener("hashchange", openFromHash);
})();
