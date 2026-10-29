import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { Investigation, PARAMS, CLUE_TEXT, HINT_TEXT, OBSERVATION_IDS } from './investigation.mjs';
import { Sfx } from './audio.mjs';

const $ = id => document.getElementById(id);
const COARSE = matchMedia('(pointer: coarse)').matches;
const sfx = new Sfx();
const DT = 1 / 60;

// ------------------------------------------------------------------ renderer, sky, light (pattern from tools/qingxi-encounter-a)
const canvas = $('world');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(devicePixelRatio, COARSE ? 1.5 : 1.75));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
const scene = new THREE.Scene();
const HORIZON = new THREE.Color('#c9d2c4');
const FOG = new THREE.FogExp2(HORIZON, 0.02);
scene.fog = FOG;
const SUN_DIR = new THREE.Vector3(0.5, 0.62, 0.45).normalize();
const sky = new THREE.Mesh(new THREE.SphereGeometry(300, 32, 16), new THREE.ShaderMaterial({
  side: THREE.BackSide, depthWrite: false, fog: false,
  uniforms: { sun: { value: SUN_DIR }, top: { value: new THREE.Color('#7499ad') }, hor: { value: HORIZON }, warm: { value: new THREE.Color('#f3d9a8') } },
  vertexShader: 'varying vec3 vDir; void main(){ vDir = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
  fragmentShader: `varying vec3 vDir; uniform vec3 sun, top, hor, warm;
    void main(){ float h = clamp(vDir.y, -0.2, 1.0); vec3 c = mix(hor, top, pow(max(h,0.0), 0.6));
      float s = max(dot(normalize(vDir), sun), 0.0); c += warm * (pow(s, 6.0) * 0.3 + pow(s, 400.0) * 2.0);
      gl_FragColor = vec4(c, 1.0); }`,
}));
scene.add(sky);
scene.add(new THREE.HemisphereLight(0xdde6e8, 0x4d4630, 1.05));
const sun = new THREE.DirectionalLight(0xffe4bc, 2.9);
sun.castShadow = true;
sun.shadow.mapSize.set(COARSE ? 1024 : 2048, COARSE ? 1024 : 2048);
Object.assign(sun.shadow.camera, { left: -16, right: 16, top: 16, bottom: -16, near: 1, far: 90 });
sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.03;
scene.add(sun, sun.target);
{
  const pm = new THREE.PMREMGenerator(renderer), env = new THREE.Scene();
  env.add(sky.clone());
  const g = new THREE.Mesh(new THREE.CircleGeometry(200, 24), new THREE.MeshBasicMaterial({ color: 0x504a31 }));
  g.rotation.x = -Math.PI / 2; g.position.y = -2; env.add(g);
  scene.environment = pm.fromScene(env, 0.04).texture;
  scene.environmentIntensity = 0.55;
}
function rand(seed) { let s = seed >>> 0; return () => ((s = (1664525 * s + 1013904223) >>> 0) / 2 ** 32); }
function canvasTex(size, paint, repeat) {
  const c = document.createElement('canvas'); c.width = c.height = size; paint(c.getContext('2d'), size);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(repeat, repeat); t.anisotropy = 4;
  return t;
}

// ------------------------------------------------------------------ the river: A01 modules chained at their ports (art/exports/.../A01_*_model_info.json)
// Blender (Z-up, upstream +Y) -> three (Y-up, upstream -Z). A Blender yaw maps to the same three rotation.y.
const TOP = 1.15, BED = 0.25, WATER = 0.30, HALF_W = 1.2;
const MODULES = {
  A01_straight_01: { L: 6.0, turn: 0 }, A01_bend_left_01: { L: 6.5, turn: 25 }, A01_narrow_01: { L: 6.0, turn: 0 }, A01_bend_right_01: { L: 6.5, turn: -40 },
  A01_end_source_01: { L: 4.0, turn: 0 },   // terminal: closes the run upstream (no out port)
};
// Two assemblies of the same four shapes (?route=b for the second); the same shape never sits next to itself.
const ROUTE = new URLSearchParams(location.search).get('route') === 'b' ? 'b' : 'a';
const CHAIN = ROUTE === 'b'
  ? ['A01_straight_01', 'A01_bend_right_01', 'A01_narrow_01', 'A01_bend_left_01', 'A01_end_source_01']    // downstream -> upstream, ~29.5 m
  : ['A01_straight_01', 'A01_bend_left_01', 'A01_narrow_01', 'A01_bend_right_01', 'A01_end_source_01'];
const at = id => CHAIN.indexOf(id);   // props are placed by module shape, so both routes keep the same story
/** Module-local course: (u along, s across; + = right bank looking upstream) -> Blender local (x, y). */
function courseAt(m, u, s) {
  const k = THREE.MathUtils.degToRad(m.turn) / m.L, a = k * u;
  const px = Math.abs(k) < 1e-9 ? 0 : (Math.cos(a) - 1) / k, py = Math.abs(k) < 1e-9 ? u : Math.sin(a) / k;
  return [px + Math.cos(a) * s, py + Math.sin(a) * s, a];
}
const placed = [];   // { id, x, z, yaw }
{
  let x = 0, z = 15, yaw = 0;
  for (const id of CHAIN) {
    placed.push({ id, x, z, yaw });
    const m = MODULES[id], [ox, oy] = courseAt(m, m.L, 0);
    [x, z] = toWorld({ x, z, yaw }, ox, oy);
    yaw += THREE.MathUtils.degToRad(m.turn);
  }
}
function toWorld(mod, bx, by) {
  const lx = bx, lz = -by, c = Math.cos(mod.yaw), s = Math.sin(mod.yaw);
  return [mod.x + lx * c + lz * s, mod.z - lx * s + lz * c];
}
/** World position + yaw of module-local (u, s). */
function onRiver(i, u, s) {
  const mod = placed[i], [bx, by, a] = courseAt(MODULES[mod.id], u, s), [x, z] = toWorld(mod, bx, by);
  return { x, z, yaw: mod.yaw + a };
}
const centre = [];
placed.forEach((mod, i) => { const L = MODULES[mod.id].L; for (let u = 0; u <= L; u += 0.25) centre.push(onRiver(i, u, 0)); });
/** Distance to the river centre line, or Infinity beyond its two ends. */
function riverDist(x, z) {
  let best = Infinity;
  for (let i = 0; i < centre.length - 1; i++) {
    const a = centre[i], b = centre[i + 1], dx = b.x - a.x, dz = b.z - a.z, l2 = dx * dx + dz * dz;
    if (l2 < 1e-9) continue;   // module joins repeat a point
    const t =((x - a.x) * dx + (z - a.z) * dz) / l2;
    if ((i === 0 && t < 0) || (i === centre.length - 2 && t > 1)) continue;
    const tt = Math.min(1, Math.max(0, t)), d = Math.hypot(x - (a.x + dx * tt), z - (a.z + dz * tt));
    best = Math.min(best, d);
  }
  return best;
}

