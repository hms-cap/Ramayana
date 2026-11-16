/* Reader pages opened at a stotra (#vA-B, from Pariśiṣṭa → Stotras): a bar under the header with the stotra's
   name, how far in you are and Chant; ‹ goes back to the list at this stotra; an end card after the last verse.
   app.js marks the verses (markRange). Opening Chant from the list sets sessionStorage "vr.stchant". */
(function () {
  "use strict";
  var T = window.Translit, P = window.VRPrefs, D = window.VRDaily;
  var B = document.body.dataset, ROOT = B.root || "";
  var PRE = { ram: "", mbh: "mbh/", gita: "gita/" };
  var bar = null, cur = null, idx = null;

  function sc() { var s = (P && P.get().script) || "knda"; return s === "deva" || s === "iast" ? s : "knda"; }
  function name3(iast) { var x = T.iastToSlp1(iast); return { knda: T.render(x, "knda", false), deva: T.render(x, "deva", false), iast: iast }; }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function digits(n) { return sc() === "iast" ? String(n) : T.digits(String(n), sc()); }
  function here() {
    var m = /(?:^|\/)(?:(mbh|gita)\/)?(vu|ce)\/(\d+)\/(\d+)\/?$/.exec(location.pathname.replace(/index\.html$/, ""));
    return m ? { w: m[1] || "ram", ed: m[2], k: +m[3], s: +m[4] } : null;
  }
  function range() { var m = /^#v(\d+)-(\d+)$/.exec(location.hash); return m ? [+m[1], +m[2]] : null; }
  function href(st, key) {   // reader address of a stotra: the given edition, else the first one it has
    var k = key && st.loc[key] ? key : Object.keys(st.loc)[0], l = st.loc[k];
    var pre = k === "gita" ? "gita/vu/" : PRE[st.w] + k + "/";
    return ROOT + pre + l[0] + "/" + l[1] + "/#v" + l[2] + "-" + l[3];
  }
  function listHref(st) { return ROOT + "appendix/stotras/#" + st.id; }
  function find(list, h, r) {
    var key = h.w === "gita" ? "gita" : h.ed;
    return list.filter(function (st) {
      var l = st.loc[key];
      return l && (h.w === "gita" || st.w === h.w) && l[0] === h.k && l[1] === h.s && l[2] === r[0] && l[3] === r[1];
    })[0] || null;
  }
  function verses(r) {
    return [].filter.call(document.querySelectorAll(".verses > .verse[id]"), function (li) { var n = +li.id.slice(1); return n >= r[0] && n <= r[1]; });
  }
  function chant(st, back) {
    var r = range(); if (!r || !window.VRChant || !window.VRChant.openRange) return;
    window.VRChant.openRange(r[0], r[1], { title: name3(st.n), id: st.id, back: back,
      onDone: function () { if (D && D.has(st.id)) D.mark(st.id, true); } });
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
    var st = find(idx, h, r); cur = st; if (!st) return;
    var vs = verses(r); if (!vs.length) return;
    var nm = name3(st.n)[sc()], n = r[1] - r[0] + 1;
    bar = document.createElement("div");
    bar.className = "stbar"; bar.setAttribute("role", "region"); bar.setAttribute("aria-label", "Stotra");
    bar.innerHTML = '<a class="stbar-bk" href="' + esc(listHref(st)) + '" aria-label="Back to Stotras">‹</a>' +
      '<div class="stbar-nm"><b lang="' + (sc() === "knda" ? "sa-Knda" : sc() === "deva" ? "sa-Deva" : "sa-Latn") + '">' + esc(nm) + '</b><small><span class="stbar-pos"></span></small></div>' +
      '<button type="button" class="stbar-go">▶ Chant</button><i class="stbar-prog" aria-hidden="true"><i></i></i>';
    var hdr = document.querySelector("header.bar, .bar");
    var anchor = document.querySelector(".reader") || document.querySelector("main");
    anchor.parentNode.insertBefore(bar, anchor);
    bar.style.top = (hdr ? hdr.getBoundingClientRect().height : 0) + "px";
    document.body.classList.add("in-stotra");
    document.querySelectorAll("[data-back]").forEach(function (a) { if (!a.dataset.up) a.dataset.up = a.getAttribute("href"); a.setAttribute("href", listHref(st)); a.setAttribute("aria-label", "Back to Stotras"); });
    // the end card, after the last verse of the stotra
    var i = idx.indexOf(st), nx = null;
    for (var j = i + 1; j < idx.length; j++) { if (idx[j].w === st.w || (st.w === "mbh" && idx[j].w === "mbh")) { nx = idx[j]; break; } }
    var end = document.createElement("li");
    end.className = "st-endli";
    var inD = D && D.has(st.id);
    end.innerHTML = '<p><b>End of ' + esc(nm) + '</b><small>' + n + " verse" + (n === 1 ? "" : "s") + "</small></p>" +
      '<div class="st-endacts"><button type="button" class="stb dk" data-st-again>▶ Chant</button>' +
      (nx ? '<a class="stb" href="' + esc(href(nx, h.w === "gita" ? "vu" : h.ed)) + '">Next: ' + esc(name3(nx.n)[sc()]) + " ›</a>" : "") +
      '<a class="stb gh" href="' + esc(listHref(st)) + '">Back to list</a>' +
      (D ? '<button type="button" class="stb gh" data-st-dly aria-pressed="' + inD + '">' + (inD ? "★ Daily" : "☆ Daily") + "</button>" : "") + "</div>";
    vs[vs.length - 1].after(end);
    // only the stotra's own verses are shown; a note above says so and offers the whole chapter
    var ol = document.querySelector(".verses"), total = document.querySelectorAll(".verses > .verse[id]").length;
    if (ol && total > n) {
      var note = document.createElement("p"); note.className = "st-note";
      note.innerHTML = 'Showing the stotra only (' + digits(n) + " of " + digits(total) + ' verses). <button type="button" data-st-all>Show the whole chapter</button>';
      ol.parentNode.insertBefore(note, ol);
    }
    progress();
  }
  function progress() {
    if (!bar) return;
    var r = range(), vs = verses(r), top = bar.getBoundingClientRect().bottom + 4, at = 0;
    for (var i = 0; i < vs.length; i++) { if (vs[i].getBoundingClientRect().bottom > top) { at = i; break; } at = i; }
    var n = vs.length;
    bar.querySelector(".stbar-pos").textContent = "Verses " + digits(r[0]) + "–" + digits(r[1]) + " · " + digits(at + 1) + " of " + digits(n);
    bar.querySelector(".stbar-prog > i").style.width = Math.round((at + 1) / n * 100) + "%";
  }

  document.addEventListener("click", function (e) {
    if (!cur) return;
    var al = e.target.closest("[data-st-all]");
    if (al) { var on = document.body.classList.toggle("st-all"); al.textContent = on ? "Show the stotra only" : "Show the whole chapter"; if (on) { var f = document.querySelector(".verse.st-first"); if (f) f.scrollIntoView({ block: "start" }); } return; }
    var b = e.target.closest(".stbar-go, [data-st-again]");
    if (b) { chant(cur, false); return; }
    b = e.target.closest("[data-st-dly]");
    if (b && D) { var on = D.toggle(cur.id); b.setAttribute("aria-pressed", on); b.textContent = on ? "★ Daily" : "☆ Daily"; return; }
    // ‹ in the bar or the page header: back to the list (history when we came from it, so its place is kept)
    b = e.target.closest(".stbar-bk, [data-back], .st-endli a.gh");
    if (b && document.body.classList.contains("in-stotra")) {
      e.preventDefault(); e.stopPropagation();
      var ref = ""; try { ref = document.referrer ? new URL(document.referrer).pathname : ""; } catch (x) { /* ignore */ }
      if (/\/appendix\/stotras\/?$/.test(ref) && history.length > 1) history.back(); else location.assign(listHref(cur));
    }
  }, true);
  var t;
  window.addEventListener("scroll", function () { clearTimeout(t); t = setTimeout(progress, 80); }, { passive: true });
  window.addEventListener("hashchange", paint);
  document.addEventListener("prefs-changed", paint);

  if (!range()) { if (!/#v\d+-\d+/.test(location.hash)) return; }
  fetch(ROOT + "data/stotras.json").then(function (r) { return r.json(); }).then(function (list) {
    idx = list; paint();
    var want = null; try { want = sessionStorage.getItem("vr.stchant"); sessionStorage.removeItem("vr.stchant"); } catch (e) { /* ignore */ }
    if (cur && want && want === location.pathname + location.hash) chant(cur, true);
  }).catch(function () { /* offline without the index: the verses are still marked */ });
})();
