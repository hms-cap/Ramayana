/* Reader pages opened at a stotra or gītā (#vA-B, from Pariśiṣṭa → Stotras / Gītās): only its verses are shown, with
   a bar under the header (name, part, position, Chant); ‹ goes back to the list at this item; an end card after the
   last verse (Next part for gītās that run over several adhyāyas). app.js marks the verses (markRange).
   Index: data/stotras.json [{id, t:"s"|"g", l: list path, w, n, e, by, to, parts:{vu|ce|gita: [[k,s,a,b],…]}}].
   sessionStorage "vr.stchant" (a path+hash, or JSON {p, back}) opens chant straight away on arrival. */
(function () {
  "use strict";
  var T = window.Translit, P = window.VRPrefs, D = window.VRDaily;
  var B = document.body.dataset, ROOT = B.root || "";
  var PRE = { ram: "", mbh: "mbh/", gita: "gita/" };
  var bar = null, cur = null, idx = null, nextAfterPop = null;

  function sc() { var s = (P && P.get().script) || "knda"; return s === "deva" || s === "iast" ? s : "knda"; }
  function name3(iast) { var x = T.iastToSlp1(iast); return { knda: T.render(x, "knda", false), deva: T.render(x, "deva", false), iast: iast }; }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function digits(n) { return sc() === "iast" ? String(n) : T.digits(String(n), sc()); }
  function here() {
    var m = /(?:^|\/)(?:(mbh|gita)\/)?(vu|ce)\/(\d+)\/(\d+)\/?$/.exec(location.pathname.replace(/index\.html$/, ""));
    return m ? { w: m[1] || "ram", ed: m[2], k: +m[3], s: +m[4] } : null;
  }
  function range() { var m = /^#v(\d+)-(\d+)$/.exec(location.hash); return m ? [+m[1], +m[2]] : null; }
  function partHref(st, key, i) {   // reader address of part i in the given edition (else the first edition it has)
    var k = key && st.parts[key] ? key : Object.keys(st.parts)[0], p = st.parts[k][i || 0];
    var pre = k === "gita" ? "gita/vu/" : PRE[st.w] + k + "/";
    return ROOT + pre + p[0] + "/" + p[1] + "/#v" + p[2] + "-" + p[3];
  }
  function multi(st) { return Object.keys(st.parts).some(function (k) { return st.parts[k].length > 1; }); }
  function listHref(st) { return ROOT + (st.l || "appendix/stotras/") + (multi(st) ? st.id + "/" : "#" + st.id); }
  function isGita(st) { return st.t === "g"; }
  // passages can overlap (the Brāhmaṇagītā is inside the Anugītā): the one opened last wins ("vr.stid", this tab)
  function prefId() { try { return sessionStorage.getItem("vr.stid"); } catch (e) { return null; } }
  function setId(id) { try { sessionStorage.setItem("vr.stid", id); } catch (e) { /* ignore */ } }
  function find(list, h, r) {   // → {st, key, i (part), n (parts)}
    var key = h.w === "gita" ? "gita" : h.ed, want = prefId();
    if (want) {
      var pick = list.filter(function (x) { return x.id === want; });
      list = pick.concat(list.filter(function (x) { return x.id !== want; }));
    }
    for (var j = 0; j < list.length; j++) {
      var st = list[j], pp = st.parts[key];
      if (!pp || (h.w !== "gita" && st.w !== h.w)) continue;
      for (var i = 0; i < pp.length; i++) {
        var p = pp[i];
        if (p[0] === h.k && p[1] === h.s && p[2] === r[0] && p[3] === r[1]) return { st: st, key: key, i: i, n: pp.length };
      }
    }
    return null;
  }
  function verses(r) {
    return [].filter.call(document.querySelectorAll(".verses > .verse[id]"), function (li) { var n = +li.id.slice(1); return n >= r[0] && n <= r[1]; });
  }
  function u(h) { var x = new URL(h, location.href); return x.pathname + x.hash; }
  function goNext(back) {   // next part, keeping history short: leave the chant's own entry first, then replace this page
    var h = partHref(cur.st, cur.key, cur.i + 1);
    try { sessionStorage.setItem("vr.stchant", JSON.stringify({ p: u(h), back: back })); } catch (e) { /* ignore */ }
    nextAfterPop = h; history.back();
  }
  function chant(back) {
    var r = range(); if (!r || !window.VRChant || !window.VRChant.openRange) return;
    var st = cur.st, last = cur.i === cur.n - 1;
    window.VRChant.openRange(r[0], r[1], {
      title: name3(st.n), id: st.id, back: back,
      part: cur.n > 1 ? { i: cur.i + 1, n: cur.n } : null,
      next: last ? null : function () { goNext(back); },
      onDone: function () { if (last && D && D.has(st.id)) D.mark(st.id, true); }
    });
  }

  function clear() {
    if (bar) bar.remove(); bar = null;
    document.querySelectorAll(".st-endli, .st-note").forEach(function (x) { x.remove(); });
    document.body.classList.remove("st-all");
    document.body.classList.remove("in-stotra");
    document.querySelectorAll("[data-back][data-up]").forEach(function (a) { a.setAttribute("href", a.dataset.up); a.setAttribute("aria-label", "Back"); });
  }
  function paint() {
    clear();
    var h = here(), r = range(); if (!h || !r || !idx) return;
    cur = find(idx, h, r); if (!cur) return;
    setId(cur.st.id);
    try {   // last stotra / gītā read, for Home → Continue reading
      localStorage.setItem("vr.last.st", JSON.stringify({ id: cur.st.id, title: name3(cur.st.n), href: location.pathname + location.hash, list: cur.st.t === "g" ? "gitas" : "stotras", ts: Date.now() }));
    } catch (e) { /* ignore */ }
    var st = cur.st, vs = verses(r); if (!vs.length) { cur = null; return; }
    var nm = name3(st.n)[sc()], n = r[1] - r[0] + 1, multi = cur.n > 1, last = cur.i === cur.n - 1;
    var what = isGita(st) ? "Gītās" : "Stotras";
    bar = document.createElement("div");
    bar.className = "stbar"; bar.setAttribute("role", "region"); bar.setAttribute("aria-label", isGita(st) ? "Gītā" : "Stotra");
    bar.innerHTML = '<a class="stbar-bk" href="' + esc(listHref(st)) + '" aria-label="Back to ' + what + '">‹</a>' +
      '<div class="stbar-nm"><b lang="' + (sc() === "knda" ? "sa-Knda" : sc() === "deva" ? "sa-Deva" : "sa-Latn") + '">' + esc(nm) + '</b><small><span class="stbar-pos"></span></small></div>' +
      '<button type="button" class="stbar-go">▶ Chant</button><i class="stbar-prog" aria-hidden="true"><i></i></i>';
    var hdr = document.querySelector("header.bar, .bar");
    var anchor = document.querySelector(".reader") || document.querySelector("main");
    anchor.parentNode.insertBefore(bar, anchor);
    bar.style.top = (hdr ? hdr.getBoundingClientRect().height : 0) + "px";
    document.body.classList.add("in-stotra");
    document.querySelectorAll("[data-back]").forEach(function (a) { if (!a.dataset.up) a.dataset.up = a.getAttribute("href"); a.setAttribute("href", listHref(st)); a.setAttribute("aria-label", "Back to " + what); });
    // the end card, after the last verse of this part
    var end = document.createElement("li");
    end.className = "st-endli";
    var inD = D && D.has(st.id), acts = "";
    if (!last) {
      end.innerHTML = '<p><b>End of part ' + digits(cur.i + 1) + " of " + digits(cur.n) + '</b><small>' + esc(nm) + "</small></p>" +
        '<div class="st-endacts"><a class="stb dk" data-replace href="' + esc(partHref(st, cur.key, cur.i + 1)) + '">Next part ›</a>' +
        '<button type="button" class="stb" data-st-again>▶ Chant this part</button><a class="stb gh" href="' + esc(listHref(st)) + '">Back to list</a></div>';
    } else {
      var i = idx.indexOf(st), nx = null;
      for (var j = i + 1; j < idx.length; j++) { if (idx[j].w === st.w && idx[j].t === st.t) { nx = idx[j]; break; } }
      acts = '<button type="button" class="stb dk" data-st-again>▶ Chant' + (multi ? " this part" : "") + "</button>" +
        (nx ? '<a class="stb" data-st-id="' + esc(nx.id) + '" href="' + esc(partHref(nx, cur.key === "gita" ? "vu" : cur.key, 0)) + '">Next: ' + esc(name3(nx.n)[sc()]) + " ›</a>" : "") +
        '<a class="stb gh" href="' + esc(listHref(st)) + '">Back to list</a>' +
        (D ? '<button type="button" class="stb gh" data-st-dly aria-pressed="' + inD + '">' + (inD ? "★ Daily" : "☆ Daily") + "</button>" : "");
      end.innerHTML = '<p><b>End of ' + esc(nm) + '</b><small>' + (multi ? "Part " + digits(cur.n) + " of " + digits(cur.n) + " · " : "") + n + " verse" + (n === 1 ? "" : "s") + "</small></p>" +
        '<div class="st-endacts">' + acts + "</div>";
    }
    vs[vs.length - 1].after(end);
    // only these verses are shown; a note above says so and offers the whole chapter
    var ol = document.querySelector(".verses"), total = document.querySelectorAll(".verses > .verse[id]").length;
    if (ol && total > n) {
      var note = document.createElement("p"); note.className = "st-note";
      note.innerHTML = "Showing " + (isGita(st) ? "the gītā" : "the stotra") + " only (" + digits(n) + " of " + digits(total) + ' verses). <button type="button" data-st-all>Show the whole chapter</button>';
      ol.parentNode.insertBefore(note, ol);
    }
    progress();
  }
  function progress() {
    if (!bar || !cur) return;
    var r = range(), vs = verses(r), top = bar.getBoundingClientRect().bottom + 4, at = 0;
    for (var i = 0; i < vs.length; i++) { if (vs[i].getBoundingClientRect().bottom > top) { at = i; break; } at = i; }
    var n = vs.length;
    bar.querySelector(".stbar-pos").textContent = (cur.n > 1 ? "Part " + digits(cur.i + 1) + " of " + digits(cur.n) + " · " : "") +
      "Verses " + digits(r[0]) + "–" + digits(r[1]) + " · " + digits(at + 1) + " of " + digits(n);
    bar.querySelector(".stbar-prog > i").style.width = Math.round((at + 1) / n * 100) + "%";
  }

  document.addEventListener("click", function (e) {
    if (!cur) return;
    var nid = e.target.closest("[data-st-id]"); if (nid) setId(nid.dataset.stId);
    var al = e.target.closest("[data-st-all]");
    if (al) { var on = document.body.classList.toggle("st-all"); al.textContent = on ? "Show " + (isGita(cur.st) ? "the gītā" : "the stotra") + " only" : "Show the whole chapter"; if (on) { var f = document.querySelector(".verse.st-first"); if (f) f.scrollIntoView({ block: "start" }); } return; }
    var b = e.target.closest(".stbar-go, [data-st-again]");
    if (b) { chant(false); return; }
    b = e.target.closest("[data-st-dly]");
    if (b && D) { var on2 = D.toggle(cur.st.id); b.setAttribute("aria-pressed", on2); b.textContent = on2 ? "★ Daily" : "☆ Daily"; return; }
    // ‹ in the bar or the page header: back to the list (history when we came from it, so its place is kept)
    b = e.target.closest(".stbar-bk, [data-back], .st-endli a.gh");
    if (b && document.body.classList.contains("in-stotra")) {
      e.preventDefault(); e.stopPropagation();
      var ref = ""; try { ref = document.referrer ? new URL(document.referrer).pathname : ""; } catch (x) { /* ignore */ }
      if (window.VRNav && VRNav.canBack()) history.back();   // the trail knows where we came from (v0.23)
      else if (window.VRNav) VRNav.replace(listHref(cur.st)); else location.assign(listHref(cur.st));
    }
  }, true);
  window.addEventListener("popstate", function () { if (nextAfterPop) { var h = nextAfterPop; nextAfterPop = null; (window.VRNav ? VRNav.replace(h) : location.replace(h)); } });
  var t;
  window.addEventListener("scroll", function () { clearTimeout(t); t = setTimeout(progress, 80); }, { passive: true });
  window.addEventListener("hashchange", paint);
  document.addEventListener("prefs-changed", paint);

  if (!range()) return;
  // hide the other verses at once (before the first scroll), so the page starts at the first verse of the range;
  // paint() keeps this if the range is a known stotra / gītā part and clears it otherwise
  document.body.classList.add("in-stotra");
  function top() { var f = document.querySelector(".verse.st-first"); if (f) { f.scrollIntoView({ block: "start" }); window.scrollBy(0, -((bar ? bar.getBoundingClientRect().bottom : 0) + 4)); } }
  fetch(ROOT + "data/stotras.json").then(function (r) { return r.json(); }).then(function (list) {
    idx = list; paint();
    if (!cur) document.body.classList.remove("in-stotra"); else top();
    var want = null; try { want = sessionStorage.getItem("vr.stchant"); sessionStorage.removeItem("vr.stchant"); } catch (e) { /* ignore */ }
    var w = want, back = true;
    if (want && want.charAt(0) === "{") { try { var o = JSON.parse(want); w = o.p; back = !!o.back; } catch (e) { w = null; } }
    if (cur && w && w === location.pathname + location.hash) chant(back);
  }).catch(function () { document.body.classList.remove("in-stotra"); });
})();
