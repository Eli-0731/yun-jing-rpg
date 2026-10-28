const CACHE = 'qingxi-guide-c-v2';
const FILES = ['./','index.html','style.css','landscape.css','state.js','app.js','manifest.webmanifest','icon.svg',...['Q01','Q02','Q03','Q04'].map(id=>`previews/${id}-close.png`)];
self.addEventListener('install', e => { e.waitUntil(caches.open(CACHE).then(c=>c.addAll(FILES))); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('qingxi-guide-c-')&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())); });
self.addEventListener('fetch', e => {
  if(e.request.method!=='GET'||new URL(e.request.url).origin!==location.origin||!e.request.url.startsWith(self.registration.scope))return;
  e.respondWith(caches.match(e.request).then(c=>c||fetch(e.request)));
});
