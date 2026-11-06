// Old-channel repair demo: place B02–B05 by port into the board's slots, pick a direction, complete.
// Rendering and input only — every rule lives in src/waterworks-core.mjs. Results are a local demo and never
// reach an official inventory or ledger (see CONTRACT.md).
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import * as core from './src/waterworks-core.mjs';

const $ = id => document.getElementById(id);
const params = new URLSearchParams(location.search);
const WALK = params.has('walk');
const ROOT = '../../';
const [board, catalog, fixture] = await Promise.all(['data/board.json', 'data/catalog.json', 'data/fixture-observations.json'].map(async p => (await fetch(p)).json()));
const ctx = { board, catalog };
const obsKey = fixture.sets[params.get('obs')] ? params.get('obs') : fixture.default;

// ---------------------------------------------------------------- state
let S = core.newSession(board, catalog, fixture.sets[obsKey].observationIds);
let selected = 'P2', lastResult = null, view = null;
const SLOT = Object.fromEntries(board.slots.map(s => [s.id, s]));
const PALETTE = ['B02', 'B02-V03', 'B02-V04', 'B05', 'B03', 'B03-V04', 'B03-V02', 'B03-V03', 'B04-V02', 'B04', 'B02-V05'];
const PATCHES = ['B07', 'B07-V02', 'B07-V03'];
const KEYS = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-'];
const CHOICE_KEYS = { q: 'clear_silt', w: 'restore_channel', e: 'protect_nursery' };
const CHOICE_HINT = { clear_silt: '三通分流進回流溝', restore_channel: '走原本舊渠、補破槽', protect_nursery: '繞開育幼區 80 cm 外' };
const LEVEL = { risk: '有風險', safe: '安全', unknown: '未知', dry: '沒有流水' };
const SILT = { slowing: '淤積拖慢水量', remaining: '仍有淤積（未經過）', cleared: '已清淤', unknown: '未知' };
const CRACK = { patched: '已補好', leaking: '漏水', bypassed: '水沒經過', unknown: '未知' };
const matName = k => board.materialNames[k] ?? k;
const costText = c => Object.entries(c).map(([k, v]) => `${matName(k)} ${v}`).join('、') || '無';

// ---------------------------------------------------------------- scene
const canvas = $('view');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: WALK });
renderer.setPixelRatio(WALK ? 1 : Math.min(devicePixelRatio, 2));
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace; renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;
const scene = new THREE.Scene(); scene.background = new THREE.Color('#a9bcb3'); scene.fog = new THREE.Fog('#a9bcb3', 14, 30);
const camera = new THREE.PerspectiveCamera(38, 1, 0.05, 80);
scene.add(new THREE.HemisphereLight('#eef3ea', '#4a4035', 1.15));
const sun = new THREE.DirectionalLight('#ffe9cc', 2.4); sun.position.set(-4, 9, 2); sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048); Object.assign(sun.shadow.camera, { left: -7, right: 7, top: 7, bottom: -7, near: 0.5, far: 25 }); sun.shadow.bias = -0.0004;
sun.target.position.set(-0.6, 0, -3); scene.add(sun, sun.target);

// Blender (x, y, z-up) -> three (x, y-up, z): (x, z, -y)
const b2t = (x, y, z = 0) => new THREE.Vector3(x, z, -y);
const mat = (c, o = {}) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.95, ...o });
function flat(rect, z, material) {   // rect [x0, y0, x1, y1] in Blender plan
  const m = new THREE.Mesh(new THREE.PlaneGeometry(rect[2] - rect[0], rect[3] - rect[1]), material);
  m.rotation.x = -Math.PI / 2; m.position.copy(b2t((rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2, z)); m.receiveShadow = true; scene.add(m); return m;
}
function canvasTex(w, h, draw, repeat) {
  const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = t.wrapT = THREE.RepeatWrapping; if (repeat) t.repeat.set(...repeat); return t;
}
// ground, stream, zones
const grassTex = canvasTex(256, 256, (g, w, h) => {
  g.fillStyle = '#66734f'; g.fillRect(0, 0, w, h);
  for (let i = 0; i < 1400; i++) { const x = (i * 97) % w, y = (i * 61 + (i * i) % 37) % h; g.fillStyle = i % 3 ? 'rgba(40,52,30,.25)' : 'rgba(150,160,100,.25)'; g.fillRect(x, y, 2, 5); }
}, [10, 10]);
flat([-9, -5, 7, 11], -0.005, mat('#ffffff', { map: grassTex }));
const streamTex = canvasTex(128, 128, (g, w, h) => {
  g.fillStyle = '#4f8a95'; g.fillRect(0, 0, w, h); g.strokeStyle = 'rgba(220,240,240,.35)'; g.lineWidth = 2;
  for (let i = 0; i < 9; i++) { g.beginPath(); for (let x = 0; x <= w; x += 8) g.lineTo(x, (i * 14 + 6 + Math.sin(x / 13 + i) * 3) % h); g.stroke(); }
}, [8, 1]);
flat([-9, -3.6, 7, -1.85], 0.01, mat('#ffffff', { map: streamTex, roughness: 0.25, metalness: 0.05 }));
flat([-9, -1.95, 7, -1.75], 0.005, mat('#8d7f66'));   // stream bank
const Z = board.zones;
const nurseryMat = mat('#cdbb92');
flat(Z.nursery.rect, 0.02, nurseryMat);
const nurseryRing = flat(Z.nursery.rect.map((v, i) => v + (i < 2 ? -0.12 : 0.12)), 0.012, mat('#888', { transparent: true, opacity: 0.55 }));
{ // low bamboo fence round the nursery, gap on the far side
  const [x0, y0, x1, y1] = Z.nursery.rect, post = mat('#8a7348');
  const posts = [];
  for (let x = x0; x <= x1 + 1e-6; x += 0.25) posts.push([x, y0], [x, y1]);
  for (let y = y0 + 0.25; y < y1 - 1e-6; y += 0.25) posts.push([x0, y]);
  for (const [x, y] of posts) { const m = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.03, 0.5, 6), post); m.position.copy(b2t(x, y, 0.25)); m.castShadow = true; scene.add(m); }
  for (const [a, b] of [[[x0, y0], [x1, y0]], [[x0, y1], [x1, y1]], [[x0, y0], [x0, y1]]]) for (const z of [0.2, 0.42]) {
    const len = Math.hypot(b[0] - a[0], b[1] - a[1]), m = new THREE.Mesh(new THREE.BoxGeometry(len, 0.03, 0.03), post);
    m.position.copy(b2t((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, z)); m.rotation.y = Math.atan2(b[1] - a[1], b[0] - a[0]); m.castShadow = true; scene.add(m);
  }
  for (const [x, y, c] of [[1.4, 3.75, '#c45a3c'], [2.1, 3.55, '#3c7fc4'], [1.9, 4.0, '#d8b53c']]) { const m = new THREE.Mesh(new THREE.SphereGeometry(0.08, 14, 10), mat(c, { roughness: 0.6 })); m.position.copy(b2t(x, y, 0.1)); m.castShadow = true; scene.add(m); }
}
const tracks = new THREE.Group(); scene.add(tracks);   // children's footprints from the nursery to the old channel (nursery_tracks)
for (let i = 0; i < 9; i++) {
  const m = new THREE.Mesh(new THREE.CircleGeometry(0.045, 10), mat('#6b5236')); m.scale.set(0.7, 1.3, 1); m.rotation.x = -Math.PI / 2;
  m.position.copy(b2t(0.72 - i * 0.07, 3.55 + (i % 2) * 0.09 + i * 0.02, 0.026)); tracks.add(m);
}
flat(Z.drain.rect, 0.012, mat('#4c5a52', { roughness: 0.4 }));
const drainWater = flat(Z.drain.rect.map((v, i) => v + (i < 2 ? 0.08 : -0.08)), 0.03, mat('#7d6a46', { transparent: true, opacity: 0, roughness: 0.2 }));