// ------------------------------------------------------------------ surrounding ground with a trench where the river tiles sit
const groundTex = canvasTex(256, (g, n) => { const r = rand(3); g.fillStyle = '#5a5634'; g.fillRect(0, 0, n, n);
  for (let i = 0; i < 2600; i++) { g.fillStyle = r() < 0.55 ? `rgba(${92 + r() * 40},${80 + r() * 30},${44 + r() * 16},.5)` : `rgba(${58 + r() * 22},${74 + r() * 26},${36 + r() * 12},.45)`;
    g.fillRect(r() * n, r() * n, 1 + r() * 3, 1 + r() * 3); } }, 40);
// The open ground is a flat plane with the river corridor cut out by an alpha mask (no sloped trench faces that could
// poke through the channel at bends); the river tiles fill the hole.
const groundMask = (() => {
  const n = 2048, c = document.createElement('canvas'); c.width = c.height = n; const g = c.getContext('2d');
  g.fillStyle = '#fff'; g.fillRect(0, 0, n, n);
  const px = v => (v + 80) / 160 * n;
  g.strokeStyle = '#000'; g.lineWidth = 2 * 3.42 / 160 * n; g.lineCap = 'butt'; g.lineJoin = 'round';
  g.beginPath(); centre.forEach((q, i) => (i ? g.lineTo(px(q.x), px(q.z)) : g.moveTo(px(q.x), px(q.z)))); g.stroke();
  const t = new THREE.CanvasTexture(c); t.anisotropy = 4; return t;
})();
const ground = new THREE.Mesh(new THREE.PlaneGeometry(160, 160).rotateX(-Math.PI / 2),
  new THREE.MeshStandardMaterial({ map: groundTex, alphaMap: groundMask, alphaTest: 0.5, roughness: 1 }));
ground.position.y = -0.012;
ground.receiveShadow = true;
scene.add(ground);
const wind = { value: 0 };
{ // dry grass cards on the open ground (demo backdrop, not delivered assets)
  const tex = canvasTex(256, (g, n) => { const r = rand(9); g.clearRect(0, 0, n, n);
    for (let i = 0; i < 42; i++) { const x = 14 + r() * (n - 28), h = n * (0.35 + r() * 0.6), lean = (r() - 0.5) * 80, w = 2 + r() * 3.5;
      const grd = g.createLinearGradient(0, n, 0, n - h), hue = 38 + r() * 26;
      grd.addColorStop(0, `hsl(${hue + 20},35%,16%)`); grd.addColorStop(0.6, `hsl(${hue},38%,30%)`); grd.addColorStop(1, `hsl(${hue - 6},42%,48%)`);
      g.fillStyle = grd; g.beginPath(); g.moveTo(x - w, n); g.quadraticCurveTo(x + lean * 0.4, n - h * 0.55, x + lean, n - h); g.quadraticCurveTo(x + lean * 0.4, n - h * 0.55, x + w, n); g.fill(); } }, 1);
  const quad = new THREE.PlaneGeometry(0.5, 0.34, 1, 2); quad.translate(0, 0.17, 0);
  const parts = [0, 1, 2].map(k => quad.clone().rotateY(k * Math.PI / 3));
  const pos = [], uv = [], idx = [];
  for (const g of parts) { const b = pos.length / 3; pos.push(...g.attributes.position.array); uv.push(...g.attributes.uv.array); idx.push(...Array.from(g.index.array, v => v + b)); }
  const clump = new THREE.BufferGeometry();
  clump.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); clump.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  clump.setAttribute('normal', new THREE.Float32BufferAttribute(Array.from({ length: pos.length / 3 }, () => [0, 1, 0]).flat(), 3)); clump.setIndex(idx);
  const mat = new THREE.MeshStandardMaterial({ map: tex, alphaTest: 0.45, side: THREE.DoubleSide, roughness: 0.95 });
  mat.onBeforeCompile = sh => { sh.uniforms.uTime = wind;
    sh.fragmentShader = sh.fragmentShader.replace('#include <normal_fragment_begin>', 'vec3 normal = normalize( vNormal ); vec3 nonPerturbedNormal = normal;');
    sh.vertexShader = 'uniform float uTime;\n' + sh.vertexShader.replace('#include <begin_vertex>', `#include <begin_vertex>
      vec4 wp = instanceMatrix * vec4(0.0,0.0,0.0,1.0); float hh = max(position.y, 0.0);
      transformed.x += sin(uTime*1.6 + wp.x*0.35 + wp.z*0.22) * hh * hh * 0.5;`); };
  const N = COARSE ? 5000 : 12000, mesh = new THREE.InstancedMesh(clump, mat, N), r = rand(77), m4 = new THREE.Matrix4(), c = new THREE.Color();
  let n = 0;
  for (let i = 0; i < N * 4 && n < N; i++) {
    const x = (r() - 0.5) * 70 - 3, z = (r() - 0.5) * 70 - 2;
    if (riverDist(x, z) < 3.6) continue;
    const k = 0.6 + r() * 0.8;
    m4.compose(new THREE.Vector3(x, 0, z), new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), r() * 3), new THREE.Vector3(k, k * (0.6 + r() * 0.9), k));
    mesh.setMatrixAt(n, m4); c.setHSL(0.11 + r() * 0.06, 0.25 + r() * 0.2, 0.6 + r() * 0.25); mesh.setColorAt(n, c); n++;
  }
  mesh.count = n; mesh.receiveShadow = true; scene.add(mesh);
}
{ // hillside trees beyond the corridor (demo backdrop, not delivered assets)
  const r = rand(31), trunkG = new THREE.CylinderGeometry(0.16, 0.26, 3, 6).translate(0, 1.5, 0);
  const crownG = new THREE.ConeGeometry(1.6, 3.6, 7).translate(0, 4.2, 0), crown2 = new THREE.ConeGeometry(1.1, 2.6, 7).translate(0, 5.8, 0);
  const meshes = [[trunkG, 0x3b2a1d], [crownG, 0x34482e], [crown2, 0x3d5233]].map(([g, c]) => new THREE.InstancedMesh(g, new THREE.MeshStandardMaterial({ color: c, roughness: 0.95 }), 140));
  const m = new THREE.Matrix4(); let n = 0;
  for (let i = 0; i < 1200 && n < 140; i++) {
    const x = (r() - 0.5) * 80 - 3, z = (r() - 0.5) * 80 - 2;
    const d = riverDist(x, z);
    if (d < 8 || (d === Infinity && Math.hypot(x - 0, z - 15) < 9)) continue;
    const k = 0.8 + r() * 0.7;
    m.compose(new THREE.Vector3(x, 0, z), new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), r() * 6), new THREE.Vector3(k, k * (0.9 + r() * 0.4), k));
    for (const im of meshes) im.setMatrixAt(n, m);
    n++;
  }
  for (const im of meshes) { im.count = n; im.castShadow = true; scene.add(im); }
}

