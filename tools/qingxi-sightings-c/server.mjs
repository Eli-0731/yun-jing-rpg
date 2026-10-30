// Local demo server for 青溪見聞 C. Eli-0731. Serves only this tool, its models, previews and the A2/A3 block data, on loopback.
import http from 'node:http';import path from 'node:path';import{fileURLToPath}from'node:url';import{readFile}from'node:fs/promises';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..'),base='/tools/qingxi-sightings-c/';
const allowed=[base,'/art/exports/qingxi-sightings-c/','/art/previews/qingxi-sightings-c/','/tools/qingxi-terrain/blocks/'];
const types={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.mjs':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json; charset=utf-8','.png':'image/png','.svg':'image/svg+xml','.glb':'model/gltf-binary'};
const server=http.createServer(async(req,res)=>{try{const url=new URL(req.url,'http://127.0.0.1');if(url.pathname==='/'){res.writeHead(302,{Location:base+'index.html'});res.end();return;}
  let route=decodeURIComponent(url.pathname);if(route+'/'===base)route=base;if(route.endsWith('/'))route+='index.html';
  const file=path.resolve(root,'.'+route);
  if(!file.startsWith(root+path.sep)||!allowed.some(p=>route.startsWith(p))||route.includes('..')||route.includes('\\')){res.writeHead(403);res.end('Forbidden');return;}
  const body=await readFile(file);res.writeHead(200,{'Content-Type':types[path.extname(file)]||'application/octet-stream','Cache-Control':'no-cache'});res.end(body);}
  catch{res.writeHead(404);res.end('Not found');}});
server.listen(Number(process.env.PORT||4331),'127.0.0.1',()=>console.log('Qingxi sightings: http://127.0.0.1:'+server.address().port+base));
