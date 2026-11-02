/* Service worker. Two caches:
   vr-shell-<version>  app shell (pages that make up the app, scripts, styles, fonts, icons): cache first,
                       replaced as a whole on every release
   vr-data             texts and data (sarga pages, JSON): stale-while-revalidate, never dropped by an update */
importScripts('static/version.js');
const VERSION = self.VRAMAYANA.version;
const SHELL = 'vr-shell-' + VERSION, DATA = 'vr-data';
const SHELL_FILES = /*SHELL_FILES*/[];
const scope = self.registration.scope;
const abs = (p) => new URL(p, scope).href;
const shellSet = new Set(SHELL_FILES.map(abs));

self.addEventListener('install', (e) => {
  e.waitUntil((async () => {
    const c = await caches.open(SHELL);
    await c.addAll(SHELL_FILES.map((p) => new Request(abs(p), { cache: 'reload' })));
    await self.skipWaiting();
  })());
});
self.addEventListener('activate', (e) => {
  e.waitUntil((async () => {
    for (const k of await caches.keys()) if (k.startsWith('vr-shell-') && k !== SHELL) await caches.delete(k);
    await self.clients.claim();
  })());
});
self.addEventListener('message', (e) => { if (e.data === 'version' && e.source) e.source.postMessage({ version: VERSION }); });

const OFFLINE = '<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>Not downloaded yet</title><body style="font:1.1rem system-ui;padding:2rem"><h1>Not downloaded yet</h1><p>This page has not been opened or downloaded on this device, and you are offline.</p><p><a href="' + scope + '">Home</a></p>';

self.addEventListener('fetch', (e) => {
  const r = e.request;
  if (r.method !== 'GET') return;
  const u = new URL(r.url);
  if (u.origin !== location.origin || u.searchParams.has('fresh')) return;
  const key = u.origin + u.pathname;
  if (shellSet.has(key) || shellSet.has(key.replace(/index\.html$/, ''))) {
    e.respondWith(caches.open(SHELL).then((c) => c.match(key.replace(/index\.html$/, ''), { ignoreSearch: true })).then((m) => m || fetch(r)));
    return;
  }
  e.respondWith((async () => {
    const c = await caches.open(DATA);
    const hit = await c.match(r, { ignoreSearch: true });
    const net = fetch(r).then((res) => { if (res.ok) c.put(r, res.clone()); return res; }).catch(() => null);
    if (hit) { e.waitUntil(net); return hit; }
    const res = await net;
    if (res) return res;
    return r.mode === 'navigate' ? new Response(OFFLINE, { headers: { 'content-type': 'text/html; charset=utf-8' }, status: 503 }) : Response.error();
  })());
});
