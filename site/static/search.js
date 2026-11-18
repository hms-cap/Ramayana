(function () {
  "use strict";
  var T = window.Translit;
  var q = document.getElementById("q"), edSel = document.getElementById("ed"), kf = document.getElementById("kf");
  var status = document.getElementById("status"), list = document.getElementById("results");
  var cache = {}, timer = null, MAX = 100, WROOT = document.body.dataset.wroot || "../";
  var GITA = document.body.dataset.work === "gita";   // one unit: refs are adhyāya.verse and the filter picks an adhyāya

  function loadIndex(ed) {
    if (cache[ed]) return cache[ed];
    status.textContent = "Loading the search index…";
    cache[ed] = fetch(WROOT + "data/search-" + ed + ".json").then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    }).then(function (rows) {
      return rows.map(function (r) { return { k: r[0], s: r[1], v: r[2], slp1: r[3], key: T.looseForIndex(r[3]) }; });
    });
    cache[ed].catch(function () { delete cache[ed]; });
    return cache[ed];
  }

  function line(slp1, script, ref) {
    var savarna = !!(window.VRPrefs && window.VRPrefs.get().savarna);
    var parts = slp1.split(" / ");
    return parts.map(function (p, i) {
      var t = T.render(p, script, savarna);
      var nb = "\u00a0";
      if (script === "iast") t += i === parts.length - 1 ? nb + "||" + nb + ref + nb + "||" : nb + "|";
      else t += i === parts.length - 1 ? nb + "॥" + nb + T.digits(ref, script) + nb + "॥" : nb + "।";
      return t;
    });
  }

  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }

  function show(hits, total, ed) {
    list.textContent = "";
    hits.forEach(function (h) {
      var ref = GITA ? (h.s === 0 ? String(h.v) : h.s + "." + h.v) : h.k + "." + h.s + "." + h.v;
      var li = el("li"), a = el("a", "ref", ref);
      a.href = WROOT + ed + "/" + h.k + "/" + h.s + "/#v" + h.v;
      li.appendChild(a);
      [["knda", "sa-Knda"], ["deva", "sa-Deva"], ["iast", "sa-Latn"]].forEach(function (sc) {
        var d = el("div", "t t-" + sc[0]); d.lang = sc[1];
        var p = el("p");
        line(h.slp1, sc[0], ref).forEach(function (l) { p.appendChild(el("span", "ln", l)); });
        d.appendChild(p); li.appendChild(d);
      });
      list.appendChild(li);
    });
    status.textContent = total === 0 ? "No verses match. Try fewer letters, or a different spelling." :
      total > hits.length ? total.toLocaleString() + " verses match; showing the first " + hits.length + "." :
      total + (total === 1 ? " verse matches." : " verses match.");
  }

  function run() {
    var raw = q.value.trim(), ed = edSel.value, k = kf.value ? +kf.value : 0;
    var params = new URLSearchParams();
    if (raw) params.set("q", raw);
    if (ed !== edSel.options[0].value) params.set("ed", ed);
    if (k) params.set("k", k);
    history.replaceState(null, "", params.toString() ? "?" + params : location.pathname);
    stotras(raw);
    if (!raw) { list.textContent = ""; status.textContent = ""; return; }
    var key = T.queryToLoose(raw);
    if (key.length < 2) { list.textContent = ""; status.textContent = "Type at least two letters."; return; }
    loadIndex(ed).then(function (rows) {
      if (q.value.trim() !== raw) return;
      var hits = [], total = 0;
      for (var i = 0; i < rows.length; i++) {
        var r = rows[i];
        if (k && (GITA ? r.s : r.k) !== k) continue;
        if (r.key.indexOf(key) >= 0) { total++; if (hits.length < MAX) hits.push(r); }
      }
      show(hits, total, ed);
    }, function () { status.textContent = "The search index could not be loaded. Check your connection and search again."; });
  }

  // Stotras whose name, English title, singer or deity match: shown above the verse hits, linking to the Pariśiṣṭa.
  var ROOT = document.body.dataset.root || WROOT, stot = null, stBox = document.getElementById("st-hits");
  function stotras(raw) {
    if (!stBox) return;
    var key = T.queryToLoose(raw), low = raw.toLowerCase();
    if (!raw || key.length < 3) { stBox.hidden = true; return; }
    if (!stot) stot = fetch(ROOT + "data/stotras.json").then(function (r) { return r.json(); }).catch(function () { stot = null; return []; });
    stot.then(function (rows) {
      if (q.value.trim() !== raw) return;
      var sc = (window.VRPrefs && window.VRPrefs.get().script) || "knda"; if (sc.indexOf("-") > 0) sc = sc.split("-")[0];
      var hits = rows.filter(function (r) {
        var k = T.looseForIndex(T.iastToSlp1([r.n, r.by, r.to].join(" ").toLowerCase()));
        return k.indexOf(key) >= 0 || r.e.toLowerCase().indexOf(low) >= 0;
      }).slice(0, 6);
      stBox.textContent = ""; stBox.hidden = !hits.length;
      if (!hits.length) return;
      stBox.appendChild(el("p", "st-hits-t", "Stotras, gītās and tales"));
      hits.forEach(function (r) {
        var a = el("a", "st-hit"); a.href = ROOT + (r.l || "appendix/stotras/") + "#" + r.id;
        a.appendChild(el("b", null, T.render(T.iastToSlp1(r.n), sc, false)));
        a.appendChild(el("small", null, r.e + " · " + (r.t === "g" ? "Gītā · " : r.t === "u" ? "Upākhyāna · " : "") + (r.w === "mbh" ? "Mahābhārata" : "Rāmāyaṇa")));
        stBox.appendChild(a);
      });
    });
  }

  function schedule() { clearTimeout(timer); timer = setTimeout(run, 180); }
  q.addEventListener("input", schedule);
  edSel.addEventListener("change", run);
  kf.addEventListener("change", run);
  document.addEventListener("prefs-changed", function () { if (q.value.trim()) run(); });

  var p = new URLSearchParams(location.search);
  if (p.get("ed")) edSel.value = p.get("ed");
  if (p.get("k")) kf.value = p.get("k");
  if (p.get("q")) { q.value = p.get("q"); run(); }
})();
