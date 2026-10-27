// 青溪採集路段：獨立橫向示範（Three.js）。
// 座標：x = 沿路前進方向，y = 上，z = 朝鏡頭。GLB 由 Blender 匯出（Blender 正面 -Y → glTF +Z），正面朝向鏡頭。
// 1 單位 = 1 公尺。數量只採用伺服器回應；沒有 ?server= 時一律標示「本機演示」。
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';

const ASSETS = '../../art/exports/qingxi-gathering-visual-kit-v1/';
const VER = 'v001';
const SERVER = new URLSearchParams(location.search).get('server');   // 例如 ?server=http://127.0.0.1:8790
const PATH_W = 1.6;                    // 主路寬（公尺）
const CH0 = 40.0, PLANKS = 6;          // 支流渠：踏板段起點與模組數
let FOOT = 0.732, CH1 = CH0 + PLANKS * FOOT;   // 板面寬（載入時以 model_info 更新）
const BED_Y = -0.45, WATER_Y = BED_Y + 0.16;
let PLANK_TOP = BED_Y + 0.62;
const FORK0 = 36.5, FORK1 = 39.9, WADE_Z = 1.4, WADE_STOP = 39.6;
const X_MIN = -4, X_MAX = 59, REACH = 1.7, GATHER_SEC = 1.2;

const NODES = [
  {id: 'qinglan_01', asset: 'QX_SpiritHerb_Qinglan', name: '青溪蘭', x: 12, z: -1.15,
   observe: '溪石背陰處的一叢蘭：三支花莖垂著玉色花朵，唇瓣帶紅紫細斑，花心有微光。',
   traits: ['可採部位：花莖連花；葉與新芽留著', '工具：小鐮', '採後：花莖只剩短樁，外葉割短，割下的葉、花落在土上'],
   local: {item: '青溪蘭花莖', qty: 1}, respawn: 120, reason: '花莖已割下，根旁的新芽還沒抽出花莖'},
  {id: 'chilu_01', asset: 'QX_SpiritHerb_Chilu', name: '赤露參', x: 24, z: -1.05,
   observe: '一片茂草裡長著三株赤露參，掌狀複葉下托著一團一團深紅漿果。',
   traits: ['可採部位：成熟漿果', '工具：徒手', '採後：果梗光禿，留一顆青果；主株旁草被踩倒，一片葉折斷'],
   local: {item: '赤露參漿果', qty: 3}, respawn: 180, reason: '漿果已摘完，剩下那顆還是青的'},
  {id: 'yumai_01', asset: 'QX_EmbeddedOre_Yumai', name: '嵌地玉脈石', x: 51, z: -1.25,
   observe: '一對裂開的花崗岩半埋土中，縫裡淡玉色的脈上長出一簇發光晶柱。',
   traits: ['可採部位：晶柱', '工具：小鎬', '採後：晶柱斷成斷口、露出新鮮石疤，碎晶散落'],
   local: {item: '玉脈晶', qty: 2}, respawn: 300, reason: '晶簇已敲斷，玉脈還沒重新凝出晶尖'},
];

// ---------------------------------------------------------------- renderer / scene
const canvas = document.getElementById('view');
const renderer = new THREE.WebGLRenderer({canvas, antialias: true, preserveDrawingBuffer: true});
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
const scene = new THREE.Scene();
scene.background = skyTexture();
scene.fog = new THREE.Fog('#b9cdc6', 28, 95);
const camera = new THREE.PerspectiveCamera(34, 1, 0.05, 400);

scene.add(new THREE.HemisphereLight('#d6e8ea', '#56583e', 1.25));
const sun = new THREE.DirectionalLight('#fff1d8', 2.4);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, {left: -14, right: 14, top: 10, bottom: -10, near: 1, far: 60});
sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.02;
scene.add(sun, sun.target);

function skyTexture() {
  const c = document.createElement('canvas'); c.width = 4; c.height = 256;
  const g = c.getContext('2d'), gr = g.createLinearGradient(0, 0, 0, 256);
  gr.addColorStop(0, '#8fb3c2'); gr.addColorStop(.55, '#c9dad3'); gr.addColorStop(1, '#e4e2cf');
  g.fillStyle = gr; g.fillRect(0, 0, 4, 256);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}

