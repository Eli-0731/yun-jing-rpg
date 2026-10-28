const CACHE = 'qingxi-trial-v6';
const SHELL = ['/tools/qingxi-trial/', '/tools/qingxi-trial/index.html',
  '/tools/qingxi-trial/main.js', '/tools/qingxi-trial/scene-content.mjs', '/tools/qingxi-trial/icon.svg',
  '/tools/qingxi-trial/manifest.webmanifest'];
self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(SHELL)));
  self.skipWaiting();
});
self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key !== CACHE).map(key => caches.delete(key)))));
  self.clients.claim();
});
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET' || new URL(event.request.url).origin !== self.location.origin) return;
  event.respondWith(fetch(event.request).then(response => {
    if (response.ok) caches.open(CACHE).then(cache => cache.put(event.request, response.clone()));
    return response;
  }).catch(() => caches.match(event.request)));
});