// ---------------------------------------------------------------- text labels (sprites)
function label(text, { color = '#23211d', bg = 'rgba(246,242,232,.92)', size = 0.22, bold = true } = {}) {
  const c = document.createElement('canvas'), g = c.getContext('2d'), px = 44;
  g.font = `${bold ? 700 : 400} ${px}px "Microsoft JhengHei","Noto Sans TC",sans-serif`;
  const w = Math.ceil(g.measureText(text).width) + 28; c.width = w; c.height = px + 22;
  g.font = `${bold ? 700 : 400} ${px}px "Microsoft JhengHei","Noto Sans TC",sans-serif`;
  g.fillStyle = bg; g.beginPath(); g.roundRect(0, 0, w, c.height, 14); g.fill();
  g.fillStyle = color; g.textBaseline = 'middle'; g.fillText(text, 14, c.height / 2 + 2);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  // constant on-screen size (sizeAttenuation off), so close-up player shots stay readable
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: t, depthTest: false, transparent: true, sizeAttenuation: false }));
  const k = size * 0.105; s.scale.set(k * w / c.height, k, 1); s.renderOrder = 10; return s;
}
function setLabel(holder, text, opts) {
  const key = text + JSON.stringify(opts ?? {});
  if (holder.userData.key === key) return;
  holder.userData.key = key; holder.clear(); if (text) holder.add(label(text, opts));
}
const zoneLabels = {};
for (const [k, z] of Object.entries(Z)) {
  const h = new THREE.Group(); h.position.copy(b2t((z.rect[0] + z.rect[2]) / 2, k === 'field' ? z.rect[3] - 0.35 : (z.rect[1] + z.rect[3]) / 2, 0.9)); scene.add(h); zoneLabels[k] = h;
}
const unknownMarks = {};
for (const [id, pos] of Object.entries({ silt: [0.55, 0.5], crack: [-0.65, 3.6], nursery: [1.75, 3.2] })) {
  const h = new THREE.Group(); h.position.copy(b2t(pos[0], pos[1], 0.75)); h.add(label('？未調查', { color: '#6b5414', bg: 'rgba(244,236,210,.95)', size: 0.2 })); scene.add(h); unknownMarks[id] = h;
}

// ---------------------------------------------------------------- models
const loader = new GLTFLoader();
const cache = new Map();
const load = url => { if (!cache.has(url)) cache.set(url, loader.loadAsync(ROOT + url).then(g => g.scene)); return cache.get(url); };
const urls = [...Object.values(catalog.pieces), ...Object.values(catalog.scenery)].flatMap(p => [p.glb, p.waterGlb]).filter(Boolean);
await Promise.all(urls.map(load));
const clone = async url => {
  const o = (await load(url)).clone(true);
  o.traverse(m => { if (m.isMesh) { m.castShadow = true; m.receiveShadow = true; } });
  return o;
};
function rippleTex() {
  return canvasTex(64, 128, (g, w, h) => {
    g.fillStyle = '#5c9fab'; g.fillRect(0, 0, w, h); g.strokeStyle = 'rgba(230,248,248,.5)'; g.lineWidth = 2;
    for (let i = 0; i < 6; i++) { g.beginPath(); for (let x = 0; x <= w; x += 4) g.lineTo(x, (i * 22 + 5 + Math.sin(x / 9 + i * 1.7) * 4) % h); g.stroke(); }
  });
}
const stillMat = new THREE.MeshStandardMaterial({ color: '#4d8590', roughness: 0.12, transparent: true, opacity: 0.78, depthWrite: false });
const spillMat = new THREE.MeshStandardMaterial({ color: '#5d9fae', roughness: 0.1, transparent: true, opacity: 0.6, depthWrite: false });