// ------------------------------------------------------------------ props on the river
const SLUICE = onRiver(0, 3.4, 3.05), SLUICE2 = onRiver(at('A01_narrow_01'), 3.6, 3.05), FORMATION = onRiver(at('A01_bend_left_01'), 2.0, -4.3);   // on the open ground beyond the inner bank, clear of the sluice crack
const SILT = onRiver(at('A01_bend_left_01'), 3.7, 0.15), MARKER = onRiver(at('A01_narrow_01'), 1.2, -0.95);
const START_P = onRiver(0, 1.2, 2.55);
const BL = at('A01_bend_left_01'), NR = at('A01_narrow_01'), BR = at('A01_bend_right_01'), ES = at('A01_end_source_01');
const NURSERY = onRiver(BR, 3.3, 2.15), GAUGE = onRiver(0, 2.2, -1.2), RESONANCE = onRiver(ES, 1.6, -2.75);
const BAMBOO = onRiver(BL, 4.2, 4.1), PAVILION = onRiver(BR, 3.6, 5.2), SILT2 = onRiver(0, 0.5, -0.55), SILT3 = onRiver(BR, 0.9, 0);   // bamboo: a stretch of right bank with no sluice, so its gap is the path
const FORDS = [['A08_steps_line_01', onRiver(0, 4.9, 0)], ['A08_gravel_bar_01', onRiver(BL, 1.1, 0)], ['A08_slabs_stagger_01', onRiver(BR, 5.6, 0)]];
/** yaw that turns a model's local -Z (Blender +Y) towards (x, z) */
const faceTo = (from, x, z) => Math.atan2(-(x - from.x), -(z - from.z));
const LAYOUT = [
  ...placed.map((m, mi) => ({ id: m.id, x: m.x, y: -TOP, z: m.z, rot: m.yaw, terrain: true, mi })),
  { id: 'A02_side_crack_01', x: SLUICE.x, y: 0, z: SLUICE.z, rot: SLUICE.yaw - Math.PI / 2 },
  { id: 'A02_end_break_01', x: SLUICE2.x, y: 0, z: SLUICE2.z, rot: SLUICE2.yaw - Math.PI / 2 },
  { id: 'A03_FormationBase', x: FORMATION.x, y: 0, z: FORMATION.z, rot: 0.8 },
  { id: 'A04_SiltBar', x: SILT.x, y: -TOP + BED, z: SILT.z, rot: SILT.yaw, walk: true, silt: 'blocking' },
  { id: 'A04_SiltBar_cleared', x: SILT.x, y: -TOP + BED, z: SILT.z, rot: SILT.yaw, hidden: true, silt: 'cleared' },
  { id: 'A06_MarkerStone', x: MARKER.x, y: -TOP + WATER - 0.35, z: MARKER.z, rot: 0.4 },
  ...[[0, 1.6, 1.75, 1], [0, 4.0, -1.8, 2], [1, 5.4, 1.85, 3], [2, 4.7, -1.65, 1], [3, 2.0, 1.95, 2], [3, 4.6, -1.7, 3], [4, 2.5, -1.8, 1],
      [1, 2.6, -1.9, 2], [2, 1.8, 1.9, 3], [0, 5.6, 1.9, 2]].map(([i, u, s, v], k) => {
    const p = onRiver(i, u, s); return { id: `A05_WitheredSedge_0${v}`, x: p.x, y: null, z: p.z, rot: k * 1.7, plant: true }; }),
  // batch two
  ...FORDS.map(([id, q]) => ({ id, x: q.x, y: -TOP, z: q.z, rot: q.yaw, walk: true, ford: true })),
  { id: 'A07_NurseryTracks', x: NURSERY.x, y: null, z: NURSERY.z, rot: faceTo(NURSERY, onRiver(BR, 3.3, 0).x, onRiver(BR, 3.3, 0).z), walk: true },
  { id: 'A09_WaterGauge', x: GAUGE.x, y: -TOP, z: GAUGE.z, rot: GAUGE.yaw + Math.PI / 2 },
  // the clump grows on the open ground and has toppled towards the river; its gap (under the 2 m arch) sits on the bank-top path
  { id: 'A10_FallenBamboo', x: BAMBOO.x, y: 0, z: BAMBOO.z, rot: BAMBOO.yaw + Math.PI, plant: true },
  { id: 'A11_PavilionRuin', x: PAVILION.x, y: 0, z: PAVILION.z, rot: faceTo(PAVILION, onRiver(BR, 3.6, 0).x, onRiver(BR, 3.6, 0).z) + Math.PI, walk: true },
  { id: 'A12_ResonanceStone', x: RESONANCE.x, y: null, z: RESONANCE.z, rot: 0.6, resonance: true },
  { id: 'A04_SiltSide_02', x: SILT2.x, y: -TOP + BED, z: SILT2.z, rot: SILT2.yaw, walk: true },
  { id: 'A04_SiltJam_03', x: SILT3.x, y: -TOP + BED, z: SILT3.z, rot: SILT3.yaw, walk: true },
  // background dressing, reused read-only from the forest encounter kit (PR #39): hides the open downstream cut until the core team joins the village river
  { id: 'A03_FallenLog', x: placed[0].x, y: -0.15, z: placed[0].z + 1.4, rot: Math.PI / 2 + 0.15, forest: true },
  { id: 'A06_RootStump', x: onRiver(at('A01_bend_right_01'), 3.2, 3.9).x, y: 0, z: onRiver(at('A01_bend_right_01'), 3.2, 3.9).z, rot: 2.0, forest: true },
];
const loader = new GLTFLoader();
const ray = new THREE.Raycaster(), DOWN = new THREE.Vector3(0, -1, 0);
const heightCache = new Map();
const terrain = [];
const occluders = [];
const siltModels = {}, resonanceMats = [], riverWater = [], placedItems = [], hullWalls = [], sockets = [];
let loaded = 0;
const progress = () => { loaded++; $('load-text').textContent = `載入模型 ${loaded}/${LAYOUT.length}`; $('load-bar').style.setProperty('--p', `${loaded / LAYOUT.length * 100}%`); };
const cache = {};
const glb = url => (cache[url] ||= loader.loadAsync(url));
// terrain first (later props sit on it), then everything else
const order = [...LAYOUT.filter(it => it.terrain), ...LAYOUT.filter(it => !it.terrain)];
for (const it of order) {
  const g = await glb(`./${it.forest ? 'forest' : 'assets'}/${it.id}.glb`).catch(e => { $('load-text').textContent = `模型載入失敗：${e.message}`; throw e; });
  const o = g.scene.clone(true);
  const y = it.y ?? groundY(it.x, it.z) - 0.02;
  o.position.set(it.x, y, it.z); o.rotation.y = it.rot; o.visible = !it.hidden;
  o.updateMatrixWorld(true);   // later props raycast onto this one before the first frame renders
  // <key>_Collision is the model's convex collision hull: never drawn; its ground outline becomes a wall polygon.
  const hulls = [];
  o.traverse(m => { if (m.isMesh && /_Collision$/.test(m.name)) hulls.push(m); else if (/^SOCKET_/.test(m.name)) sockets.push({ name: m.name, node: m, item: it.id }); });
  for (const h of hulls) {
    if (o.visible) hullWalls.push({ poly: hullOutline(h), id: it.id });
    h.removeFromParent();
  }
  o.traverse(m => { if (m.isMesh) { m.castShadow = !it.terrain; m.receiveShadow = true; if (m.material.transparent) { m.castShadow = false; m.material.depthWrite = false; } } });
  scene.add(o);
  if (it.terrain || it.walk) terrain.push(o);
  else if (!it.plant) occluders.push(o);   // plants (sedge, the bamboo screen) never push the camera in
  if (it.silt) siltModels[it.silt] = o;
  if (it.resonance) o.traverse(m => { if (m.isMesh && m.material.emissiveMap) resonanceMats.push(m.material); });
  if (it.terrain && it.id.startsWith('A01')) o.traverse(m => { if (m.isMesh && /_Water$/.test(m.name)) riverWater.push({ mesh: m, module: it.mi }); });   // water is its own node, apart from the land
  placedItems.push({ ...it, object: o });
  progress();
}
heightCache.clear();   // heights sampled while models were still arriving are stale
$('loading').classList.add('done');
setTimeout(() => ($('loading').hidden = true), 700);

