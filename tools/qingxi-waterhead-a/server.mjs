import http from 'node:http';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

// Local-only static server: loopback bind, GET/HEAD, fixed allowlist. No API, no persistence, no rewards.
const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(here, '../..');
const KIT = ['A01_straight_01', 'A01_bend_left_01', 'A01_narrow_01', 'A01_bend_right_01', 'A01_end_source_01', 'A02_side_crack_01', 'A02_end_break_01',
  'A03_FormationBase', 'A04_SiltBar', 'A04_SiltBar_cleared', 'A04_SiltSide_02', 'A04_SiltJam_03', 'A05_WitheredSedge_01', 'A05_WitheredSedge_02',
  'A05_WitheredSedge_03', 'A06_MarkerStone', 'A07_NurseryTracks', 'A08_steps_line_01', 'A08_slabs_stagger_01', 'A08_gravel_bar_01', 'A09_WaterGauge',
  'A10_FallenBamboo', 'A11_PavilionRuin', 'A12_ResonanceStone'];
// Background dressing reused read-only from the delivered forest encounter kit (PR #39, same author).
const FOREST = ['A06_RootStump', 'A03_FallenLog'];
const routes = {
  '/assets/': { root: path.join(repo, 'art/exports/qingxi-waterhead-a'), allow: KIT.map(k => `${k}.glb`) },
  '/forest/': { root: path.join(repo, 'art/exports/qingxi-encounter-a'), allow: FOREST.map(k => `${k}.glb`) },
  '/vendor/': { root: path.join(here, 'node_modules/three'), allow: null },
};
const SHELL = ['index.html', 'app.mjs', 'investigation.mjs', 'audio.mjs', 'style.css', 'observations.example.json'];
const types = { '.html': 'text/html; charset=utf-8', '.mjs': 'text/javascript', '.js': 'text/javascript', '.css': 'text/css', '.glb': 'model/gltf-binary',
  '.json': 'application/json' };
const PORT = Number(process.env.PORT || 4182);

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
}).listen(PORT, '127.0.0.1', () => console.log(`Upstream investigation: http://127.0.0.1:${PORT} (local demo; no rewards)`));
