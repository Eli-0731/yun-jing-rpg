const CACHE='qingxi-return-c-batch1';
const FILES=['./','index.html','style.css','state.js','app.js','icon.svg','manifest.webmanifest','previews/return-corner.png',...['C01','C02','C03','C04'].map(id=>`previews/${id}-close.png`)];
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(FILES))));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('qingxi-return-c-')&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',e=>{if(e.request.method==='GET'&&new URL(e.request.url).origin===location.origin&&e.request.url.startsWith(self.registration.scope))e.respondWith(caches.match(e.request).then(c=>c||fetch(e.request)));});
