/* Adhyāya list of a gītā: edition tabs, and remember which passage was opened (so the reader's Back lands here). */
(function () {
  "use strict";
  var art = document.querySelector(".passage"); if (!art) return;
  var id = art.dataset.pid, tabs = [].slice.call(document.querySelectorAll("[data-pt-tab]")), secs = [].slice.call(document.querySelectorAll("[data-pt-sec]"));
  function show(ed) {
    secs.forEach(function (s) { s.hidden = s.dataset.ptSec !== ed; });
    tabs.forEach(function (t) { var on = t.dataset.ptTab === ed; t.classList.toggle("on", on); t.setAttribute("aria-selected", on ? "true" : "false"); });
  }
  var first = secs.length ? secs[0].dataset.ptSec : "";
  function start() { var h = location.hash.slice(1); show(secs.some(function (s) { return s.dataset.ptSec === h; }) ? h : first); }
  tabs.forEach(function (t) { t.addEventListener("click", function (e) { e.preventDefault(); show(t.dataset.ptTab); try { history.replaceState(history.state, "", "#" + t.dataset.ptTab); } catch (x) { /* ignore */ } }); });
  window.addEventListener("hashchange", start); start();
  document.addEventListener("click", function (e) {
    var a = e.target.closest("[data-pread], [data-pchant]");
    if (!a || e.defaultPrevented || e.button > 0 || e.metaKey || e.ctrlKey || e.shiftKey) return;
    try { sessionStorage.setItem("vr.stid", id); } catch (x) { /* ignore */ }
    if (a.hasAttribute("data-pchant")) {
      e.preventDefault();
      var u = new URL(a.href, location.href);
      try { sessionStorage.setItem("vr.stchant", u.pathname + u.hash); } catch (x) { /* ignore */ }
      location.assign(a.href);
    }
  });
})();