/** 2D convex hull (x, z) of a hull mesh's world-space vertices (Andrew's monotone chain). */
function hullOutline(mesh) {
  const pos = mesh.geometry.attributes.position, v = new THREE.Vector3(), pts = [];
  for (let i = 0; i < pos.count; i++) { v.fromBufferAttribute(pos, i).applyMatrix4(mesh.matrixWorld); pts.push([+v.x.toFixed(3), +v.z.toFixed(3)]); }
  pts.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const cross = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  const half = list => { const h = []; for (const p of list) { while (h.length > 1 && cross(h[h.length - 2], h[h.length - 1], p) <= 0) h.pop(); h.push(p); } h.pop(); return h; };
  return [...half(pts), ...half([...pts].reverse())];
}

// ------------------------------------------------------------------ ground height (visual + walkability): raycast onto tiles, silt and ground
// The open ground is flat (y 0) outside the river trench, so only the river tiles and the silt bar are raycast;
// results are cached on a 5 cm grid (walkability samples the same few points every step).
function groundY(x, z) {
  const key = Math.round(x * 20) * 100003 + Math.round(z * 20);
  let y = heightCache.get(key);
  if (y !== undefined) return y;
  ray.set(new THREE.Vector3(x, 4, z), DOWN); ray.far = 8;
  const hit = ray.intersectObjects(terrain, true).find(h => !h.object.material.transparent);
  y = hit ? hit.point.y : riverDist(x, z) < 3.3 ? -2.5 : 0;
  if (heightCache.size > 200000) heightCache.clear();
  heightCache.set(key, y);
  return y;
}
/** Walkable: inside the river corridor and not too steep (the outer cliff of the right bend cannot be climbed). */
function walkable(x, z) {
  const d = riverDist(x, z);
  if (!(d < 7.5)) return false;
  // central differences over 0.8 m: single pebbles in the tile mesh do not count, the outer cliff (~75 deg) still does
  const e = 0.4;
  const g = Math.max(Math.abs(groundY(x + e, z) - groundY(x - e, z)), Math.abs(groundY(x, z + e) - groundY(x, z - e))) / (2 * e);
  return g < 1.4;
}

/** A model-local Blender (x, y) point -> world circle, for a model placed at `at` with three rotation.y = rot. */
function localToWorld(atp, rot, bx, by, r) {
  const lx = bx, lz = -by, c = Math.cos(rot), sn = Math.sin(rot);
  return { x: atp.x + lx * c + lz * sn, z: atp.z - lx * sn + lz * c, r };
}

