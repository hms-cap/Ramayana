/* Settings sheet (v0.22): segmented controls, size stepper, text-to-show, pañcāṅga place, update check.
   Preferences themselves live in app.js (VRPrefs); this file only draws and drives the sheet. */
(function () {
  "use strict";
  var root = document.documentElement, sheet = document.getElementById("settings");
  if (!sheet || !window.VRPrefs) return;
  var SIZES = ["s", "m", "l"];
  var PLACES = [["Bengaluru", 12.9716, 77.5946], ["Mysuru", 12.2958, 76.6394], ["Chennai", 13.0827, 80.2707], ["Hyderabad", 17.385, 78.4867],
    ["Mumbai", 19.076, 72.8777], ["Pune", 18.5204, 73.8567], ["Delhi", 28.6139, 77.209], ["Varanasi", 25.3176, 82.9739], ["Kolkata", 22.5726, 88.3639]];
  function $(s, r) { return (r || document).querySelector(s); }
  function $$(s, r) { return [].slice.call((r || document).querySelectorAll(s)); }
  function size() { return VRPrefs.get().size || "m"; }
  function setRadio(btns, on) { btns.forEach(function (b) { b.setAttribute("aria-checked", on(b) ? "true" : "false"); }); }

  /* ---- place (same default rule as home.js) ---- */
  function place() {
    try { var p = JSON.parse(localStorage.getItem("vr.place") || "null"); if (p && isFinite(p.lat) && isFinite(p.lon)) return p; } catch (e) { /* ignore */ }
    var tz = ""; try { tz = Intl.DateTimeFormat().resolvedOptions().timeZone || ""; } catch (e) { /* ignore */ }
    return /Kolkata|Calcutta/.test(tz) ? { lat: 12.9716, lon: 77.5946, name: "Bengaluru", guess: true } : { name: "Your time zone", guess: true };
  }
  function savePlace(p) {
    try { localStorage.setItem("vr.place", JSON.stringify(p)); } catch (e) { /* ignore */ }
    document.dispatchEvent(new CustomEvent("place-changed", { detail: p }));
    paint();
  }

  function paint() {
    var p = VRPrefs.get(), sz = size(), ids = $$("[data-ed-show]").map(function (b) { return b.dataset.edShow; }).filter(function (x) { return x !== "both"; });
    setRadio($$("[data-set-knfont]"), function (b) { return (p.knfont || "serif") === b.dataset.setKnfont; });
    setRadio($$("[data-set-theme]"), function (b) { return (p.theme || "light") === b.dataset.setTheme; });
    $$("[data-size-dot]").forEach(function (d) { d.classList.toggle("on", d.dataset.sizeDot === sz); });
    var i = SIZES.indexOf(sz);
    $("[data-size-step='-1']").disabled = i <= 0; $("[data-size-step='1']").disabled = i >= SIZES.length - 1;
    if (ids.length) {
      var off = VRPrefs.off(), shown = ids.filter(function (x) { return off.indexOf(x) < 0; }), cur = shown.length === 1 ? shown[0] : "both";
      setRadio($$("[data-ed-show]"), function (b) { return b.dataset.edShow === cur; });
    }
    var pl = place(), el = $("#set-place"); if (el) el.textContent = pl.name;
    $$("#placesheet [data-place]").forEach(function (b) { b.setAttribute("aria-checked", b.dataset.place === pl.name ? "true" : "false"); });
  }

  /* ---- place sub-sheet ---- */
  var plist = $("#placesheet .pl-list");
  if (plist) plist.innerHTML = PLACES.map(function (x) {
    return '<button type="button" role="radio" aria-checked="false" class="set-go" data-place="' + x[0] + '" data-lat="' + x[1] + '" data-lon="' + x[2] + '"><span>' + x[0] + '</span><b aria-hidden="true">✓</b></button>';
  }).join("");

  document.addEventListener("click", function (e) {
    var t;
    if ((t = e.target.closest("[data-set-knfont]"))) { VRPrefs.set("knfont", t.dataset.setKnfont === "serif" ? "" : "sans"); return; }
    if ((t = e.target.closest("[data-set-theme]"))) { VRPrefs.set("theme", t.dataset.setTheme === "light" ? "" : t.dataset.setTheme); return; }
    if ((t = e.target.closest("[data-size-step]"))) {
      var n = SIZES[Math.max(0, Math.min(SIZES.length - 1, SIZES.indexOf(size()) + (+t.dataset.sizeStep)))];
      VRPrefs.set("size", n === "m" ? "" : n); return;
    }
    if ((t = e.target.closest("[data-ed-show]"))) {
      var ids = $$("[data-ed-show]").map(function (b) { return b.dataset.edShow; }).filter(function (x) { return x !== "both"; });
      VRPrefs.setOff(t.dataset.edShow === "both" ? [] : ids.filter(function (x) { return x !== t.dataset.edShow; })); return;
    }
    if ((t = e.target.closest("[data-place]"))) {
      savePlace({ lat: +t.dataset.lat, lon: +t.dataset.lon, name: t.dataset.place });
      var m = $("#pl-msg"); if (m) m.textContent = t.dataset.place + " chosen."; return;
    }
    if (e.target.closest("#pl-loc")) {
      var msg = $("#pl-msg");
      if (!navigator.geolocation) { msg.textContent = "This device cannot share its location."; return; }
      msg.textContent = "Finding your location…";
      navigator.geolocation.getCurrentPosition(function (pos) {
        savePlace({ lat: pos.coords.latitude, lon: pos.coords.longitude, name: "Your location" }); msg.textContent = "Using your location.";
      }, function () { msg.textContent = "Location not available. Choose a place below."; }, { maximumAge: 864e5, timeout: 10000 });
    }
  });
  document.addEventListener("prefs-changed", paint);

  /* ---- version / update check ---- */
  var ver = $(".set-ver"), msg = $("#set-ver-msg"), chk = $("#set-chk"), mine = (self.VRAMAYANA && self.VRAMAYANA.version) || "0";
  function newer(a, b) { a = a.split(".").map(Number); b = b.split(".").map(Number); for (var i = 0; i < 3; i++) { if ((a[i] || 0) !== (b[i] || 0)) return (a[i] || 0) > (b[i] || 0); } return false; }
  function say(t, upd) {
    msg.textContent = t; var old = $("#set-upd"); if (old) old.remove();
    if (upd) { var b = document.createElement("button"); b.type = "button"; b.id = "set-upd"; b.className = "set-chk go"; b.textContent = "Update now"; b.addEventListener("click", function () { apply(b, upd); }); ver.appendChild(b); }
  }
  function apply(btn, v) {
    btn.disabled = true; msg.textContent = "Getting version " + v + "…";
    var done = false;
    function reload() { if (!done) { done = true; location.reload(); } }
    var sw = navigator.serviceWorker;
    if (!sw) { reload(); return; }
    sw.addEventListener("controllerchange", reload);
    setTimeout(reload, 3000);
    sw.getRegistration().then(function (reg) {
      if (!reg) { reload(); return; }
      return reg.update().then(function () {
        var w = reg.installing || reg.waiting;
        if (!w) { reload(); return; }
        w.addEventListener("statechange", function () { if (w.state === "activated") reload(); });
      });
    }).catch(reload);
  }
  if (chk) chk.addEventListener("click", function () {
    var root_ = ver.dataset.root || "";
    chk.disabled = true; say("Checking…");
    fetch(root_ + "static/version.js?ts=" + Date.now(), { cache: "no-store" })
      .then(function (r) { if (!r.ok) throw new Error("http"); return r.text(); })
      .then(function (t) {
        var m = /version:\s*'([\d.]+)'/.exec(t); if (!m) throw new Error("parse");
        if (newer(m[1], mine)) say("Version " + m[1] + " is available.", m[1]);
        else say("You have the latest version. Checked " + new Date().toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" }) + ".");
      })
      .catch(function () { say("Could not check. Are you online?"); })
      .then(function () { chk.disabled = false; });
  });
  paint();
})();
