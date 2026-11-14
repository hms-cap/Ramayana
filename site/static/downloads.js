/* Settings > Downloads: save one chip (kāṇḍa / parva) at a time for offline reading. Same cache ("vr-data") and pack list
   (data/offline.json) as the About page. */
(function () {
  "use strict";
  var ROOT = document.body.dataset.root || "";
  var list = document.getElementById("dl-list");
  if (!list || !("caches" in window)) return;
  var sheet = document.getElementById("dlsheet"), sum = document.getElementById("dl-sum");
  var allBtn = document.getElementById("dl-all"), clearBtn = document.getElementById("dl-clear");
  var packs = null, have = new Set(), work = null, jobs = {}, loaded = false;
  var WORKS = { ram: "Rāmāyaṇa", mbh: "Mahābhārata", gita: "Bhagavadgītā" };
  var OFFK = { ram: "off", mbh: "offMbh", gita: "offGita" };

  function abs(u) { return new URL(ROOT + u, location.href).href; }
  function mb(n) { return n < 1048576 ? Math.max(1, Math.round(n / 1024)) + " KB" : (n / 1048576).toFixed(n < 10485760 ? 1 : 0) + " MB"; }
  function offFor(w) { var o = (VRPrefs.get() || {})[OFFK[w]]; return Array.isArray(o) ? o : ["ce"]; }
  function enabled(p) { return p.e && offFor(p.w).indexOf(p.e) < 0; }
  function chips(w) {                                   // one entry per chip: its packs for the texts that are switched on
    var m = {}, order = [];
    packs.forEach(function (p) {
      if (p.w !== w || !p.e || !enabled(p)) return;
      if (!m[p.k]) { m[p.k] = { k: p.k, u: p.u, packs: [] }; order.push(p.k); }
      m[p.k].packs.push(p);
    });
    return order.map(function (k) { return m[k]; });
  }
  function core(w) { return packs.filter(function (p) { return p.w === w && !p.e; })[0]; }
  function urlsOf(ps) { var r = []; ps.forEach(function (p) { r = r.concat(p.urls); }); return r; }
  function stored(ps) { var u = urlsOf(ps), n = u.filter(function (x) { return have.has(abs(x)); }).length; return [n, u.length]; }
  function bytes(ps) { return ps.reduce(function (a, p) { return a + p.bytes; }, 0); }
  function name(u) { return '<span class="sx sx-kn" lang="kn">' + u[0] + '</span><span class="sx sx-deva" lang="sa">' + u[1] + '</span><span class="sx sx-iast" lang="sa-Latn">' + u[2] + '</span>'; }

  function refresh() {
    return caches.open("vr-data").then(function (c) { return c.keys(); }).then(function (ks) { have = new Set(ks.map(function (r) { return r.url; })); paint(); });
  }
  function rowHtml(key, label, ps) {
    var st = stored(ps), job = jobs[key], full = st[0] === st[1], btn, state;
    if (job) { btn = '<button type="button" class="btn rm" data-dl-cancel="' + key + '">Cancel</button>'; state = "Downloading…"; }
    else if (full) { btn = '<span class="btn ok">✓ Saved</span><button type="button" class="btn rm" data-dl-remove="' + key + '">Remove</button>'; state = "Saved"; }
    else { btn = '<button type="button" class="btn" data-dl="' + key + '">Download</button>'; state = st[0] ? st[0] + " of " + st[1] + " pages saved" : ""; }
    var pct = job ? Math.round(100 * job.done / Math.max(1, job.total)) : 0;
    return '<div class="dl"><div class="nm">' + label + "<small>" + mb(bytes(ps)) + (state ? " · " + state : "") + "</small>" +
      (job ? '<div class="pg"><i style="width:' + pct + '%"></i></div>' : "") + "</div>" + btn + "</div>";
  }
  var byKey = {};
  function paint() {
    if (!packs) return;
    var cs = chips(work), cr = core(work);
    byKey = {};
    var html = cs.map(function (c) { byKey["k" + c.k] = c.packs; return rowHtml("k" + c.k, c.packs.length && cs.length > 1 ? name(c.u) : name(c.u), c.packs); }).join("");
    if (cr) { byKey.core = [cr]; html += rowHtml("core", "Search index and verse-of-the-day cards", [cr]); }
    list.innerHTML = html;
    var every = cs.reduce(function (a, c) { return a.concat(c.packs); }, []).concat(cr ? [cr] : []);
    byKey.all = every;
    var st = stored(every);
    document.getElementById("dl-all-name").textContent = "All of " + WORKS[work];
    document.getElementById("dl-all-size").textContent = mb(bytes(every)) + (st[0] === st[1] ? " · all saved" : "");
    allBtn.hidden = st[0] === st[1]; allBtn.disabled = !!jobs.all;
    var used = packs.filter(function (p) { var s = stored([p]); return s[0] === s[1] && s[1]; }).reduce(function (a, p) { return a + p.bytes; }, 0);
    document.getElementById("dl-used").textContent = used ? "About " + mb(used) + " saved on this device" : "Nothing saved yet";
    clearBtn.hidden = !used;
    var done = packs.filter(function (p) { var s = stored([p]); return p.e && s[0] === s[1]; }).length;
    if (sum) sum.textContent = done ? done + " saved" : "Save for offline";
    document.querySelectorAll("[data-dl-work]").forEach(function (b) { b.setAttribute("aria-selected", b.dataset.dlWork === work ? "true" : "false"); });
  }
  function run(key) {
    var ps = byKey[key]; if (!ps || jobs[key]) return;
    var todo = urlsOf(ps).filter(function (u) { return !have.has(abs(u)); }).map(abs);
    if (!todo.length) return;
    if (!navigator.onLine) { document.getElementById("dl-used").textContent = "You are offline. Try again when you are connected."; return; }
    var job = jobs[key] = { done: 0, total: todo.length, cancel: false, failed: 0 };
    paint();
    caches.open("vr-data").then(function (c) {
      function worker() {
        var u = todo.shift(); if (!u || job.cancel) return Promise.resolve();
        return fetch(u).then(function (r) { if (!r.ok) throw 0; return c.put(u, r); }).catch(function () { job.failed++; })
          .then(function () { job.done++; if (job.done % 4 === 0) paint(); return worker(); });
      }
      return Promise.all([worker(), worker(), worker(), worker(), worker(), worker()]);
    }).then(function () { delete jobs[key]; return refresh(); }).then(function () {
      if (job.failed) document.getElementById("dl-used").textContent = job.failed + " files failed. Try again.";
    });
  }
  function remove(key) {
    var ps = byKey[key]; if (!ps) return Promise.resolve();
    return caches.open("vr-data").then(function (c) {
      return Promise.all(urlsOf(ps).map(function (u) { return c.delete(abs(u), { ignoreSearch: true }); }));
    }).then(refresh);
  }
  function load() {
    if (loaded) return paint(); loaded = true;
    fetch(ROOT + "data/offline.json").then(function (r) { return r.json(); }).then(function (d) { packs = d.packs; return refresh(); })
      .catch(function () { loaded = false; list.innerHTML = '<p class="hint">The list of downloads could not be loaded.</p>'; });
  }
  document.addEventListener("click", function (e) {
    var t;
    if ((t = e.target.closest("[data-open-sheet=dlsheet]"))) {
      var w = document.body.dataset.work; work = work || (WORKS[w] ? w : "ram"); load(); return;
    }
    if (!sheet || sheet.hidden) return;
    if ((t = e.target.closest("[data-dl-work]"))) { work = t.dataset.dlWork; paint(); return; }
    if ((t = e.target.closest("[data-dl]"))) { run(t.dataset.dl); return; }
    if ((t = e.target.closest("[data-dl-cancel]"))) { var j = jobs[t.dataset.dlCancel]; if (j) j.cancel = true; return; }
    if ((t = e.target.closest("[data-dl-remove]"))) { remove(t.dataset.dlRemove); return; }
    if (e.target.closest("#dl-all")) { run("all"); return; }
    if (e.target.closest("#dl-clear") && packs && confirm("Remove all downloaded pages from this device?")) {
      byKey.every = packs; remove("every"); }
  });
  document.addEventListener("prefs-changed", function () { if (loaded && packs) paint(); });
})();