// ------------------------------------------------------------------ rules world
const START = { x: START_P.x, z: START_P.z, heading: Math.PI };   // facing upstream (-z)
const sluiceFace = (p, off) => ({ x: p.x - Math.cos(p.yaw) * off, z: p.z + Math.sin(p.yaw) * off });   // a point on the river side of the trough
const WORLD = {
  start: START,
  clues: [
    { id: 'cracked_sluice', ...sluiceFace(SLUICE, 0.45), range: 2.4 },
    { id: 'cracked_sluice', ...sluiceFace(SLUICE2, 0.2), range: 2.4 },
    { id: 'silt_buildup', x: SILT.x, z: SILT.z, range: 3.4, clearRange: 3.4 },
    { id: 'silt_buildup', x: SILT2.x, z: SILT2.z, range: 3.0 },
    { id: 'silt_buildup', x: SILT3.x, z: SILT3.z, range: 3.2 },
    { id: 'nursery_tracks', x: NURSERY.x, z: NURSERY.z, range: 2.8 },
  ],
  hints: [{ id: 'marker_stone', x: MARKER.x, z: MARKER.z, range: 3.0 }, { id: 'water_gauge', x: GAUGE.x, z: GAUGE.z, range: 2.6 },
    { id: 'resonance_stone', x: RESONANCE.x, z: RESONANCE.z, range: 2.8 }],
  zones: [{ id: 'nursery', x: NURSERY.x, z: NURSERY.z, r: 4.2 }],
  walls: [
    ...hullWalls,   // A02 troughs, A03 formation, A06 marker, A09 gauge, A12 resonance stone: their real collision hulls
    { ...onRiver(at('A01_narrow_01'), 3.0, -1.35), r: 0.75 }, { ...onRiver(at('A01_narrow_01'), 2.9, 1.4), r: 0.75 },
    ...[1.2, 1.7, 2.2, 2.7, 3.2, 3.7, 4.2, 4.7, 5.2].map(u => ({ ...onRiver(at('A01_bend_right_01'), u, -1.4), r: 0.3 })),   // foot of the outer strata cliff
    // A10 bamboo screen (local x -1.9..0.3); its gap (local x 0.3..1.5) stays open
    ...[-1.7, -1.25, -0.8, -0.35, 0.1].flatMap(bx => [-0.6, 0, 0.6].map(by => localToWorld(BAMBOO, BAMBOO.yaw + Math.PI, bx, by, 0.36))),
    // the end-source boulder jam
    ...[[2.5, -0.6], [2.6, 0.7], [3.2, -1.5], [3.3, 0.1], [3.2, 1.6], [3.7, -0.8], [3.7, 1.0]].map(([u, sv]) => ({ ...onRiver(ES, u, sv), r: 0.55 })),
  ],
  walkable,
};
let inv = new Investigation(WORLD);

// ------------------------------------------------------------------ player stand-in (clearly not the final character)
function labelSprite(text) {
  const c = document.createElement('canvas'); c.width = 128; c.height = 48; const g = c.getContext('2d');
  g.fillStyle = 'rgba(14,26,23,.8)'; g.fillRect(0, 0, 128, 48); g.strokeStyle = '#d6b26a'; g.strokeRect(1, 1, 126, 46);
  g.fillStyle = '#efe6d2'; g.font = '26px sans-serif'; g.textAlign = 'center'; g.fillText(text, 64, 34);
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(c), depthTest: false })); s.scale.set(0.5, 0.19, 1); return s;
}
const player = new THREE.Group();
{
  const cloth = new THREE.MeshStandardMaterial({ color: 0x5c7368, roughness: 0.8 }), skin = new THREE.MeshStandardMaterial({ color: 0xc9a98a, roughness: 0.7 });
  const body = new THREE.Mesh(new THREE.CapsuleGeometry(0.26, 0.75, 4, 12), cloth); body.position.y = 0.9; body.castShadow = true;
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.17, 16, 12), skin); head.position.y = 1.58; head.castShadow = true;
  const armG = new THREE.CapsuleGeometry(0.07, 0.5, 3, 8).translate(0, -0.28, 0);
  const armL = new THREE.Mesh(armG, cloth), armR = new THREE.Mesh(armG, cloth);
  armL.position.set(-0.33, 1.32, 0); armR.position.set(0.33, 1.32, 0);
  const label = labelSprite('替身'); label.position.y = 2.0;
  player.add(body, head, armL, armR, label);
  Object.assign(player.userData, { head, armR });
  scene.add(player);
}

// ------------------------------------------------------------------ input
const keys = new Set();
let stick = { x: 0, y: 0 }, autoMove = null;
let camYaw = Math.PI, camPitch = 0.32;
const eventLog = [];
const alias = { ArrowUp: 'KeyW', ArrowDown: 'KeyS', ArrowLeft: 'KeyA', ArrowRight: 'KeyD' };
addEventListener('keydown', e => {
  sfx.unlock();
  const k = alias[e.code] || e.code;
  if (['Space', 'KeyW', 'KeyA', 'KeyS', 'KeyD'].includes(k)) e.preventDefault();
  if (e.repeat) return;
  if (k === 'KeyE') act('observe'); else if (k === 'KeyR') act('home');
  keys.add(k);
});
addEventListener('keyup', e => keys.delete(alias[e.code] || e.code));
addEventListener('blur', () => keys.clear());
canvas.addEventListener('contextmenu', e => e.preventDefault());
let drag = null;
canvas.addEventListener('pointerdown', e => { sfx.unlock(); drag = { id: e.pointerId, x: e.clientX, y: e.clientY, moved: 0 }; canvas.setPointerCapture(e.pointerId); });
canvas.addEventListener('pointermove', e => {
  if (!drag || drag.id !== e.pointerId) return;
  const dx = e.clientX - drag.x, dy = e.clientY - drag.y; drag.moved += Math.abs(dx) + Math.abs(dy);
  camYaw -= dx * 0.005; camPitch = THREE.MathUtils.clamp(camPitch + dy * 0.003, 0.05, 0.95); drag.x = e.clientX; drag.y = e.clientY;
});
canvas.addEventListener('pointerup', e => { if (drag && drag.moved < 6 && e.pointerType === 'mouse' && e.button === 0) act('observe'); drag = null; });
{
  const el = $('stick'), knob = el.querySelector('i'); let id = null;
  const move = e => { const r = el.getBoundingClientRect(), dx = e.clientX - (r.left + r.width / 2), dy = e.clientY - (r.top + r.height / 2);
    const l = Math.min(1, Math.hypot(dx, dy) / (r.width / 2)), a = Math.atan2(dy, dx); stick = { x: Math.cos(a) * l, y: Math.sin(a) * l };
    knob.style.transform = `translate(${stick.x * 36}px, ${stick.y * 36}px)`; };
  el.addEventListener('pointerdown', e => { sfx.unlock(); id = e.pointerId; el.setPointerCapture(id); move(e); });
  el.addEventListener('pointermove', e => e.pointerId === id && move(e));
  const end = () => { id = null; stick = { x: 0, y: 0 }; knob.style.transform = ''; };
  el.addEventListener('pointerup', end); el.addEventListener('pointercancel', end);
  const tap = (btn, fn) => btn.addEventListener('pointerdown', e => { e.preventDefault(); sfx.unlock(); fn(); });
  tap($('t-use'), () => act('observe')); tap($('t-home'), () => act('home'));
}
$('reset').onclick = () => { inv.reset(); camYaw = Math.PI; renderBook(); toast('', 'info', '線索簿已清空，回到入口'); };
$('export').onclick = () => showHandoff();
$('close').onclick = () => ($('result').hidden = true);

