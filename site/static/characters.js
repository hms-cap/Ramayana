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

  // Family trees are wider than a phone: open each one scrolled to its founder (the top row),
  // and give it a "Whole tree" switch that shrinks it to the width of the screen.
  function centre(box) {
    if (!box.offsetParent || box.classList.contains("fit")) return;
    var nodes = [].slice.call(box.querySelectorAll("a.node")), top = null;
    nodes.forEach(function (n) { var b = n.getBBox(); if (!top || b.y < top.y - 1) top = b; });
    if (top) box.scrollLeft = Math.max(0, top.x + top.width / 2 - box.clientWidth / 2);
  }
  var boxes = [].slice.call(document.querySelectorAll(".tree"));
  boxes.forEach(function (box) {
    var svg = box.querySelector("svg");
    if (!svg || svg.getAttribute("width") <= box.clientWidth) return;
    var b = document.createElement("button");
    b.type = "button"; b.className = "tree-fit"; b.textContent = "Whole tree"; b.setAttribute("aria-pressed", "false");
    b.addEventListener("click", function () {
      var on = box.classList.toggle("fit");
      b.setAttribute("aria-pressed", on ? "true" : "false"); b.textContent = on ? "Actual size" : "Whole tree";
      if (!on) centre(box);
    });
    box.parentNode.insertBefore(b, box);
  });
  function centreAll() { boxes.forEach(centre); }
  centreAll();
  document.querySelectorAll("[data-tr-tab]").forEach(function (t) { t.addEventListener("click", function () { setTimeout(centreAll, 0); }); });
  window.addEventListener("hashchange", function () { setTimeout(centreAll, 0); });
})();