// ---------------------------------------------------------------- terrain
function rnd(seed) { let s = seed >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }
function vnoise(x, z) { return Math.sin(x * 1.7 + Math.sin(z * 2.3)) * .5 + Math.sin(z * 1.1 - x * .6) * .3 + Math.sin(x * 4.1 + z * 3.7) * .2; }

function groundPatch(x0, x1, z0, z1) {
  const g = new THREE.PlaneGeometry(x1 - x0, z1 - z0, Math.ceil((x1 - x0) * 2), Math.ceil((z1 - z0) * 2));
  g.rotateX(-Math.PI / 2); g.translate((x0 + x1) / 2, 0, (z0 + z1) / 2);
  const p = g.attributes.position, col = [];
  const grass = new THREE.Color('#5d7240'), dry = new THREE.Color('#8d8a58'), dirt = new THREE.Color('#9a8566'), wet = new THREE.Color('#4a4535');
  const c = new THREE.Color();
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i), z = p.getZ(i), n = vnoise(x, z);
    const onPath = Math.abs(z - pathZ(x)) < PATH_W / 2 + .12 * n;
    c.copy(grass).lerp(dry, .5 + .5 * Math.sin(x * .31 + n));
    if (onPath) c.copy(dirt).lerp(dry, .25 + .15 * n);
    if (z > 1.9) c.lerp(wet, Math.min(1, (z - 1.9) / .5));
    if (!onPath && z < 1.8) p.setY(i, .04 * n + (z < -4 ? (-4 - z) * .05 : 0));
    col.push(c.r, c.g, c.b);
  }
  g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3)); g.computeVertexNormals();
  const m = new THREE.Mesh(g, new THREE.MeshStandardMaterial({vertexColors: true, roughness: .95}));
  m.receiveShadow = true; scene.add(m);
}
function pathZ(x) { return 0; }      // 主路沿 z = 0，寬 1.6 m

function wall(ax, az, bx, bz) {      // 河岸 / 渠岸的土壁（0 → 河床）
  const g = new THREE.PlaneGeometry(Math.hypot(bx - ax, bz - az), -BED_Y);
  const m = new THREE.Mesh(g, new THREE.MeshStandardMaterial({color: '#5a4c3a', roughness: 1, side: THREE.DoubleSide}));
  m.position.set((ax + bx) / 2, BED_Y / 2, (az + bz) / 2); m.rotation.y = -Math.atan2(bz - az, bx - ax);
  m.receiveShadow = true; scene.add(m);
}

