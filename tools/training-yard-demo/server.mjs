import http from 'node:http';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
const here=path.dirname(fileURLToPath(import.meta.url));
const roots={ '/assets/':path.resolve(here,'../../art/exports/qingxi-training-yard-v1'), '/vendor/':path.resolve(here,'node_modules/three') };
const types={'.html':'text/html; charset=utf-8','.mjs':'text/javascript','.js':'text/javascript','.css':'text/css','.glb':'model/gltf-binary','.json':'application/json','.webmanifest':'application/manifest+json','.svg':'image/svg+xml','.png':'image/png'};
http.createServer(async(req,res)=>{
 try{
  if(req.method!=='GET'&&req.method!=='HEAD'){res.writeHead(405);return res.end();}
  const pathname=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
  const prefix=Object.keys(roots).find(p=>pathname.startsWith(p));
  const root=prefix?roots[prefix]:here;
  const rel=prefix?pathname.slice(prefix.length):(pathname==='/'?'index.html':pathname.slice(1));
  const file=path.resolve(root,rel);
  if(!file.startsWith(root+path.sep)||(!prefix&&!['index.html','app.mjs','rhythm.mjs','style.css','manifest.webmanifest','icon.svg','icon-192.png','icon-512.png','sw.js'].includes(rel))){res.writeHead(403);return res.end();}
  const data=await readFile(file);res.writeHead(200,{'Content-Type':types[path.extname(file)]||'application/octet-stream','Cache-Control':'no-store'});res.end(req.method==='HEAD'?undefined:data);
 }catch{res.writeHead(404);res.end('Not found');}
}).listen(4178,'127.0.0.1',()=>console.log('Training yard: http://127.0.0.1:4178 (local demo; no rewards)'));
