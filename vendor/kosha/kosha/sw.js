/* Service worker of the standalone Dictionary app (scope: this folder). Its own, narrower scope means it, and not
   Vedāvalokanam's worker one folder up, handles this app's pages.
   - The app shell (this folder, the shared styles, code, fonts) is stored on install, per version of this app.
   - Dictionary data (../data/kosha/…) goes in the same cache Vedāvalokanam uses, 'vedalokana-data': read once, it opens offline
     from then on, and a download in either app serves both. When online it is refreshed in the background. */
importScripts('version.js');
const VERSION = self.KOSHA_APP.version;
const SHELL = `kosha-shell-${VERSION}`;
const DATA = 'vedalokana-data';
const SHELL_FILES = [
  './', 'index.html', 'app.js', 'kosha.css', 'version.js', 'manifest.webmanifest',
  'icons/icon.svg', 'icons/icon-192.png', 'icons/apple-touch-icon.png',
  '../styles.css', '../kosha-ui.js', '../kosha.js', '../translit.js', '../search-key.js', '../common.js', '../lipi.js',
  '../fonts/IBMPlexSans-Var.woff', '../fonts/GentiumBookPlus-Regular.woff', '../fonts/GentiumBookPlus-Italic.woff', '../fonts/GentiumBookPlus-Bold.woff',
  '../fonts/NotoSerifDevanagari-Vedic.woff', '../fonts/NotoSerifKannada-Vedic.woff',
  '../fonts/NotoSerifDevanagari-Std.woff', '../fonts/NotoSerifKannada-Std.woff',
  '../fonts/Shobhika-Vedic.woff', '../fonts/Shobhika-Std.woff',
];
const DATA_CORE = ['../data/kosha/shards.json', '../data/kosha/wotd.json', '../data/offline.json'];

self.addEventListener('install', (e) => {
  e.waitUntil((async () => {
    const shell = await caches.open(SHELL);
    await shell.addAll(SHELL_FILES.map((u) => new Request(u, { cache: 'reload' })));
    const data = await caches.open(DATA);
    await Promise.all(DATA_CORE.map(async (u) => { try { const r = await fetch(u, { cache: 'reload' }); if (r.ok) await data.put(new URL(u, self.location).href, r); } catch { /* stored on first use */ } }));
    await self.skipWaiting();
  })());
});
self.addEventListener('activate', (e) => {
  e.waitUntil((async () => {
    for (const k of await caches.keys()) if (k.startsWith('kosha-shell-') && k !== SHELL) await caches.delete(k);
    await self.clients.claim();
  })());
});

const parent = new URL('../', self.registration.scope).pathname; // the folder with data/, fonts/ and the shared code
const inData = (url) => url.pathname.startsWith(parent + 'data/');

async function staleWhileRevalidate(e, key) {
  const cache = await caches.open(DATA);
  const hit = await cache.match(key);
  const net = fetch(e.request).then((r) => { if (r.ok) cache.put(key, r.clone()); return r; }).catch(() => null);
  if (hit) { e.waitUntil(net); return hit; }
  return (await net) || new Response('Offline and not downloaded yet', { status: 503, statusText: 'Offline' });
}
self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.origin !== self.location.origin || url.searchParams.has('fresh')) return;
  if (e.request.mode === 'navigate') {
    e.respondWith((async () => (await caches.match('index.html', { cacheName: SHELL })) || fetch(e.request))());
  } else if (inData(url)) {
    e.respondWith(staleWhileRevalidate(e, url.origin + url.pathname));
  } else {
    e.respondWith((async () => (await caches.match(url.origin + url.pathname, { cacheName: SHELL })) || fetch(e.request))());
  }
});
self.addEventListener('message', (e) => { if (e.data === 'version') e.source?.postMessage({ version: VERSION }); });