function buildTerrain() {
  groundPatch(-14, CH0, -30, 2.4);
  groundPatch(CH1, 70, -30, 2.4);
  const bed = new THREE.Mesh(new THREE.PlaneGeometry(120, 60), new THREE.MeshStandardMaterial({color: '#3c3a2c', roughness: 1}));
  bed.rotation.x = -Math.PI / 2; bed.position.set(28, BED_Y, 0); bed.receiveShadow = true; scene.add(bed);
  wall(-14, 2.4, CH0, 2.4); wall(CH1, 2.4, 70, 2.4); wall(CH0, -30, CH0, 2.4); wall(CH1, -30, CH1, 2.4);
  // 溪水：前方主溪＋穿過路的支流渠
  water = new THREE.Mesh(new THREE.PlaneGeometry(130, 14, 260, 28), new THREE.MeshStandardMaterial({color: '#3f6f69', roughness: .12, metalness: 0, transparent: true, opacity: .8}));
  water.rotation.x = -Math.PI / 2; water.position.set(28, WATER_Y, 9.4); scene.add(water);
  const ch = new THREE.Mesh(new THREE.PlaneGeometry(CH1 - CH0, 32.4, 10, 64), water.material);
  ch.rotation.x = -Math.PI / 2; ch.position.set((CH0 + CH1) / 2, WATER_Y, -13.8); scene.add(ch);
  // 涉水路線：濕滑半沒的石頭（示範中不能通行）
  const r = rnd(7), stoneMat = new THREE.MeshStandardMaterial({color: '#59605a', roughness: .35});
  for (let x = CH0 + .35; x < CH1; x += .62) {
    const s = new THREE.Mesh(new THREE.SphereGeometry(.26, 12, 8), stoneMat);
    s.scale.set(1 + r() * .4, .45, .9 + r() * .3); s.position.set(x, WATER_Y - .05 + r() * .03, WADE_Z + (r() - .5) * .3);
    s.castShadow = s.receiveShadow = true; scene.add(s);
  }
  ribbon([[-6, 0], [CH0 + .02, 0]], PATH_W, '#9a8768');                         // 主路 1.6 m
  ribbon([[CH1 - .02, 0], [60, 0]], PATH_W, '#9a8768');
  ribbon([[FORK0, 0], [FORK0 + 1.5, .55], [FORK1, WADE_Z]], 1.0, '#857559');   // 岔路：涉水
  // 遠山
  [['#8ea79f', -38, 9, 1], ['#a8bbb4', -62, 15, 2], ['#bccbc4', -90, 22, 3]].forEach(([c, z, h, s]) => {
    const sh = new THREE.Shape(); sh.moveTo(-60, 0);
    const rr = rnd(s * 11);
    for (let x = -60; x <= 130; x += 4) sh.lineTo(x, h * (.55 + .45 * Math.sin(x * .05 * s + s) * Math.sin(x * .023 + 1)) + rr() * h * .12);
    sh.lineTo(130, 0); sh.lineTo(-60, 0);
    const m = new THREE.Mesh(new THREE.ShapeGeometry(sh), new THREE.MeshBasicMaterial({color: c, fog: true}));
    m.position.set(0, -.5, z); scene.add(m);
  });
}
function ribbon(pts, w, color) {
  const v = [], idx = [];
  const curve = new THREE.CatmullRomCurve3(pts.map(([x, z]) => new THREE.Vector3(x, .03, z)));
  const N = 24;
  for (let i = 0; i <= N; i++) {
    const p = curve.getPoint(i / N), t = curve.getTangent(i / N), n = new THREE.Vector3(-t.z, 0, t.x).multiplyScalar(w / 2);
    v.push(p.x + n.x, p.y, p.z + n.z, p.x - n.x, p.y, p.z - n.z);
    if (i < N) idx.push(2 * i, 2 * i + 1, 2 * i + 2, 2 * i + 1, 2 * i + 3, 2 * i + 2);
  }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(v, 3)); g.setIndex(idx); g.computeVertexNormals();
  const m = new THREE.Mesh(g, new THREE.MeshStandardMaterial({color, roughness: 1, side: THREE.DoubleSide})); m.receiveShadow = true; scene.add(m);
}
let water;

// ---------------------------------------------------------------- models
const loader = new GLTFLoader();
const models = {}, missing = [];
function glbUrl(key) { const aid = key.replace(/_(pre|post)$/, ''); return `${ASSETS}${aid}/${VER}/${key}.glb`; }
async function loadModel(key) {
  try {
    let g;
    for (let i = 0; ; i++) {                       // 大檔並行下載偶爾中斷：重試兩次；404 直接放棄
      try { g = await loader.loadAsync(glbUrl(key)); break; }
      catch (e) { if (i >= 2 || /404/.test(e.message)) throw e; await new Promise(r => setTimeout(r, 400 * (i + 1))); }
    }
    g.scene.traverse(o => { if (o.isMesh) { o.castShadow = o.receiveShadow = true; } });
    models[key] = g.scene;
  } catch (e) {
    console.warn('GLB', key, e); missing.push(key); models[key] = placeholder(key);
  }
}
function placeholder(key) {               // 找不到 GLB 時的替代方塊（畫面上會標示缺件）
  const m = new THREE.Mesh(new THREE.BoxGeometry(.5, .5, .5), new THREE.MeshStandardMaterial({color: '#c04a3a', wireframe: true}));
  m.position.y = .25; const g = new THREE.Group(); g.add(m); g.userData.placeholder = key; return g;
}
function place(key, x, y, z, ry = 0, s = 1) {
  const o = models[key].clone(); o.position.set(x, y, z); o.rotation.y = ry; o.scale.setScalar(s); scene.add(o); return o;
}
function sizeOf(o) { return new THREE.Box3().setFromObject(o).getSize(new THREE.Vector3()); }

