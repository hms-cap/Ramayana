/* Home (verse of the day, continue, kāṇḍa chips), My list, tab badge, Back button. */
(function () {
  "use strict";
  var T = window.Translit, P = window.VRPrefs, S = window.VRSaved;
  var B = document.body.dataset, ROOT = B.root || "", WROOT = B.wroot || "", PRE = B.prefix || "", MBH = B.work === "mbh", GITA = B.work === "gita";
  var SCR = ["knda", "deva", "iast"], LAST = ({ mbh: "vr.last.mbh", gita: "vr.last.gita" }[B.work] || "vr.last");
  function sc() { var s = (P.get().script) || "knda"; return SCR.indexOf(s) >= 0 ? s : "knda"; }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function langOf(x) { return x === "knda" ? "sa-Knda" : x === "deva" ? "sa-Deva" : "sa-Latn"; }
  function getJSON(u) { return fetch(u).then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); }); }
  function lastPlace() { try { return JSON.parse(localStorage.getItem(LAST) || "null"); } catch (e) { return null; } }

  /* ---- Back button: history.back() when we came from inside the site, else the parent page ---- */
  document.addEventListener("click", function (e) {
    var b = e.target.closest("[data-back]");
    if (!b) return;
    var same = false;
    try { same = document.referrer && new URL(document.referrer).origin === location.origin && history.length > 1; } catch (x) { /* ignore */ }
    if (same) { e.preventDefault(); history.back(); }
  });

  /* ---- badge on My ---- */
  function badge() {
    var n = S.list().length;
    document.querySelectorAll(".badge-n").forEach(function (b) { b.hidden = !n; b.textContent = n; });
  }
  badge();

  /* ---- My list page ---- */
  var mySaved = document.getElementById("my-saved");
  if (mySaved) {
    var paintMy = function () {
      var l = S.list(), s = sc();
      mySaved.innerHTML = l.map(function (it) {
        var label = it.kind === "verse"
          ? '<span class="t-' + s + '" lang="' + langOf(s) + '">' + esc(T.render(it.slp[0], s, !!P.get().savarna)) + '</span> <small>' + esc(it.label) + '</small>'
          : '<span lang="' + langOf(s) + '">' + esc((it.titles && it.titles[s]) || it.label) + '</span> <small>' + esc(it.label || "") + '</small>';
        return '<li><a href="' + ROOT + it.href + '">' + label + '</a> <button type="button" class="act" data-unsave="' + esc(it.id) + '" aria-label="Remove">✕</button></li>';
      }).join("");
      document.getElementById("my-empty").hidden = l.length > 0;
      var out = [];
      ["vr.last", "vr.last.mbh", "vr.last.gita"].forEach(function (key) {
        var last = null; try { last = JSON.parse(localStorage.getItem(key) || "null"); } catch (e) { /* ignore */ }
        if (last) out.push('<a href="' + ROOT + last.href.replace(/^\/[^/]*\//, "").replace(/^\//, "") + '">' + esc(last.titles[s] || last.src) + ' · ' + esc(last.src) + ' ' + last.v + '</a>');
      });
      document.getElementById("my-last").innerHTML = out.length ? out.join("<br>") : "Nothing yet.";
    };
    document.addEventListener("click", function (e) {
      var b = e.target.closest("[data-unsave]"); if (!b) return;
      var id = b.dataset.unsave, it = S.list().filter(function (x) { return x.id === id; })[0];
      if (it) S.toggle(it); paintMy(); badge();
    });
    document.addEventListener("prefs-changed", paintMy);
    paintMy();
  }

  var votd = document.getElementById("votd");
  if (!votd) return;

  /* opening the app fresh (no page of this site before it) returns to the work used last */
  if (B.work === "ram" && document.body.classList.contains("page-home")) {
    var fresh = true;
    try { fresh = !document.referrer || new URL(document.referrer).origin !== location.origin; } catch (e) { /* ignore */ }
    try { var pw = window.VRPrevWork; if (fresh && (pw === "mbh" || pw === "gita") && !/[?&]work=ram/.test(location.search)) { location.replace(ROOT + pw + "/"); return; } } catch (e) { /* ignore */ }
  }

  /* ---- greeting date, quick Chant chip ---- */
  var gd = document.getElementById("greet-date");
  if (gd) { try { gd.textContent = new Date().toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "long" }); } catch (e) { /* ignore */ } }
  var qc = document.getElementById("quick-chant");
  if (qc) qc.addEventListener("click", function () {
    var l = lastPlace(), base = location.pathname.replace(/index\.html$/, ""), path = "vu/1/1/", at = 0;
    if (l) { path = l.href.indexOf(base) === 0 ? l.href.slice(base.length) : l.href.replace(/^\/[^/]+\//, ""); at = l.i; }
    try { sessionStorage.setItem("vr.chant", JSON.stringify({ moves: 1, fromList: true, origin: location.href, resume: at })); } catch (e) { /* ignore */ }
    location.assign(WROOT + path.replace(/#.*$/, ""));
  });

  /* ---- Continue ---- */
  (function () {
    var l = lastPlace(); if (!l) return;
    var s = sc(), box = document.getElementById("continue");
    var rel = l.href.replace(location.pathname.replace(/[^/]*$/, ""), "");   // site-relative path
    // stored href is a full pathname; make it relative to the site root
    var base = location.pathname.replace(/index\.html$/, "");
    var path = l.href.indexOf(base) === 0 ? l.href.slice(base.length) : l.href.replace(/^\/[^/]+\//, "");
    var RES = '<svg width="16" height="16" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 10h12M11 5l5 5-5 5"/></svg>';
    document.getElementById("cont-label").textContent = "Continue reading";
    document.getElementById("cont-icon").innerHTML = RES; document.getElementById("cont-go-ic").innerHTML = RES;
    document.getElementById("cont-go-t").textContent = "Resume";
    document.getElementById("cont-barwrap").hidden = false;
    document.getElementById("cont-where").lang = "";
    document.getElementById("cont-where").textContent = (l.titles[s] || l.src) + " · verse " + l.v + " of " + l.of;
    document.getElementById("cont-bar").style.width = Math.round(100 * (l.i + 1) / l.of) + "%";
    document.getElementById("cont-go").href = WROOT + path;
  })();

  /* ---- verse of the day ---- */
  var grammar = null, ix = null, card = null, idx = 0, cardNo = 0, shuffled = false, today = null;
  var LAB = {
    verse: ["Śloka", "ಶ್ಲೋಕ"], words: ["Words and grammar", "ಪದಗಳು ಮತ್ತು ವ್ಯಾಕರಣ"], metre: ["Metre", "ಛಂದಸ್ಸು"],
    ctx: [B.epicEn || "In the epic", B.epicKn || "ರಾಮಾಯಣದಲ್ಲಿ"], other: ["Other recension", "ಇನ್ನೊಂದು ಪಾಠ"], m: ["Meaning", "ಅರ್ಥ"], u: ["Use and significance", "ಬಳಕೆ ಮತ್ತು ಮಹತ್ವ"],
    kind: ["Today's śloka", "ಇಂದಿನ ಶ್ಲೋಕ"], another: ["Another śloka", "ಇನ್ನೊಂದು ಶ್ಲೋಕ"]
  };
  var CWSTAT = {
    match: ["Same verse in the", "ಎರಡೂ ಪಾಠಗಳಲ್ಲಿ ಇದೆ:"], variant: ["Different reading in the", "ಪಾಠಭೇದ:"], regrouped: ["Lines grouped differently in the", "ಪಾದಗಳ ಗುಂಪು ಬೇರೆ:"],
    partial: ["Only partly in the", "ಭಾಗಶಃ ಮಾತ್ರ:"], absent: ["Not in the", "ಇಲ್ಲ:"]
  };
  function L(key, s) { return LAB[key][s === "knda" ? 1 : 0]; }

  function lines(c, s) {
    var d = s === "iast" ? ["|", "||"] : ["।", "॥"], sav = !!P.get().savarna;
    return c.slp.map(function (l, i) {
      var t = T.render(l, s, sav);
      return t + " " + (i === c.slp.length - 1 ? d[1] + " " + (s === "iast" ? c.ref : T.digits(c.ref, s)) + " " + d[1] : d[0]);
    });
  }
  function gl(t, s) {
    if (!grammar) return "";
    var en = s !== "knda", o = [];
    ["pos", "f", "g", "c", "n", "p", "l"].forEach(function (k) {
      var key = k === "pos" ? t.pos : t[k]; if (!key) return;
      var e = grammar[k] && grammar[k][key]; if (e) o.push(en ? e.en : e.kn);
    });
    return o.join(" · ");
  }
  function plain(c) {
    var s = sc(), sav = !!P.get().savarna, kn = s === "knda", out = [];
    var cx = c.ctx || {}, kname0 = s === "knda" ? cx.kn : s === "deva" ? cx.deva : cx.iast, nn0 = function (n) { return s === "iast" ? n : T.digits(n, s); };
    out.push({ key: "verse", lines: lines(c, s), ref: c.ref, where: cx.s ? (kname0 || "") + " " + nn0(cx.s) + (cx.v ? "." + nn0(cx.v) : "") : c.ref,
      meta: [c.meter].filter(Boolean).join(" · ") });
    if (c.m) out.push({ key: "m", text: c.m[kn ? 1 : 0] });
    if (c.w && c.w.length) out.push({ key: "words", dl: c.w.map(function (u) {
      return [u.f.map(function (f) { return T.render(f, s, sav); }).join("-"), gl(u.t, s) + (gl(u.t, s) ? " — " : "") + (kn && u.k ? u.k : u.g)];
    }), note: kn ? "ನಿಘಂಟಿನ ಅರ್ಥಗಳು (ಇಂಗ್ಲಿಷ್; ಕನ್ನಡ ಅರ್ಥ ಇರುವಲ್ಲಿ ಕನ್ನಡ — ಅದು ಇನ್ನೂ ಪರಿಶೀಲನೆಯಾಗಿಲ್ಲ); ಸ್ವಯಂಚಾಲಿತ" : "Dictionary senses of each base word, chosen automatically" });
    if (c.meter) out.push({ key: "metre", text: c.meter, scan: c.scan });
    var x = c.ctx, kname = s === "knda" ? x.kn : s === "deva" ? x.deva : x.iast, nn = function (n) { return s === "iast" ? n : T.digits(n, s); };
    out.push({ key: "ctx", text: kname + " · " + (kn ? (B.subKn || "ಸರ್ಗ") + " " : s === "deva" ? (B.subDeva || "सर्गः") + " " : (B.subEn || "sarga") + " ") + nn(x.s) + (x.title ? " — " + x.title : "") + " · " + nn(x.v) + " / " + nn(x.of) });
    if (c.cw) out.push({ key: "other", text: CWSTAT[c.cw.status][kn ? 1 : 0] + " " + (kn ? (c.cw.other_kn || "ಪರಂಪರಾಗತ ಪಾಠ") : (c.cw.other || "Traditional Text")) + (c.cw.refs.length ? " " + c.cw.refs.join(", ") : "") });
    if (c.u) out.push({ key: "u", text: c.u[kn ? 1 : 0] });
    return out;
  }
  function marked(l) {                              // verse line -> HTML with the end mark (daṇḍa, number) in <span class="d">
    var m = /^(.*?)(\s+(?:[।|]|(?:॥|\|\|)\s.*))$/.exec(l);
    if (!m) return esc(l);
    var end = m[2].replace(/^(\s*)(॥|\|\|)\s.*$/, "$1$2");   // ॥ alone: the reference is printed under the verse
    return esc(m[1]) + '<span class="d">' + esc(end) + "</span>";
  }
  // Shrink the verse until its longest word fits the card, so a long compound is not broken mid-word.
  function fitVerse(el) {
    if (!el) return;
    el.style.fontSize = "";
    var size = parseFloat(getComputedStyle(el).fontSize), avail = el.clientWidth - size;   // 1em: the indent of later lines
    var probe = document.createElement("span");
    probe.style.cssText = "position:absolute;visibility:hidden;white-space:nowrap";
    el.appendChild(probe);
    var widest = 0;
    el.textContent.split(/\s+/).forEach(function (w) { if (w) { probe.textContent = w; widest = Math.max(widest, probe.getBoundingClientRect().width); } });
    el.removeChild(probe);
    if (widest > avail && widest > 0) el.style.fontSize = Math.max(size * 0.6, size * avail / widest * 0.98) + "px";
  }
  function cardHtml(sec, s) {
    var h = '<h3 class="vc-label">' + esc(L(sec.key, s)) + "</h3>";
    if (sec.lines) {
      h += '<div class="vc-verse t-' + s + '" lang="' + langOf(s) + '">' + sec.lines.map(function (l) { return '<span class="ln">' + marked(l) + "</span>"; }).join("") + "</div>" +
        '<p class="vc-ref">' + esc(sec.where || sec.ref) + (sec.meta ? " · " + esc(sec.meta) : "") + "</p>";
    } else if (sec.dl) {
      h += '<dl class="vc-dl" lang="en">' + sec.dl.map(function (r) { return '<dt lang="' + langOf(s) + '">' + esc(r[0]) + "</dt><dd>" + esc(r[1]) + "</dd>"; }).join("") + "</dl>" + '<p class="vc-note">' + esc(sec.note) + "</p>";
    } else {
      h += "<p>" + esc(sec.text) + "</p>";
      if (sec.scan) h += '<p class="vc-scan" lang="sa" aria-label="scansion">' + sec.scan.map(esc).join("<br>") + "</p>";
    }
    return h;
  }
  function draw(dir) {
    var s = sc(), secs = plain(card), slide = votd.querySelector(".votd-slide");
    cardNo = Math.max(0, Math.min(secs.length - 1, cardNo));
    var reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
    slide.innerHTML = cardHtml(secs[cardNo], s);
    var vv = slide.querySelector(".vc-verse");
    fitVerse(vv);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () { if (vv && vv.isConnected) fitVerse(vv); });
    slide.setAttribute("aria-label", (cardNo + 1) + " / " + secs.length);
    if (dir && !reduce && slide.animate) slide.animate([{ transform: "translateX(" + (dir * 40) + "px)", opacity: 0 }, { transform: "none", opacity: 1 }], { duration: 240, easing: "ease" });
    votd.querySelector(".votd-name").textContent = L(secs[cardNo].key, s);
    votd.querySelector(".votd-kind").textContent = L(shuffled ? "another" : "kind", s);
    votd.dataset.face = secs[cardNo].key;
    var info = document.getElementById("votd-info"); info.textContent = cardNo ? "Back to the śloka" : "Metre, place, other text";
    var dots = votd.querySelector(".votd-dots");
    dots.innerHTML = secs.map(function (x, i) { return '<button type="button" role="tab" aria-selected="' + (i === cardNo) + '" aria-label="' + esc(L(x.key, s)) + '" data-card="' + i + '"></button>'; }).join("");
    var vp = card.cw && card.cw.status === "match" && card.cw.paths && card.cw.paths[0];
    document.getElementById("votd-open").href = WROOT + ((P.off().indexOf(card.ed || "ce") >= 0 && vp) ? vp : card.path);
    document.getElementById("votd-today").hidden = !shuffled;
    var wb = document.getElementById("votd-words"), hasW = secs.some(function (x) { return x.key === "words"; });
    wb.setAttribute("aria-disabled", hasW ? "false" : "true"); wb.setAttribute("aria-pressed", secs[cardNo].key === "words" ? "true" : "false");
    paintSave();
  }
  function saveId() { return (MBH ? "dm-mbh-vu-" : GITA ? "dm-gita-vu-" : "dm-ce-") + card.ref; }
  function paintSave() {
    var b = document.getElementById("votd-save"), on = S.has(saveId());
    b.setAttribute("aria-pressed", on); b.setAttribute("aria-label", on ? "Saved. Tap to remove" : "Save"); b.title = on ? "Saved" : "Save";
    var t = b.querySelector(".lbl"); if (t) t.textContent = on ? "Saved ✓" : "Save";
  }
  function cardAt(k) { return getJSON(WROOT + "data/daily/c" + Math.floor(k / ix.chunk) + ".json").then(function (a) { return a[k % ix.chunk]; }); }
  function show(k, isShuffle) {
    return cardAt(k).then(function (c) { card = c; idx = k; shuffled = isShuffle; cardNo = 0; draw(0); }, function () {
      card = JSON.parse(votd.dataset.fallback); shuffled = false; cardNo = 0; draw(0);
    });
  }
  var day = Math.floor((Date.now() - new Date().getTimezoneOffset() * 60000) / 86400000);
  card = JSON.parse(votd.dataset.fallback);
  Promise.all([getJSON(ROOT + "data/grammar.json").then(function (g) { grammar = g; }, function () { }),
    getJSON(WROOT + "data/daily/index.json").then(function (i) { ix = i; today = (day * 7919) % ix.n; })]).then(function () { return show(today, false); },
    function () { draw(0); });

  votd.addEventListener("click", function (e) {
    var d = e.target.closest("[data-card]");
    if (d) { cardNo = +d.dataset.card; draw(0); return; }
    if (e.target.closest(".votd-actions") || e.target.closest(".votd-dots") || e.target.closest(".hole")) return;
    if (e.target.closest(".votd-slide")) { var n = plain(card).length; cardNo = (cardNo + 1) % n; draw(1); }
  });
  votd.addEventListener("keydown", function (e) {
    if (!e.target.closest(".votd-slide")) return;
    var n = plain(card).length;
    if (e.key === "ArrowRight") { cardNo = (cardNo + 1) % n; draw(1); e.preventDefault(); }
    if (e.key === "ArrowLeft") { cardNo = (cardNo + n - 1) % n; draw(-1); e.preventDefault(); }
  });
  var sx = null;
  votd.addEventListener("touchstart", function (e) { sx = e.touches[0].clientX; }, { passive: true });
  votd.addEventListener("touchend", function (e) {
    if (sx === null) return; var dx = e.changedTouches[0].clientX - sx; sx = null;
    if (Math.abs(dx) < 40) return;
    var n = plain(card).length; cardNo = (cardNo + (dx < 0 ? 1 : n - 1)) % n; draw(dx < 0 ? 1 : -1);
    e.preventDefault();
  });
  document.getElementById("votd-another").addEventListener("click", function () {
    if (!ix) return; var k; do { k = Math.floor(Math.random() * ix.n); } while (k === idx);
    show(k, true);
  });
  var menu = document.getElementById("votd-menu"), more = document.getElementById("votd-more");
  function menuOpen(on) { menu.hidden = !on; more.setAttribute("aria-expanded", on ? "true" : "false"); if (on) { var f = menu.querySelector("button:not([hidden])"); if (f) f.focus(); } }
  more.addEventListener("click", function () { menuOpen(menu.hidden); });
  menu.addEventListener("click", function (e) { if (e.target.closest("button") && e.target.closest("button").id !== "votd-save") menuOpen(false); });
  document.addEventListener("click", function (e) { if (!menu.hidden && !e.target.closest("#votd-menu") && !e.target.closest("#votd-more")) menuOpen(false); });
  votd.addEventListener("keydown", function (e) { if (e.key === "Escape" && !menu.hidden) { menuOpen(false); more.focus(); e.stopPropagation(); } });
  document.getElementById("votd-info").addEventListener("click", function () {
    if (cardNo) { cardNo = 0; draw(-1); return; }
    var secs = plain(card), at = -1; secs.forEach(function (x, i) { if (at < 0 && (x.key === "metre" || x.key === "ctx")) at = i; });
    cardNo = at < 0 ? 0 : at; draw(1);
  });
  document.getElementById("votd-words").addEventListener("click", function () {
    var secs = plain(card), at = -1; secs.forEach(function (x, i) { if (x.key === "words") at = i; });
    if (at < 0) { this.title = "No word-by-word for this śloka"; return; }
    cardNo = at; draw(1);
  });
  document.getElementById("votd-today").addEventListener("click", function () { show(today, false); });
  document.getElementById("votd-save").addEventListener("click", function () {
    S.toggle({ id: saveId(), kind: "verse", href: PRE + card.path, label: (MBH ? "Mahābhārata " : GITA ? "Bhagavadgītā " : "CE ") + card.ref, slp: card.slp }); paintSave(); badge();
  });
  document.addEventListener("prefs-changed", function () {
    if (card) draw(0);
    });

  /* ---- share picture: all cards in one tall PNG ---- */
  function paintShare(secs, s, drawIt, ctx, known) {
    var Wd = 1080, pad = 60, inner = Wd - 2 * pad - 2 * 44, y = 0;
    var kn = document.documentElement.dataset.knfont === "sans" ? "'Noto Sans Kannada'" : "'Noto Serif Kannada'";
    var fam = s === "knda" ? kn + ",'Noto Serif Devanagari',serif" : s === "deva" ? "'Noto Serif Devanagari',serif" : "'Cormorant Garamond',serif";
    var ui = "'Plus Jakarta Sans',sans-serif";
    function wrap(text, font, width) {
      ctx.font = font; var words = text.split(/\s+/), lines = [], cur = "";
      words.forEach(function (w) { var t = cur ? cur + " " + w : w; if (ctx.measureText(t).width > width && cur) { lines.push(cur); cur = w; } else cur = t; });
      if (cur) lines.push(cur); return lines;
    }
    function txt(t, x, yy, font, color, align) { if (!drawIt) return; ctx.font = font; ctx.fillStyle = color; ctx.textAlign = align || "left"; ctx.fillText(t, x, yy); }
    var top = 70, cardTop0 = 190;
    if (drawIt) {
      var g = ctx.createLinearGradient(0, 0, 0, known.total); g.addColorStop(0, "#1B2358"); g.addColorStop(1, "#2F3C9C");
      ctx.fillStyle = g; ctx.fillRect(0, 0, Wd, known.total);
      ctx.fillStyle = "#FFFBF2"; ctx.strokeStyle = "#C9A24B"; ctx.lineWidth = 3;
      ctx.beginPath(); if (ctx.roundRect) ctx.roundRect(pad, cardTop0 - 20, Wd - 2 * pad, known.cardH, 30); else ctx.rect(pad, cardTop0 - 20, Wd - 2 * pad, known.cardH);
      ctx.fill(); ctx.stroke();
    }
    y = top + 30;                                    // brand + heading drawn after the card
    var cardTop = 190; y = cardTop + 44;
    var x0 = pad + 44;
    secs.forEach(function (sec, si) {
      if (si) { if (drawIt) { ctx.fillStyle = "#E4D9BD"; ctx.fillRect(x0, y, inner, 2); } y += 34; }
      txt(L(sec.key, s).toUpperCase(), x0, y + 20, "700 24px " + ui, "#2F3C9C"); y += 52;
      if (sec.lines) {
        var size = 46; ctx.font = "400 " + size + "px " + fam;
        while (size > 32 && sec.lines.some(function (l) { ctx.font = "400 " + size + "px " + fam; return ctx.measureText(l).width > inner; })) size -= 2;
        sec.lines.forEach(function (l) { wrap(l, "400 " + size + "px " + fam, inner).forEach(function (w) { txt(w, x0, y + size, "400 " + size + "px " + fam, "#1B1712"); y += Math.round(size * 1.7); }); });
        wrap(sec.ref + (sec.meta ? " · " + sec.meta : ""), "500 28px " + ui, inner).forEach(function (w) { txt(w, x0, y + 24, "500 28px " + ui, "#A86A12"); y += 40; });
      } else if (sec.dl) {
        sec.dl.forEach(function (r) {
          txt(r[0], x0, y + 34, "400 34px " + fam, "#1B1712"); y += 52;
          wrap(r[1], "400 26px " + ui, inner).forEach(function (w) { txt(w, x0, y + 20, "400 26px " + ui, "#4A4F66"); y += 36; });
          y += 8;
        });
      } else {
        wrap(sec.text, "400 32px " + (/[ऀ-෿]/.test(sec.text) ? fam : ui), inner).forEach(function (w) { txt(w, x0, y + 28, "400 32px " + (/[ऀ-෿]/.test(sec.text) ? fam : ui), "#1B1712"); y += 48; });
        (sec.scan || []).forEach(function (w) { txt(w, x0, y + 28, "400 30px " + fam, "#6B6255"); y += 46; });
      }
      y += 10;
    });
    var cardH = y - cardTop + 20, total = cardTop + cardH + 130;
    if (drawIt) {
      txt(B.workKn || "ವಾಲ್ಮೀಕಿ ರಾಮಾಯಣ", pad, 100, "400 44px " + kn + ",serif", "#FFFBF2");
      txt(L("kind", s), pad, 150, "500 30px " + ui, "#E8D9A8");
      txt(B.site || "ramayana-blond.vercel.app", Wd / 2, total - 56, "400 26px " + ui, "#E8D9A8", "center");
    }
    return { total: total, cardH: cardH };
  }
  document.getElementById("votd-share").addEventListener("click", function () {
    var btn = this, s = sc(), secs = plain(card);
    var fam = [document.documentElement.dataset.knfont === "sans" ? "'Noto Sans Kannada'" : "'Noto Serif Kannada'", "'Noto Serif Devanagari'", "'Cormorant Garamond'", "'Plus Jakarta Sans'"];
    btn.setAttribute("aria-busy", "true");
    Promise.all(fam.map(function (f) { return document.fonts.load("30px " + f, secs.map(function (x) { return (x.lines || [x.text || ""]).join(" "); }).join(" ").slice(0, 300)); })).then(function () {
      var c = document.createElement("canvas"), ctx = c.getContext("2d");
      c.width = 1080; c.height = 100; var m = paintShare(secs, s, false, ctx);
      c.height = m.total; ctx = c.getContext("2d"); paintShare(secs, s, true, ctx, m);
      return new Promise(function (r) { c.toBlob(r, "image/png"); });
    }).then(function (blob) {
      var file = new File([blob], "sloka-" + card.ref + ".png", { type: "image/png" });
      if (navigator.canShare && navigator.canShare({ files: [file] })) {
        return navigator.share({ files: [file] }).catch(function (e) { if (!e || e.name !== "AbortError") throw e; });
      }
      var a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = file.name; document.body.appendChild(a); a.click(); a.remove();
    }).catch(function () { }).then(function () { btn.removeAttribute("aria-busy"); });
  });
})();
