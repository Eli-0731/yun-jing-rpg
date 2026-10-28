// Offline cache for the local showcase. Bump VERSION whenever a model or page file changes.
const VERSION = 'qingxi-training-yard-v4';
const SHELL = [
  './', './index.html', './style.css', './app.mjs', './practice.mjs', './audio.mjs', './manifest.webmanifest',
  './icon.svg', './icon-192.png', './icon-512.png',
  './vendor/build/three.module.js', './vendor/examples/jsm/loaders/GLTFLoader.js', './vendor/examples/jsm/utils/BufferGeometryUtils.js',
  ...['training-shelter', 'qi-striking-post', 'agility-post', 'weapon-rack', 'engraved-training-stone', 'training-banner'].map(n => `./assets/${n}.glb`),
  './world/village-gate-v13.glb',
];
self.addEventListener('install', e => e.waitUntil(caches.open(VERSION).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())));
self.addEventListener('activate', e => e.waitUntil(Promise.all([
  caches.keys().then(keys => Promise.all(keys.filter(k => k.startsWith('qingxi-training-yard-') && k !== VERSION).map(k => caches.delete(k)))),
  self.clients.claim(),
])));
self.addEventListener('fetch', e => {
  const req = e.request, url = new URL(req.url);
  if (req.method !== 'GET' || url.origin !== self.location.origin) return;
  // Network first so an updated page is never shadowed by the cache; the cache answers when offline.
  e.respondWith(fetch(req).then(res => {
    if (res.ok && res.type === 'basic') { const copy = res.clone(); e.waitUntil(caches.open(VERSION).then(c => c.put(req, copy))); }
    return res;
  }).catch(() => caches.match(req).then(hit => hit || Response.error())));
});