// ---------------------------------------------------------------- player（替身：人物製作已停，只用簡單形體）
const player = new THREE.Group();
{
  const robe = new THREE.MeshStandardMaterial({color: '#2f5a55', roughness: .8}), skin = new THREE.MeshStandardMaterial({color: '#d9b896', roughness: .7});
  const body = new THREE.Mesh(new THREE.CapsuleGeometry(.2, .78, 6, 14), robe); body.position.y = .62;
  const head = new THREE.Mesh(new THREE.SphereGeometry(.13, 16, 12), skin); head.position.y = 1.36;
  const hat = new THREE.Mesh(new THREE.ConeGeometry(.3, .14, 20), new THREE.MeshStandardMaterial({color: '#b39a62', roughness: .9})); hat.position.y = 1.52;
  const basket = new THREE.Mesh(new THREE.CylinderGeometry(.13, .1, .26, 14), new THREE.MeshStandardMaterial({color: '#8a6a3c', roughness: .9})); basket.position.set(0, .86, -.2);
  [body, head, hat, basket].forEach(m => { m.castShadow = true; player.add(m); });
}
scene.add(player);
const P = {x: 1.2, z: 0, y: 0, lane: 'plank', chosen: false, face: 1, vx: 0};

// ---------------------------------------------------------------- nodes / markers
function marker() {
  const c = document.createElement('canvas'); c.width = c.height = 64;
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  const s = new THREE.Sprite(new THREE.SpriteMaterial({map: t, depthTest: false, transparent: true})); s.scale.set(.42, .42, 1); s.renderOrder = 10;
  s.userData.draw = (ch, bg) => { const g = c.getContext('2d'); g.clearRect(0, 0, 64, 64); g.fillStyle = bg; g.beginPath(); g.arc(32, 32, 28, 0, 7); g.fill();
    g.fillStyle = '#fff'; g.font = 'bold 38px sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(ch, 32, 34); t.needsUpdate = true; };
  return s;
}
function setNodeModel(n, post) {
  if (n.obj) scene.remove(n.obj);
  n.obj = place(`${n.asset}_${post ? 'post' : 'pre'}`, n.x, 0, n.z);
  const sz = sizeOf(n.obj), h = sz.y; n.h = h; n.size = Math.max(sz.x, sz.z);
  n.marker.position.set(n.x, Math.max(h, .5) + .45, n.z);
}
function refreshMarker(n) {
  if (n.state === 'ready') n.marker.userData.draw('?', 'rgba(60,110,95,.9)');
  if (n.state === 'observed') n.marker.userData.draw('!', 'rgba(190,130,40,.95)');
  if (n.state === 'spent') n.marker.userData.draw('…', 'rgba(90,90,90,.85)');
}

// ---------------------------------------------------------------- UI
const $ = id => document.getElementById(id);
const ui = {prompt: $('prompt'), toast: $('toast'), card: $('card'), bar: $('bar'), bag: $('bagList'), where: $('where')};
const bag = [];
let toastT = 0;
function nag(msg) { if (ui.toast.textContent !== msg || toastT < 1) toast(msg, 'bad'); }   // 被擋時重複提醒，不洗掉同一則
function toast(msg, kind = '') { ui.toast.textContent = msg; ui.toast.className = kind; ui.toast.hidden = false; toastT = 4.5; }
function showCard(n) {
  $('cardName').textContent = n.name;
  $('cardState').textContent = {ready: '未觀察', observed: '已觀察，可採集', spent: '已採過'}[n.state];
  $('cardBody').textContent = n.state === 'spent' ? spentText(n) : n.observe;
  $('cardTraits').innerHTML = n.traits.map(t => `<li>${t}</li>`).join('');
  ui.card.hidden = false;
}
function spentText(n) {
  const left = Math.max(0, Math.ceil(n.readyAt - now()));
  const why = n.serverReason || n.reason;
  return `尚未再生：${why}。` + (left ? `約 ${Math.floor(left / 60)} 分 ${left % 60} 秒後再生（${n.serverReason ? '伺服器回覆' : '本機計時'}）。` : '');
}
function renderBag() {
  ui.bag.innerHTML = bag.length ? bag.map(b => `<li>${b.item} ×${b.qty}${b.official ? '' : '<span class="note">本機演示，非正式數量</span>'}</li>`).join('') : '<li class="dim">尚未採集</li>';
}
{
  const m = $('mode');
  if (SERVER) { m.className = 'mode server'; m.textContent = `伺服器模式：數量以 ${SERVER} 回應為準`; }
  else { m.className = 'mode local'; m.textContent = '本機演示：未連線伺服器，採集數量不是正式結果'; }
}

// ---------------------------------------------------------------- gather logic
const clock = new THREE.Clock(); let tNow = 0; const now = () => tNow;
let gathering = null;
function nearNode() {
  let best = null;
  for (const n of NODES) { const d = Math.abs(P.x - n.x); if (d < REACH && P.lane === 'plank' && (!best || d < Math.abs(P.x - best.x))) best = n; }
  return best;
}
async function act() {
  const n = nearNode(); if (!n || gathering) return;
  if (n.state === 'ready') { n.state = 'observed'; refreshMarker(n); showCard(n); camMode = 'near'; toast(`觀察：${n.name}。再按 E 採集。`); return; }
  if (n.state === 'spent') { showCard(n); toast(spentText(n), 'bad'); return; }
  gathering = {n, t: 0}; ui.bar.hidden = false;
}
async function finishGather(n) {
  ui.bar.hidden = true;
  if (SERVER) {
    let res;
    try {
      const r = await fetch(`${SERVER.replace(/\/$/, '')}/gather`, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({node: n.id, asset: n.asset})});
      res = await r.json();
      if (!r.ok || !res.ok) { n.serverReason = res.reason || `伺服器拒絕（HTTP ${r.status}）`; if (res.respawn_seconds) { n.state = 'spent'; n.readyAt = now() + res.respawn_seconds; refreshMarker(n); } toast(n.serverReason, 'bad'); showCard(n); return; }
    } catch (e) { toast('伺服器沒有回應，這次不算採集，現場不變。', 'bad'); return; }
    bag.push({item: res.item, qty: res.qty, official: true});
    n.serverReason = res.reason || null; n.readyAt = now() + (res.respawn_seconds ?? n.respawn);
    toast(`採得 ${res.item} ×${res.qty}（伺服器回應）`, 'ok');
  } else {
    bag.push({...n.local, official: false});
    n.serverReason = null; n.readyAt = now() + n.respawn;
    toast(`本機演示：${n.local.item} ×${n.local.qty}（非正式數量）`, 'ok');
  }
  n.state = 'spent'; setNodeModel(n, true); refreshMarker(n); renderBag(); showCard(n);
}
function tickNodes() {
  for (const n of NODES) if (n.state === 'spent' && now() >= n.readyAt) {
    n.state = 'ready'; setNodeModel(n, false); refreshMarker(n); n.serverReason = null;
    if (Math.abs(P.x - n.x) < 12) toast(`${n.name} 已再生${SERVER ? '' : '（本機計時）'}`);
  }
}

