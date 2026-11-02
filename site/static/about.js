/* About page: version state, "Check for updates", offline download packs. */
(function () {
  "use strict";
  var ROOT = document.body.dataset.root || "";
  var state = document.getElementById("app-state"), msg = document.getElementById("update-msg"), btn = document.getElementById("check-update");
  var secure = location.protocol === "https:" || location.hostname === "localhost";
  function newer(a, b) {            // is a newer than b?  ("0.4.1" vs "0.4.0")
    var x = a.split(".").map(Number), y = b.split(".").map(Number);
    for (var i = 0; i < 3; i++) { if ((x[i] || 0) !== (y[i] || 0)) return (x[i] || 0) > (y[i] || 0); }
    return false;
  }
  var mine = (self.VRAMAYANA && self.VRAMAYANA.version) || "0";
  function paintState() {
    if (!("serviceWorker" in navigator) || !secure) { state.textContent = "Offline use needs a secure (https) connection."; return; }
    state.textContent = navigator.serviceWorker.controller ? "Installed · ready to work offline" : "Getting ready for offline use…";
  }
  paintState();
  if ("serviceWorker" in navigator) navigator.serviceWorker.ready.then(paintState, function () { });

  function getVersion() {
    var u = ROOT + "static/version.js?fresh=" + Date.now();
    return fetch(u, { cache: "no-store" }).then(function (r) { if (!r.ok) throw new Error("http"); return r.text(); })
      .then(function (t) { var m = /version:\s*'([\d.]+)'/.exec(t); if (!m) throw new Error("parse"); return m[1]; });
  }
  btn.addEventListener("click", function () {
    if (!navigator.onLine) { msg.textContent = "You are offline. Try again when you are connected."; return; }
    msg.textContent = "Checking…"; btn.disabled = true;
    getVersion().then(function (v) {
      if (!newer(v, mine)) { msg.textContent = "You have the latest version (" + mine + ")."; return; }
      if (!("serviceWorker" in navigator)) { msg.textContent = "Version " + v + " is available. Reload the page to use it."; return; }
      msg.textContent = "Version " + v + " found. Getting it…";
      return navigator.serviceWorker.getRegistration().then(function (reg) {
        if (!reg) { msg.textContent = "Version " + v + " is available. Reload the page to use it."; return; }
        return reg.update().then(function () {
          var w = reg.installing || reg.waiting;
          if (!w) { msg.textContent = "Version " + v + " is available. Reload the page to use it."; return; }
          w.addEventListener("statechange", function () {
            if (w.state === "activated" || w.state === "installed") { btn.textContent = "Restart to use " + v; btn.disabled = false; btn.onclick = function () { location.reload(); }; msg.textContent = "Ready."; }
            if (w.state === "redundant") msg.textContent = "The update could not be installed. Try again.";
          });
        });
      });
    }).catch(function () { msg.textContent = "Could not reach the server to check. Try again later."; })
      .then(function () { if (!btn.onclick) btn.disabled = false; });
  });

  /* ---- offline packs ---- */
  var list = document.getElementById("packs"), pmsg = document.getElementById("pack-msg"), all = document.getElementById("pack-all");
  if (!("caches" in window)) { list.innerHTML = '<li class="status">This browser cannot store pages for offline use.</li>'; all.hidden = true; return; }
  var packs = [], have = new Set();
  function mb(n) { return (n / 1048576).toFixed(1) + " MB"; }
  function abs(u) { return new URL(ROOT + u, location.href).href; }
  function refresh() {
    return caches.open("vr-data").then(function (c) { return c.keys(); }).then(function (ks) { have = new Set(ks.map(function (r) { return r.url; })); paint(); });
  }
  function paint() {
    list.innerHTML = packs.map(function (p, i) {
      var n = p.urls.filter(function (u) { return have.has(abs(u)); }).length, done = n === p.urls.length;
      return '<li><span>' + p.label + ' <small>' + mb(p.bytes) + " · " + (done ? "stored" : n ? n + " of " + p.urls.length + " stored" : "not stored") + '</small></span> ' +
        (done ? "" : '<button type="button" class="act" data-pack="' + i + '">Download</button>') + "</li>";
    }).join("");
  }
  function download(sel) {
    var todo = [];
    sel.forEach(function (p) { p.urls.forEach(function (u) { if (!have.has(abs(u))) todo.push(abs(u)); }); });
    if (!todo.length) { pmsg.textContent = "Already stored."; return Promise.resolve(); }
    if (!navigator.onLine) { pmsg.textContent = "You are offline. Downloads resume when you are connected."; window.addEventListener("online", function once() { window.removeEventListener("online", once); download(sel); }); return Promise.resolve(); }
    var n = 0, total = todo.length, failed = 0;
    return caches.open("vr-data").then(function (c) {
      function worker() {
        var u = todo.shift(); if (!u) return Promise.resolve();
        return fetch(u).then(function (r) { if (!r.ok) throw 0; return c.put(u, r); }).catch(function () { failed++; })
          .then(function () { n++; pmsg.textContent = "Downloading " + n + " of " + total + "…"; return worker(); });
      }
      return Promise.all([worker(), worker(), worker(), worker(), worker(), worker()]);
    }).then(function () { pmsg.textContent = failed ? failed + " files failed. Try again." : "Done."; return refresh(); });
  }
  fetch(ROOT + "data/offline.json").then(function (r) { return r.json(); }).then(function (d) { packs = d.packs; return refresh(); })
    .catch(function () { list.innerHTML = '<li class="status">The list of downloads could not be loaded.</li>'; });
  list.addEventListener("click", function (e) { var b = e.target.closest("[data-pack]"); if (b) download([packs[+b.dataset.pack]]); });
  all.addEventListener("click", function () { download(packs); });
})();
