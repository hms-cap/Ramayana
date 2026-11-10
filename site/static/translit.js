/* Sanskrit transliteration via SLP1 — browser mirror of etl/translit.py.
   tests/test_js_parity.py checks both implementations give identical output. */
(function (global) {
  "use strict";
  var VOWELS = "aAiIuUfFxXeEoO";
  var LONG = "AIUFXeEoO";
  var CONS = "kKgGNcCjJYwWqQRtTdDnpPbBmyrlvSzshL";
  var STOP_NASAL = {};
  "kKgG".split("").forEach(function (c) { STOP_NASAL[c] = "N"; });
  "cCjJ".split("").forEach(function (c) { STOP_NASAL[c] = "Y"; });
  "wWqQ".split("").forEach(function (c) { STOP_NASAL[c] = "R"; });
  "tTdD".split("").forEach(function (c) { STOP_NASAL[c] = "n"; });
  "pPbB".split("").forEach(function (c) { STOP_NASAL[c] = "m"; });

  function zip(keys, vals) {
    var o = {}, v = Array.from(vals);
    keys.split("").forEach(function (k, i) { o[k] = v[i]; });
    return o;
  }
  var SCRIPTS = {
    deva: {
      vowels: zip(VOWELS, "अआइईउऊऋॠऌॡएऐओऔ"),
      signs: zip("AiIuUfFxXeEoO", "ािीुूृॄॢॣेैोौ"),
      cons: zip(CONS, "कखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसहळ"),
      virama: "्", M: "ं", H: "ः", "~": "ँ", "'": "ऽ", digits: Array.from("०१२३४५६७८९")
    },
    knda: {
      vowels: zip(VOWELS, "ಅಆಇಈಉಊಋೠಌೡಏಐಓಔ"),
      signs: zip("AiIuUfFxXeEoO", "ಾಿೀುೂೃೄೢೣೇೈೋೌ"),
      cons: zip(CONS, "ಕಖಗಘಙಚಛಜಝಞಟಠಡಢಣತಥದಧನಪಫಬಭಮಯರಲವಶಷಸಹಳ"),
      virama: "್", M: "ಂ", H: "ಃ", "~": "ಁ", "'": "ಽ", digits: Array.from("೦೧೨೩೪೫೬೭೮೯")
    }
  };

  var IAST2SLP = {
    ai: "E", au: "O", kh: "K", gh: "G", ch: "C", jh: "J", "ṭh": "W", "ḍh": "Q",
    th: "T", dh: "D", ph: "P", bh: "B",
    "ā": "A", "ī": "I", "ū": "U", "ṛ": "f", "ṝ": "F", "ḷ": "x", "ḹ": "X",
    "ṅ": "N", "ñ": "Y", "ṭ": "w", "ḍ": "q", "ṇ": "R", "ś": "S", "ṣ": "z",
    "ṃ": "M", "ṁ": "M", "ḥ": "H", "m̐": "~"
  };
  var SLP2IAST = {};
  Object.keys(IAST2SLP).forEach(function (k) { if (k !== "ṁ") SLP2IAST[IAST2SLP[k]] = k; });
  SLP2IAST.L = "ḻ";
  var IAST_RE = new RegExp(Object.keys(IAST2SLP).sort(function (a, b) { return b.length - a.length; })
    .map(function (k) { return k.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }).join("|"), "g");

  function iastToSlp1(t) {
    return t.normalize("NFC").toLowerCase().replace(IAST_RE, function (m) { return IAST2SLP[m]; });
  }
  function slp1ToIast(t) {
    var o = "";
    for (var i = 0; i < t.length; i++) o += SLP2IAST[t[i]] !== undefined ? SLP2IAST[t[i]] : t[i];
    return o;
  }

  function slp1ToBrahmic(text, script) {
    var t = SCRIPTS[script], out = [], pending = false;
    for (var i = 0; i < text.length; i++) {
      var ch = text[i];
      if (t.cons[ch] !== undefined) {
        if (pending) out.push(t.virama);
        out.push(t.cons[ch]); pending = true;
      } else if (t.vowels[ch] !== undefined) {
        if (pending) { if (ch !== "a") out.push(t.signs[ch]); pending = false; }
        else out.push(t.vowels[ch]);
      } else {
        if (pending) { out.push(t.virama); pending = false; }
        if (ch === "M" || ch === "H" || ch === "~" || ch === "'") out.push(t[ch]);
        else if (ch >= "0" && ch <= "9") out.push(t.digits[+ch]);
        else out.push(ch);
      }
    }
    if (pending) out.push(t.virama);
    return out.join("");
  }

  var REV = {};
  Object.keys(SCRIPTS).forEach(function (s) {
    var t = SCRIPTS[s];
    Object.keys(t.vowels).forEach(function (k) { REV[t.vowels[k]] = ["V", k]; });
    Object.keys(t.signs).forEach(function (k) { REV[t.signs[k]] = ["S", k]; });
    Object.keys(t.cons).forEach(function (k) { REV[t.cons[k]] = ["C", k]; });
    REV[t.virama] = ["X", ""];
    ["M", "H", "~", "'"].forEach(function (k) { REV[t[k]] = ["O", k]; });
    t.digits.forEach(function (d, i) { REV[d] = ["O", String(i)]; });
  });

  function brahmicToSlp1(text) {
    text = text.normalize("NFC");
    var out = [], pending = false;
    for (var i = 0; i < text.length; i++) {
      var ch = text[i];
      if (ch === "़" || ch === "಼" || ch === "‌" || ch === "‍") continue;
      var r = REV[ch];
      if (r && r[0] === "C") { if (pending) out.push("a"); out.push(r[1]); pending = true; continue; }
      if (r && r[0] === "S") { out.push(r[1]); pending = false; continue; }
      if (r && r[0] === "X") { pending = false; continue; }
      if (pending) { out.push("a"); pending = false; }
      if (r) out.push(r[1]);
      else if (ch === "।" || ch === "॥") out.push("|");
      else out.push(ch);
    }
    if (pending) out.push("a");
    return out.join("");
  }

  var CONS_RE = new RegExp("([" + CONS + "]) +(?=\\S)", "g");
  function joinForDisplay(s) { return s.replace(CONS_RE, "$1").replace(/ +'/g, "'"); }
  function paraSavarna(s) {
    var o = "";
    for (var i = 0; i < s.length; i++) {
      var n = s[i + 1];
      o += (s[i] === "M" && n !== undefined && STOP_NASAL[n]) ? STOP_NASAL[n] : s[i];
    }
    return o;
  }
  /* Kannada print usage: class nasal before a stop of its own class -> anusvāra (ಸಂಗ, ಪಂಚ, ಅಂತ); inside a word only */
  function anusvaraBeforeStops(s) {
    return s.replace(/[NYRnm](?=[kKgGcCjJwWqQtTdDpPbB])/g, function (m, i) { return STOP_NASAL[s[i + 1]] === m ? "M" : m; });
  }
  function render(slp1, script, savarna) {
    if (script === "iast") return slp1ToIast(slp1);
    if (script === "knda" && !savarna) slp1 = anusvaraBeforeStops(slp1);
    var s = joinForDisplay(slp1);
    if (savarna) s = paraSavarna(s);
    return slp1ToBrahmic(s, script);
  }
  function digits(n, script) {
    if (script === "iast") return String(n);
    var d = SCRIPTS[script].digits;
    return String(n).replace(/[0-9]/g, function (c) { return d[+c]; });
  }

  var LOOSE = {
    A: "a", I: "i", U: "u", f: "ri", F: "ri", x: "li", X: "li", E: "ai", O: "au",
    K: "k", G: "g", N: "n", C: "c", J: "j", Y: "n", w: "t", W: "t", q: "d", Q: "d", R: "n",
    T: "t", D: "d", P: "p", B: "b", S: "s", z: "s", L: "l", H: "", "~": "n", "'": ""
  };
  var LAB_FRIC = "pPbBmyrlvSzsh";
  function looseKey(slp1) {
    var s = slp1.replace(/[^A-Za-z'~]/g, ""), o = "";
    for (var i = 0; i < s.length; i++) {
      var ch = s[i];
      if (ch === "M") {
        var n = s[i + 1];
        o += (n === undefined || LAB_FRIC.indexOf(n) >= 0 || VOWELS.indexOf(n) >= 0) ? "m" : "n";
      } else o += LOOSE[ch] !== undefined ? LOOSE[ch] : ch;
    }
    return o;
  }
  function collapse(s) { return s.replace(/(.)\1/g, "$1"); }
  function looseForIndex(slp1) { return collapse(looseKey(slp1)); }
  function asciiQueryToLoose(q) {
    q = q.toLowerCase().replace(/[^a-z]/g, "");
    q = q.replace(/ee/g, "i").replace(/oo/g, "u").replace(/aa/g, "a").replace(/ou/g, "au").replace(/w/g, "v");
    q = q.replace(/([bcdgjkptsr])h/g, "$1").replace(/h$/, "");
    q = q.replace(/ksh/g, "ks").replace(/x/g, "ks");
    return collapse(q);
  }
  /* Any query (Kannada, Devanāgarī, IAST, plain English letters) -> loose key */
  function queryToLoose(q) {
    q = q.normalize("NFC").trim();
    if (/[ऀ-ॿಀ-೿]/.test(q)) return looseForIndex(brahmicToSlp1(q));
    if (/[^\x00-\x7F]/.test(q)) return looseForIndex(iastToSlp1(q));
    return asciiQueryToLoose(q);
  }

  global.Translit = {
    iastToSlp1: iastToSlp1, slp1ToIast: slp1ToIast, slp1ToBrahmic: slp1ToBrahmic,
    brahmicToSlp1: brahmicToSlp1, joinForDisplay: joinForDisplay, paraSavarna: paraSavarna, anusvaraBeforeStops: anusvaraBeforeStops,
    render: render, digits: digits, looseKey: looseKey, looseForIndex: looseForIndex,
    asciiQueryToLoose: asciiQueryToLoose, queryToLoose: queryToLoose
  };
})(typeof window !== "undefined" ? window : globalThis);
