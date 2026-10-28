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
const LAYOUT = [
  ...placed.map(m => ({ id: m.id, x: m.x, y: -TOP, z: m.z, rot: m.yaw, terrain: true })),
  { id: 'A02_side_crack_01', x: SLUICE.x, y: 0, z: SLUICE.z, rot: SLUICE.yaw - Math.PI / 2 },
  { id: 'A02_end_break_01', x: SLUICE2.x, y: 0, z: SLUICE2.z, rot: SLUICE2.yaw - Math.PI / 2 },
  { id: 'A03_FormationBase', x: FORMATION.x, y: 0, z: FORMATION.z, rot: 0.8 },
  { id: 'A04_SiltBar', x: SILT.x, y: -TOP + BED, z: SILT.z, rot: SILT.yaw, walk: true, silt: 'blocking' },
  { id: 'A04_SiltBar_cleared', x: SILT.x, y: -TOP + BED, z: SILT.z, rot: SILT.yaw, hidden: true, silt: 'cleared' },
  { id: 'A06_MarkerStone', x: MARKER.x, y: -TOP + WATER - 0.35, z: MARKER.z, rot: 0.4 },
  ...[[0, 1.6, 1.75], [0, 4.6, -1.8], [1, 5.4, 1.85], [2, 4.7, -1.65], [3, 2.0, 1.95], [3, 4.6, -1.7], [4, 2.5, -1.8]].map(([i, u, s], k) => {
    const p = onRiver(i, u, s); return { id: 'A05_WitheredSedge_01', x: p.x, y: null, z: p.z, rot: k * 1.7 }; }),
  // background dressing, reused read-only from the forest encounter kit (PR #39): hides the open downstream cut until the core team joins the village river
  { id: 'A03_FallenLog', x: placed[0].x, y: -0.15, z: placed[0].z + 1.4, rot: Math.PI / 2 + 0.15, forest: true },
  { id: 'A06_RootStump', x: onRiver(at('A01_bend_right_01'), 3.2, 3.9).x, y: 0, z: onRiver(at('A01_bend_right_01'), 3.2, 3.9).z, rot: 2.0, forest: true },
];
const loader = new GLTFLoader();
const ray = new THREE.Raycaster(), DOWN = new THREE.Vector3(0, -1, 0);
const heightCache = new Map();
const terrain = [];
const occluders = [];
const siltModels = {};
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
  o.traverse(m => { if (m.isMesh) { m.castShadow = !it.terrain; m.receiveShadow = true; if (m.material.transparent) { m.castShadow = false; m.material.depthWrite = false; } } });
  scene.add(o);
  if (it.terrain || it.walk) terrain.push(o);
  else if (it.id !== 'A05_WitheredSedge_01') occluders.push(o);
  if (it.silt) siltModels[it.silt] = o;
  progress();
}
$('loading').classList.add('done');
setTimeout(() => ($('loading').hidden = true), 700);

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

