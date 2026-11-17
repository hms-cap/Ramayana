/* Read page: tint the unit being read. Kāṇḍa / parva page: pin "Continue here" and tint the saved sarga (v0.22). */
(function () {
  "use strict";
  var B = document.body;
  var LAST = ({ mbh: "vr.last.mbh", gita: "vr.last.gita" }[B.dataset.work] || "vr.last"), ED = B.dataset.ed;
  if (B.classList.contains("page-read")) {   // the unit being read, tinted
    var rl; try { rl = JSON.parse(localStorage.getItem(LAST) || "null"); } catch (e) { rl = null; }
    var rm = rl && rl.href && /(?:vu|ce)\/(\d+)\/(\d+)\//.exec(rl.href);
    if (rm) {
      var want = B.dataset.work === "gita" ? rm[2] : rm[1];
      document.querySelectorAll("#kcells .kcell").forEach(function (c) { if (c.dataset.k === want) { c.classList.add("now"); c.setAttribute("aria-current", "true"); } });
    }
    return;
  }
  if (!B.classList.contains("page-kanda")) return;
  var box = document.getElementById("kcont"), list = document.querySelector("ol.sargas"); if (!box || !list) return;
  var K = (location.pathname.match(/\/(?:vu|ce)\/(\d+)\/?$/) || [])[1];
  var l; try { l = JSON.parse(localStorage.getItem(LAST) || "null"); } catch (e) { l = null; }
  var m = l && l.href && /(vu|ce)\/(\d+)\/(\d+)\//.exec(l.href);
  if (!m || m[1] !== ED || m[2] !== K) return;
  var s = m[3], li = list.querySelector('li[data-s="' + s + '"]'); if (!li) return;
  li.classList.add("now"); li.querySelector("a").setAttribute("aria-current", "true");
  var T = window.Translit, num = li.querySelector(".sn"), first = li.querySelector(".first");
  var a = document.createElement("a"); a.className = "kc-pin"; a.href = s + "/";
  var lab = document.createElement("span"); lab.className = "kc-lab"; lab.textContent = "Continue here · " + (B.dataset.subEn || "sarga") + " " + s;
  a.appendChild(lab);
  if (first) { var f = document.createElement("span"); f.className = "kc-first"; f.setAttribute("lang", first.getAttribute("lang") || ""); f.textContent = first.textContent; a.appendChild(f); }
  box.appendChild(a); box.hidden = false;
})();