// B01 source with its water (always running)
const source = await clone(catalog.scenery.B01.glb); scene.add(source);
const sourceWater = await clone(catalog.scenery.B01.waterGlb);
const srcTex = rippleTex(); sourceWater.traverse(m => { if (m.isMesh) { m.material = new THREE.MeshStandardMaterial({ map: srcTex, roughness: 0.1, transparent: true, opacity: 0.82, depthWrite: false }); m.castShadow = false; } });
scene.add(sourceWater);
// the village field is the F01 irrigation field (plank weir held full, so the outlet stays dry); its in port sits on
// the board's field terminal and the field water rises with the supply that reaches it
const fieldTerm = board.terminals.find(t => t.kind === 'field');
const field = await clone(catalog.scenery.F01.glb); field.position.copy(b2t(...fieldTerm.pos)); field.rotation.y = core.yawOf(fieldTerm.dir); scene.add(field);
const fieldWater = await clone(catalog.scenery.F01.waterGlb); fieldWater.position.copy(field.position); fieldWater.rotation.y = field.rotation.y; scene.add(fieldWater);
const fieldTex = rippleTex();
const fieldWaters = {};
fieldWater.traverse(m => {
  if (!m.isMesh) return;
  m.castShadow = false; m.userData.baseY = m.position.y;
  m.material = /_(inlet)$/.test(m.name) ? new THREE.MeshStandardMaterial({ map: fieldTex, roughness: 0.1, transparent: true, opacity: 0.8, depthWrite: false }) : stillMat;
  fieldWaters[m.name.replace('WATER_F01_', '')] = m;
});
// scenery: B11 material cart at the start, B12 completion stele by the field, B09 flow float on the source outlet
const cart = await clone(catalog.scenery.B11.glb); cart.position.copy(b2t(1.7, -0.9)); cart.rotation.y = -2.2; scene.add(cart);
const stele = await clone(catalog.scenery.B12.glb); stele.position.copy(b2t(3.7, 6.4)); stele.rotation.y = Math.PI * 0.15; scene.add(stele);
const pegs = { restore_channel: stele.getObjectByName('B12_peg_1'), protect_nursery: stele.getObjectByName('B12_peg_2'), clear_silt: stele.getObjectByName('B12_peg_3') };
const silt = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.09, 1.0), mat('#6e5a3c', { roughness: 1 })); silt.position.copy(b2t(0, 0.5, 0.145)); scene.add(silt);
const crackMark = new THREE.Group(); crackMark.position.copy(b2t(board.crackMark.pos[0] - 0.01, board.crackMark.pos[1], 0.18)); scene.add(crackMark);
{ const pts = [[0, -0.12], [0.02, -0.05], [-0.015, 0.0], [0.02, 0.06], [0, 0.12]].map(([y, z]) => new THREE.Vector3(0, z, -y));
  const tube = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 20, 0.012, 6), mat('#b3261e', { emissive: '#7a120c' })); crackMark.add(tube); }

// slot markers and hit areas
const slotViews = {};
const markerMat = (c, o = 0.9) => new THREE.LineBasicMaterial({ color: c, transparent: true, opacity: o, depthTest: false });
for (const s of board.slots) {
  const g = new THREE.Group(); g.position.copy(b2t(s.pos[0], s.pos[1], 0.03)); g.rotation.y = core.yawOf(s.dir); scene.add(g);
  const outline = new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints([[-0.3, 0], [0.3, 0], [0.3, 0.92], [-0.3, 0.92]].map(([x, y]) => new THREE.Vector3(x, 0, -y))), markerMat('#ffffff'));
  const arrow = new THREE.Mesh(new THREE.ConeGeometry(0.09, 0.22, 3), new THREE.MeshBasicMaterial({ color: '#ffffff', transparent: true, opacity: 0.85, depthTest: false }));
  arrow.rotation.x = -Math.PI / 2; arrow.position.set(0, 0.02, -0.2); outline.renderOrder = arrow.renderOrder = 5;
  const hit = new THREE.Mesh(new THREE.PlaneGeometry(0.8, 1.0), new THREE.MeshBasicMaterial({ visible: false })); hit.rotation.x = -Math.PI / 2; hit.position.set(0, 0.25, -0.5); hit.userData.slot = s.id;
  const tag = new THREE.Group(); tag.position.set(0, 0.75, -0.5);
  g.add(outline, arrow, hit, tag);
  slotViews[s.id] = { group: g, outline, arrow, hit, tag, piece: null, pieceId: null };
}
const portMarks = new THREE.Group(); scene.add(portMarks);
const spills = new THREE.Group(); scene.add(spills);

// ---------------------------------------------------------------- piece instances follow the design
async function makePiece(slotId, id) {
  const s = SLOT[slotId], p = catalog.pieces[id];
  const g = new THREE.Group(); g.position.copy(b2t(s.pos[0], s.pos[1])); g.rotation.y = core.yawOf(s.dir);
  g.add(await clone(p.glb));
  const waters = [];
  if (p.waterGlb) {
    const w = await clone(p.waterGlb); g.add(w);
    w.traverse(m => {
      if (!m.isMesh) return;
      const tex = rippleTex();
      m.userData.flowMat = new THREE.MeshStandardMaterial({ map: tex, roughness: 0.1, transparent: true, opacity: 0.8, depthWrite: false });
      m.castShadow = false; m.visible = false; m.userData.level = 0; waters.push(m);
    });
  }
  const gate = g.getObjectByName('B05_gate');
  let wheel = null;
  if (gate) { gate.userData.baseY = gate.position.y; const b6 = await clone(catalog.scenery.B06.glb); b6.position.set(0.392, 0.9, -0.5); g.add(b6); wheel = b6.getObjectByName('B06_wheel'); }
  return { group: g, waters, gate, wheel, id, slotId };
}
let patchView = null, patchId = null;
async function syncModels() {
  for (const s of board.slots) {
    const id = s.fixed ?? S.design.placed[s.id] ?? null, v = slotViews[s.id];
    if (v.pieceId === id) continue;
    if (v.piece) scene.remove(v.piece.group);
    v.piece = null; v.pieceId = id;
    if (id) { v.piece = await makePiece(s.id, id); scene.add(v.piece.group); }
  }
  const want = S.design.patches[board.crackMark.slot] ?? null;
  if (want !== patchId) {
    if (patchView) scene.remove(patchView);
    patchView = null; patchId = want;
    if (want) { patchView = await clone(catalog.pieces[want].glb); patchView.position.copy(b2t(board.crackMark.pos[0], board.crackMark.pos[1], board.crackMark.z)); patchView.rotation.y = core.yawOf(board.crackMark.dir); scene.add(patchView); }
  }
}

