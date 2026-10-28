// Serves the novice village WebGL/PWA build (artifacts/webgl-novice-village) on loopback.
//   node tools/qingxi-webgl/serve.mjs            http://127.0.0.1:4190/
//   http://127.0.0.1:4190/?abc-smoke             runs the in-game smoke; result in the browser console
//   http://127.0.0.1:4190/?touch                 forces the on-screen touch controls with a mouse
// Loopback counts as a secure context, so the PWA service worker and "install" work locally.
import { createServer } from 'node:http';
import { createReadStream, existsSync, statSync } from 'node:fs';
import { extname, join, normalize, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(fileURLToPath(new URL('../../artifacts/webgl-novice-village', import.meta.url)));
const port = Number(process.env.PORT || 4190);
const types = {
  '.html': 'text/html; charset=utf-8', '.js': 'application/javascript', '.json': 'application/json',
  '.webmanifest': 'application/manifest+json', '.wasm': 'application/wasm', '.data': 'application/octet-stream',
  '.png': 'image/png', '.ico': 'image/x-icon', '.css': 'text/css', '.svg': 'image/svg+xml',
};

createServer((req, res) => {
  const url = new URL(req.url, 'http://localhost');
  let path = normalize(join(root, decodeURIComponent(url.pathname)));
  if (path !== root && !path.startsWith(root + sep)) { res.writeHead(403).end(); return; }
  if (existsSync(path) && statSync(path).isDirectory()) path = join(path, 'index.html');
  if (!existsSync(path)) { res.writeHead(404).end('not found'); return; }
  // Unity names compressed files *.js.gz, *.wasm.gz, *.data.gz; send them gzip-encoded with the inner type.
  const gz = path.endsWith('.gz');
  const type = types[extname(gz ? path.slice(0, -3) : path)] || 'application/octet-stream';
  const headers = { 'Content-Type': type, 'Cache-Control': 'no-cache' };
  if (gz) headers['Content-Encoding'] = 'gzip';
  res.writeHead(200, headers);
  createReadStream(path).pipe(res);
}).listen(port, '127.0.0.1', () => console.log(`Qingxi novice village (WebGL/PWA): http://127.0.0.1:${port}/`));
