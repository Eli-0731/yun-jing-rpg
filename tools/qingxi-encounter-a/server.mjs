import http from 'node:http';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

// Local-only static server: loopback bind, GET/HEAD, fixed allowlist. No API, no persistence, no rewards.
const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(here, '../..');
const KIT = ['A01_SlopeTile', 'A02_HollowTile', 'A03_FallenLog', 'A04_MossBoulderCover', 'A05_LayeredRockCover', 'A06_RootStump',
  'A07_RabbitTrailTile', 'A08_BrokenBambooFence', 'A09_StoneShelter', 'A10_WatchPlatform', 'A11_WarningClothRack', 'A12_VineDummy'];
const routes = {
  '/assets/': { root: path.join(repo, 'art/exports/qingxi-encounter-a'), allow: KIT.map(k => `${k}.glb`) },
  // Rabbit v003 is reused read-only (Johnnnny0823 / Codex, PR #21); this demo does not modify it.
  '/rabbit/': { root: path.join(repo, 'art/exports/qingxi-mountain-rabbit-v003'), allow: ['QingxiMountainRabbit_v003.glb'] },
  '/vendor/': { root: path.join(here, 'node_modules/three'), allow: null },
};
const SHELL = ['index.html', 'app.mjs', 'encounter.mjs', 'audio.mjs', 'style.css'];
const types = { '.html': 'text/html; charset=utf-8', '.mjs': 'text/javascript', '.js': 'text/javascript', '.css': 'text/css', '.glb': 'model/gltf-binary' };
const PORT = Number(process.env.PORT || 4181);

http.createServer(async (req, res) => {
  try {
    if (req.method !== 'GET' && req.method !== 'HEAD') { res.writeHead(405); return res.end(); }
    const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
    const prefix = Object.keys(routes).find(p => pathname.startsWith(p));
    const rel = prefix ? pathname.slice(prefix.length) : pathname === '/' ? 'index.html' : pathname.slice(1);
    const root = prefix ? routes[prefix].root : here;
    const file = path.resolve(root, rel);
    const ok = prefix ? (routes[prefix].allow ? routes[prefix].allow.includes(rel) : /^(build|examples\/jsm)\//.test(rel)) : SHELL.includes(rel);
    if (!file.startsWith(root + path.sep) || !ok) { res.writeHead(403); return res.end(); }
    const data = await readFile(file);
    res.writeHead(200, { 'Content-Type': types[path.extname(file)] || 'application/octet-stream', 'Cache-Control': 'no-store' });
    res.end(req.method === 'HEAD' ? undefined : data);
  } catch { res.writeHead(404); res.end('Not found'); }
}).listen(PORT, '127.0.0.1', () => console.log(`Forest encounter: http://127.0.0.1:${PORT} (local demo; no drops)`));