// which water meshes of a piece are wet: by segment name (gate upstream/downstream, tee branches)
function waterState(slotId, mesh, ev) {
  const wet = ev.wet[slotId], flowing = (ev.flow[slotId] ?? 0) > 1e-6;
  if (!wet) return null;
  const n = mesh.name;
  const branch = port => { const e = ev.edges[slotId]?.find(x => x.port.name === port); if (!e) return null; if (e.to && ev.inst[e.to]) return ev.wet[e.to] ? ((ev.flow[e.to] ?? 0) > 1e-6 ? 'flow' : 'still') : null; return flowing ? 'flow' : null; };
  if (/downstream$/.test(n)) return flowing ? 'flow' : null;
  if (/upstream$/.test(n)) return flowing ? 'flow' : 'still';
  if (/to_left$/.test(n)) return branch('out_left');
  if (/to_right$/.test(n)) return branch('out_right');
  return flowing ? 'flow' : 'still';
}

// ---------------------------------------------------------------- floats (B09-style flow tokens) along flowing paths
const floatGeo = new THREE.CylinderGeometry(0.05, 0.05, 0.035, 12), floatMat = mat('#a8763e', { roughness: 0.7 }), flagMat = mat('#c0392b');
function makeFloat() {
  const g = new THREE.Group(), b = new THREE.Mesh(floatGeo, floatMat), f = new THREE.Mesh(new THREE.BoxGeometry(0.004, 0.06, 0.05), flagMat);
  f.position.set(0, 0.05, 0.02); g.add(b, f); g.visible = false; scene.add(g); return g;
}
const floats = Array.from({ length: 14 }, () => ({ obj: makeFloat(), route: null, d: 0 }));
let routes = [];
function centerline(inst, port) {
  const a = inst.slot.pos, da = inst.slot.dir, b = port.pos, db = port.dir;
  const cross = da[0] * db[1] - da[1] * db[0];
  if (Math.abs(cross) < 1e-6) return [a, b];
  const t = ((b[0] - a[0]) * db[1] - (b[1] - a[1]) * db[0]) / cross, c = [a[0] + da[0] * t, a[1] + da[1] * t];
  const pts = [];
  for (let i = 0; i <= 8; i++) { const u = i / 8; pts.push([(1 - u) ** 2 * a[0] + 2 * u * (1 - u) * c[0] + u * u * b[0], (1 - u) ** 2 * a[1] + 2 * u * (1 - u) * c[1] + u * u * b[1]]); }
  return pts;
}
function buildRoutes(ev) {
  const out = [];
  const walk = (slotId, pts, share) => {
    const inst = ev.inst[slotId];
    if (inst.piece.kind === 'gate' && !inst.gateOpen) return;
    const live = ev.edges[slotId].filter(e => e.to === null || e.to === 'drain' || e.to === 'field' || (ev.flow[e.to] ?? 0) > 1e-6);
    for (const e of live) {
      const seg = centerline(inst, e.port), next = [...pts, ...seg.slice(pts.length ? 1 : 0)];
      if (e.to && ev.inst[e.to]) walk(e.to, next, share / live.length);
      else out.push({ pts: next, share: share / live.length, flow: ev.flow[slotId] });
    }
  };
  walk(board.slots.find(s => s.pos[0] === board.source.pos[0] && s.pos[1] === board.source.pos[1]).id, [[0, -1.4], [0, 0]], 1);
  for (const r of out) { r.len = [0]; for (let i = 1; i < r.pts.length; i++) r.len.push(r.len[i - 1] + Math.hypot(r.pts[i][0] - r.pts[i - 1][0], r.pts[i][1] - r.pts[i - 1][1])); }
  return out;
}
let floatSpawn = 0, floatSeq = 0;
function updateFloats(dt) {
  floatSpawn -= dt;
  if (routes.length && floatSpawn <= 0) {
    const f = floats.find(x => !x.route);
    if (f) { f.route = routes[floatSeq++ % routes.length]; f.d = 0; }
    floatSpawn = 0.9;
  }
  for (const f of floats) {
    if (!f.route) { f.obj.visible = false; continue; }
    const r = f.route, speed = 0.25 + 0.55 * Math.min(1, r.flow ?? 0.5);
    f.d += speed * dt;
    const L = r.len.at(-1);
    if (f.d >= L || !routes.includes(r)) { f.route = null; f.obj.visible = false; continue; }
    let i = 1; while (r.len[i] < f.d) i++;
    const u = (f.d - r.len[i - 1]) / Math.max(1e-6, r.len[i] - r.len[i - 1]), p = r.pts[i - 1], q = r.pts[i];
    f.obj.position.copy(b2t(p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u, 0.3 + Math.sin(f.d * 9) * 0.004));
    f.obj.rotation.y = Math.atan2(q[1] - p[1], q[0] - p[0]); f.obj.visible = true;
  }
}