// ------------------------------------------------------------------ rules world
const START = { x: START_P.x, z: START_P.z, heading: Math.PI };   // facing upstream (-z)
const sluiceFace = (p, off) => ({ x: p.x - Math.cos(p.yaw) * off, z: p.z + Math.sin(p.yaw) * off });   // a point on the river side of the trough
const WORLD = {
  start: START,
  clues: [
    { id: 'cracked_sluice', ...sluiceFace(SLUICE, 0.45), range: 2.4 },
    { id: 'cracked_sluice', ...sluiceFace(SLUICE2, 0.2), range: 2.4 },
    { id: 'silt_buildup', x: SILT.x, z: SILT.z, range: 3.4 },
  ],
  hints: [{ id: 'marker_stone', x: MARKER.x, z: MARKER.z, range: 3.0 }],
  walls: [
    ...[-1.2, -0.4, 0.4, 1.2].flatMap(t => [onRiver(0, 3.4 + t, 3.05), onRiver(at('A01_narrow_01'), 3.6 + t, 3.05)]).map(q => ({ x: q.x, z: q.z, r: 0.42 })),   // A02 troughs
    { x: FORMATION.x, z: FORMATION.z, r: 0.95 }, { x: MARKER.x, z: MARKER.z, r: 0.5 },
    { ...onRiver(at('A01_narrow_01'), 3.0, -1.35), r: 0.75 }, { ...onRiver(at('A01_narrow_01'), 2.9, 1.4), r: 0.75 },
    ...[1.2, 1.7, 2.2, 2.7, 3.2, 3.7, 4.2, 4.7, 5.2].map(u => ({ ...onRiver(at('A01_bend_right_01'), u, -1.4), r: 0.3 })),   // foot of the outer strata cliff     // the two pinch rocks of the narrow module
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
  if (kind === 'observe') inv.observe();
}

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
  $('verdict').textContent = v === 'full' ? '三種跡象都看到了：可以回去完整說明缺水原因' : v === 'discuss' ? '已有兩種跡象：可以回去討論導水方案' : '';
}
function showHandoff() {
  const j = inv.toJSON();
  $('result-title').textContent = j.verdict === 'full' ? '三種跡象齊全' : j.verdict === 'discuss' ? '可回去討論導水方案' : `已看到 ${j.observationIds.length} 種跡象`;
  $('result-detail').textContent = j.observationIds.length ? `記下：${j.observationIds.map(id => CLUE_TEXT[id].title).join('、')}。` : '還沒有記下任何跡象。';
  $('result-json').textContent = JSON.stringify(j, null, 2);
  $('result').hidden = false;
}
function handle(ev) {
  switch (ev.type) {
    case 'clue': sfx.chime(ev.count === 1 ? 1 : ev.count === 2 ? 1.12 : 1.26); toast(CLUE_TEXT[ev.id].title, 'good', CLUE_TEXT[ev.id].note); renderBook(); break;
    case 'verdict': setTimeout(() => { toast(ev.verdict === 'full' ? '三種跡象齊全' : '可以回去討論導水方案', 'good', '線索簿可匯出交給工匠與村民'); }, 1600);
      if (ev.verdict === 'discuss') setTimeout(showHandoff, 3200); break;
    case 'already': sfx.knock(); toast('', 'info', '這裡已經記下了'); break;
    case 'look-closer': sfx.tick(); toast('', 'info', '再看仔細一點…'); break;
    case 'hint': sfx.tick(); toast('', 'info', HINT_TEXT[ev.id]); break;
    case 'nothing': toast('', 'info', '這裡沒什麼特別的'); break;
    case 'returned': toast('', 'info', '回到下游入口（線索簿保留）'); break;
  }
}
const KEY = COARSE ? '按「觀察」' : 'E／點擊';
const PROMPT = {
  cracked_sluice: `${KEY} 觀察：岸上的舊石槽`,
  silt_buildup: `${KEY} 觀察：河道裡堆起的東西`,
};

// ------------------------------------------------------------------ frame
function resize() { renderer.setSize(innerWidth, innerHeight, false); camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); }
const camera = new THREE.PerspectiveCamera(COARSE ? 62 : 55, 1, 0.05, 400);
const planCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 200);
let viewMode = 'play';   // 'play' | 'plan' | 'eye'
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
  if (reach && reach.kind === 'clue') $('prompt').textContent = inv.observationIds.includes(reach.id) ? '已記在線索簿' : PROMPT[reach.id];
  else if (reach && reach.kind === 'hint') $('prompt').textContent = `${KEY} 看看這塊石頭`;
  else {
    const d = riverDist(p.x, p.z);
    $('prompt').textContent = d < 1.0 ? '水只剩中間一道細流，兩邊的卵石都露出來了' : inv.verdict ? '可以按「線索 JSON」交接，或繼續找第三種跡象' : '沿岸往上游走，看看水為什麼變少';
  }
  sfx.streamLevel(Math.max(0, 1 - riverDist(p.x, p.z) / 6));
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
  groundY, riverDist,
  setSilt(cleared) { siltModels.blocking.visible = !cleared; siltModels.cleared.visible = cleared; heightCache.clear(); },
};
