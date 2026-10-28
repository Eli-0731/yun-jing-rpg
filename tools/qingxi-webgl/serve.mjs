// Serves the novice village WebGL/PWA build (artifacts/webgl-novice-village) on loopback.
//   node tools/qingxi-webgl/serve.mjs            http://127.0.0.1:4190/
//   http://127.0.0.1:4190/?abc-smoke             runs the in-game smoke; result in the browser console
//   http://127.0.0.1:4190/?touch                 forces the on-screen touch controls with a mouse
// Loopback counts as a secure context, so the PWA service worker and "install" work locally.
import { createServer } from 'node:http';
import { createReadStream, existsSync, readdirSync, statSync } from 'node:fs';
import { extname, join, normalize, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(fileURLToPath(new URL('../../artifacts/webgl-novice-village', import.meta.url)));
const port = Number(process.env.PORT || 4190);
const types = {
  '.html': 'text/html; charset=utf-8', '.js': 'application/javascript', '.json': 'application/json',
  '.webmanifest': 'application/manifest+json', '.wasm': 'application/wasm', '.data': 'application/octet-stream',
  '.png': 'image/png', '.ico': 'image/x-icon', '.css': 'text/css', '.svg': 'image/svg+xml',
};

// A new build must never be hidden behind the old one: Unity keeps game data in IndexedDB and the PWA
// service worker keeps its own cache. The build version is the data file's timestamp; the first page load
// after a rebuild gets Clear-Site-Data (cache + storage) and a reload, so players never clear anything by hand.
function buildVersion() {
  const build = join(root, 'Build');
  if (!existsSync(build)) return '0';
  const data = readdirSync(build).find(f => f.includes('.data'));
  return data ? String(Math.floor(statSync(join(build, data)).mtimeMs)) : '0';
}

function serviceWorker(version) {
  return `const cacheName = 'qingxi-novice-village-${version}';
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil((async () => {
  for (const key of await caches.keys()) if (key !== cacheName) await caches.delete(key);
  await self.clients.claim();
})()));
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith((async () => {
    try {
      const response = await fetch(e.request);
      if (response.ok) (await caches.open(cacheName)).put(e.request, response.clone());
      return response;
    } catch (offline) {
      const cached = await caches.match(e.request);
      if (cached) return cached;
      throw offline;
    }
  })());
});
`;
}

createServer((req, res) => {
  const url = new URL(req.url, 'http://localhost');
  let path = normalize(join(root, decodeURIComponent(url.pathname)));
  if (path !== root && !path.startsWith(root + sep)) { res.writeHead(403).end(); return; }
  if (existsSync(path) && statSync(path).isDirectory()) path = join(path, 'index.html');
  if (!existsSync(path)) { res.writeHead(404).end('not found'); return; }
  const version = buildVersion();
  const seen = /(?:^|;\s*)qx-build=([^;]+)/.exec(req.headers.cookie || '')?.[1];
  // Unity's PWA template ships a cache-first worker with a fixed cache name, so a page opened once keeps the
  // old build forever. Serve a network-first worker whose cache is named after the build; offline still works.
  if (url.pathname.endsWith('/ServiceWorker.js')) {
    const headers = { 'Content-Type': 'application/javascript', 'Cache-Control': 'no-store' };
    if (seen !== version) { headers['Clear-Site-Data'] = '"cache", "storage"'; headers['Set-Cookie'] = `qx-build=${version}; Path=/; SameSite=Lax`; }
    res.writeHead(200, headers).end(serviceWorker(version));
    return;
  }
  if (path.endsWith('index.html')) {
    if (seen !== version) {
      // Wipe the old build's caches, remember this build, and come straight back to the same URL.
      res.writeHead(303, {
        'Clear-Site-Data': '"cache", "storage"',
        'Set-Cookie': `qx-build=${version}; Path=/; SameSite=Lax`,
        Location: req.url,
        'Cache-Control': 'no-store',
      }).end();
      return;
    }
  }
  // Unity names compressed files *.js.gz, *.wasm.gz, *.data.gz; send them gzip-encoded with the inner type.
  const gz = path.endsWith('.gz');
  const type = types[extname(gz ? path.slice(0, -3) : path)] || 'application/octet-stream';
  // ETag / Last-Modified let Unity's IndexedDB data cache revalidate instead of trusting a stale copy.
  const stat = statSync(path);
  const etag = `"${stat.size}-${Math.floor(stat.mtimeMs)}"`;
  if (req.headers['if-none-match'] === etag) { res.writeHead(304, { ETag: etag }).end(); return; }
  const headers = { 'Content-Type': type, 'Cache-Control': 'no-cache', ETag: etag, 'Last-Modified': stat.mtime.toUTCString() };
  if (gz) headers['Content-Encoding'] = 'gzip';
  res.writeHead(200, headers);
  createReadStream(path).pipe(res);
}).listen(port, '127.0.0.1', () => console.log(`Qingxi novice village (WebGL/PWA): http://127.0.0.1:${port}/`));