// ---------------------------------------------------------------- refresh: rules -> scene + panel
let fieldShown = 0, toastT = 0;
async function refresh() {
  await syncModels();
  view = core.preview(ctx, S);
  const ev = view.ev, obs = S.obs;
  // slot markers
  const issueSlots = new Set(ev.issues.filter(i => i.blocking).map(i => i.slot));
  const nextSlots = new Set(ev.issues.filter(i => i.code === 'EMPTY_NEXT').map(i => i.next));
  for (const s of board.slots) {
    const v = slotViews[s.id], filled = !!v.pieceId, sel = s.id === selected;
    const c = sel ? '#ffd24a' : nextSlots.has(s.id) ? '#ff8f6b' : issueSlots.has(s.id) ? '#ff6b5b' : '#ffffff';
    v.outline.material.color.set(c); v.arrow.material.color.set(c);
    v.outline.visible = sel || !filled || issueSlots.has(s.id); v.arrow.visible = !filled;
    v.outline.material.opacity = filled ? 0.95 : 0.75;
    const txt = filled ? `${s.id}·${v.pieceId}${s.fixed ? '舊' : ''}` : s.id;
    setLabel(v.tag, txt, { size: sel ? 0.2 : 0.16, color: sel ? '#7a4b00' : issueSlots.has(s.id) ? '#a2412f' : '#23211d' });
    v.tag.position.y = filled ? 1.0 : 0.45;
  }
  // water per mesh, spill puddles and broken-port marks
  for (const s of board.slots) {
    const v = slotViews[s.id];
    if (!v.piece) continue;
    for (const m of v.piece.waters) {
      const st = waterState(s.id, m, ev);
      m.userData.target = st ? 1 : 0;
      m.material = st === 'still' ? stillMat : m.userData.flowMat;
      m.userData.speed = st === 'flow' ? 0.3 + 0.7 * (ev.flow[s.id] ?? 0) : 0;
    }
  }
  portMarks.clear(); spills.clear();
  for (const i of ev.issues) {
    if (!i.port) continue;
    const p = ev.inst[i.slot].ports.find(x => x.name === i.port);
    const ring = new THREE.Mesh(new THREE.RingGeometry(0.16, 0.22, 24), new THREE.MeshBasicMaterial({ color: i.blocking ? '#ff3b2f' : '#e0b040', transparent: true, opacity: 0.9, depthTest: false, side: THREE.DoubleSide }));
    ring.rotation.x = -Math.PI / 2; ring.position.copy(b2t(p.pos[0], p.pos[1], 0.42)); ring.renderOrder = 6; ring.userData.pulse = true; portMarks.add(ring);
    const tag = label(i.blocking ? `${i.slot}「${i.port}」斷開` : `${i.slot} 閘外未接`, { color: '#fff', bg: i.blocking ? 'rgba(170,40,30,.92)' : 'rgba(140,110,30,.92)', size: 0.15 });
    tag.position.copy(b2t(p.pos[0], p.pos[1], 0.7)); portMarks.add(tag);
    if (i.blocking && (ev.flow[i.slot] ?? 0) > 1e-6) {
      const puddle = new THREE.Mesh(new THREE.CircleGeometry(0.45, 28), spillMat); puddle.rotation.x = -Math.PI / 2;
      puddle.position.copy(b2t(p.pos[0] + p.dir[0] * 0.35, p.pos[1] + p.dir[1] * 0.35, 0.03)); spills.add(puddle);
    }
  }
  routes = buildRoutes(ev);
  // world states
  const T = board.truth, knows = id => obs.includes(id);
  silt.visible = !S.ledger.siltCleared && knows(T.silt.observation);
  crackMark.visible = knows(T.crack.observation) && ev.metrics.crack !== 'patched';
  tracks.visible = knows(T.nursery.observation);
  for (const u of ['silt', 'crack', 'nursery']) unknownMarks[u].visible = !knows(T[u].observation) && !(u === 'silt' && S.ledger.siltCleared);
  const lv = ev.metrics.nursery.level;
  nurseryRing.material.color.set({ risk: '#d2402f', safe: '#3f9a6e', unknown: '#c9a43a', dry: '#9a948a' }[lv]);
  setLabel(zoneLabels.nursery, `育幼區 · ${LEVEL[lv]}${ev.metrics.nursery.gap != null && lv !== 'dry' ? ` ${Math.round(ev.metrics.nursery.gap * 100)} cm` : ''}`, { color: { risk: '#a2412f', safe: '#24493f', unknown: '#6b5414', dry: '#555' }[lv] });
  setLabel(zoneLabels.field, `村田 · 進水 ${ev.metrics.villageSupply}%${ev.unknowns.length && ev.metrics.villageSupply ? '（預估）' : ''}`, { color: '#24493f' });
  setLabel(zoneLabels.drain, ev.metrics.drainFlow > 0 ? `回流溝 · 泥水 ${ev.metrics.drainFlow}%` : '回流溝（流回溪）', { size: 0.17 });
  for (const [k, peg] of Object.entries(pegs)) if (peg) peg.visible = S.ledger.completed.some(c => c.outcomeId === core.CHOICES[k].outcomeId);
  renderPanel();
}

