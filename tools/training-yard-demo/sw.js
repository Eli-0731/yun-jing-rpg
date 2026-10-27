const VERSION='qingxi-training-yard-v3';
const SHELL=[
  './','./index.html','./style.css','./app.mjs','./rhythm.mjs','./manifest.webmanifest','./icon.svg','./icon-192.png','./icon-512.png',
  './vendor/build/three.module.js',
  './vendor/examples/jsm/loaders/GLTFLoader.js',
  './vendor/examples/jsm/utils/BufferGeometryUtils.js',
  ...['training-shelter','qi-striking-post','agility-post','weapon-rack','engraved-training-stone','training-banner'].map(name=>`./assets/${name}.glb`)
];

self.addEventListener('install',event=>{
  event.waitUntil(caches.open(VERSION).then(cache=>cache.addAll(SHELL)).then(()=>self.skipWaiting()));
});

self.addEventListener('activate',event=>{
  event.waitUntil(Promise.all([
    caches.keys().then(keys=>Promise.all(keys.filter(key=>key.startsWith('qingxi-training-yard-')&&key!==VERSION).map(key=>caches.delete(key)))),
    self.clients.claim()
  ]));
});

self.addEventListener('fetch',event=>{
  const request=event.request;
  const url=new URL(request.url);
  if(request.method!=='GET'||url.origin!==self.location.origin||url.pathname.startsWith('/v1/'))return;
  event.respondWith(caches.match(request).then(cached=>cached||fetch(request).then(response=>{
    if(response.ok&&response.type==='basic'){
      const copy=response.clone();
      event.waitUntil(caches.open(VERSION).then(cache=>cache.put(request,copy)));
    }
    return response;
  })));
});