function act(kind) {
  if (kind === 'home') { inv.returnToEntrance(); camYaw = Math.PI; return; }
  if (kind !== 'observe') return;
  const r = inv.inReach(), p = inv.player;
  if (r && r.id === 'silt_buildup' && inv.observationIds.includes('silt_buildup') && !inv.siltCleared &&
      Math.hypot(SILT.x - p.x, SILT.z - p.z) < 3.4) { inv.clearSilt(); return; }
  if (onPavilion()) { showHandoff(); return; }
  inv.observe();
}
const onPavilion = () => { const p = inv.player; return Math.hypot(p.x - PAVILION.x, p.z - PAVILION.z) < 1.6; };
let waterRise = 0;   // 0..1, animates the downstream water up after the silt is raked open

// ------------------------------------------------------------------ feedback
function toast(text, kind = 'info', sub = '') {
  const t = $('toast'); if (!text && !sub) return;
  t.innerHTML = `${text}${sub ? `<small>${sub}</small>` : ''}`; t.className = `toast ${kind}`; void t.offsetWidth; t.classList.add('show');
}
function renderBook() {
  for (const li of $('book').children) {
    const id = li.dataset.id, found = inv.observationIds.includes(id);
    li.classList.toggle('found', found);
    if (found) li.innerHTML = `${CLUE_TEXT[id].title}<small>${CLUE_TEXT[id].note}</small>`;
  }
  const v = inv.verdict;
  $('verdict').textContent = v === 'full' ? '三種原因都找到了：回水工場說明給工匠聽' : v === 'discuss' ? '已有兩種跡象：可以回水工場和工匠商量怎麼讓水回來' : '';
}
// What the player can do with the notes (part B's choices); the raw handoff JSON is a developer view only (?dev=1).
const NEXT_STEP = {
  cracked_sluice: '修補古水路：把石槽的破口補起來，水就不會一路漏在岸上。',
  silt_buildup: '清理泥沙：把堵在河道裡的泥沙和斷枝清開，讓水重新流下來。',
  nursery_tracks: '避開育幼處：妖獸在上游育幼，改道或等牠們離開，不要硬闖。',
};
const DEV = new URLSearchParams(location.search).has('dev');
function showHandoff() {
  const j = inv.toJSON(), n = j.observationIds.length;
  $('result-title').textContent = j.verdict === 'full' ? '找齊三種原因' : j.verdict === 'discuss' ? '可以回去商量了' : n ? '還差一點線索' : '還沒有發現';
  $('result-list').innerHTML = j.observationIds.map(id => `<li><b>${CLUE_TEXT[id].title}</b>${CLUE_TEXT[id].note}</li>`).join('') || '<li>沿岸走走，靠近看看石槽、河道和泥地。</li>';
  $('result-next').textContent = n >= 2
    ? `帶著手札回水工場找工匠商量要先處理哪一樁：${j.observationIds.map(id => NEXT_STEP[id]).join(' ')}`
    : '再找到一種跡象，就能回水工場和工匠商量怎麼讓水回來。';
  $('result-json').hidden = !DEV;
  $('result-json').textContent = JSON.stringify(j, null, 2);
  $('result').hidden = false;
}
function handle(ev) {
  switch (ev.type) {
    case 'clue': sfx.chime(ev.count === 1 ? 1 : ev.count === 2 ? 1.12 : 1.26); toast(CLUE_TEXT[ev.id].title, 'good', CLUE_TEXT[ev.id].note); renderBook(); break;
    case 'verdict': setTimeout(() => { toast(ev.verdict === 'full' ? '三種原因都找到了' : '可以回去商量了', 'good', '帶著手札回水工場找工匠'); }, 1600);
      if (ev.verdict === 'discuss') setTimeout(showHandoff, 3200); break;
    case 'already': sfx.knock(); toast('', 'info', '這裡已經記下了'); break;
    case 'look-closer': sfx.tick(); toast('', 'info', '再看仔細一點…'); break;
    case 'hint': sfx.tick(); toast('', 'info', HINT_TEXT[ev.id]); break;
    case 'nothing': toast('', 'info', '這裡沒什麼特別的'); break;
    case 'returned': toast('', 'info', '回到下游入口（線索簿保留）'); break;
    case 'silt-cleared':
      siltModels.blocking.visible = false; siltModels.cleared.visible = true; heightCache.clear(); waterRise = 0.0001; sfx.whoosh();
      toast('扒開了一道口子', 'good', '積水沿著缺口流下，下游的水位慢慢漲了一點'); break;
    case 'look-first': toast('', 'info', '先看清楚河道裡堆了什麼'); break;
    case 'enter-zone': if (ev.id === 'nursery') { sfx.growl(); document.body.classList.add('wary');
      toast('低低的嗚聲', 'bad', '泥地上有幼獸的足跡…放輕腳步，別再往前'); } break;
    case 'leave-zone': if (ev.id === 'nursery') { document.body.classList.remove('wary'); toast('', 'info', '退開了，嗚聲停了'); } break;
  }
}
const KEY = COARSE ? '按「觀察」' : 'E／點擊';
const PROMPT = {
  cracked_sluice: `${KEY} 觀察：岸上的舊石槽`,
  silt_buildup: `${KEY} 觀察：河道裡堆起的東西`,
  nursery_tracks: `${KEY} 觀察：泥地上的足跡`,
};
const HINT_PROMPT = { marker_stone: '看看這塊石頭', water_gauge: '讀一讀水位尺', resonance_stone: '摸摸這塊會發光的石頭' };

