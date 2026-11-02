/* Home (verse of the day, continue, kāṇḍa chips), My list, tab badge, Back button. */
(function () {
  "use strict";
  var T = window.Translit, P = window.VRPrefs, S = window.VRSaved;
  var ROOT = document.body.dataset.root || "";
  var SCR = ["knda", "deva", "iast"], LAST = "vr.last";
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
      var last = lastPlace();
      document.getElementById("my-last").innerHTML = last
        ? '<a href="' + ROOT + last.href.replace(/^\/[^/]*\//, "").replace(/^\//, "") + '">' + esc(last.titles[s] || last.src) + ' · ' + esc(last.src) + ' ' + last.v + '</a>' : "Nothing yet.";
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

  /* ---- Continue ---- */
  (function () {
    var l = lastPlace(); if (!l) return;
    var s = sc(), box = document.getElementById("continue");
    var rel = l.href.replace(location.pathname.replace(/[^/]*$/, ""), "");   // site-relative path
    // stored href is a full pathname; make it relative to the site root
    var base = location.pathname.replace(/index\.html$/, "");
    var path = l.href.indexOf(base) === 0 ? l.href.slice(base.length) : l.href.replace(/^\/[^/]+\//, "");
    box.hidden = false;
    document.getElementById("cont-where").textContent = (l.titles[s] || l.src) + " · verse " + l.v + " of " + l.of;
    document.getElementById("cont-bar").style.width = Math.round(100 * (l.i + 1) / l.of) + "%";
    document.getElementById("cont-go").href = ROOT + path;
    document.getElementById("cont-chant").addEventListener("click", function () {
      try { sessionStorage.setItem("vr.chant", JSON.stringify({ moves: 1, fromList: true, origin: location.href, resume: l.i })); } catch (e) { /* ignore */ }
      location.assign(ROOT + path.replace(/#.*$/, ""));
    });
  })();

  /* ---- kāṇḍa tiles with sarga chips ---- */
  var chipEd = ((P.get().off || []).indexOf("ce") >= 0) ? "vu" : "ce";
  function fillChips(tile) {
    var n = +tile.dataset["n" + chipEd.charAt(0).toUpperCase() + chipEd.slice(1)] || +tile.getAttribute("data-n-" + chipEd), k = tile.dataset.k, box = tile.querySelector(".chips"), h = "";
    var s = sc();
    for (var i = 1; i <= n; i++) h += '<a href="' + ROOT + chipEd + "/" + k + "/" + i + '/">' + (s === "iast" ? i : T.digits(i, s)) + "</a>";
    box.innerHTML = h;
  }
  document.querySelectorAll(".tile").forEach(function (t) {
    t.querySelector(".tile-btn").addEventListener("click", function () {
      var b = t.querySelector(".tile-btn"), box = t.querySelector(".chips"), open = b.getAttribute("aria-expanded") === "true";
      b.setAttribute("aria-expanded", open ? "false" : "true"); box.hidden = open;
      if (!open) fillChips(t);
    });
  });
  document.querySelectorAll("[data-chip-ed]").forEach(function (b) {
    b.addEventListener("click", function () {
      chipEd = b.dataset.chipEd;
      document.querySelectorAll("[data-chip-ed]").forEach(function (x) { x.setAttribute("aria-checked", x === b ? "true" : "false"); });
      document.querySelectorAll(".tile .tile-btn[aria-expanded=true]").forEach(function (x) { fillChips(x.closest(".tile")); });
    });
  });

  /* ---- verse of the day ---- */
  var grammar = null, ix = null, card = null, idx = 0, cardNo = 0, shuffled = false, today = null;
  var LAB = {
    verse: ["Śloka", "ಶ್ಲೋಕ"], words: ["Words and grammar", "ಪದಗಳು ಮತ್ತು ವ್ಯಾಕರಣ"], metre: ["Metre", "ಛಂದಸ್ಸು"],
    ctx: ["In the epic", "ರಾಮಾಯಣದಲ್ಲಿ"], other: ["Other recension", "ಇನ್ನೊಂದು ಪಾಠ"], m: ["Meaning", "ಅರ್ಥ"], u: ["Use and significance", "ಬಳಕೆ ಮತ್ತು ಮಹತ್ವ"],
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
    out.push({ key: "verse", lines: lines(c, s), ref: c.ref, meta: [c.meter].filter(Boolean).join(" · ") });
    if (c.m) out.push({ key: "m", text: c.m[kn ? 1 : 0] });
    if (c.w && c.w.length) out.push({ key: "words", dl: c.w.map(function (u) {
      return [u.f.map(function (f) { return T.render(f, s, sav); }).join("-"), gl(u.t, s) + (gl(u.t, s) ? " — " : "") + u.g];
    }), note: kn ? "ನಿಘಂಟಿನ ಅರ್ಥಗಳು (ಇಂಗ್ಲಿಷ್); ಸ್ವಯಂಚಾಲಿತ" : "Dictionary senses of each base word, chosen automatically" });
    if (c.meter) out.push({ key: "metre", text: c.meter, scan: c.scan });
    var x = c.ctx, kname = s === "knda" ? x.kn : s === "deva" ? x.deva : x.iast, nn = function (n) { return s === "iast" ? n : T.digits(n, s); };
    out.push({ key: "ctx", text: kname + " · " + (kn ? "ಸರ್ಗ " : s === "deva" ? "सर्गः " : "sarga ") + nn(x.s) + (x.title ? " — " + x.title : "") + " · " + nn(x.v) + " / " + nn(x.of) });
    if (c.cw) out.push({ key: "other", text: CWSTAT[c.cw.status][kn ? 1 : 0] + " " + (kn ? "ಪರಂಪರಾಗತ ಪಾಠ" : "Traditional Text") + (c.cw.refs.length ? " " + c.cw.refs.join(", ") : "") });
    if (c.u) out.push({ key: "u", text: c.u[kn ? 1 : 0] });
    return out;
  }
  function cardHtml(sec, s) {
    var h = '<h3 class="vc-label">' + esc(L(sec.key, s)) + "</h3>";
    if (sec.lines) {
      h += '<div class="vc-verse t-' + s + '" lang="' + langOf(s) + '">' + sec.lines.map(function (l) { return '<span class="ln">' + esc(l) + "</span>"; }).join("") + "</div>" +
        '<p class="vc-ref">' + esc(sec.ref) + (sec.meta ? " · " + esc(sec.meta) : "") + "</p>";
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
    slide.setAttribute("aria-label", (cardNo + 1) + " / " + secs.length);
    if (dir && !reduce && slide.animate) slide.animate([{ transform: "translateX(" + (dir * 40) + "px)", opacity: 0 }, { transform: "none", opacity: 1 }], { duration: 240, easing: "ease" });
    votd.querySelector(".votd-name").textContent = L(secs[cardNo].key, s);
    votd.querySelector(".votd-kind").textContent = L(shuffled ? "another" : "kind", s);
    var dots = votd.querySelector(".votd-dots");
    dots.innerHTML = secs.map(function (x, i) { return '<button type="button" role="tab" aria-selected="' + (i === cardNo) + '" aria-label="' + esc(L(x.key, s)) + '" data-card="' + i + '"></button>'; }).join("");
    document.getElementById("votd-open").href = ROOT + card.path;
    document.getElementById("votd-today").hidden = !shuffled;
    paintSave();
  }
  function saveId() { return "dm-ce-" + card.ref; }
  function paintSave() {
    var b = document.getElementById("votd-save"), on = S.has(saveId());
    b.setAttribute("aria-pressed", on); b.firstChild.nodeValue = on ? "★ " : "☆ "; b.querySelector("span").textContent = on ? "Saved" : "Save";
  }
  function cardAt(k) { return getJSON(ROOT + "data/daily/c" + Math.floor(k / ix.chunk) + ".json").then(function (a) { return a[k % ix.chunk]; }); }
  function show(k, isShuffle) {
    return cardAt(k).then(function (c) { card = c; idx = k; shuffled = isShuffle; cardNo = 0; draw(0); }, function () {
      card = JSON.parse(votd.dataset.fallback); shuffled = false; cardNo = 0; draw(0);
    });
  }
  var day = Math.floor((Date.now() - new Date().getTimezoneOffset() * 60000) / 86400000);
  card = JSON.parse(votd.dataset.fallback);
  Promise.all([getJSON(ROOT + "data/grammar.json").then(function (g) { grammar = g; }, function () { }),
    getJSON(ROOT + "data/daily/index.json").then(function (i) { ix = i; today = (day * 7919) % ix.n; })]).then(function () { return show(today, false); },
    function () { draw(0); });

  votd.addEventListener("click", function (e) {
    var d = e.target.closest("[data-card]");
    if (d) { cardNo = +d.dataset.card; draw(0); return; }
    if (e.target.closest(".votd-actions") || e.target.closest(".votd-dots")) return;
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
  document.getElementById("votd-today").addEventListener("click", function () { show(today, false); });
  document.getElementById("votd-save").addEventListener("click", function () {
    S.toggle({ id: saveId(), kind: "verse", href: card.path, label: "CE " + card.ref, slp: card.slp }); paintSave(); badge();
  });
  document.addEventListener("prefs-changed", function () {
    if (card) draw(0);
    if ((P.get().off || []).indexOf(chipEd) >= 0) {
      chipEd = chipEd === "ce" ? "vu" : "ce";
      document.querySelectorAll("[data-chip-ed]").forEach(function (x) { x.setAttribute("aria-checked", x.dataset.chipEd === chipEd ? "true" : "false"); });
      document.querySelectorAll(".tile .tile-btn[aria-expanded=true]").forEach(function (x) { fillChips(x.closest(".tile")); });
    }
  });

  /* ---- share picture: all cards in one tall PNG ---- */
  function paintShare(secs, s, drawIt, ctx, known) {
    var Wd = 1080, pad = 60, inner = Wd - 2 * pad - 2 * 44, y = 0;
    var fam = s === "knda" ? "'Tiro Kannada','Tiro Devanagari Sanskrit',serif" : s === "deva" ? "'Tiro Devanagari Sanskrit',serif" : "'Alegreya',serif";
    var ui = "'Alegreya Sans',sans-serif";
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
      txt("ವಾಲ್ಮೀಕಿ ರಾಮಾಯಣ", pad, 100, "400 44px 'Tiro Kannada',serif", "#FFFBF2");
      txt(L("kind", s), pad, 150, "500 30px " + ui, "#E8D9A8");
      txt("hms-cap.github.io/Ramayana", Wd / 2, total - 56, "400 26px " + ui, "#E8D9A8", "center");
    }
    return { total: total, cardH: cardH };
  }
  document.getElementById("votd-share").addEventListener("click", function () {
    var btn = this, s = sc(), secs = plain(card);
    var fam = ["'Tiro Kannada'", "'Tiro Devanagari Sanskrit'", "'Alegreya'", "'Alegreya Sans'"];
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
