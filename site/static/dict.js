/* Word look-up in the dictionary: tap a word in the word-by-word panel to see its Śabdārtha Kaustubha entry
   (Sanskrit → Kannada) under it. The dictionary app and its data are in dict/ (see etl/sync_kosha.sh); this file
   reuses that app's own look-up code (kosha.js, search-key.js), loaded only on the first tap. */
(function () {
  "use strict";
  var T = window.Translit, body = document.body;
  if (!T || !body.dataset.root) return;
  var base = new URL(body.dataset.root + "dict/", document.baseURI).href;
  var mods = null, jsonCache = {}, keysP = null;

  function load() {
    return mods || (mods = Promise.all(["kosha.js", "search-key.js", "translit.js", "lipi.js"].map(function (f) { return import(base + f); }))
      .then(function (m) { return { k: m[0], s: m[1], t: m[2], l: m[3] }; }));
  }
  function get(u, text) {
    return jsonCache[u] || (jsonCache[u] = fetch(u).then(function (r) { if (!r.ok) throw new Error(r.status); return text ? r.text() : r.json(); }).catch(function (e) { delete jsonCache[u]; throw e; }));
  }
  var data = {
    keys: function () { return keysP || (keysP = get(base + "data/kosha/keys.tsv", true).then(function (t) { return t.split("\n").filter(Boolean).map(function (l) { return l.split("\t"); }); }).catch(function (e) { keysP = null; throw e; })); },
    manifest: function () { return get(base + "data/kosha/shards.json"); },
    shard: function (f) { return get(base + "data/kosha/" + f + ".json"); }
  };
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function script() { var s = document.documentElement.dataset.script || "knda"; return /^knda/.test(s) ? "knda" : s === "iast" ? "iast" : "deva"; }
  function sk(M, text, sc) {
    if (sc === "knda") return M.l.toKnda(text).replace(/॰/g, ".");
    if (sc === "iast") return M.t.devaToIast(text);
    return text;
  }

  async function entriesFor(M, lemma) {
    var d = T.render(lemma, "deva", false), keys = await data.keys();
    var qk = M.s.looseKey(M.t.devaToIast(d)), m = M.k.matchKeys(keys, qk, { prefixLimit: 5 });
    // the headword spelled exactly like the lemma, when there is one; otherwise up to two with the same sound-key
    var heads = m.exact.indexOf(d) >= 0 ? [d] : m.exact.slice(0, 2);
    var out = [];
    for (var i = 0; i < heads.length; i++) { var e = await M.k.lookup(data, heads[i]); if (e) out.push(e); }
    return { lemma: d, entries: out, near: m.prefix };
  }

  function entryHTML(M, e, sc) {
    var href = base + "kosha/" + M.k.koshaHref(e[0]);
    var senses = e[2].slice(0, 3).map(function (s) {
      var kn = (s[1] || "").length > 170 ? s[1].slice(0, 170).replace(/\s+\S*$/, "") + "…" : (s[1] || "");
      return '<li>' + (s[0] ? '<small lang="sa">' + esc(sk(M, s[0], sc)) + "</small> " : "") + '<span lang="kn">' + esc(kn) + "</span></li>";
    }).join("");
    var der = e[2][0] && e[2][0][3] ? '<p class="dc-d"><small>Derivation</small> <span lang="sa">' + esc(sk(M, e[2][0][3], sc)) + "</span></p>" : "";
    return '<div class="dc-e"><div class="dc-h"><b lang="sa">' + esc(sk(M, e[0], sc)) + '</b> <a href="' + href + '">Full entry in Kosha</a></div>' +
      '<ol class="dc-s">' + senses + "</ol>" + der + (e[2].length > 3 ? '<p class="dc-m"><a href="' + href + '">' + (e[2].length - 3) + " more senses</a></p>" : "") + "</div>";
  }

  async function show(li) {
    var old = li.querySelector(".dcard");
    if (old) { old.remove(); li.querySelector(".w").setAttribute("aria-expanded", "false"); return; }
    var w = li.querySelector(".w"); w.setAttribute("aria-expanded", "true");
    var card = document.createElement("div"); card.className = "dcard"; card.setAttribute("role", "region"); card.setAttribute("aria-label", "Dictionary entry");
    card.textContent = "Looking up…"; li.appendChild(card);
    try {
      var M = await load(), sc = script(), html = "";
      var lemmas = (li.dataset.l || "").split(" ").filter(Boolean);
      var found = 0, missing = [];
      for (var i = 0; i < lemmas.length; i++) {
        var r = await entriesFor(M, lemmas[i]);
        if (r.entries.length) { found++; html += (lemmas.length > 1 ? '<p class="dc-l" lang="sa">' + esc(sk(M, r.lemma, sc)) + "</p>" : "") + r.entries.map(function (e) { return entryHTML(M, e, sc); }).join(""); }
        else missing.push(r);
      }
      missing.forEach(function (r) {
        html += '<p class="dc-no">No entry for <b lang="sa">' + esc(sk(M, r.lemma, sc)) + "</b> in the dictionary." +
          (r.near.length ? " Near it: " + r.near.slice(0, 4).map(function (h) { return '<a lang="sa" href="' + base + "kosha/" + M.k.koshaHref(h) + '">' + esc(sk(M, h, sc)) + "</a>"; }).join(", ") + "." : "") + "</p>";
      });
      html += '<p class="dc-c">Śabdārtha Kaustubha, Sanskrit–Kannada. <a href="' + base + 'kosha/#/kosha?find=1">Search the dictionary</a></p>';
      card.innerHTML = html;
    } catch (err) {
      card.innerHTML = '<p class="dc-no">Could not load the dictionary. Check the connection, or <a href="' + base + 'kosha/">open it</a>.</p>';
    }
  }

  document.addEventListener("click", function (e) {
    var w = e.target.closest(".wbw-list .w[role=button]");
    if (w) { e.preventDefault(); show(w.closest("li")); }
  });
  document.addEventListener("keydown", function (e) {
    var w = e.target.closest && e.target.closest(".wbw-list .w[role=button]");
    if (w && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); show(w.closest("li")); }
  });
})();