// ---------------------------------------------------------------- input / movement
const keys = new Set();
let camMode = 'side';
addEventListener('keydown', e => {
  const k = e.key.toLowerCase(); keys.add(k);
  if (k === 'e' && !e.repeat) act();
  if (k === 'c' && !e.repeat) camMode = camMode === 'side' ? 'near' : 'side';
  if (k === 'w' || k === 'arrowup') chooseLane('plank');
  if (k === 's' || k === 'arrowdown') chooseLane('wade');
  if (k === 'escape') { ui.card.hidden = true; camMode = 'side'; }
});
addEventListener('keyup', e => keys.delete(e.key.toLowerCase()));
function chooseLane(l) {
  if (P.x < FORK0 || P.x > FORK1 + .05 || (P.lane === l && P.chosen)) return;
  P.lane = l; P.chosen = true; toast(l === 'plank' ? '選擇：踏板路線（板面平、乾，可直接走過）' : '選擇：涉水踩石（試試看）');
}
function surfaceY(x, lane) {
  if (lane === 'plank' && x > CH0 - .15 && x < CH1 + .15) {
    const e = Math.min(x - (CH0 - .15), (CH1 + .15) - x); return PLANK_TOP * Math.min(1, e / .3);   // 上下踏板緩升，不需要跳
  }
  return 0;
}
function move(dt) {
  const dir = (keys.has('d') || keys.has('arrowright') ? 1 : 0) - (keys.has('a') || keys.has('arrowleft') ? 1 : 0);
  P.vx += ((dir * 2.4) - P.vx) * Math.min(1, dt * 10);
  let nx = P.x + P.vx * dt;
  if (!P.chosen && P.x <= FORK1 && nx > FORK1) {                                   // 臨水岔口：一定要先選路才能往前
    nx = FORK1; nag('岔口：先選路。W 走踏板，S 涉水踩石。');
  }
  if (nx < FORK0 && P.lane === 'wade') P.lane = 'plank';                         // 回到岔口前，回主路
  if (P.lane === 'wade' && nx > WADE_STOP) {
    nx = WADE_STOP; nag('石面濕滑、水深過膝，這條不能過。按 W 改走踏板。');
  }
  nx = Math.min(X_MAX, Math.max(X_MIN, nx)); P.x = nx;
  if (Math.abs(dir) > 0) P.face = dir;
  const tz = P.lane === 'wade' ? WADE_Z * THREE.MathUtils.smoothstep(P.x, FORK0, FORK1) : 0;
  P.z += (tz - P.z) * Math.min(1, dt * 8);
  P.y += (surfaceY(P.x, P.lane) - P.y) * Math.min(1, dt * 12);
  player.position.set(P.x, P.y, P.z); player.rotation.y = P.face > 0 ? Math.PI / 2 : -Math.PI / 2;
  if (Math.abs(P.vx) > .2) player.children[0].position.y = .62 + Math.abs(Math.sin(tNow * 9)) * .03;
  if (gathering && (Math.abs(P.x - gathering.n.x) > REACH || Math.abs(dir) > 0)) { gathering = null; ui.bar.hidden = true; toast('採集中斷'); }
}
function updatePrompt() {
  const n = nearNode(); let p = '';
  if (n) p = n.state === 'ready' ? `E：觀察 ${n.name}` : n.state === 'observed' ? `E：採集 ${n.name}` : `E：查看 ${n.name} 為何還沒再生`;
  else if (P.x >= FORK0 && P.x <= FORK1 + .05) p = `岔口：W 踏板路線（往玉脈石）　·　S 涉水踩石　　目前：${P.lane === 'plank' ? '踏板' : '涉水'}`;
  else if (P.x < 3) p = '安全點：採藥山門。往右走（D）沿溪找靈草與礦石。';
  ui.prompt.textContent = p;
  if (!n && !ui.card.hidden && camMode === 'near') camMode = 'side';
  if (!n) ui.card.hidden = true;
  const seg = P.x < 3 ? '採藥山門（安全點）' : P.x < FORK0 ? '溪畔小路' : P.x < CH0 ? '岔口' : P.x < CH1 ? '渡溪踏板' : '玉脈石灘';
  ui.where.innerHTML = `<b>${seg}</b><br><span class="dim">x ${P.x.toFixed(1)} m　路寬 ${PATH_W} m${P.y > .05 ? '　板面高 ' + P.y.toFixed(2) + ' m' : ''}</span>`;
}

