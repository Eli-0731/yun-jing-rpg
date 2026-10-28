const CACHE='qingxi-water-report-c-batch1';
const P='../../art/previews/qingxi-water-report-c/';
const FILES=['./index.html','style.css','fixtures.js','responses.js','state.js','app.js','icon.svg','manifest.webmanifest',...['dry','partial','restored'].map(x=>P+'corner-'+x+'.png'),...['C01','C02','C03','C04'].map(x=>P+x+'-close.png'),P+'eye-height-1p7m.png'];
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(FILES))));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(x=>x.startsWith('qingxi-water-report-c-')&&x!==CACHE).map(x=>caches.delete(x)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',e=>{const u=new URL(e.request.url);if(e.request.method==='GET'&&u.origin===location.origin&&(u.pathname.startsWith('/tools/qingxi-water-report-c/')||u.pathname.startsWith('/art/previews/qingxi-water-report-c/')))e.respondWith(caches.match(e.request).then(c=>c||fetch(e.request)));});
