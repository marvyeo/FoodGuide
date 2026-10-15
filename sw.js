// Makan Map service worker — lets the installed app open offline.
// App files and data/places.json: network first, cached copy when offline (so a merged data PR shows up on next open).
// Fonts, Leaflet and OneMap tiles: cache first. Google sign-in and Sheets always go to the network.
const CACHE = 'makanmap-v7';
const TILES = 'makanmap-tiles-v2';
const SHELL = ['./', './index.html', './manifest.json', './data/places.json', './icons/icon-192.png', './icons/icon-512.png'];
const CDN_HOSTS = ['fonts.googleapis.com', 'fonts.gstatic.com', 'cdnjs.cloudflare.com', 'cdn.jsdelivr.net'];
const MAX_TILES = 600;

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).catch(() => {}).then(() => self.skipWaiting()));
});
self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k !== CACHE && k !== TILES).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
async function trimTiles() {
  const c = await caches.open(TILES); const keys = await c.keys();
  for (let i = 0; i < keys.length - MAX_TILES; i++) await c.delete(keys[i]);
}
self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin === self.location.origin) {
    e.respondWith(fetch(req).then(res => {
      if (res.ok) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(req, copy)); }
      return res;
    }).catch(() => caches.match(req, { ignoreSearch: true })
      .then(hit => hit || (req.mode === 'navigate' ? caches.match('./index.html') : Response.error()))));
    return;
  }
  if (CDN_HOSTS.includes(url.hostname) || (url.hostname === 'www.onemap.gov.sg' && url.pathname.startsWith('/maps/tiles/'))) {
    const tile = (url.hostname === 'www.onemap.gov.sg' && url.pathname.startsWith('/maps/tiles/'));
    e.respondWith(caches.open(tile ? TILES : CACHE).then(async c => {
      const hit = await c.match(req);
      if (hit) return hit;
      return fetch(req).then(res => { if (res.ok || res.type === 'opaque') { c.put(req, res.clone()); if (tile) trimTiles(); } return res; });
    }));
  }
});
