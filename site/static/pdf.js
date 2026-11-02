/* PDF without a library. Indic text needs a shaping engine, so each page is
   drawn as an image with the browser's own text shaping and the images are
   written into a PDF by hand. Text in the PDF is therefore not selectable;
   "Print" -> "Save as PDF" is the text alternative. */
(function () {
  "use strict";
  var W = 794, H = 1123, M = 54, FOOT = 14, SCALE = 2;
  var enc = new TextEncoder();

  function b64(buf) {
    var s = "", a = new Uint8Array(buf);
    for (var i = 0; i < a.length; i += 0x8000) s += String.fromCharCode.apply(null, a.subarray(i, i + 0x8000));
    return btoa(s);
  }
  // @font-face rules of the site stylesheet whose family is wanted, fonts inlined as data: URLs
  function fontCss(families) {
    var link = document.querySelector('link[rel=stylesheet][href*="style.css"]');
    return fetch(link.href).then(function (r) { return r.text(); }).then(function (css) {
      var faces = css.match(/@font-face\s*\{[^}]*\}/g) || [];
      faces = faces.filter(function (f) { return families.some(function (n) { return f.indexOf('"' + n + '"') >= 0; }); });
      return Promise.all(faces.map(function (f) {
        var m = /url\("([^"]+)"\)/.exec(f);
        return fetch(new URL(m[1], link.href)).then(function (r) { return r.arrayBuffer(); }).then(function (buf) {
          return f.replace(m[0], 'url("data:font/woff;base64,' + b64(buf) + '")');
        });
      }));
    }).then(function (a) { return a.join("\n"); });
  }
  var DOC_CSS =
    "html,body{margin:0;background:#fff;color:#000}.stage{box-sizing:border-box;width:" + (W - 2 * M) + "px;font-size:15pt}" +
    "h1{text-align:center;font-weight:700;font-size:20pt;margin:0 0 4pt}.pd-src{text-align:center;font-size:11pt;margin:0 0 14pt}" +
    "p{margin:0 0 8pt;text-align:justify;word-break:keep-all;hyphens:none}" +
    ".foot{font:10pt 'Alegreya Sans',sans-serif;color:#555;text-align:center}";

  function stackFor(lang) {
    if (lang === "sa-Knda") return { fam: "'Tiro Kannada','Tiro Devanagari Sanskrit',serif", lh: 2.4 * 0.9, names: ["Tiro Kannada", "Tiro Devanagari Sanskrit"] };
    if (lang === "sa-Deva") return { fam: "'Tiro Devanagari Sanskrit',serif", lh: 2.15 * 0.9, names: ["Tiro Devanagari Sanskrit"] };
    return { fam: "'Alegreya',serif", lh: 1.6, names: ["Alegreya"] };
  }

  function layout(docEl, css) {
    return new Promise(function (resolve, reject) {
      var fr = document.createElement("iframe");
      fr.style.cssText = "position:fixed;left:-10000px;top:0;width:" + W + "px;height:" + H + "px;border:0;visibility:hidden";
      document.body.appendChild(fr);
      var d = fr.contentDocument; d.open();
      d.write("<!doctype html><html lang='" + docEl.lang + "'><head><meta charset='utf-8'><style>" + css + "</style></head><body></body></html>");
      d.close();
      var stage = d.createElement("div"); stage.className = "stage"; stage.lang = docEl.lang;
      stage.innerHTML = docEl.innerHTML; d.body.appendChild(stage);
      var wait = (d.fonts && d.fonts.ready) || Promise.resolve();
      Promise.all([wait, d.fonts ? d.fonts.load("20pt " + stackFor(docEl.lang).fam.split(",")[0], docEl.textContent.slice(0, 200)) : 0])
        .then(function () { return new Promise(function (r) { setTimeout(r, 60); }); })
        .then(function () { resolve({ frame: fr, doc: d, stage: stage }); }, reject);
    });
  }
  function leavesOf(stage, limit) {
    var out = [];
    (function walk(el) {
      [].forEach.call(el.children, function (c) {
        var r = c.getBoundingClientRect();
        if (r.height > limit && c.children.length) walk(c); else out.push(c);
      });
    })(stage);
    return out;
  }
  function paginate(stage) {
    var limit = H - 2 * M - FOOT, leaves = leavesOf(stage, limit), pages = [[]], acc = 0;
    leaves.forEach(function (l, i) {
      var cs = getComputedStyle(l), h = l.getBoundingClientRect().height + parseFloat(cs.marginTop) + parseFloat(cs.marginBottom);
      if (acc + h > limit && acc > 0) { pages.push([]); acc = 0; }
      l.setAttribute("data-pl", i); pages[pages.length - 1].push(i); acc += h;
    });
    return pages;
  }
  function drawPage(L, ids, n, N, css, title, lang) {
    var st = stackFor(lang), clone = L.stage.cloneNode(true);
    [].slice.call(clone.querySelectorAll("[data-pl]")).forEach(function (e) { if (ids.indexOf(+e.getAttribute("data-pl")) < 0) e.remove(); });
    var foot = (title + " · " + n + " / " + N).replace(/&/g, "&amp;").replace(/</g, "&lt;");
    var inner = new XMLSerializer().serializeToString(clone);
    var svg = '<svg xmlns="http://www.w3.org/2000/svg" width="' + W + '" height="' + H + '"><foreignObject width="' + W + '" height="' + H + '">' +
      '<div xmlns="http://www.w3.org/1999/xhtml" lang="' + lang + '" style="width:' + W + 'px;height:' + H + 'px;background:#fff;position:relative;font-family:' + st.fam + ';line-height:' + st.lh + '">' +
      '<style><![CDATA[' + css + ']]></style><div style="position:absolute;left:' + M + 'px;top:' + M + 'px">' + inner + '</div>' +
      '<div class="foot" style="position:absolute;left:0;right:0;bottom:' + (M / 2) + 'px">' + foot + '</div></div></foreignObject></svg>';
    return new Promise(function (resolve, reject) {
      var img = new Image();
      img.onload = function () {
        try {
          var c = document.createElement("canvas"); c.width = W * SCALE; c.height = H * SCALE;
          var g = c.getContext("2d"); g.fillStyle = "#fff"; g.fillRect(0, 0, c.width, c.height); g.drawImage(img, 0, 0, c.width, c.height);
          var url = c.toDataURL("image/jpeg", 0.88), bin = atob(url.split(",")[1]), a = new Uint8Array(bin.length);
          for (var i = 0; i < bin.length; i++) a[i] = bin.charCodeAt(i);
          resolve({ bytes: a, w: c.width, h: c.height });
        } catch (e) { reject(e); }   // a tainted canvas (older Safari) lands here
      };
      img.onerror = function () { reject(new Error("page image failed")); };
      img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
    });
  }
  function hexUtf16(s) {
    var h = "FEFF";
    for (var i = 0; i < s.length; i++) h += ("0000" + s.charCodeAt(i).toString(16)).slice(-4);
    return "<" + h.toUpperCase() + ">";
  }
  function writePdf(images, title) {
    var parts = [], offsets = [], len = 0;
    function put(x) { var b = typeof x === "string" ? enc.encode(x) : x; parts.push(b); len += b.length; }
    function obj(n, body) { offsets[n] = len; put(n + " 0 obj\n"); put(body); put("\nendobj\n"); }
    var N = images.length;
    // object numbers: 1 catalog, 2 pages, 3 info, then per page: image, content, page
    put("%PDF-1.4\n%\xE2\xE3\xCF\xD3\n");
    obj(1, "<< /Type /Catalog /Pages 2 0 R >>");
    var kids = images.map(function (_, i) { return (6 + i * 3) + " 0 R"; }).join(" ");
    obj(2, "<< /Type /Pages /Kids [" + kids + "] /Count " + N + " >>");
    obj(3, "<< /Title " + hexUtf16(title) + " /Producer (Valmiki Ramayana reader) >>");
    images.forEach(function (im, i) {
      var b = 3 + i * 3 + 1;
      offsets[b] = len; put(b + " 0 obj\n<< /Type /XObject /Subtype /Image /Width " + im.w + " /Height " + im.h + " /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length " + im.bytes.length + " >>\nstream\n");
      put(im.bytes); put("\nendstream\nendobj\n");
      var content = "q 595.28 0 0 841.89 0 0 cm /Im0 Do Q";
      obj(b + 1, "<< /Length " + content.length + " >>\nstream\n" + content + "\nendstream");
      obj(b + 2, "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595.28 841.89] /Resources << /XObject << /Im0 " + b + " 0 R >> >> /Contents " + (b + 1) + " 0 R >>");
    });
    var total = 4 + N * 3, xref = len;
    var x = "xref\n0 " + total + "\n0000000000 65535 f \n";
    for (var n = 1; n < total; n++) x += ("0000000000" + (offsets[n] || 0)).slice(-10) + " 00000 n \n";
    put(x + "trailer\n<< /Size " + total + " /Root 1 0 R /Info 3 0 R >>\nstartxref\n" + xref + "\n%%EOF\n");
    return new Blob(parts, { type: "application/pdf" });
  }

  /* docEl: a detached .pdf-doc element. Returns a Promise<Blob>. */
  function make(docEl, title, progress) {
    var st = stackFor(docEl.lang), L;
    return fontCss(st.names.concat(["Alegreya Sans"])).then(function (fc) {
      var css = fc + "\n" + DOC_CSS + ".stage{font-family:" + st.fam + ";line-height:" + st.lh + "}";
      return layout(docEl, css).then(function (l) {
        L = l; var pages = paginate(l.stage), images = [], N = pages.length;
        return pages.reduce(function (p, ids, i) {
          return p.then(function () {
            if (progress) progress(i + 1, N);
            return new Promise(function (r) { setTimeout(r, 0); }).then(function () { return drawPage(l, ids, i + 1, N, css, title, docEl.lang); })
              .then(function (im) { images.push(im); });
          });
        }, Promise.resolve()).then(function () { return writePdf(images, title); });
      });
    }).then(function (b) { if (L) L.frame.remove(); return b; }, function (e) { if (L) L.frame.remove(); throw e; });
  }
  window.VRPdf = { make: make, _paginate: paginate };
})();
