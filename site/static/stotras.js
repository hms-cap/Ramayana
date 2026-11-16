/* Pariśiṣṭa → Stotras: work tabs, deity chips, search, Read / Chant links, and "My daily stotras".
   The address keeps the stotra you opened (#id), so Back from the reader lands on it. Without JavaScript
   every section is shown and the links still open the reader at the hymn. */
(function () {
  "use strict";
  var T = window.Translit, D = window.VRDaily, P = window.VRPrefs;
  var tabs = [].slice.call(document.querySelectorAll("[data-st-tab]"));
  var secs = [].slice.call(document.querySelectorAll("[data-st-sec]"));
  if (!secs.length) return;
  var ids = tabs.map(function (t) { return t.dataset.stTab; });
  var q = document.getElementById("st-q");

  function setHash(h) { try { history.replaceState(history.state, "", "#" + h); } catch (e) { /* ignore */ } }
  function show(w) {
    secs.forEach(function (s) { s.hidden = s.dataset.stSec !== w; });
    tabs.forEach(function (t) { var on = t.dataset.stTab === w; t.classList.toggle("on", on); t.setAttribute("aria-selected", on ? "true" : "false"); });
  }
  function workOf(li) { var s = li && li.closest("[data-st-sec]"); return s && s.dataset.stSec; }
  function start() {
    var h = decodeURIComponent(location.hash.slice(1)), li = h && document.getElementById(h);
    if (li && li.classList.contains("st")) { show(workOf(li)); focusItem(li); return; }
    if (ids.indexOf(h) >= 0) { show(h); return; }
    var w = null;
    try { w = localStorage.getItem("vr.work"); } catch (e) { /* ignore */ }
    if (w === "gita") w = "mbh";
    show(ids.indexOf(w) >= 0 ? w : ids[0]);
  }
  function focusItem(li) {
    document.querySelectorAll(".st.st-now").forEach(function (x) { x.classList.remove("st-now"); });
    li.hidden = false; li.classList.add("st-now");
    setTimeout(function () { li.scrollIntoView({ block: "center" }); }, 0);
  }
  tabs.forEach(function (t) {
    t.addEventListener("click", function (e) { e.preventDefault(); show(t.dataset.stTab); setHash(t.dataset.stTab); filter(); });
  });

  // ---- deity chips and search (both narrow the visible section) ----
  function norm(s) { return String(s).normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase(); }
  function filter() {
    var raw = q ? q.value.trim() : "", plain = norm(raw), loose = raw && T ? T.queryToLoose(raw) : "";
    secs.forEach(function (sec) {
      var on = sec.querySelector("[data-deity][aria-pressed=true]"), dei = on ? on.dataset.deity : "", any = false;
      sec.querySelectorAll(".st").forEach(function (li) {
        var f = li.dataset.find || "", ok = !dei || li.dataset.deity === dei;
        if (ok && raw) {
          ok = norm(f).indexOf(plain) >= 0;
          if (!ok && loose.length >= 2 && T) ok = T.looseForIndex(T.iastToSlp1(f)).indexOf(loose) >= 0;
        }
        li.hidden = !ok; any = any || ok;
      });
      sec.querySelectorAll(".st-grp").forEach(function (g) { g.hidden = !g.querySelector(".st:not([hidden])"); });
      var none = sec.querySelector(".st-none"); if (none) none.hidden = any;
    });
  }
  document.addEventListener("click", function (e) {
    var c = e.target.closest("[data-deity]");
    if (c && c.tagName === "BUTTON") {
      c.parentNode.querySelectorAll("[data-deity]").forEach(function (b) { b.setAttribute("aria-pressed", b === c ? "true" : "false"); });
      filter();
    }
  });
  if (q) q.addEventListener("input", function () {
    filter();
    // a match in the other work only: switch to it
    var cur = secs.filter(function (s) { return !s.hidden; })[0];
    if (cur && !cur.querySelector(".st:not([hidden])")) {
      var other = secs.filter(function (s) { return s !== cur && s.querySelector(".st:not([hidden])"); })[0];
      if (other) show(other.dataset.stSec);
    }
  });

  // ---- Read and Chant: remember the item in the address first, so Back returns to it ----
  document.addEventListener("click", function (e) {
    var a = e.target.closest("[data-st-read], [data-st-chant]");
    if (!a || e.defaultPrevented || e.button > 0 || e.metaKey || e.ctrlKey || e.shiftKey) return;
    var id = a.dataset.id || (a.closest(".st") || {}).id;
    if (id) setHash(id);
    if (a.hasAttribute("data-st-chant")) {
      e.preventDefault();
      var u = new URL(a.href, location.href);
      try { sessionStorage.setItem("vr.stchant", u.pathname + u.hash); } catch (x) { /* ignore */ }
      location.assign(a.href);
    }
  });

  // ---- daily stotras ----
  var box = document.getElementById("st-daily"), dl = document.getElementById("st-dlist");
  function paintDaily() {
    if (!D) return;
    document.querySelectorAll("[data-st-daily]").forEach(function (b) {
      var on = D.has(b.closest(".st").id);
      b.setAttribute("aria-pressed", on ? "true" : "false"); b.textContent = on ? "★ Daily" : "☆ Daily";
    });
    var list = D.ids().map(function (id) { return document.getElementById(id); }).filter(Boolean);
    box.hidden = !list.length;
    var d = new Date();
    document.getElementById("st-today").textContent = d.toLocaleDateString(undefined, { weekday: "long", day: "numeric", month: "long" });
    dl.innerHTML = "";
    list.forEach(function (li) {
      var id = li.id, done = D.done(id), href = li.querySelector("[data-st-read]").getAttribute("href");
      var row = document.createElement("div"); row.className = "st-drow" + (done ? " done" : "");
      row.innerHTML = '<button type="button" class="st-tick" data-st-tick="' + id + '" aria-pressed="' + done + '" aria-label="Done today">' + (done ? "✓" : "") + "</button>" +
        '<a class="st-dname" href="' + href + '" data-st-read data-id="' + id + '">' + li.querySelector(".st-name").innerHTML + "</a>" +
        '<a class="stb" href="' + href + '" data-st-chant data-id="' + id + '" aria-label="Chant">▶</a>';
      dl.appendChild(row);
    });
  }
  document.addEventListener("click", function (e) {
    var b = e.target.closest("[data-st-daily]");
    if (b && D) { D.toggle(b.closest(".st").id); return; }
    b = e.target.closest("[data-st-tick]");
    if (b && D) { D.mark(b.dataset.stTick, !D.done(b.dataset.stTick)); }
  });
  document.addEventListener("daily-changed", paintDaily);
  window.addEventListener("pageshow", paintDaily);   // back from a chant that ticked one off
  window.addEventListener("hashchange", start);
  if (P) document.addEventListener("prefs-changed", paintDaily);

  start(); filter(); paintDaily();
})();
