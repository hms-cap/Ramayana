(function () {
  "use strict";
  var T = window.Translit;
  var q = document.getElementById("q"), edSel = document.getElementById("ed"), kf = document.getElementById("kf");
  var status = document.getElementById("status"), list = document.getElementById("results");
  var cache = {}, timer = null, MAX = 100;

  function loadIndex(ed) {
    if (cache[ed]) return cache[ed];
    status.textContent = "Loading the search index…";
    cache[ed] = fetch("../data/search-" + ed + ".json").then(function (r) {
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
      var ref = h.k + "." + h.s + "." + h.v;
      var li = el("li"), a = el("a", "ref", ref);
      a.href = "../" + ed + "/" + h.k + "/" + h.s + "/#v" + h.v;
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
    if (!raw) { list.textContent = ""; status.textContent = ""; return; }
    var key = T.queryToLoose(raw);
    if (key.length < 2) { list.textContent = ""; status.textContent = "Type at least two letters."; return; }
    loadIndex(ed).then(function (rows) {
      if (q.value.trim() !== raw) return;
      var hits = [], total = 0;
      for (var i = 0; i < rows.length; i++) {
        var r = rows[i];
        if (k && r.k !== k) continue;
        if (r.key.indexOf(key) >= 0) { total++; if (hits.length < MAX) hits.push(r); }
      }
      show(hits, total, ed);
    }, function () { status.textContent = "The search index could not be loaded. Check your connection and search again."; });
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
