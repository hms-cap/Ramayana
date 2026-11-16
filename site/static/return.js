/* "Back to the verse": leaving a reader page through a link (a character, a metre, search, Saved, About, the
   Pariśiṣṭa) remembers the verse; those pages then show a pill that returns to it. Kept in this tab's session,
   cleared on return to any reader page. Home and Read are left out: they have their own Continue card. */
(function () {
  "use strict";
  var KEY = "vr.from", T = window.Translit, P = window.VRPrefs;
  var B = document.body.dataset, ROOT = B.root || "";
  var READER = /\/(?:mbh\/|gita\/)?(?:vu|ce)\/\d+\/\d+\/?(?:index\.html)?$/;
  function get() { try { var v = JSON.parse(sessionStorage.getItem(KEY) || "null"); return v && Date.now() - v.ts < 3 * 3600e3 ? v : null; } catch (e) { return null; } }
  function set(v) { try { if (v) sessionStorage.setItem(KEY, JSON.stringify(v)); else sessionStorage.removeItem(KEY); } catch (e) { /* ignore */ } }
  function sc() { var s = (P && P.get().script) || "knda"; return s === "deva" || s === "iast" ? s : "knda"; }

  if (document.body.classList.contains("page-sarga")) {
    set(null);   // back in the text
    var rd = document.querySelector(".reader");
    document.addEventListener("click", function (e) {
      var a = e.target.closest("a[href]");
      if (!a || !rd || a.target === "_blank" || a.hasAttribute("data-back") || a.closest(".crumbs, .stbar, .st-endli")) return;
      var u; try { u = new URL(a.href, location.href); } catch (x) { return; }
      if (u.origin !== location.origin || READER.test(u.pathname) || u.pathname === location.pathname) return;
      var li = a.closest(".verse[id]");
      if (!li) {
        var all = document.querySelectorAll(".verses > .verse[id]");
        for (var i = 0; i < all.length; i++) { if (all[i].offsetParent && all[i].getBoundingClientRect().bottom > 100) { li = all[i]; break; } }
      }
      if (!li) return;
      var n = li.id.slice(1), s = location.pathname.replace(/\/(index\.html)?$/, "").split("/").pop();
      var lab = {};
      ["knda", "deva", "iast"].forEach(function (x) {
        var t = (rd.dataset["title" + x.charAt(0).toUpperCase() + x.slice(1)] || "").split(" · ")[0];
        var ref = B.work === "gita" ? s + "." + n : s + "." + n;
        lab[x] = t + " " + (x === "iast" || !T ? ref : T.digits(ref, x));
      });
      set({ href: location.pathname + location.search + "#v" + n, lab: lab, ts: Date.now() });
    }, true);
    return;
  }
  if (/\bpage-(home|read|kanda|edition)\b/.test(document.body.className)) return;
  var v = get(); if (!v) return;
  var pill = document.createElement("div");
  pill.className = "retpill";
  pill.innerHTML = '<a href="' + v.href.replace(/"/g, "&quot;") + '"><span aria-hidden="true">‹</span> Back to <b></b></a><button type="button" aria-label="Dismiss">✕</button>';
  function label() { pill.querySelector("b").textContent = v.lab[sc()] || v.lab.iast; }
  label();
  document.body.appendChild(pill);
  document.addEventListener("prefs-changed", label);
  pill.querySelector("button").addEventListener("click", function () { set(null); pill.remove(); });
  pill.querySelector("a").addEventListener("click", function () { set(null); });
})();
