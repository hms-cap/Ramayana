/* Kāṇḍa cards (Home, Read) open a bottom sheet with the sarga numbers. */
(function () {
  "use strict";
  var T = window.Translit, P = window.VRPrefs, ROOT = document.body.dataset.wroot || "", MBH = document.body.dataset.work === "mbh", LASTK = MBH ? "vr.last.mbh" : "vr.last";
  var sheet = document.getElementById("ksheet");
  if (!sheet) return;
  var SCR = ["knda", "deva", "iast"], cur = null, ed = P.off().indexOf("vu") >= 0 ? "ce" : "vu";
  function sc() { var s = P.get().script || "knda"; return SCR.indexOf(s) >= 0 ? s : "knda"; }
  function num(i) { var s = sc(); return s === "iast" ? String(i) : T.digits(i, s); }
  function last() { try { return JSON.parse(localStorage.getItem(LASTK) || "null"); } catch (e) { return null; } }

  function paint() {
    if (!cur) return;
    if (P.off().indexOf(ed) >= 0) ed = ed === "ce" ? "vu" : "ce";
    var k = cur.dataset.k, n = +cur.getAttribute("data-n-" + ed) || 0, s = sc();
    document.getElementById("ks-title").textContent = cur.dataset.kn;
    document.getElementById("ks-sub").textContent = cur.dataset.en + " · " + n + " " + (MBH ? "adhyāyas" : "sargas");
    sheet.querySelectorAll("[data-chip-ed]").forEach(function (b) { b.setAttribute("aria-checked", b.dataset.chipEd === ed ? "true" : "false"); });
    var st = document.getElementById("ks-start");
    st.href = ROOT + ed + "/" + k + "/1/"; st.textContent = "Start from " + num(1);
    var l = last(), m = l && /(ce|vu)\/(\d+)\/(\d+)\//.exec(l.href), rs = document.getElementById("ks-resume"), at = 0;
    if (m && m[1] === ed && m[2] === k) { at = +m[3]; rs.hidden = false; rs.href = ROOT + ed + "/" + k + "/" + at + "/"; rs.textContent = "Resume " + num(at); } else rs.hidden = true;
    var h = "";
    for (var i = 1; i <= n; i++) h += '<a href="' + ROOT + ed + "/" + k + "/" + i + '/"' + (i === at ? ' aria-current="true"' : "") + (s === "iast" ? "" : ' lang="' + (s === "deva" ? "sa" : "kn") + '"') + ">" + num(i) + "</a>";
    document.getElementById("ks-chips").innerHTML = h;
  }
  function open(card) {
    cur = card;
    var art = document.getElementById("ks-art"), svg = card.querySelector("svg");
    art.setAttribute("style", card.getAttribute("style")); art.innerHTML = svg ? svg.outerHTML : "";
    paint(); VRSheet.open("ksheet");
  }
  document.addEventListener("click", function (e) {
    var c = e.target.closest("button.kcard"); if (c) { open(c); return; }
    var b = e.target.closest("#ksheet [data-chip-ed]"); if (b) { ed = b.dataset.chipEd; paint(); }
  });
  document.addEventListener("prefs-changed", paint);
})();