// ---------------------------------------------------------------- panel
function renderPanel() {
  const ev = view.ev, m = ev.metrics, d = S.design, sel = SLOT[selected];
  $('top').innerHTML = `<div class="row tight">
    <button data-act="undo" ${S.past.length ? '' : 'disabled'}>↶ 撤回</button><button data-act="redo" ${S.future.length ? '' : 'disabled'}>↷ 重做</button>
    <button data-act="clear" ${Object.keys(d.placed).length || Object.keys(d.patches).length ? '' : 'disabled'}>清空重排</button></div>`;
  $('clues').innerHTML = `<h2>${board.title}</h2>
    <div class="dim">工程 <code>${board.id}</code> · 線索組 <select id="obsSel">${Object.entries(fixture.sets).map(([k, v]) => `<option value="${k}" ${k === obsKey ? 'selected' : ''}>${v.label}</option>`).join('')}</select></div>
    <div>${Object.entries(fixture.observations).map(([k, o]) => `<span class="chip ${S.obs.includes(k) ? '' : 'miss'}">${o.label}</span>`).join('')}</div>
    ${Object.entries(fixture.observations).filter(([k]) => S.obs.includes(k)).map(([, o]) => `<div class="clue">· ${o.text}</div>`).join('')}`;
  // selected slot + palette
  const placed = sel.fixed ?? d.placed[selected];
  let html = `<h2>${selected} 槽位 <span class="dim">入口 ${core.fmtPos(sel.pos)} 朝${core.dirName(sel.dir)}</span></h2>`;
  if (sel.fixed) {
    html += `<div>${sel.fixed} ${catalog.pieces[sel.fixed].name}（${sel.label}）</div>`;
    if (selected === board.truth.silt.slot) html += `<div class="dim">${S.ledger.siltCleared ? '已清淤。' : S.obs.includes('silt_buildup') ? '淤了一半深，水量只剩六成；選「先清淤」方向可以排掉。' : '淤積程度沒有調查。'}</div>`;
    if (sel.old && selected === board.truth.crack.slot) {
      html += `<h3>補石（B07 家族，依裂口形狀）</h3><div class="pal">${PATCHES.map((id, i) => {
        const p = catalog.pieces[id], on = d.patches[selected] === id, left = (board.pieceStock[id] ?? 0) - (on ? 0 : Object.values(d.patches).filter(x => x === id).length);
        return `<button data-act="patch" data-piece="${id}" class="${on ? 'on' : ''}" ${left <= 0 && !on ? 'disabled' : ''}><span class="k">${KEYS[i]}</span><b>${id}</b><small>${p.name}</small></button>`;
      }).join('')}</div>${d.patches[selected] ? `<div class="row" style="margin-top:6px"><button data-act="unpatch">拆下補石</button></div>` : ''}`;
    }
  } else {
    const fits = new Set(core.fitsFor(ctx, sel));
    html += `<div class="pal">${PALETTE.map((id, i) => {
      const p = catalog.pieces[id], on = placed === id;
      const left = (board.pieceStock[id] ?? 0) - Object.values(d.placed).filter(x => x === id).length;
      const kind = core.KIND_LABEL[p.kind] + (p.side ? (p.side === 'left' ? '·左' : '·右') : '');
      return `<button data-act="place" data-piece="${id}" class="${on ? 'on' : ''}" ${left <= 0 && !on ? 'disabled' : ''}><span class="k">${KEYS[i]}</span><b>${id}</b> ${kind}${fits.has(id) ? ' <span class="fit">✓接得上</span>' : ''}<small>${p.name} · 剩 ${left}</small></button>`;
    }).join('')}</div>`;
    const gate = placed && catalog.pieces[placed].kind === 'gate';
    html += `<div class="row" style="margin-top:6px">${placed ? `<button data-act="remove">拆掉 ${placed}（Del）</button>` : ''}${gate ? `<button data-act="gate" class="${d.gates[selected] ? 'on' : ''}">${d.gates[selected] ? '閘門開著 · 按 G 關' : '閘門關著 · 按 G 開'}</button>` : ''}</div>`;
  }
  $('slot').innerHTML = html;
  $('dir').innerHTML = `<h2>處理方向</h2><div class="dirs">${Object.entries(core.CHOICES).map(([k, c]) => `<button data-act="choose" data-choice="${k}" class="${d.choice === k ? 'on' : ''}">${c.label}<small>${Object.entries(CHOICE_KEYS).find(([, v]) => v === k)[0].toUpperCase()} · ${CHOICE_HINT[k]}</small></button>`).join('')}</div>`;
  const lvClass = `lv-${m.nursery.level}`;
  $('status').innerHTML = `<h2>水路狀態</h2>
    <div class="dim">村田進水</div><div class="meter"><i style="width:${m.villageSupply}%"></i></div>
    <dl class="kv"><dt>村田</dt><dd>${m.villageSupply}%${ev.unknowns.length && m.villageSupply ? '（預估，未計未知風險）' : ''}${m.drainFlow ? ` · 回流溝 ${m.drainFlow}%` : ''}${m.spill ? ` · <b class="lv-risk">漫出 ${m.spill}%</b>` : ''}</dd>
    <dt>育幼區</dt><dd class="${lvClass}">${LEVEL[m.nursery.level]}${m.nursery.gap != null && m.nursery.level !== 'dry' ? `（流水距 ${Math.round(m.nursery.gap * 100)} cm）` : ''}</dd>
    <dt>淤積</dt><dd>${SILT[m.silt]}</dd><dt>P4 破槽</dt><dd>${CRACK[m.crack]}</dd>
    <dt>花費</dt><dd>${costText(view.cost)}</dd></dl>
    ${ev.unknowns.map(u => `<div class="iss unk">⚠ 未知風險：${u.text}</div>`).join('')}
    ${ev.issues.map(i => `<div class="iss ${i.blocking ? '' : 'info'}" data-act="goto" data-slot="${i.slot}">${i.blocking ? '✖' : 'ⓘ'} ${i.message}<span class="fix"><b>修法：</b>${i.fix}</span></div>`).join('')}
    ${view.problems.filter(p => !ev.issues.some(i => i.code === p.code && i.message === p.message)).map(p => `<div class="iss info">・${p.message}</div>`).join('')}
    ${view.ready ? `<div class="ok">可以完工：${core.CHOICES[d.choice].label}</div>` : ''}`;
  const L = S.ledger, rid = core.requestIdFor(S), done = L.receipts[rid];
  $('done').innerHTML = `<button class="go" data-act="complete" ${view.ready || done ? '' : 'disabled'}>${done ? '已完工 · 再按一次（重送同一請求）' : '完工（Enter）'}</button>
    <div class="dim" style="margin-top:4px">請求編號 <code>${rid}</code></div>
    <h3>本機展示材料（不入正式背包）</h3><div>${Object.entries(L.stock).map(([k, v]) => `${matName(k)} ${v}`).join(' · ')}</div>
    <div class="dim">本機貢獻 ${L.contribution} · 完工 ${L.completed.length} 次${L.completed.length ? '：' + L.completed.map(c => `#${c.seq} ${c.outcomeId}`).join('、') : ''}</div>`;
}