// ---------------------------------------------------------------- camera
const camPos = new THREE.Vector3(), camLook = new THREE.Vector3();
let freeCam = null;                    // 走查截圖用的固定鏡頭（qxDemo.view）
function updateCamera(dt, snap = false) {
  if (freeCam) { camera.position.copy(freeCam[0]); camera.lookAt(freeCam[1]); sun.position.set(freeCam[1].x - 7, 12, 9); sun.target.position.set(freeCam[1].x + 2, 0, -1); return; }
  const n = nearNode();
  let pos, look;
  const near = camMode === 'near' && n;
  player.visible = !near; for (const m of NODES) if (m.marker) m.marker.visible = !(near && m === n);   // 觀察近景：替身與標記不擋畫面
  if (near) {
    const side = P.x > n.x ? -1 : 1, r = Math.max(.9, n.size * .95);
    pos = new THREE.Vector3(n.x + side * r * .45, n.h * .55 + r * .55, n.z + r * 1.7); look = new THREE.Vector3(n.x, n.h * .38, n.z);
  } else { pos = new THREE.Vector3(P.x + 1.6 * P.face, 2.4, 9.5); look = new THREE.Vector3(P.x + 1.6 * P.face, .85, -.6); }
  const k = snap ? 1 : Math.min(1, dt * 3);
  camPos.lerp(pos, k); camLook.lerp(look, k); camera.position.copy(camPos); camera.lookAt(camLook);
  sun.position.set(P.x - 7, 12, 9); sun.target.position.set(P.x + 2, 0, -1);
}

