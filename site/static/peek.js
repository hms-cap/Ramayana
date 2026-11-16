/* Peek: tapping a "Different reading in the …" badge link opens the other edition's verse in a bottom sheet instead of leaving the page. */
(function () {
  "use strict";
  var T = window.Translit, P = window.VRPrefs;
  if (!T || !P) return;
  var cache = new Map();
  var ui = null, token = 0;           // ui = {back, sheet, from} while open

  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function script() { var s = P.get().script || "knda"; return s === "knda-deva" ? "knda" : s; }
  function cleanLine(t) { return t.replace(/[\s ]*[|।॥].*$/, "").trim(); }
  function linesOf(li) {
    var out = [];
    Array.prototype.forEach.call(li.querySelectorAll(".t-iast .ln"), function (e) { var t = cleanLine(e.textContent); if (t) out.push(t); });
    return out;
  }
  function key(w) { return T.looseForIndex(T.iastToSlp1(w)); }
  function words(lines) { return lines.join(" ").split(/\s+/).filter(Boolean); }
  function noHash(h) { return h.replace(/#.*$/, ""); }

  function loadPage(url) {
    if (!cache.has(url)) {
      cache.set(url, fetch(url).then(function (r) {
        if (!r.ok) throw new Error(r.status);
        return r.text();
      }).then(function (h) { return new DOMParser().parseFromString(h, "text/html"); }));
      cache.get(url).catch(function () { cache.delete(url); });
    }
    return cache.get(url);
  }
  function getVerse(a) {
    var m = /(\d+)\s*$/.exec(a.textContent.trim());
    if (!m) return Promise.reject(new Error("no verse"));
    var n = m[1];
    return loadPage(noHash(a.href)).then(function (doc) {
      var li = doc.querySelector("li.verse#v" + n);
      var lines = li ? linesOf(li) : [];
      if (!lines.length) throw new Error("missing");
      return { n: n, ref: a.textContent.trim(), lines: lines, href: noHash(a.href) + "#v" + n };
    });
  }

  // a word counts as the same if it is in our verse, or (texts differ in sandhi and word division) if it occurs
  // inside our verse written without spaces, allowing a changed final sound
  function has(mine, w) {
    var k = key(w); if (!k || mine[k]) return true;
    var core = k.length > 3 ? k.slice(0, -1) : k;
    return mine._all.indexOf(core) >= 0;
  }
  function renderVerse(v, mine) {
    var sc = script(), sav = !!P.get().savarna, diff = 0;
    var html = v.lines.map(function (line) {
      return line.split(/\s+/).filter(Boolean).map(function (w) {
        var r = esc(T.render(T.iastToSlp1(w), sc, sav));
        if (mine && !has(mine, w)) { diff++; return "<mark>" + r + "</mark>"; }
        return r;
      }).join(" ");
    });
    return { diff: diff, html: '<div class="pk-verse" lang="' + (sc === "knda" ? "sa-Knda" : sc === "deva" ? "sa-Deva" : "sa-Latn") + '">' +
      html.map(function (l) { return '<p class="pk-ln">' + l + "</p>"; }).join("") + "</div>" };
  }

  function unitWord() {
    var w = document.body.dataset.work, i = script() === "knda" ? 0 : script() === "deva" ? 1 : 2;
    var sub = w === "ram" || !w ? ["ಸರ್ಗ", "सर्गः", "Sarga"] : ["ಅಧ್ಯಾಯ", "अध्यायः", "Adhyāya"];
    return sub[i];
  }

  function close(fromPop) {
    if (!ui) return;
    var u = ui; ui = null; token++;
    document.removeEventListener("keydown", u.key, true);
    u.back.remove(); u.sheet.remove();
    if (u.from && u.from.focus) { try { u.from.focus(); } catch (e) { /* ignore */ } }
    if (!fromPop) { try { history.back(); } catch (e) { /* ignore */ } }
  }
  window.addEventListener("popstate", function () { if (ui) close(true); });

  function open(a) {
    if (ui) close(true);
    var badge = a.closest(".badge"), li = a.closest(".verse");
    var tm = /\bin the ([^:]+):/.exec(badge ? badge.textContent : "");
    var label = tm ? tm[1].trim() : "other text";
    var links = badge ? Array.prototype.slice.call(badge.querySelectorAll("a")) : [a];
    var mine = null;
    if (li) { mine = {}; var ws = words(linesOf(li)); ws.forEach(function (w) { mine[key(w)] = 1; }); mine._all = ws.map(key).join(""); }

    var back = document.createElement("div"); back.className = "pk-back";
    var sheet = document.createElement("div"); sheet.className = "pk-sheet";
    sheet.setAttribute("role", "dialog"); sheet.setAttribute("aria-modal", "true"); sheet.setAttribute("aria-labelledby", "pk-title");
    var refs = links.map(function (l) { return l.textContent.trim(); }).join(", ");
    sheet.innerHTML = '<div class="pk-head"><h2 id="pk-title" class="pk-title">' + esc(label + " · " + refs) + '</h2>' +
      '<button type="button" class="pk-x" aria-label="Close">✕</button></div>' +
      '<div class="pk-body" aria-live="polite"><p class="pk-msg">Loading…</p></div>' +
      '<div class="pk-foot"></div>';
    document.body.appendChild(back); document.body.appendChild(sheet);
    var x = sheet.querySelector(".pk-x"), body = sheet.querySelector(".pk-body"), foot = sheet.querySelector(".pk-foot");
    var first = links[0], chap = /(\d+)\/(?:#.*)?$/.exec(first.getAttribute("href") || "");
    var vn = (/(\d+)\s*$/.exec(first.textContent.trim()) || [0, ""])[1];
    var openHref = noHash(first.href) + "#v" + vn;
    var sc = script(), num = chap ? (sc === "iast" ? chap[1] : T.digits(chap[1], sc)) : "";
    foot.innerHTML = '<a class="pk-open" href="' + esc(openHref) + '">Open ' + esc((unitWord() + " " + num).trim()) + " in the " + esc(label) + "</a>";

    var my = ++token;
    var u = ui = { back: back, sheet: sheet, from: a };
    u.key = function (e) {
      if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); close(); return; }
      if (e.key === "Tab") {
        var f = Array.prototype.slice.call(sheet.querySelectorAll("a[href],button")); if (!f.length) return;
        var s = f[0], l = f[f.length - 1];
        if (e.shiftKey && document.activeElement === s) { e.preventDefault(); l.focus(); }
        else if (!e.shiftKey && document.activeElement === l) { e.preventDefault(); s.focus(); }
        else if (!sheet.contains(document.activeElement)) { e.preventDefault(); s.focus(); }
      }
    };
    document.addEventListener("keydown", u.key, true);
    back.addEventListener("click", function () { close(); });
    x.addEventListener("click", function () { close(); });
    try { history.pushState({ peek: 1 }, ""); } catch (e) { /* ignore */ }
    x.focus();

    Promise.all(links.map(function (l) { return getVerse(l); })).then(function (vs) {
      if (my !== token) return;
      var total = 0, out = vs.map(function (v) {
        var r = renderVerse(v, mine); total += r.diff;
        return '<section class="pk-v">' + (vs.length > 1 ? '<h3 class="pk-ref">' + esc(v.ref) + "</h3>" : "") + r.html + "</section>";
      }).join("");
      var note = mine ? (total ? total + (total === 1 ? " word differs" : " words differ") : "Same words, different order or lines") : "";
      body.innerHTML = out + (note ? '<p class="pk-note">' + note + "</p>" : "");
    }).catch(function () {
      if (my !== token) return;
      body.innerHTML = '<p class="pk-msg">Could not load this verse.</p>';
    });
  }

  document.addEventListener("click", function (e) {
    if (e.defaultPrevented || e.button || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    var a = e.target.closest && e.target.closest(".verse .badge a");
    if (!a) return;
    e.preventDefault(); open(a);
  });
})();