// ------------------------------------------------------------------ frame
function resize() { renderer.setSize(innerWidth, innerHeight, false); camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); }
const camera = new THREE.PerspectiveCamera(COARSE ? 62 : 55, 1, 0.05, 400);
const planCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 200);
let viewMode = 'play';   // 'play' | 'plan' | 'eye'
let showColliders = false, colliderGroup = null;
/** Seams (module joints, white) and collision circles (red) for the seam / collision review sheet. */
function drawColliders() {
  if (colliderGroup) scene.remove(colliderGroup);
  colliderGroup = new THREE.Group();
  const red = new THREE.MeshBasicMaterial({ color: 0xe0563f, transparent: true, opacity: 0.55, depthTest: false });
  for (const w of WORLD.walls) {
    let g;
    if (w.poly) { const sh = new THREE.Shape(w.poly.map(([x, z]) => new THREE.Vector2(x, -z))); g = new THREE.ShapeGeometry(sh).rotateX(-Math.PI / 2); }
    else g = new THREE.CircleGeometry(w.r, 20).rotateX(-Math.PI / 2).translate(w.x, 0, w.z);
    const m = new THREE.Mesh(g, red); m.position.y = 3; m.renderOrder = 5; colliderGroup.add(m);
  }
  // water sockets (cyan arrows, pointing along the flow): where a diversion pipe or the B waterworks snaps on
  for (const sk of sockets) {
    const p = sk.node.getWorldPosition(new THREE.Vector3()), d = new THREE.Vector3(0, 1, 0).applyQuaternion(sk.node.getWorldQuaternion(new THREE.Quaternion()));
    const a = new THREE.ArrowHelper(d.setY(0).normalize(), p.setY(3.05), 0.9, 0x4fd6d0, 0.3, 0.2);
    a.traverse(c => { if (c.material) { c.material.depthTest = false; c.renderOrder = 7; } }); colliderGroup.add(a);
  }
  const seam = new THREE.LineBasicMaterial({ color: 0xffffff, depthTest: false });
  placed.forEach((m, i) => {
    const a = onRiver(i, 0, -3.5), b = onRiver(i, 0, 3.5);
    const l = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(a.x, 3, a.z), new THREE.Vector3(b.x, 3, b.z)]), seam); l.renderOrder = 6;
    colliderGroup.add(l);
  });
  const zone = new THREE.Mesh(new THREE.RingGeometry(4.1, 4.2, 48).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ color: 0xf1b54a, depthTest: false }));
  zone.position.set(NURSERY.x, 3, NURSERY.z); colliderGroup.add(zone);
  scene.add(colliderGroup);
}
function setPlan(on) {
  viewMode = on ? 'plan' : 'play';
  document.body.classList.toggle('plan', on);
  scene.fog = on ? null : FOG;   // the plan camera sits 60 m up: no distance haze on the review sheet
  for (const el of document.querySelectorAll('.tag')) el.remove();
  if (!on) return;
  const xs = centre.map(c => c.x), zs = centre.map(c => c.z);
  const cx = (Math.min(...xs) + Math.max(...xs)) / 2, cz = (Math.min(...zs) + Math.max(...zs)) / 2;
  const half = Math.max(Math.max(...xs) - Math.min(...xs), (Math.max(...zs) - Math.min(...zs)) * innerWidth / innerHeight) / 2 + 6;
  const a = innerWidth / innerHeight;
  Object.assign(planCam, { left: -half, right: half, top: half / a, bottom: -half / a });
  planCam.position.set(cx, 60, cz); planCam.up.set(0, 0, -1); planCam.lookAt(cx, 0, cz); planCam.updateProjectionMatrix(); planCam.updateMatrixWorld();
  const tag = (x, z, text, cls) => { const v = new THREE.Vector3(x, 0, z).project(planCam), el = document.createElement('div');
    el.className = `tag ${cls}`; el.textContent = text; el.style.left = `${(v.x + 1) / 2 * innerWidth}px`; el.style.top = `${(1 - v.y) / 2 * innerHeight}px`;
    document.body.append(el); };
  placed.forEach((m, i) => { const c = onRiver(i, MODULES[m.id].L / 2, -3.9); tag(c.x, c.z, `${i + 1}. ${m.id}`, 'mod'); });
  tag(SLUICE.x, SLUICE.z, 'A02_side_crack_01 破槽', 'clue'); tag(SLUICE2.x, SLUICE2.z, 'A02_end_break_01 破槽', 'clue');
  tag(SILT.x, SILT.z, 'A04_SiltBar 泥沙', 'clue'); tag(MARKER.x, MARKER.z, 'A06 示跡石', 'aux'); tag(FORMATION.x, FORMATION.z, 'A03 舊陣基', 'aux');
  tag(START.x, START.z, '入口（下游）', 'start');
  for (const it of placedItems) if (!it.terrain && !it.forest && !it.id.startsWith('A05') && !it.hidden && !/^A0[236]_/.test(it.id))
    tag(it.x, it.z, it.id, it.walk ? 'aux' : 'clue');
  if (showColliders) drawColliders();
}
addEventListener('resize', resize); resize();
let last = performance.now(), acc = 0, bob = 0;
const camPos = new THREE.Vector3(), tmp = new THREE.Vector3(), tmp2 = new THREE.Vector3(), camRay = new THREE.Raycaster();
renderBook();