function showCard(r, replay) {
  const o = r.outcome, cmp = core.compareDirections(ctx, S);
  const lv = { risk: '有風險', safe: '安全', dry: '沒有流水' };
  $('card').innerHTML = `<h2>${replay ? '重送：回傳同一張收據' : '完工'} · ${core.CHOICES[o.choice].label}</h2>
    <div class="dim">結果 <code>${o.outcomeId}</code> · 請求 <code>${r.requestId}</code> · 本機演示，不入正式背包</div>
    <div class="tiles"><div class="tile">村田<b>${o.villageSupply}%</b>${o.villageText}</div>
      <div class="tile">育幼區<b class="lv-${o.nursery}">${lv[o.nursery]}</b>${o.nurseryText}</div>
      <div class="tile">淤積／破槽<b>${SILT[o.silt]}</b>P4：${CRACK[o.crack]}</div></div>
    ${o.discovered.map(t => `<div class="iss unk">完工後發現：${t}</div>`).join('')}
    <div class="${replay ? 'ok' : 'dim'}">${replay ? '同一請求再送一次：材料沒有再扣、貢獻沒有再加。' : ''}扣除：${costText(r.consumed)} · 本機貢獻 +${r.contribution}</div>
    <h3>三個方向的取捨（參考擺法、同一份線索與目前淤積狀態）</h3>
    <table><tr><th>方向</th><th>村田今天</th><th>育幼區</th><th>淤積</th><th>花費</th></tr>
    ${cmp.map(c => `<tr class="${c.choice === o.choice ? 'me' : ''}"><td>${core.CHOICES[c.choice].label}<br><span class="dim">${c.title}</span></td><td>${c.villageSupply}%</td><td class="lv-${c.nursery}">${lv[c.nursery]}</td><td>${SILT[c.silt]}</td><td>${costText(c.cost)}</td></tr>`).join('')}</table>
    <div class="row"><button data-act="closecard">繼續規劃</button><button data-act="complete">再按一次完工</button></div>`;
  $('card').hidden = false;
}
function toast(text, bad = false) { const t = $('toast'); t.textContent = text; t.className = bad ? 'bad' : ''; t.hidden = false; toastT = bad ? 4.5 : 3; }

// ---------------------------------------------------------------- actions
async function act(type, a = {}) {
  let r;
  switch (type) {
    case 'select': selected = a.slot; break;
    case 'undo': r = core.undo(S); break;
    case 'redo': r = core.redo(S); break;
    case 'place': r = core.act(ctx, S, { type: 'place', slot: a.slot ?? selected, piece: a.piece }); break;
    case 'remove': r = core.act(ctx, S, { type: 'remove', slot: a.slot ?? selected }); break;
    case 'patch': r = core.act(ctx, S, { type: 'patch', slot: a.slot ?? selected, piece: a.piece }); break;
    case 'unpatch': r = core.act(ctx, S, { type: 'unpatch', slot: a.slot ?? selected }); break;
    case 'gate': r = core.act(ctx, S, { type: 'gate', slot: a.slot ?? selected, open: a.open }); break;
    case 'choose': r = core.act(ctx, S, { type: 'choose', choice: S.design.choice === a.choice ? null : a.choice }); break;
    case 'clear': r = core.act(ctx, S, { type: 'clear' }); $('card').hidden = true; break;
    case 'closecard': $('card').hidden = true; break;
    case 'complete': {
      const rid = core.requestIdFor(S);
      const res = core.complete(ctx, S, rid);
      if (!res.ok) { toast(res.problems ? `還不能完工：\n${res.problems.slice(0, 3).map(p => '・' + p.message).join('\n')}` : res.message, true); break; }
      S = res.session; lastResult = res;
      showCard(res, res.replayed);
      if (res.replayed) toast(`同一請求 ${rid} 重送：回傳原收據，材料沒有再扣`);
      break;
    }
  }
  if (r) { if (!r.ok) toast(r.message, true); else S = r.session; }
  await refresh();
  return r;
}