// ---------------------------------------------------------------- frame
function resize() { const w = innerWidth, h = innerHeight; renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix(); }
addEventListener('resize', resize);
function frame() {
  step(Math.min(.05, clock.getDelta()));
  renderer.render(scene, camera); requestAnimationFrame(frame);
}
function step(dt) {
  tNow += dt;
  move(dt); tickNodes(); updatePrompt(); updateCamera(dt);
  if (gathering) { gathering.t += dt; ui.bar.firstElementChild.style.width = `${Math.min(100, gathering.t / GATHER_SEC * 100)}%`; if (gathering.t >= GATHER_SEC) { const n = gathering.n; gathering = null; finishGather(n); } }
  if (toastT > 0 && (toastT -= dt) <= 0) ui.toast.hidden = true;
  const wp = water.geometry.attributes.position;
  for (let i = 0; i < wp.count; i += 1) wp.setZ(i, Math.sin(wp.getX(i) * 1.3 + tNow * 1.4) * .012 + Math.sin(wp.getY(i) * 2.1 - tNow) * .008);
  wp.needsUpdate = true;
}

// ---------------------------------------------------------------- boot
(async () => {
  try {                                                  // 板面尺寸取自匯出的 model_info，渠寬 = 6 個模組
    const info = await (await fetch(`${ASSETS}QX_CreekSteppingPlank/${VER}/QX_CreekSteppingPlank_model_info.json`)).json();
    const f = info.build_notes?.foot_surface_size_m, top = info.build_notes?.foot_surface_top_m;
    FOOT = (typeof f === 'string' ? JSON.parse(f) : f)[0]; if (top) PLANK_TOP = BED_Y + top;
  } catch (e) { console.warn('plank model_info', e); }
  CH1 = CH0 + PLANKS * FOOT;
  resize(); buildTerrain();
  const keysToLoad = ['QX_GatheringLandmark', 'QX_CreekSteppingPlank', 'QX_WaterReeds', ...NODES.flatMap(n => [`${n.asset}_pre`, `${n.asset}_post`])];
  await Promise.all(keysToLoad.map(loadModel));
  place('QX_GatheringLandmark', 0, 0, -2.6);
  // 踏板：模組按板面寬（不是含卵石的外寬）首尾相接，板面連續沒有縫，走過去不用跳
  for (let i = 0; i < PLANKS; i++) place('QX_CreekSteppingPlank', CH0 + FOOT * (i + .5), BED_Y, 0, i % 2 ? Math.PI : 0, 1);
  const r = rnd(3);
  for (const [x, z] of [[4.5, 2.25], [9, 2.3], [17.5, 2.2], [21, 2.35], [30, 2.25], [34.5, 2.3], [39.4, 1.9], [39.5, -1.6], [45.3, -1.8], [45.2, 2.0], [55, 2.3]])
    place('QX_WaterReeds', x, 0, z, r() * 6.28, .85 + r() * .3);
  for (const n of NODES) { n.state = 'ready'; n.marker = marker(); scene.add(n.marker); setNodeModel(n, false); refreshMarker(n); }
  P.lane = 'plank'; updateCamera(0, true);
  $('loading').remove();
  if (missing.length) toast(`缺少 GLB：${missing.join('、')}（以紅色線框代替）`, 'bad');
  else toast('從採藥山門出發，往右沿溪走。');
  frame();
  if (new URLSearchParams(location.search).has('walk')) window.walkResult = await (await import('./walkthrough.js')).run(window.qxDemo);
})();

