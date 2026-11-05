// The standalone Dictionary app (Śabdārtha Kaustubha). The screens are in ../kosha-ui.js, shared with Vedāvalokanam.
import { createKosha } from '../kosha-ui.js';
import { koshaHref } from '../kosha.js';
import { toKnda } from '../lipi.js';

const $ = (s, el = document) => el.querySelector(s);
const main = $('#main');
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const SUN_SVG = '<svg class="hero-sun" width="260" height="260" viewBox="0 0 260 260" aria-hidden="true"><circle cx="130" cy="130" r="46"/><circle cx="130" cy="130" r="70" class="r1"/><circle cx="130" cy="130" r="94" class="r2"/><circle cx="130" cy="130" r="118" class="r3"/></svg>';
const ARROW = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>';
// ---------- settings: theme and the script of the Sanskrit (kept under its own key, apart from Vedāvalokanam's) ----------
const PREFS_KEY = 'kosha.prefs';
const prefs = { theme: 'system', script: 'deva' };
try { Object.assign(prefs, JSON.parse(localStorage.getItem(PREFS_KEY) || '{}')); } catch { /* storage unavailable */ }
const savePrefs = () => { try { localStorage.setItem(PREFS_KEY, JSON.stringify(prefs)); } catch { /* storage unavailable */ } };
const darkMQ = window.matchMedia?.('(prefers-color-scheme: dark)');
function applyTheme() {
  const root = document.documentElement;
  if (prefs.theme === 'light' || prefs.theme === 'dark') root.setAttribute('data-theme', prefs.theme); else root.removeAttribute('data-theme');
  const dark = prefs.theme === 'dark' || (prefs.theme !== 'light' && darkMQ?.matches);
  document.querySelector('meta[name="theme-color"]')?.setAttribute('content', dark ? '#101215' : '#0F5F7A');
}
darkMQ?.addEventListener?.('change', applyTheme);
applyTheme();
// Kannada script: the Sanskrit (anything marked lang="sa") is shown converted from Devanagari; Kannada meanings and English are left alone
const DEVA = /[\u0900-\u097F]/;
function toScript(root) {
  if (prefs.script !== 'knda' || !root) return;
  const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  const hit = [];
  for (let n = w.nextNode(); n; n = w.nextNode()) if (DEVA.test(n.data) && n.parentElement?.closest('[lang="sa"]')) hit.push(n);
  // only write what changed: signs that stay the same in Kannada (the danda) would otherwise match again and loop forever
  // the abbreviation sign (माघ॰) is written as a full stop in Kannada (ಮಾಘ.)
  for (const n of hit) { const t = toKnda(n.data).replace(/\u0970/g, '.'); if (t !== n.data) n.data = t; }
}
const scriptObserver = new MutationObserver((ms) => {
  if (prefs.script !== 'knda') return;
  for (const m of ms) { if (m.type === 'characterData') toScript(m.target.parentNode); else m.addedNodes.forEach((n) => toScript(n.nodeType === 3 ? n.parentNode : n)); }
});
scriptObserver.observe(document.body, { subtree: true, childList: true, characterData: true });
let readerNav = null; // the previous and next word, for swipes and the arrow keys
const getHash = () => location.hash;
const go = (h) => { if (location.hash === h) route(); else location.hash = h; };
const json = async (u) => { const r = await fetch(u); if (!r.ok) throw new Error(`Could not load ${u} (${r.status})`); return r.json(); };
const tsv = async (u) => { const r = await fetch(u); if (!r.ok) throw new Error(`Could not load ${u} (${r.status})`); return (await r.text()).split('\n'); };
const K = createKosha({
  main, $, esc, T: esc, Tp: (en) => en, go, getHash, json, tsv, SUN_SVG, ARROW, base: '../',
  setTitle: (t) => { document.title = t ? `${t} — Śabdārtha Kaustubha` : 'Śabdārtha Kaustubha — Sanskrit–Kannada dictionary'; },
  setReaderNav: (v) => { readerNav = v; },
  sourcesHref: '#/about',
  creditExtra: ' · <button type="button" class="k-dl" id="kDl"></button>',
});

