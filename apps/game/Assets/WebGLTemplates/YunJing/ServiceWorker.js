/* Network-first and version-scoped. Unity substitutes the triple-brace tokens. */
const cacheName = {{{JSON.stringify(COMPANY_NAME + "-" + PRODUCT_NAME + "-" + PRODUCT_VERSION )}}} + '-' + {{{ JSON.stringify(LOADER_FILENAME) }}};
const prefix = 'yun-jing-';
const key = prefix + cacheName;
self.addEventListener('install', event => event.waitUntil(self.skipWaiting()));
self.addEventListener('activate', event => event.waitUntil((async () => {
  for (const name of await caches.keys()) if (name.startsWith(prefix) && name !== key) await caches.delete(name);
  await self.clients.claim();
})()));
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET' || new URL(event.request.url).origin !== self.location.origin) return;
  event.respondWith((async () => {
    const cache = await caches.open(key);
    try {
      const response = await fetch(event.request);
      if (response.ok) await cache.put(event.request, response.clone());
      return response;
    } catch (error) {
      const saved = await cache.match(event.request);
      if (saved) return saved;
      throw error;
    }
  })());
});
const unityBuildFiles = [
  'Build/{{{ LOADER_FILENAME }}}', 'Build/{{{ DATA_FILENAME }}}',
  'Build/{{{ FRAMEWORK_FILENAME }}}', 'Build/{{{ CODE_FILENAME }}}',
#if USE_THREADS
  'Build/{{{ WORKER_FILENAME }}}',
#endif
#if SYMBOLS_FILENAME
  'Build/{{{ SYMBOLS_FILENAME }}}',
#endif
];