// 自動走查／截圖用：teleport(x, 'plank'|'wade')、press('e')、state()
window.qxDemo = {
  teleport(x, lane = 'plank') { P.x = x; P.lane = lane; P.chosen = P.chosen || x > FORK1; P.vx = 0; P.z = lane === 'wade' ? WADE_Z * THREE.MathUtils.smoothstep(x, FORK0, FORK1) : 0; P.y = surfaceY(x, lane); move(0); updateCamera(0, true); },
  press(k) { dispatchEvent(new KeyboardEvent('keydown', {key: k})); dispatchEvent(new KeyboardEvent('keyup', {key: k})); },
  // 確定性步進（背景分頁不跑 requestAnimationFrame 時也能測）：按住方向鍵 sec 秒
  advance(sec, dir = 0) { const k = dir > 0 ? 'd' : dir < 0 ? 'a' : null; if (k) keys.add(k);
    for (let t = 0; t < sec; t += 1 / 30) step(1 / 30); if (k) keys.delete(k); renderer.render(scene, camera); return this.state(); },
  walk(dx, sec = 1) { return Promise.resolve(this.advance(sec, dx)); },
  cam(m) { camMode = m; freeCam = null; },
  view(pos, look) { freeCam = pos ? [new THREE.Vector3(...pos), new THREE.Vector3(...look)] : null; updateCamera(0, true); },
  skip(sec) { tNow += sec; },
  // 走查截圖：畫面＋主要介面文字合成一張 PNG，送到 serve.py --capture 的資料夾
  async capture(name) {
    renderer.render(scene, camera);
    const c = document.createElement('canvas'); c.width = canvas.width; c.height = canvas.height;
    const g = c.getContext('2d'), k = canvas.width / innerWidth; g.drawImage(canvas, 0, 0);
    const box = (el, align) => {
      if (!el || el.hidden || !el.textContent.trim() || getComputedStyle(el).display === 'none') return;
      const r = el.getBoundingClientRect(), cs = getComputedStyle(el);
      g.fillStyle = cs.backgroundColor; g.fillRect(r.left * k, r.top * k, r.width * k, r.height * k);
      g.fillStyle = cs.color; g.font = `${15 * k}px "Microsoft JhengHei", sans-serif`; g.textBaseline = 'top';
      const lines = el.innerText.split('\n').filter(Boolean); lines.forEach((t, i) => g.fillText(t, (r.left + 10) * k, (r.top + 6 + i * 21) * k, (r.width - 20) * k));
    };
    ['mode', 'where', 'bag', 'card', 'prompt', 'toast'].forEach(id => box($(id)));
    const blob = await new Promise(r => c.toBlob(r, 'image/png'));
    const res = await fetch(`/__capture?name=${encodeURIComponent(name)}.png`, {method: 'POST', body: blob});
    return res.status;
  },
  state() { return {x: P.x, y: P.y, z: P.z, lane: P.lane, bag, missing, nodes: NODES.map(n => ({id: n.id, state: n.state, readyIn: n.state === 'spent' ? Math.max(0, n.readyAt - tNow) : 0}))}; },
};