function frame(ms) {
  const dt = Math.min((ms - last) / 1000, 0.05); last = ms; wind.value = ms / 1000;
  let f = (keys.has('KeyW') ? 1 : 0) - (keys.has('KeyS') ? 1 : 0) - stick.y, rgt = (keys.has('KeyD') ? 1 : 0) - (keys.has('KeyA') ? 1 : 0) + stick.x;
  const l = Math.hypot(f, rgt); if (l > 1) { f /= l; rgt /= l; }
  const fx = Math.sin(camYaw), fz = Math.cos(camYaw);
  const vx = autoMove ? autoMove[0] : fx * f - fz * rgt, vz = autoMove ? autoMove[1] : fz * f + fx * rgt;
  acc += dt;
  const still = Math.hypot(vx, vz) < 0.05;   // standing still: the stand-in looks where the camera looks
  while (acc >= DT) { inv.step(DT, still && !autoMove ? { heading: camYaw } : { moveX: vx, moveZ: vz }); acc -= DT; }
  for (const ev of inv.drainEvents()) { handle(ev); eventLog.push(ev); if (eventLog.length > 200) eventLog.shift(); }
  const s = inv.snapshot(), p = s.player, py = groundY(p.x, p.z);
  const moving = Math.hypot(vx, vz) > 0.1;
  bob = moving ? bob + dt * 9 : 0;
  player.position.set(p.x, py + (moving ? Math.abs(Math.sin(bob)) * 0.03 : 0), p.z); player.rotation.y = p.heading;
  player.visible = viewMode === 'play';
  // look ring + prompt
  const reach = s.inReach, focus = inv.focus;
  const k = reach && reach.kind === 'clue' && !inv.observationIds.includes(reach.id) ? Math.min(1, (focus?.held || 0) / PARAMS.dwell) : 0;
  $('look').classList.toggle('on', k > 0); $('look').style.setProperty('--k', k.toFixed(3));
  player.userData.head.rotation.x = reach ? 0.25 : 0;
  if (reach && reach.kind === 'clue') $('prompt').textContent = !inv.observationIds.includes(reach.id) ? PROMPT[reach.id]
    : reach.id === 'silt_buildup' && !inv.siltCleared && Math.hypot(SILT.x - p.x, SILT.z - p.z) < 3.4 ? `${KEY} 扒開一點泥沙看看` : '已記在線索簿';
  else if (onPavilion()) $('prompt').textContent = `觀測亭殘基：${KEY} 翻開手札，比較三處跡象`;
  else if (reach && reach.kind === 'hint') $('prompt').textContent = `${KEY} ${HINT_PROMPT[reach.id]}`;
  else {
    const d = riverDist(p.x, p.z);
    $('prompt').textContent = d < 1.0 ? '水只剩中間一道細流，兩邊的卵石都露出來了' : inv.verdict === 'full' ? '三種原因都找到了：回水工場說明給工匠聽' : inv.verdict ? '可以回水工場商量了，或繼續找第三種跡象' : '沿岸往上游走，看看水為什麼變少';
  }
  sfx.streamLevel(Math.max(0, 1 - riverDist(p.x, p.z) / 6) * (1 + waterRise * 0.6));
  // the resonance stone answers when you come close: its veins brighten and it hums (no arrow, no marker)
  const near = Math.max(0, 1 - Math.hypot(p.x - RESONANCE.x, p.z - RESONANCE.z) / 6);
  for (const m of resonanceMats) m.emissiveIntensity = 0.35 + near * (1.6 + 0.4 * Math.sin(ms * 0.004));
  sfx.hum(near);
  // after the silt is raked open the water below it rises a little over a few seconds
  if (waterRise > 0 && waterRise < 1) waterRise = Math.min(1, waterRise + dt / 3);
  for (const w of riverWater) w.mesh.position.y = w.module <= at('A01_bend_left_01') ? 0.07 * waterRise : 0;
  // third-person camera with collision (pattern from tools/qingxi-encounter-a)
  const fwdX = Math.sin(camYaw), fwdZ = Math.cos(camYaw), rightX = -fwdZ, rightZ = fwdX;
  const dist = 4.6, pitch = camPitch;
  const place = shoulder => {
    const t = new THREE.Vector3(p.x + rightX * shoulder, py + 1.25, p.z + rightZ * shoulder);
    const c = new THREE.Vector3(t.x - fwdX * dist * Math.cos(pitch), t.y + Math.sin(pitch) * dist, t.z - fwdZ * dist * Math.cos(pitch));
    camRay.set(t, tmp2.copy(c).sub(t).normalize()); camRay.far = c.distanceTo(t);
    const block = camRay.intersectObjects([...occluders, ...terrain], true).find(h => !h.object.material.transparent);
    const free = block ? block.distance - 0.25 : dist;
    if (block) c.copy(t).addScaledVector(camRay.ray.direction, Math.max(0.6, free));
    return { t, c, free };
  };
  let view = place(0.6);
  if (view.free < 1.2) { const alt = place(-0.6); if (alt.free > view.free) view = alt; }
  camPos.copy(view.c);
  camera.position.lerp(camPos, Math.min(1, dt * 8 || 1)); camera.lookAt(tmp.copy(view.t));
  sun.position.set(p.x + SUN_DIR.x * 40, SUN_DIR.y * 40, p.z + SUN_DIR.z * 40); sun.target.position.set(p.x, 0, p.z);
  if (viewMode === 'eye') { camera.position.set(p.x, py + 1.7, p.z); camera.lookAt(p.x + Math.sin(camYaw) * 10, py + 1.7 - Math.tan(camPitch - 0.32) * 10, p.z + Math.cos(camYaw) * 10); }
  if (viewMode === 'plan') { sun.shadow.camera.left = -40; sun.shadow.camera.right = 40; sun.shadow.camera.top = 40; sun.shadow.camera.bottom = -40; sun.shadow.camera.updateProjectionMatrix(); }
  renderer.render(scene, viewMode === 'plan' ? planCam : camera);
  requestAnimationFrame(frame);
}
camera.position.set(START.x, 2.5, START.z + 4.4);
requestAnimationFrame(frame);

let highSheet = null;
/** A flat water ribbon of half-width hw along a polyline (review view of the old high water). */
function ribbon(pts, hw, y) {
  const pos = [], idx = [];
  pts.forEach((p, i) => {
    const q = pts[Math.min(i + 1, pts.length - 1)], o = pts[Math.max(i - 1, 0)], dx = q.x - o.x, dz = q.z - o.z, l = Math.hypot(dx, dz) || 1;
    pos.push(p.x - dz / l * hw, y, p.z + dx / l * hw, p.x + dz / l * hw, y, p.z - dx / l * hw);
    if (i) idx.push(2 * i - 2, 2 * i - 1, 2 * i, 2 * i - 1, 2 * i + 1, 2 * i);
  });
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setIndex(idx); g.computeVertexNormals();
  return new THREE.Mesh(g, new THREE.MeshStandardMaterial({ color: 0x1f3b39, transparent: true, opacity: 0.6, roughness: 0.1, side: THREE.DoubleSide, depthWrite: false }));
}

// Debug / capture hook (local only).
globalThis.__wh = {
  get inv() { return inv; }, act, showHandoff, onRiver,
  autoMove(v) { autoMove = v; },
  events: () => eventLog.slice(),
  teleport(x, z, yawDeg = 180) { inv.player.x = x; inv.player.z = z; camYaw = THREE.MathUtils.degToRad(yawDeg); inv.player.heading = camYaw; },
  look(yawDeg, pitch = 0.32) { camYaw = THREE.MathUtils.degToRad(yawDeg); camPitch = pitch; inv.player.heading = camYaw; },
  face(x, z) { const p = inv.player; inv.player.heading = Math.atan2(x - p.x, z - p.z); },
  spots: { SLUICE, SLUICE2, SILT, MARKER, FORMATION, START, clues: WORLD.clues },
  state: () => inv.snapshot(),
  route: ROUTE, chain: CHAIN, setPlan, eye(on) { viewMode = on ? 'eye' : 'play'; },
  colliders(on) { showColliders = on; if (!on && colliderGroup) { scene.remove(colliderGroup); colliderGroup = null; } },
  /** review only: the old high water (0.86 m) over the whole run, to show the fords under water */
  highWater(on) { if (on && !highSheet) { const pts = centre.map(c => new THREE.Vector3(c.x, 0, c.z)); highSheet = ribbon(pts, 2.4, -TOP + 0.86); scene.add(highSheet); }
    if (highSheet) highSheet.visible = on; },
  more: { NURSERY, GAUGE, RESONANCE, BAMBOO, PAVILION, SILT2, SILT3, FORDS: FORDS.map(([id, q]) => ({ id, ...q })) },
  groundY, riverDist,
  setSilt(cleared) { siltModels.blocking.visible = !cleared; siltModels.cleared.visible = cleared; heightCache.clear(); },
};