let routing = false;
async function route() {
  const h = location.hash;
  const m = h.match(/^#\/kosha(?:\/([^?]*))?(?:\?(.*))?$/);
  const head = m?.[1] ? decodeURIComponent(m[1]) : null;
  const params = new URLSearchParams(m?.[2] || '');
  routing = true;
  const about = /^#\/about/.test(h);
  try { if (about) await viewAbout(); else await K.view(head, params); }
  catch (err) { main.innerHTML = `<div class="col"><h1>Couldn’t load this page</h1><p class="lede">${esc(err.message)}. Check your connection and reload.</p></div>`; readerNav = null; }
  if (prefs.script === 'knda') toScript(main);
  chrome(head, params, about);
  // the list scrolls itself to a letter, to where you left it, or to the author note
  const placed = !about && !head && (params.get('at') || params.get('about') || params.get('letter') || params.get('find'));
  if (!placed) window.scrollTo(0, 0);
  main.focus({ preventScroll: true });
  paintDownload();
  routing = false;
}
function chrome(head, params, about) {
  const home = !about && !head && !params.get('letter') && !params.get('at') && !params.get('find') && !params.get('about');
  $('#backBtn').hidden = home;
  document.title = about ? 'About — Śabdārtha Kaustubha' : document.title;
  $('#brand').classList.toggle('when-back', !home);
  const find = !!params.get('find');
  document.querySelectorAll('#kbar [data-k]').forEach((a) => ((a.dataset.k === 'home' && home) || (a.dataset.k === 'find' && find) || (a.dataset.k === 'about' && about) ? a.setAttribute('aria-current', 'page') : a.removeAttribute('aria-current')));
}
window.addEventListener('hashchange', () => { if (!location.hash || location.hash === '#' || location.hash === '#/') { history.replaceState(null, '', '#/kosha'); } route(); });
// swipe sideways on a word, or press the arrow keys, for the neighbouring word
let sx = 0; let sy = 0; let st = 0;
document.addEventListener('touchstart', (e) => { const t = e.touches[0]; sx = t.clientX; sy = t.clientY; st = Date.now(); }, { passive: true });
document.addEventListener('touchend', (e) => {
  if (!readerNav || e.target.closest?.('input, textarea, .k-sug, details')) return;
  const t = e.changedTouches[0]; const dx = t.clientX - sx; const dy = t.clientY - sy;
  if (Math.abs(dx) < 70 || Math.abs(dy) > Math.abs(dx) * 0.6 || Date.now() - st > 700) return;
  const to = dx < 0 ? readerNav.next : readerNav.prev; if (to) go(to.href);
}, { passive: true });
document.addEventListener('keydown', (e) => {
  if (!readerNav || e.target.closest?.('input, textarea') || e.metaKey || e.ctrlKey || e.altKey) return;
  const to = e.key === 'ArrowRight' ? readerNav.next : e.key === 'ArrowLeft' ? readerNav.prev : null; if (to) go(to.href);
});

// ---------- offline: the app shell is stored by the service worker; the words are stored here on request ----------
const DATA_CACHE = 'vedalokana-data'; // the same store Vedāvalokanam uses, so a download in either app serves both
const abs = (f) => new URL(`../${f}`, location.href).href;
let pack = null; let state = 'idle';
async function loadPack() { try { pack = (await json('../data/offline.json')).packs.find((p) => p.id === 'kosha'); } catch { pack = null; } }
async function haveCount() { const c = await caches.open(DATA_CACHE); const have = new Set((await c.keys()).map((r) => r.url)); return pack.files.filter((f) => have.has(abs(f))).length; }
async function paintDownload(msg) {
  const b = $('#kDl'); if (!b) return;
  if (!pack || !('caches' in window)) { b.hidden = true; return; }
  const n = await haveCount().catch(() => 0);
  const done = n === pack.files.length;
  b.disabled = state === 'busy' || done;
  b.textContent = msg || (done ? 'Available offline' : state === 'busy' ? 'Downloading…' : `Download for offline use (${Math.round(pack.bytes / 1e6)} MB)`);
}
async function download() {
  if (state === 'busy' || !pack) return;
  state = 'busy'; navigator.storage?.persist?.().catch(() => {});
  const c = await caches.open(DATA_CACHE); const have = new Set((await c.keys()).map((r) => r.url));
  const todo = pack.files.filter((f) => !have.has(abs(f))); let done = pack.files.length - todo.length; let failed = 0;
  const tick = () => paintDownload(`Downloading… ${Math.round((done / pack.files.length) * 100)}%`);
  await Promise.all(Array.from({ length: 6 }, async () => {
    while (todo.length) { const f = todo.shift(); try { const r = await fetch(`../${f}`); if (!r.ok) throw new Error(r.status); await c.put(abs(f), r); } catch { failed++; } done++; tick(); }
  }));
  state = 'idle'; paintDownload(failed ? `${failed} files did not download. Try again.` : undefined);
}
main.addEventListener('click', (e) => { if (e.target.closest('#kDl')) download(); });


// ---------- About and settings: appearance, script, offline status, version and update ----------
const verOf = (t) => (String(t).match(/version:\s*'(\d+\.\d+\.\d+)'/) || [])[1];
const newer = (a, b) => { const x = a.split('.').map(Number); const y = b.split('.').map(Number); for (let i = 0; i < 3; i++) if (x[i] !== y[i]) return x[i] > y[i]; return false; };
async function offlineReport() {
  if (!('serviceWorker' in navigator) || !('caches' in window)) return { ready: false, text: 'This browser cannot keep the app for offline use.' };
  const shell = (await caches.keys()).includes(`kosha-shell-${window.KOSHA_APP.version}`);
  const ctrl = !!navigator.serviceWorker.controller;
  const total = pack?.files.length || 0; const n = pack ? await haveCount().catch(() => 0) : 0;
  if (!shell || !ctrl) return { ready: false, text: 'The app is not stored on this device yet. Reload once while online.', n, total };
  if (total && n === total) return { ready: true, text: 'Ready offline: the app and all dictionary words are stored on this device.', n, total };
  return { ready: false, partial: true, text: `The app opens offline. ${n} of ${total} dictionary files are stored; words you have opened work offline, and the download below stores the rest.`, n, total };
}
async function viewAbout() {
  const man = await K.data.manifest().catch(() => null);
  const ver = window.KOSHA_APP;
  main.innerHTML = `<div class="col ab">
    <h1>About</h1>
    <p class="lede">Śabdārtha Kaustubha: a Sanskrit–Kannada dictionary${man ? ` of ${man.count.toLocaleString('en-US')} words` : ''}.</p>
    <h2>Appearance</h2>
    <div class="seg" id="abTheme" role="group" aria-label="Theme">${['light', 'dark', 'system'].map((t) => `<button type="button" data-v="${t}" aria-pressed="${prefs.theme === t}">${t[0].toUpperCase() + t.slice(1)}</button>`).join('')}</div>
    <h2>Script for the Sanskrit</h2>
    <div class="seg" id="abScript" role="group" aria-label="Script">${[['deva', 'Devanagari'], ['knda', 'ಕನ್ನಡ']].map(([v, l]) => `<button type="button" data-v="${v}" aria-pressed="${prefs.script === v}">${l}</button>`).join('')}</div>
    <p class="muted"><small>Kannada meanings stay as they are; the Sanskrit words, derivations and quotations change script.</small></p>
    <h2>Offline</h2>
    <p id="abOff" role="status">Checking…</p>
    <button type="button" class="ab-btn" id="abDl"></button>
    <h2>Version</h2>
    <p>Śabdārtha Kaustubha app <b>${esc(ver.version)}</b><span class="muted"> · ${esc(ver.released)}</span></p>
    <button type="button" class="ab-btn" id="abUp">Check for updates</button>
    <p id="abUpS" class="muted" role="status"></p>
    <h2>The dictionary</h2>
    <p>Compiled by Chakravarti Srinivasa Gopalacharya. <a href="#/kosha?about=author">About the author</a></p>
    <p class="muted"><small>The text is read from the open digital edition distributed by the indic-dict project (<a href="https://github.com/indic-dict/stardict-sanskrit" rel="noopener">github.com/indic-dict/stardict-sanskrit</a>). Words are looked up by their headword; meanings are in Kannada.</small></p>
  </div>`;
  const pick = (id, key, fn) => $(id).addEventListener('click', (e) => {
    const b = e.target.closest('button[data-v]'); if (!b) return;
    prefs[key] = b.dataset.v; savePrefs(); fn(); $(id).querySelectorAll('button').forEach((x) => x.setAttribute('aria-pressed', String(x === b)));
  });
  pick('#abTheme', 'theme', applyTheme);
  pick('#abScript', 'script', () => { route(); }); // redraw: back to Devanagari too
  $('#abDl').addEventListener('click', async () => { await download(); fillOffline(); });
  $('#abUp').addEventListener('click', checkUpdate);
  fillOffline();
}
async function fillOffline() {
  const el = $('#abOff'); if (!el) return;
  const r = await offlineReport();
  el.innerHTML = r.ready ? `<span class="ab-ok">${esc(r.text)}</span>` : esc(r.text);
  const b = $('#abDl'); if (!b) return;
  b.hidden = !pack || !('caches' in window) || r.ready;
  b.textContent = `Download the dictionary (${pack ? Math.round(pack.bytes / 1e6) : 23} MB)`;
}
async function checkUpdate() {
  const out = $('#abUpS'); const btn = $('#abUp'); btn.disabled = true; out.textContent = 'Checking…';
  try {
    const latest = verOf(await (await fetch(`version.js?fresh=${Date.now()}`, { cache: 'no-store' })).text());
    const mine = window.KOSHA_APP.version;
    if (!latest || !newer(latest, mine)) { out.textContent = `You have the latest version (${mine}).`; btn.disabled = false; return; }
    out.textContent = `Version ${latest} is available. Updating…`;
    const reg = await navigator.serviceWorker?.getRegistration();
    await reg?.update();
    const w = reg?.installing || reg?.waiting;
    if (!w) { out.textContent = `Version ${latest} is published, but this device still holds the old copy. Try again in a few minutes.`; btn.disabled = false; return; }
    // the new worker takes over by itself; reload once it has
    const done = await new Promise((res) => {
      const t = setTimeout(() => res(false), 20000);
      const ok = () => { clearTimeout(t); res(true); };
      if (w.state === 'activated') ok();
      w.addEventListener('statechange', () => { if (w.state === 'activated') ok(); if (w.state === 'redundant') { clearTimeout(t); res(false); } });
      navigator.serviceWorker.addEventListener('controllerchange', ok, { once: true });
    });
    if (done) { location.reload(); return; }
    out.textContent = 'The update did not finish. Check the connection and try again.'; btn.disabled = false;
  } catch { out.textContent = 'Could not check for updates. Are you online?'; btn.disabled = false; }
}

if ('serviceWorker' in navigator && location.protocol !== 'file:') navigator.serviceWorker.register('sw.js', { scope: './', updateViaCache: 'none' }).catch(() => {});
if (!location.hash || location.hash === '#' || location.hash === '#/') history.replaceState(null, '', '#/kosha');
loadPack().then(() => route());
