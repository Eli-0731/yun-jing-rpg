import { createServer } from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import { resolve, sep, extname } from 'node:path';

const root = resolve(import.meta.dirname, '../..');
const port = Number(process.env.QINGXI_TRIAL_PORT || 4173);
const types = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8', '.json': 'application/json; charset=utf-8',
  '.css': 'text/css; charset=utf-8', '.webmanifest': 'application/manifest+json',
  '.glb': 'model/gltf-binary', '.png': 'image/png', '.svg': 'image/svg+xml' };

createServer(async (request, response) => {
  try {
    const pathname = decodeURIComponent(new URL(request.url, 'http://localhost').pathname);
    const demoAsset = /^\/tools\/(training-yard-demo|qingxi-encounter-a)\/(vendor|assets|rabbit|world)\/(.+)$/.exec(pathname);
    const assetBase = demoAsset && ({
      'training-yard-demo/vendor': 'tools/training-yard-demo/node_modules/three',
      'training-yard-demo/assets': 'art/exports/qingxi-training-yard-v1',
      'training-yard-demo/world': 'art/exports/qingxi-entry-assets-v13',
      'qingxi-encounter-a/vendor': 'tools/qingxi-encounter-a/node_modules/three',
      'qingxi-encounter-a/assets': 'art/exports/qingxi-encounter-a',
      'qingxi-encounter-a/rabbit': 'art/exports/qingxi-mountain-rabbit-v003',
    })[`${demoAsset[1]}/${demoAsset[2]}`];
    const assetRoot = assetBase ? resolve(root, assetBase) : null;
    const absolute = demoAsset && assetRoot
      ? resolve(assetRoot, demoAsset[3])
      : resolve(root, `.${pathname.endsWith('/') ? pathname + 'index.html' : pathname}`);
    if (!absolute.startsWith(root + sep) || demoAsset && (!assetRoot || !absolute.startsWith(assetRoot + sep))) {
      response.writeHead(403).end(); return;
    }
    const metadata = await stat(absolute);
    if (!metadata.isFile()) { response.writeHead(404).end(); return; }
    response.writeHead(200, { 'Content-Type': types[extname(absolute)] || 'application/octet-stream',
      'Cache-Control': 'no-cache', 'Content-Length': metadata.size });
    response.end(await readFile(absolute));
  } catch { response.writeHead(404).end('Not found'); }
}).listen(port, '127.0.0.1', () => {
  process.stdout.write(`青溪試玩：http://127.0.0.1:${port}/tools/qingxi-trial/\n`);
});
