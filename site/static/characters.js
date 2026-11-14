/* Characters pages: the work switch on the index and the line tabs on the family-tree pages.
   Without JavaScript every section is shown one after the other. */
(function () {
  "use strict";
  function tabs(tabAttr, secAttr, dflt) {
    var tabs = [].slice.call(document.querySelectorAll("[" + tabAttr + "]"));
    if (!tabs.length) return;
    var secs = [].slice.call(document.querySelectorAll("[" + secAttr + "]"));
    var ids = tabs.map(function (t) { return t.getAttribute(tabAttr); });
    function show(id) {
      secs.forEach(function (s) { s.hidden = s.getAttribute(secAttr) !== id; });
      tabs.forEach(function (t) {
        var on = t.getAttribute(tabAttr) === id;
        t.classList.toggle("on", on); t.setAttribute("aria-selected", on ? "true" : "false");
      });
    }
    var want = decodeURIComponent(location.hash.slice(1));
    show(ids.indexOf(want) >= 0 ? want : dflt(ids));
    tabs.forEach(function (t) {
      t.addEventListener("click", function (e) {
        e.preventDefault();
        var id = t.getAttribute(tabAttr); show(id);
        try { history.replaceState(null, "", "#" + id); } catch (x) { /* ignore */ }
      });
    });
    window.addEventListener("hashchange", function () {
      var id = decodeURIComponent(location.hash.slice(1));
      if (ids.indexOf(id) >= 0) show(id);
    });
  }
  tabs("data-cw-tab", "data-cw-sec", function (ids) {
    try {
      var w = localStorage.getItem("vr.work");
      if (w === "gita") w = "mbh";
      if (ids.indexOf(w) >= 0) return w;
    } catch (e) { /* storage unavailable */ }
    return ids[0];
  });
  tabs("data-tr-tab", "data-tr-sec", function (ids) { return ids[0]; });
})();