// pointer: tap selects a slot (drags rotate the view), right click removes
const controls = new OrbitControls(camera, canvas);
controls.target.copy(b2t(-0.5, 4.0, 0)); controls.enableDamping = true; controls.minDistance = 4; controls.maxDistance = 18;
controls.maxPolarAngle = Math.PI * 0.42; controls.minPolarAngle = 0.05;
camera.position.copy(b2t(1.8, -4.4, 11.6)); controls.update();
const ray = new THREE.Raycaster(), ndc = new THREE.Vector2();
let down = null;
canvas.addEventListener('pointerdown', e => { down = { x: e.clientX, y: e.clientY, b: e.button }; });
canvas.addEventListener('pointerup', e => {
  if (!down || Math.hypot(e.clientX - down.x, e.clientY - down.y) > 8) { down = null; return; }
  const r = canvas.getBoundingClientRect(); ndc.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
  ray.setFromCamera(ndc, camera);
  const hit = ray.intersectObjects(Object.values(slotViews).map(v => v.hit))[0];
  if (hit) { const slot = hit.object.userData.slot; if (down.b === 2) act('remove', { slot }); else act('select', { slot }); }
  down = null;
});
canvas.addEventListener('contextmenu', e => e.preventDefault());
$('side').addEventListener('click', e => {
  const b = e.target.closest('[data-act]'); if (!b || b.disabled) return;
  const a = b.dataset.act;
  if (a === 'goto') act('select', { slot: b.dataset.slot });
  else act(a, { piece: b.dataset.piece, choice: b.dataset.choice });
});
$('card').addEventListener('click', e => { const b = e.target.closest('[data-act]'); if (b) act(b.dataset.act); });
$('side').addEventListener('change', e => { if (e.target.id === 'obsSel') { params.set('obs', e.target.value); location.search = params.toString(); } });
// keyboard
function step(dir) {   // nearest slot whose centre lies in that screen-ish direction (plan axes: up = north)
  const c = s => [s.pos[0] + s.dir[0] * 0.5, s.pos[1] + s.dir[1] * 0.5], here = c(SLOT[selected]);
  let best = null, bd = Infinity;
  for (const s of board.slots) {
    if (s.id === selected) continue;
    const p = c(s), dx = p[0] - here[0], dy = p[1] - here[1], along = dx * dir[0] + dy * dir[1];
    if (along <= 0.05) continue;
    const score = along + 2 * Math.abs(dx * dir[1] - dy * dir[0]);
    if (score < bd) { bd = score; best = s.id; }
  }
  if (best) act('select', { slot: best });
}
addEventListener('keydown', e => {
  if (e.target.tagName === 'SELECT') return;
  const k = e.key.toLowerCase();
  if ((e.ctrlKey || e.metaKey) && k === 'z') { e.preventDefault(); act(e.shiftKey ? 'redo' : 'undo'); return; }
  if ((e.ctrlKey || e.metaKey) && k === 'y') { e.preventDefault(); act('redo'); return; }
  if (e.ctrlKey || e.metaKey || e.altKey) return;
  const arrows = { arrowup: [0, 1], arrowdown: [0, -1], arrowleft: [-1, 0], arrowright: [1, 0] };
  if (arrows[k]) { e.preventDefault(); step(arrows[k]); return; }
  if (k === 'tab') { e.preventDefault(); const i = board.slots.findIndex(s => s.id === selected); act('select', { slot: board.slots[(i + (e.shiftKey ? -1 : 1) + board.slots.length) % board.slots.length].id }); return; }
  const i = KEYS.indexOf(e.key);
  if (i >= 0) { const sel = SLOT[selected]; if (sel.old && selected === board.truth.crack.slot) { if (PATCHES[i]) act('patch', { piece: PATCHES[i] }); } else if (!sel.fixed && PALETTE[i]) act('place', { piece: PALETTE[i] }); return; }
  if (k === 'delete' || k === 'backspace') { act(SLOT[selected].old ? 'unpatch' : 'remove'); return; }
  if (k === 'g') { act('gate'); return; }
  if (CHOICE_KEYS[k]) { act('choose', { choice: CHOICE_KEYS[k] }); return; }
  if (k === 'enter') { act('complete'); return; }
  if (k === 'escape') { act('closecard'); return; }
});

// ---------------------------------------------------------------- loop
function resize() {
  const side = $('side').getBoundingClientRect();
  const portrait = side.top > 10;
  const w = portrait ? innerWidth : innerWidth - side.width, h = portrait ? side.top : innerHeight;
  renderer.setSize(w, h); camera.aspect = w / h; camera.updateProjectionMatrix();
}
addEventListener('resize', resize); resize();
let time = 0;
function tick(dt) {
  time += dt;
  controls.update();
  streamTex.offset.x -= dt * 0.12; srcTex.offset.y -= dt * 0.35;
  for (const v of Object.values(slotViews)) {
    if (!v.piece) continue;
    for (const m of v.piece.waters) {
      const lvl = m.userData.level = THREE.MathUtils.damp(m.userData.level, m.userData.target ?? 0, 5, dt);
      m.visible = lvl > 0.02;
      m.position.y = (lvl - 1) * 0.1;
      if (m.material.map && m.userData.speed) m.material.map.offset.y -= dt * m.userData.speed;
    }
    if (v.piece.gate) {
      const open = !!S.design.gates[v.piece.slotId];
      const want = v.piece.gate.userData.baseY + (open ? 0.32 : 0), cur = v.piece.gate.position.y;
      const ny = THREE.MathUtils.damp(cur, want, 6, dt); v.piece.gate.position.y = ny;
      if (v.piece.wheel) v.piece.wheel.rotation.z += (ny - cur) / 0.22 * Math.PI * 2;
    }
  }
  const supply = view ? view.ev.metrics.villageSupply / 100 : 0;
  fieldShown = THREE.MathUtils.damp(fieldShown, supply, 1.5, dt);
  // F01: inlet runs while water arrives; the field fills from the ditch floor toward the plank crest (0.10 -> 0.30 m)
  fieldTex.offset.y -= dt * 0.3 * (supply > 0 ? 1 : 0);
  if (fieldWaters.inlet) fieldWaters.inlet.visible = supply > 0;
  if (fieldWaters.field) { fieldWaters.field.visible = fieldShown > 0.03; fieldWaters.field.position.y = fieldWaters.field.userData.baseY - (1 - fieldShown) * 0.2; }
  if (fieldWaters.field_low) fieldWaters.field_low.visible = false;
  if (fieldWaters.outlet) fieldWaters.outlet.visible = false;
  drainWater.material.opacity = THREE.MathUtils.damp(drainWater.material.opacity, view && view.ev.metrics.drainFlow > 0 ? 0.85 : 0, 3, dt);
  for (const m of portMarks.children) if (m.userData.pulse) m.material.opacity = 0.55 + 0.4 * Math.sin(time * 6);
  updateFloats(dt);
  if (toastT > 0 && (toastT -= dt) <= 0) $('toast').hidden = true;
  renderer.render(scene, camera);
}
await refresh();
$('loading').hidden = true;
let t0 = performance.now();
if (!WALK) renderer.setAnimationLoop(() => { const now = performance.now(); tick(Math.min(0.05, (now - t0) / 1000)); t0 = now; });

// ---------------------------------------------------------------- hooks for the scripted walkthrough (?walk) and checks
window.demo = { get S() { return S; }, get view() { return view; }, act, tick, camera, controls, b2t, board, core, ctx };
if (WALK) { const { runWalkthrough } = await import('./walkthrough.js'); runWalkthrough({ act, tick, canvas, camera, controls, b2t, get S() { return S; } }); }
