import http from 'node:http';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

// Local-only static server: loopback bind, GET/HEAD, fixed allowlist. No API, no persistence.
const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(here, '../..');
const ASSETS = ['training-shelter', 'qi-striking-post', 'agility-post', 'weapon-rack', 'engraved-training-stone', 'training-banner'];
const routes = {
  '/assets/': { root: path.join(repo, 'art/exports/qingxi-training-yard-v1'), allow: ASSETS.map(a => `${a}.glb`) },
  // Read-only backdrop from the core v13 entry kit (not modified here).
  '/world/': { root: path.join(repo, 'art/exports/qingxi-entry-assets-v13'), allow: ['village-gate-v13.glb'] },
  '/vendor/': { root: path.join(here, 'node_modules/three'), allow: null },
};
const SHELL = ['index.html', 'app.mjs', 'practice.mjs', 'audio.mjs', 'style.css', 'manifest.webmanifest', 'icon.svg', 'icon-192.png', 'icon-512.png', 'sw.js'];
const types = { '.html': 'text/html; charset=utf-8', '.mjs': 'text/javascript', '.js': 'text/javascript', '.css': 'text/css', '.glb': 'model/gltf-binary',
  '.json': 'application/json', '.webmanifest': 'application/manifest+json', '.svg': 'image/svg+xml', '.png': 'image/png' };
const PORT = Number(process.env.PORT || 4178);

http.createServer(async (req, res) => {
  try {
    if (req.method !== 'GET' && req.method !== 'HEAD') { res.writeHead(405); return res.end(); }
    const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
    const prefix = Object.keys(routes).find(p => pathname.startsWith(p));
    const rel = prefix ? pathname.slice(prefix.length) : pathname === '/' ? 'index.html' : pathname.slice(1);
    const root = prefix ? routes[prefix].root : here;
    const file = path.resolve(root, rel);
    const allowed = prefix ? (routes[prefix].allow ? routes[prefix].allow.includes(rel) : /^(build|examples\/jsm)\//.test(rel)) : SHELL.includes(rel);
    if (!file.startsWith(root + path.sep) || !allowed) { res.writeHead(403); return res.end(); }
    const data = await readFile(file);
    res.writeHead(200, { 'Content-Type': types[path.extname(file)] || 'application/octet-stream', 'Cache-Control': 'no-store' });
    res.end(req.method === 'HEAD' ? undefined : data);
  } catch { res.writeHead(404); res.end('Not found'); }
}).listen(PORT, '127.0.0.1', () => console.log(`Training yard: http://127.0.0.1:${PORT} (local demo; no rewards)`));
