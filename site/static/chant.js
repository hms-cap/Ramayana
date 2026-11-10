/* Chant view: a full-screen reading mode for the sarga on the page.
   Built from the verses already in the page (no extra data), so it works
   offline for every page that has been opened. Spec: Chant View design spec. */
(function () {
  "use strict";
  var P = window.VRPrefs, T = window.Translit;
  var SKEY = "vr.chant", LAST = ({ mbh: "vr.last.mbh", gita: "vr.last.gita" }[document.documentElement.dataset.work] || "vr.last"), SCR = ["knda", "deva", "iast"];
  var NB = " ", reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  var view = null;

  function ssGet() { try { return JSON.parse(sessionStorage.getItem(SKEY) || "null"); } catch (e) { return null; } }
  function ssSet(v) { try { if (v) sessionStorage.setItem(SKEY, JSON.stringify(v)); else sessionStorage.removeItem(SKEY); } catch (e) { /* ignore */ } }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }

  function chantScript() {
    var s = P.get().script || "knda";
    return SCR.indexOf(s) >= 0 ? s : "knda";
  }
  function langOf(sc) { return sc === "knda" ? "sa-Knda" : sc === "deva" ? "sa-Deva" : "sa-Latn"; }
  function pick(map, sc) { return map[sc] || ""; }

  /* ---------- the chant model, read from the page ---------- */
  function pageModel() {
    var rd = document.querySelector(".reader[data-chant]");
    if (!rd) return null;
    var sav = !!P.get().savarna;
    var verses = [].map.call(document.querySelectorAll(".verses > .verse"), function (li) {
      var o = { n: li.id.slice(1), label: li.dataset.ref, meter: li.dataset.meter || "", lines: {}, num: {} };
      SCR.forEach(function (sc) {
        var t = li.querySelector(".t-" + sc);
        var p = (sav && t.querySelector(".ps1")) || t.querySelector(".ps0") || t.querySelector("p");
        o.lines[sc] = [].map.call(p.querySelectorAll(".ln"), function (x) {
          return x.textContent.replace(/[\s ]*[।॥|].*$/, "").trim();
        }).filter(Boolean);
        o.num[sc] = li.querySelector(".n-" + sc).textContent.trim();
      });
      return o;
    });
    var prev = document.querySelector(".pager a[rel=prev]"), next = document.querySelector(".pager a[rel=next]");
    function nb(a) { return a ? { href: a.href, label: a.textContent.replace(/\s+/g, " ").trim() } : null; }
    return {
      title: { knda: rd.dataset.titleKnda, deva: rd.dataset.titleDeva, iast: rd.dataset.titleIast },
      src: rd.dataset.src, edition: rd.dataset.edition,
      parts: [{ group: 1, verses: verses }], verses: verses, prev: nb(prev), next: nb(next)
    };
  }
  function dandas(sc) { return sc === "iast" ? { one: "|", two: "||" } : { one: "।", two: "॥" }; }
  function bookVerse(v, sc) {
    var d = dandas(sc);
    return v.lines[sc].join(NB + d.one + " ") + NB + d.two + NB + v.num[sc] + NB + d.two;
  }

  /* ---------- the view ---------- */
  function lastPlace(model, i) {
    var v = model.verses[i]; if (!v) return;
    try {
      localStorage.setItem(LAST, JSON.stringify({ href: location.pathname + "#v" + v.n, v: v.n, of: model.verses.length,
        i: i, titles: model.title, src: model.src, ts: Date.now() }));
    } catch (e) { /* ignore */ }
  }

  function openChant(model, start, cont) {
    if (view) return;
    var sc0 = chantScript();
    var st = { i: Math.max(0, Math.min(model.verses.length - 1, start || 0)), sc: sc0 };
    var pr = P.get();
    var layout = pr.chantLayout === "one" ? "one" : "book";
    var size = Math.max(16, Math.min(40, +pr.chantSize || 23));
    var info = cont ? (ssGet() || { moves: 0, origin: location.href }) : { moves: 0, origin: location.href };
    history.pushState({ ov: 1 }, "", location.href);   // the overlay's own history entry
    ssSet(info);

    var opener = document.activeElement;
    var el = document.createElement("div");
    el.className = "chant"; el.setAttribute("role", "dialog"); el.setAttribute("aria-modal", "true");
    document.body.classList.add("story-open");
    el.innerHTML =
      '<div class="ch-head">' +
      '<button type="button" class="ch-x" aria-label="Close chant view">✕</button>' +
      '<span class="ch-title"></span>' +
      '<div class="ch-seg" role="group" aria-label="Layout"><button type="button" data-l="book" aria-pressed="false"><span lang="sa">पुटम्</span> Page</button><button type="button" data-l="one" aria-pressed="false"><span lang="sa">एकैकम्</span> One</button></div>' +
      '<div class="ch-seg" role="group" aria-label="Text size"><button type="button" data-z="-2" aria-label="Smaller text">A−</button><button type="button" data-z="2" aria-label="Larger text">A+</button></div>' +
      '<div class="ch-seg" role="group" aria-label="Script"><button type="button" data-s="knda" lang="kn" aria-pressed="false">ಅ</button><button type="button" data-s="deva" lang="sa" aria-pressed="false">अ</button><button type="button" data-s="iast" aria-pressed="false">A</button></div>' +
      '<button type="button" class="ch-btn ch-pdf">PDF</button>' +
      '<div class="ch-more"><button type="button" class="ch-btn ch-dots" aria-haspopup="menu" aria-expanded="false" aria-label="More">⋯</button>' +
      '<div class="ch-menu" role="menu" hidden><button type="button" role="menuitem" data-m="print">Print</button><button type="button" role="menuitem" data-m="open">Open verse with word by word</button></div></div>' +
      '</div><div class="ch-body" tabindex="-1"></div><div class="ch-foot" hidden>' +
      '<button type="button" class="ch-prev" aria-label="Previous verse">‹</button><span class="ch-count" aria-live="off"></span><button type="button" class="ch-nextv" aria-label="Next verse">›</button></div>';
    document.body.appendChild(el);
    var body = el.querySelector(".ch-body"), foot = el.querySelector(".ch-foot"), menu = el.querySelector(".ch-menu");
    view = { el: el, model: model, st: st, info: info, wake: null };
    el.setAttribute("aria-label", "Chant view, " + model.title[st.sc]);

    function cards() {
      var h = "";
      [["prev", "Previous", model.prev], ["next", "Next", model.next]].forEach(function (c) {
        if (c[2]) h += '<a class="ch-card" href="' + esc(c[2].href) + '" data-nav="' + c[0] + '"><span>' + c[1] + '</span><b>' + esc(c[2].label) + '</b></a>';
      });
      return '<div class="ch-cards">' + h + (model.next ? "" : '<p class="ch-end" lang="sa">॥ इति ॥</p>') + '</div>';
    }
    function sync() {
      el.style.setProperty("--chz", size + "px");
      el.dataset.sc = st.sc; el.classList.toggle("kn", st.sc === "knda");
      el.querySelector(".ch-title").textContent = model.title[st.sc];
      el.querySelector(".ch-title").lang = langOf(st.sc);
      el.querySelectorAll("[data-l]").forEach(function (b) { b.setAttribute("aria-pressed", b.dataset.l === layout ? "true" : "false"); });
      el.querySelectorAll("[data-s]").forEach(function (b) { b.setAttribute("aria-pressed", b.dataset.s === st.sc ? "true" : "false"); });
    }
    function renderBook() {
      foot.hidden = true; body.removeAttribute("aria-live");
      var inv = "";
      var h = '<article class="ch-page" lang="' + langOf(st.sc) + '">' + inv +
        '<h1>' + esc(model.title[st.sc]) + '</h1><p class="ch-src">(' + esc(model.src) + ')</p>';
      model.parts.forEach(function (part) {
        var vs = part.verses, g = part.group || 1;
        for (var a = 0; a < vs.length; a += g) {
          var chunk = vs.slice(a, a + g).map(function (v, k) { return '<span class="cv" data-i="' + (a + k) + '">' + esc(bookVerse(v, st.sc)) + '</span>'; });
          h += "<p>" + chunk.join(" ") + "</p>";
        }
      });
      body.innerHTML = h + '</article>' + cards();
      body.classList.remove("one");
      var t = body.querySelector('.cv[data-i="' + st.i + '"]');
      if (t) body.scrollTop = Math.max(0, t.offsetTop - 80);
    }
    function renderOne(animate) {
      var v = model.verses[st.i], d = dandas(st.sc);
      foot.hidden = false; body.setAttribute("aria-live", "polite"); body.classList.add("one");
      var last = st.i >= model.verses.length - 1;
      body.innerHTML = '<div class="ch-verse' + (animate && !reduce ? " fade" : "") + '" lang="' + langOf(st.sc) + '">' +
        v.lines[st.sc].map(function (l, k) { return '<span class="ln">' + esc(l) + NB + (k === v.lines[st.sc].length - 1 ? d.two + NB + v.num[st.sc] + NB + d.two : d.one) + '</span>'; }).join("") +
        '</div><p class="ch-ref">' + esc(v.label + (v.meter ? " · " + v.meter : "")) + '</p>' + (last ? cards() : "");
      var n = (st.sc === "iast") ? String(st.i + 1) : T.digits(st.i + 1, st.sc), N = (st.sc === "iast") ? String(model.verses.length) : T.digits(model.verses.length, st.sc);
      el.querySelector(".ch-count").textContent = n + " / " + N;
      el.querySelector(".ch-prev").disabled = st.i === 0;
      el.querySelector(".ch-nextv").disabled = last;
      body.scrollTop = 0;
    }
    function render(animate) { sync(); if (layout === "one") renderOne(animate); else renderBook(); }
    function place(i) { st.i = i; lastPlace(model, i); }
    function step(d) {
      var j = st.i + d;
      if (j < 0) { if (model.prev) go("prev"); return; }
      if (j >= model.verses.length) { if (model.next) go("next"); return; }
      place(j); renderOne(true);
    }
    function go(dir) {
      var nbr = dir === "next" ? model.next : model.prev; if (!nbr) return;
      info.moves = (info.moves || 0) + 1;
      ssSet({ moves: info.moves, origin: info.origin, fromList: info.fromList, resume: dir === "next" ? 0 : "last" });
      teardown(true);
      location.replace(nbr.href);
    }
    // book page: record the place while scrolling
    var scrollT;
    body.addEventListener("scroll", function () {
      if (layout !== "book") return;
      clearTimeout(scrollT);
      scrollT = setTimeout(function () {
        var top = body.getBoundingClientRect().top + 8, found = null;
        [].some.call(body.querySelectorAll(".cv"), function (c) { if (c.getBoundingClientRect().bottom > top) { found = c; return true; } return false; });
        if (found) place(+found.dataset.i);
      }, 120);
    });

    function teardown(keepState) {
      if (!view) return;
      document.removeEventListener("keydown", onKey, true);
      el.remove(); document.body.classList.remove("story-open");
      if (view.wake) { try { view.wake.release(); } catch (e) { /* ignore */ } }
      view = null;
      if (!keepState) ssSet(null);
      if (opener && opener.focus && !keepState) { try { opener.focus(); } catch (e) { /* ignore */ } }
    }
    view.teardown = teardown;
    view.close = function () {                      // ✕ and Esc: go back to where chanting started
      var depth = (info.moves || 0) + 1;
      teardown(false);
      if (info.moves) history.go(-depth); else history.back();
    };
    view.onPop = function () { teardown(false); };  // system Back: closes, lands on the page beneath

    function onKey(e) {
      if (menu && !menu.hidden && e.key === "Escape") { menu.hidden = true; e.stopPropagation(); return; }
      if (e.key === "Escape") { e.preventDefault(); view.close(); return; }
      if (layout === "one") {
        if (e.key === "ArrowRight" || e.key === " " || e.key === "PageDown") { e.preventDefault(); step(1); }
        else if (e.key === "ArrowLeft" || e.key === "PageUp") { e.preventDefault(); step(-1); }
      }
    }
    document.addEventListener("keydown", onKey, true);

    el.addEventListener("click", function (e) {
      var b = e.target.closest("button, a"); if (!b) return;
      if (b.classList.contains("ch-x")) return view.close();
      if (b.dataset.l) { layout = b.dataset.l; P.set("chantLayout", layout); render(false); return; }
      if (b.dataset.z) { size = Math.max(16, Math.min(40, size + +b.dataset.z)); P.set("chantSize", size); el.style.setProperty("--chz", size + "px"); return; }
      if (b.dataset.s) { st.sc = b.dataset.s; P.set("script", st.sc); el.setAttribute("aria-label", "Chant view, " + model.title[st.sc]); render(false); return; }
      if (b.classList.contains("ch-prev")) return step(-1);
      if (b.classList.contains("ch-nextv")) return step(1);
      if (b.classList.contains("ch-dots")) { menu.hidden = !menu.hidden; b.setAttribute("aria-expanded", menu.hidden ? "false" : "true"); return; }
      if (b.dataset.m === "print") { menu.hidden = true; window.VRChant.print(model, st.sc); return; }
      if (b.dataset.m === "open") {
        var n = model.verses[st.i].n; menu.hidden = true; teardown(false);
        history.replaceState(null, "", location.pathname + "#v" + n);
        var li = document.getElementById("v" + n);
        if (li) { li.scrollIntoView(); var vb = li.querySelector(".vnum"); if (vb && vb.getAttribute("aria-expanded") !== "true") vb.click(); }
        return;
      }
      if (b.classList.contains("ch-pdf")) { window.VRChant.pdf(model, st.sc, b); return; }
      if (b.dataset.nav) { e.preventDefault(); go(b.dataset.nav); }
    });
    // swipes: sideways, at least 70 px, not on the header
    var sx = null, sy = null;
    var two = null, twoLast = 0;
    el.addEventListener("touchstart", function (e) {
      if (e.touches.length === 2) { sx = null; two = (e.touches[0].clientX + e.touches[1].clientX) / 2; twoLast = two; return; }
      if (e.target.closest(".ch-head") || e.touches.length > 1) { sx = null; return; }
      sx = e.touches[0].clientX; sy = e.touches[0].clientY;
    }, { passive: true });
    el.addEventListener("touchmove", function (e) { if (two !== null && e.touches.length === 2) twoLast = (e.touches[0].clientX + e.touches[1].clientX) / 2; }, { passive: true });
    el.addEventListener("touchend", function (e) {
      if (two !== null) {                       // two fingers sideways: whole sarga, in either layout
        var d2 = twoLast - two; if (e.touches.length === 0) { two = null; if (Math.abs(d2) >= 70) go(d2 < 0 ? "next" : "prev"); }
        return;
      }
      if (sx === null) return;
      var dx = e.changedTouches[0].clientX - sx, dy = e.changedTouches[0].clientY - sy; sx = null;
      if (Math.abs(dx) < 70 || Math.abs(dx) < Math.abs(dy) * 1.5) return;
      var dir = dx < 0 ? 1 : -1;
      if (layout === "one") step(dir); else go(dir > 0 ? "next" : "prev");
    }, { passive: true });

    if (navigator.wakeLock && navigator.wakeLock.request) {
      navigator.wakeLock.request("screen").then(function (w) { if (view) view.wake = w; else w.release(); }, function () { /* ignore */ });
    }
    render(false);
    lastPlace(model, st.i);
    el.querySelector(".ch-x").focus();
  }

  window.addEventListener("popstate", function () { if (view) view.onPop(); });

  /* ---------- entry points ---------- */
  var model = pageModel();
  function open(startN) {
    var m = pageModel(); if (!m) return;
    var i = 0;
    if (startN) { i = Math.max(0, m.verses.findIndex(function (v) { return v.n === String(startN); })); }
    openChant(m, i, false);
  }
  document.addEventListener("click", function (e) {
    var b = e.target.closest(".chant-open");
    if (b) { var m = pageModel(), top = firstVisible(m); openChant(m, top, false); return; }
    b = e.target.closest(".chant-here");
    if (b) { var li = b.closest(".verse"); open(li.id.slice(1)); return; }
    b = e.target.closest(".chant-list");
    if (b) { ssSet({ moves: 1, fromList: true, origin: location.href, resume: 0 }); location.assign(b.dataset.href); return; }
    b = e.target.closest(".pdf-btn");
    if (b && model) { window.VRChant.pdf(model, chantScript(), b); }
  });
  function firstVisible(m) {
    var list = document.querySelectorAll(".verses > .verse");
    for (var i = 0; i < list.length; i++) { if (list[i].getBoundingClientRect().bottom > 90) return i; }
    return 0;
  }
  // continue a chant started on the previous work or on a list
  var r = ssGet();
  if (model && r && r.resume !== undefined && r.resume !== null) {
    var idx = r.resume === "last" ? model.verses.length - 1 : +r.resume;
    var keep = { moves: r.moves, origin: r.origin, fromList: r.fromList };
    ssSet(keep);
    history.replaceState(history.state, "", location.href);
    openChant(model, idx, true);
  } else if (model) {
    // not continuing: forget stale state from an earlier chant
    if (r && !r.moves) ssSet(null);
  }
  // reading on the page also remembers the place (for the Continue card on Home)
  if (model) {
    var t2;
    window.addEventListener("scroll", function () {
      clearTimeout(t2);
      t2 = setTimeout(function () { if (!view) lastPlace(model, firstVisible(model)); }, 400);
    }, { passive: true });
  }
  window.VRChant = window.VRChant || {};
  window.VRChant.model = pageModel;
  window.VRChant.open = open;
  window.VRChant.chantScript = chantScript;
  window.VRChant.bookVerse = bookVerse;
  window.VRChant.dandas = dandas;
  window.VRChant.langOf = langOf;

  /* ---------- print and PDF: one document built from the chant model ---------- */
  // Rule from the spec: nothing that leaves the page may rely on the page's own
  // conversion. The document is built explicitly in the chosen script.
  function chantDoc(model, sc) {
    var doc = document.createElement("div");
    doc.className = "pdf-doc"; doc.lang = langOf(sc);
    var h = '<h1>' + esc(model.title[sc]) + '</h1><p class="pd-src">(' + esc(model.src) + ')</p>';
    model.parts.forEach(function (part) {
      var vs = part.verses, g = part.group || 1;
      for (var a = 0; a < vs.length; a += g) {
        h += "<p>" + vs.slice(a, a + g).map(function (v) { return '<span class="pv">' + esc(bookVerse(v, sc)) + '</span>'; }).join("") + "</p>";
      }
    });
    doc.innerHTML = h;
    return doc;
  }
  function fileName(title) {
    return title.normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^\wऀ-ॿಀ-೿]+/g, "-").replace(/^-|-$/g, "") + ".pdf";
  }
  function toast(msg, actions) {
    var t = document.querySelector(".toast") || document.body.appendChild(Object.assign(document.createElement("div"), { className: "toast", role: "status" }));
    t.textContent = msg + " ";
    (actions || []).forEach(function (a) {
      var b = document.createElement("button"); b.type = "button"; b.textContent = a[0];
      b.addEventListener("click", function () { a[1](); t.remove(); });
      t.appendChild(b);
    });
    if (!actions) setTimeout(function () { if (t.parentNode) t.remove(); }, 6000);
  }
  function printDoc(model, sc) {
    var doc = chantDoc(model, sc); doc.id = "printDoc";
    document.body.appendChild(doc); document.body.classList.add("printing");
    var old = document.title; document.title = model.title[sc];
    function done() { doc.remove(); document.body.classList.remove("printing"); document.title = old; window.removeEventListener("afterprint", done); }
    window.addEventListener("afterprint", done);
    setTimeout(function () { window.print(); }, 60);
  }
  function loadPdf() {
    if (window.VRPdf) return Promise.resolve();
    return new Promise(function (res, rej) {
      var s = document.createElement("script"); s.src = document.querySelector(".reader").dataset.root + "static/pdf.js";
      s.onload = res; s.onerror = rej; document.head.appendChild(s);
    });
  }
  function deliver(blob, name) {
    var file = new File([blob], name, { type: "application/pdf" });
    function save() {
      var u = URL.createObjectURL(blob), a = document.createElement("a");
      a.href = u; a.download = name; document.body.appendChild(a); a.click(); a.remove();
      setTimeout(function () { URL.revokeObjectURL(u); }, 20000);
    }
    var phone = window.matchMedia && matchMedia("(pointer: coarse)").matches;
    if (phone && navigator.canShare && navigator.canShare({ files: [file] })) {
      // files only: a title, text or url makes some share sheets list a second "blob" entry
      return navigator.share({ files: [file] }).catch(function (e) {
        if (e && e.name === "AbortError") return;
        if (e && e.name === "NotAllowedError") {
          toast("PDF ready.", [["Share PDF", function () { navigator.share({ files: [file] }).catch(function () {}); }], ["Save", save]]);
        } else save();
      });
    }
    save();
  }
  function makePdf(model, sc, btn) {
    if (btn.getAttribute("aria-busy") === "true") return;
    btn.setAttribute("aria-busy", "true");
    var label = btn.textContent;
    loadPdf().then(function () {
      return window.VRPdf.make(chantDoc(model, sc), model.title[sc], function (n, N) { btn.textContent = n + "/" + N; });
    }).then(function (blob) { return deliver(blob, fileName(model.title[sc])); })
      .catch(function () { toast("Could not make the PDF — try Print and choose Save as PDF."); })
      .then(function () { btn.removeAttribute("aria-busy"); btn.textContent = label; });
  }
  window.VRChant = window.VRChant || {};
  window.VRChant.print = printDoc;
  window.VRChant.pdf = makePdf;
  window.VRChant.doc = chantDoc;
})();
