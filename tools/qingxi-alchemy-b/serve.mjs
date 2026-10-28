// Static server for the workshop demo (serves the repo root so the GLBs under art/exports load as-is).
//   node tools/qingxi-alchemy-b/serve.mjs [port]      -> http://127.0.0.1:8765/tools/qingxi-alchemy-b/
// POST /__frame?n=<int> (127.0.0.1 only) saves walkthrough frames to $QA_FRAMES or <tmp>/qingxi-alchemy-frames (outside the repo).
import { createServer } from 'node:http';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { extname, join, normalize, resolve } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(fileURLToPath(new URL('../../', import.meta.url)));
const FRAMES = process.env.QA_FRAMES ?? join(tmpdir(), 'qingxi-alchemy-frames');
const TYPES = { '.html': 'text/html; charset=utf-8', '.mjs': 'text/javascript', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json',
  '.glb': 'model/gltf-binary', '.png': 'image/png', '.md': 'text/markdown; charset=utf-8' };
const port = Number(process.argv[2] ?? 8765);

createServer(async (req, res) => {
  const url = new URL(req.url, 'http://x');
  try {
    if (req.method === 'POST' && url.pathname === '/__frame') {
      const n = Number.parseInt(url.searchParams.get('n'), 10);
      if (!Number.isInteger(n) || n < 0 || n > 99999) { res.writeHead(400).end(); return; }
      const chunks = []; for await (const c of req) chunks.push(c);
      const [, ext, b64] = Buffer.concat(chunks).toString().match(/^data:image\/(png|jpeg);base64,(.*)$/s) ?? [];
      if (!b64) { res.writeHead(400).end(); return; }
      await mkdir(FRAMES, { recursive: true }); await writeFile(join(FRAMES, `f${String(n).padStart(5, '0')}.${ext === 'jpeg' ? 'jpg' : 'png'}`), Buffer.from(b64, 'base64'));
      res.writeHead(204).end(); return;
    }
    const path = normalize(join(ROOT, decodeURIComponent(url.pathname)));
    if (!path.startsWith(ROOT)) { res.writeHead(403).end(); return; }
    const file = path.endsWith('\\') || path.endsWith('/') ? join(path, 'index.html') : path;
    const body = await readFile(file);
    res.writeHead(200, { 'content-type': TYPES[extname(file)] ?? 'application/octet-stream', 'cache-control': 'no-store' }).end(body);
  } catch {
    res.writeHead(404).end('not found');
  }
}).listen(port, '127.0.0.1', () => console.log(`http://127.0.0.1:${port}/tools/qingxi-alchemy-b/`));
