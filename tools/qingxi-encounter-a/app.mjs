import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { Encounter, PARAMS } from './encounter.mjs';
import { Sfx } from './audio.mjs';

const $ = id => document.getElementById(id);
const COARSE = matchMedia('(pointer: coarse)').matches;
const sfx = new Sfx();
const DT = PARAMS.dt;

// ------------------------------------------------------------------ renderer, sky, light
const canvas = $('world');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(devicePixelRatio, COARSE ? 1.5 : 1.75));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
const scene = new THREE.Scene();
const HORIZON = new THREE.Color('#c3d1c6');
scene.fog = new THREE.FogExp2(HORIZON, 0.022);
const SUN_DIR = new THREE.Vector3(-0.45, 0.7, -0.55).normalize();
const sky = new THREE.Mesh(new THREE.SphereGeometry(300, 32, 16), new THREE.ShaderMaterial({
  side: THREE.BackSide, depthWrite: false, fog: false,
  uniforms: { sun: { value: SUN_DIR }, top: { value: new THREE.Color('#6f98b3') }, hor: { value: HORIZON }, warm: { value: new THREE.Color('#f3d9a8') } },
  vertexShader: 'varying vec3 vDir; void main(){ vDir = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
  fragmentShader: `varying vec3 vDir; uniform vec3 sun, top, hor, warm;
    void main(){ float h = clamp(vDir.y, -0.2, 1.0); vec3 c = mix(hor, top, pow(max(h,0.0), 0.6));
      float s = max(dot(normalize(vDir), sun), 0.0); c += warm * (pow(s, 6.0) * 0.3 + pow(s, 400.0) * 2.0);
      gl_FragColor = vec4(c, 1.0); }`,
}));
scene.add(sky);
scene.add(new THREE.HemisphereLight(0xd6e6ee, 0x4b4a2c, 1.1));
const sun = new THREE.DirectionalLight(0xffe2b8, 2.8);
sun.castShadow = true;
sun.shadow.mapSize.set(COARSE ? 1024 : 2048, COARSE ? 1024 : 2048);
Object.assign(sun.shadow.camera, { left: -14, right: 14, top: 14, bottom: -14, near: 1, far: 80 });
sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.03;
scene.add(sun, sun.target);
{
  const pm = new THREE.PMREMGenerator(renderer), env = new THREE.Scene();
  env.add(sky.clone());
  const g = new THREE.Mesh(new THREE.CircleGeometry(200, 24), new THREE.MeshBasicMaterial({ color: 0x47502f }));
  g.rotation.x = -Math.PI / 2; g.position.y = -2; env.add(g);
  scene.environment = pm.fromScene(env, 0.04).texture;
  scene.environmentIntensity = 0.55;
}

// ------------------------------------------------------------------ ground, grass, trees (demo backdrop only)
function rand(seed) { let s = seed >>> 0; return () => ((s = (1664525 * s + 1013904223) >>> 0) / 2 ** 32); }
function canvasTex(size, paint, repeat) {
  const c = document.createElement('canvas'); c.width = c.height = size; paint(c.getContext('2d'), size);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(repeat, repeat); t.anisotropy = 4;
  return t;
}
const groundTex = canvasTex(256, (g, n) => { const r = rand(3); g.fillStyle = '#4d5a2f'; g.fillRect(0, 0, n, n);
  for (let i = 0; i < 2600; i++) { g.fillStyle = r() < 0.6 ? `rgba(${60 + r() * 30},${78 + r() * 30},${36 + r() * 14},.55)` : `rgba(${90 + r() * 30},${70 + r() * 20},${40 + r() * 20},.35)`;
    g.fillRect(r() * n, r() * n, 1 + r() * 3, 1 + r() * 3); } }, 50);
const ground = new THREE.Mesh(new THREE.PlaneGeometry(200, 200).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ map: groundTex, roughness: 1 }));
ground.receiveShadow = true;
scene.add(ground);
const wind = { value: 0 };
{ // grass clumps (alpha-tested cards), off the trail and props
  const tex = canvasTex(256, (g, n) => { const r = rand(9); g.clearRect(0, 0, n, n);
    for (let i = 0; i < 42; i++) { const x = 14 + r() * (n - 28), h = n * (0.35 + r() * 0.6), lean = (r() - 0.5) * 70, w = 2 + r() * 3.5;
      const grd = g.createLinearGradient(0, n, 0, n - h), hue = 72 + r() * 22;
      grd.addColorStop(0, `hsl(${hue},40%,18%)`); grd.addColorStop(0.6, `hsl(${hue},45%,30%)`); grd.addColorStop(1, `hsl(${hue - 14},40%,46%)`);
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
  const N = COARSE ? 6000 : 14000, mesh = new THREE.InstancedMesh(clump, mat, N), r = rand(77), m4 = new THREE.Matrix4(), c = new THREE.Color();
  let n = 0;
  for (let i = 0; i < N * 4 && n < N; i++) {
    const x = (r() - 0.5) * 60, z = (r() - 0.5) * 60 - 2;
    if (Math.abs(x) < 3.4 && z > -3.4 && z < 3.4) continue;          // hollow tile
    if (Math.abs(x) < 1.0 && z < -2) continue;                        // rabbit trail to the village
    const k = 0.6 + r() * 0.8;
    m4.compose(new THREE.Vector3(x, 0, z), new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), r() * 3), new THREE.Vector3(k, k * (0.6 + r() * 0.9), k));
    mesh.setMatrixAt(n, m4); c.setHSL(0.2 + r() * 0.06, 0.22 + r() * 0.2, 0.62 + r() * 0.25); mesh.setColorAt(n, c); n++;
  }
  mesh.count = n; mesh.receiveShadow = true; scene.add(mesh);
}
{ // forest edge: stylised trees beyond the play space (demo backdrop, not delivered assets)
  const r = rand(31), trunkG = new THREE.CylinderGeometry(0.16, 0.26, 3, 6).translate(0, 1.5, 0);
  const crownG = new THREE.ConeGeometry(1.6, 3.6, 7).translate(0, 4.2, 0), crown2 = new THREE.ConeGeometry(1.1, 2.6, 7).translate(0, 5.8, 0);
  const meshes = [[trunkG, 0x3b2a1d], [crownG, 0x2c4630], [crown2, 0x345338]].map(([g, c]) => new THREE.InstancedMesh(g, new THREE.MeshStandardMaterial({ color: c, roughness: 0.95 }), 120));
  const m = new THREE.Matrix4(); let n = 0;
  for (let i = 0; i < 800 && n < 120; i++) {
    const x = (r() - 0.5) * 70, z = (r() - 0.5) * 70 + 6;
    if (Math.abs(x) < 9 && z < 9 && z > -18) continue;
    const k = 0.8 + r() * 0.7;
    m.compose(new THREE.Vector3(x, 0, z), new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), r() * 6), new THREE.Vector3(k, k * (0.9 + r() * 0.4), k));
    for (const im of meshes) im.setMatrixAt(n, m);
    n++;
  }
  for (const im of meshes) { im.count = n; im.castShadow = true; scene.add(im); }
}

// ------------------------------------------------------------------ the A kit layout (three: village at -z, forest at +z)
// Blender (Z-up, -Y front) GLBs arrive Y-up with their front facing +z.
const LAYOUT = [
  { id: 'A02_HollowTile', x: 0, y: -0.6, z: 0, rot: Math.PI, terrain: true },
  { id: 'A01_SlopeTile', x: -2, y: -0.6, z: 5, rot: Math.PI, terrain: true },
  { id: 'A01_SlopeTile', x: 2, y: -0.6, z: 5, rot: Math.PI, terrain: true },
  { id: 'A01_SlopeTile', x: 5, y: -0.6, z: 1, rot: Math.PI / 2, terrain: true },
  { id: 'A07_RabbitTrailTile', x: 0, y: -0.15, z: -5.0, rot: 0, terrain: true },
  { id: 'A04_MossBoulderCover', x: -2.6, y: 0, z: -3.2, rot: 0.3 },
  { id: 'A05_LayeredRockCover', x: 3.4, y: 0, z: -1.2, rot: -1.2 },
  { id: 'A03_FallenLog', x: 3.6, y: 0, z: -5.2, rot: -0.45 },
  { id: 'A06_RootStump', x: -3.0, y: 0, z: -6.4, rot: 0.6 },
  { id: 'A08_BrokenBambooFence', x: -2.4, y: 0, z: -8.6, rot: 0 },
  { id: 'A08_BrokenBambooFence', x: 2.4, y: 0, z: -8.6, rot: Math.PI },
  { id: 'A11_WarningClothRack', x: 1.75, y: 0, z: -8.15, rot: Math.PI },
  { id: 'A10_WatchPlatform', x: -6.2, y: 0, z: -7.5, rot: Math.PI / 2 },
  { id: 'A09_StoneShelter', x: 0, y: 0, z: -11, rot: 0, floor: true },
  { id: 'A12_VineDummy', x: 3.4, y: 0, z: -10.6, rot: -Math.PI / 2, dummy: 'intact' },
  { id: 'A12_VineDummy_worn', x: 3.4, y: 0, z: -10.6, rot: -Math.PI / 2, dummy: 'worn', hidden: true },
];
const SAFE = { x: 0, z: -11 }, START = { x: 0, z: -9.95 };     // start on the stone shelter's (A09) step, inside the safe radius
const BURROW = { x: 0, z: 1.75 };
const PLATFORM = { x: -6.2, z: -7.5, deck: 1.8, ladder: { x: -4.45, z: -7.5 } };
const DUMMY = { x: 3.4, z: -10.6, r: 0.3, wearAt: 8 };
const ring = (cx, cz, x0, x1, z0, z1, r = 0.22) => { const out = [], n = Math.max(1, Math.round(Math.hypot(x1 - x0, z1 - z0) / 0.4));
  for (let i = 0; i <= n; i++) out.push({ x: cx + x0 + (x1 - x0) * i / n, z: cz + z0 + (z1 - z0) * i / n, r }); return out; };
const WORLD = {
  burrow: BURROW, safe: SAFE, start: START, respawn: START, safeZones: [], dummies: [DUMMY],   // respawn on the step: no camera room inside the shelter
  cover: [{ x: -2.6, z: -3.2, r: 0.95 }, { x: 3.4, z: -1.2, r: 1.25 }, { x: 3.6, z: -5.2, r: 0.5 }, { x: 2.5, z: -4.6, r: 0.5 }, { x: 4.7, z: -5.8, r: 0.5 }],
  walls: [{ x: -2.6, z: -3.2, r: 0.85 }, { x: 3.4, z: -1.2, r: 1.0 }, { x: 3.6, z: -5.2, r: 0.38 }, { x: 2.5, z: -4.6, r: 0.38 },
    { x: 4.7, z: -5.8, r: 0.38 }, { x: -3.0, z: -6.4, r: 0.5 },
    ...ring(-2.4, -8.6, -1.5, 1.5, 0, 0, 0.18), ...ring(2.4, -8.6, -1.5, 1.5, 0, 0, 0.18),            // A08 fences (gap on the trail)
    ...ring(0, -11, -1.0, 1.0, -0.63, -0.63), ...ring(0, -11, -0.93, -0.93, 0.5, -0.5), ...ring(0, -11, 0.93, 0.93, 0.5, -0.5),  // A09 walls
    { x: -0.98, z: -10.32, r: 0.12 }, { x: 0.98, z: -10.32, r: 0.12 },
    ...[-1, 1].flatMap(a => [-1, 1].map(b => ({ x: PLATFORM.x + 0.9 * a, z: PLATFORM.z + 0.9 * b, r: 0.13 }))),  // A10 legs
    { x: DUMMY.x, z: DUMMY.z, r: 0.3 }, { x: 1.75, z: -8.15, r: 0.12 }],
};

const loader = new GLTFLoader();
const terrain = [];
const occluders = [];   // props the third-person camera must not end up behind
const dummyModels = {};
let loaded = 0;
const TOTAL = LAYOUT.length + 1;
const progress = () => { loaded++; $('load-text').textContent = `載入模型 ${loaded}/${TOTAL}`; $('load-bar').style.setProperty('--p', `${loaded / TOTAL * 100}%`); };
const cache = {};
const glb = url => (cache[url] ||= loader.loadAsync(url));
const [, rabbitGltf] = await Promise.all([
  Promise.all(LAYOUT.map(async it => {
    const g = await glb(`./assets/${it.id}.glb`);
    const o = g.scene.clone(true);
    o.position.set(it.x, it.y, it.z); o.rotation.y = it.rot; o.visible = !it.hidden;
    o.traverse(m => { if (m.isMesh) { m.castShadow = !it.terrain; m.receiveShadow = true; } });
    scene.add(o); if (it.terrain || it.floor) terrain.push(o); if (!it.terrain) occluders.push(o);
    if (it.dummy) dummyModels[it.dummy] = o;
    progress();
  })),
  glb('./rabbit/QingxiMountainRabbit_v003.glb').then(g => { progress(); return g; }),
]).catch(e => { $('load-text').textContent = `模型載入失敗：${e.message}`; throw e; });
terrain.push(ground);
$('loading').classList.add('done');
setTimeout(() => ($('loading').hidden = true), 700);

// ------------------------------------------------------------------ ground height (visual): raycast onto the terrain tiles
const ray = new THREE.Raycaster(), DOWN = new THREE.Vector3(0, -1, 0);
function groundY(x, z) {
  ray.set(new THREE.Vector3(x, 1.0, z), DOWN); ray.far = 3;
  const hit = ray.intersectObjects(terrain, true)[0];
  return hit ? hit.point.y : 0;
}

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
  const sword = new THREE.Mesh(new THREE.BoxGeometry(0.035, 0.035, 0.85).translate(0, 0, 0.42), new THREE.MeshStandardMaterial({ color: 0xb8bcb8, metalness: 0.8, roughness: 0.3 }));
  sword.position.set(0, -0.55, 0.05); armR.add(sword);
  const label = labelSprite('替身'); label.position.y = 2.0;
  player.add(body, head, armL, armR, label);
  Object.assign(player.userData, { armL, armR, sword, body });
  scene.add(player);
}

// ------------------------------------------------------------------ rabbit (v003, unmodified) and its tells
const rabbit = rabbitGltf.scene;
rabbit.traverse(m => { if (m.isMesh) { m.castShadow = true; m.receiveShadow = true; } });
const rabbitRoot = new THREE.Group(); rabbitRoot.add(rabbit); scene.add(rabbitRoot);
const mixer = new THREE.AnimationMixer(rabbit);
const clips = Object.fromEntries(rabbitGltf.animations.map(a => [a.name.replace('Rabbit_', ''), mixer.clipAction(a)]));
let current = null;
function play(name, { speed = 1, once = false } = {}) {
  const a = clips[name]; if (!a) return;
  a.timeScale = speed;
  if (current === a) return;
  a.reset(); a.setLoop(once ? THREE.LoopOnce : THREE.LoopRepeat); a.clampWhenFinished = once;
  if (current) a.crossFadeFrom(current, 0.15, false);
  a.play(); current = a;
}
play('Idle');
// windup ground tell: a scuffed crescent of soil and a short dark streak toward the target (not a glowing line)
const scuffTex = canvasTex(128, (g, n) => { const grd = g.createRadialGradient(n / 2, n / 2, 0, n / 2, n / 2, n / 2);
  grd.addColorStop(0, 'rgba(60,40,22,.9)'); grd.addColorStop(0.6, 'rgba(70,48,26,.55)'); grd.addColorStop(1, 'rgba(70,48,26,0)'); g.fillStyle = grd; g.fillRect(0, 0, n, n); }, 1);
const scuff = new THREE.Mesh(new THREE.PlaneGeometry(1.1, 2.4).rotateX(-Math.PI / 2).translate(0, 0, 1.4),
  new THREE.MeshStandardMaterial({ map: scuffTex, transparent: true, depthWrite: false, opacity: 0, roughness: 1 }));
scene.add(scuff);
// dust puffs
const DUST = 50, dustGeo = new THREE.BufferGeometry(), dustPos = new Float32Array(DUST * 3), dustVel = new Float32Array(DUST * 3);
dustGeo.setAttribute('position', new THREE.BufferAttribute(dustPos, 3));
const dustTex = canvasTex(64, (g, n) => { const grd = g.createRadialGradient(n / 2, n / 2, 0, n / 2, n / 2, n / 2); grd.addColorStop(0, 'rgba(170,140,100,.9)'); grd.addColorStop(1, 'rgba(170,140,100,0)'); g.fillStyle = grd; g.fillRect(0, 0, n, n); }, 1);
const dust = new THREE.Points(dustGeo, new THREE.PointsMaterial({ size: 0.18, map: dustTex, transparent: true, depthWrite: false, opacity: 0 }));
dust.frustumCulled = false; scene.add(dust);
let dustLife = 0;
function puff(x, y, z, spread = 1, color = 0xb49a74) {
  dust.material.color.set(color);
  for (let i = 0; i < DUST; i++) { dustPos.set([x, y + 0.05, z], i * 3); dustVel.set([(Math.random() - 0.5) * spread * 2, Math.random() * 0.9, (Math.random() - 0.5) * spread * 2], i * 3); }
  dustLife = 0.7;
}
function tickDust(dt) {
  if (dustLife <= 0) { dust.material.opacity = 0; return; }
  dustLife -= dt;
  for (let i = 0; i < DUST * 3; i++) dustPos[i] += dustVel[i] * dt;
  dust.material.opacity = Math.max(0, dustLife / 0.7) * 0.8; dustGeo.attributes.position.needsUpdate = true;
}

// ------------------------------------------------------------------ encounter + input
let style = 'sword';
let autoMove = null;
const eventLog = [];   // recent rule events, read by the capture script   // capture/test hook only: overrides stick/keys with a world-space direction
let enc = new Encounter(WORLD, { style });
const keys = new Set();
let stick = { x: 0, y: 0 };
let camYaw = 0, camPitch = 0.32;
function setStyle(s) { style = s; $('style-sword').classList.toggle('on', s === 'sword'); $('style-body').classList.toggle('on', s === 'body');
  $('style-sword').setAttribute('aria-pressed', s === 'sword'); $('style-body').setAttribute('aria-pressed', s === 'body'); restart(false); }
$('style-sword').onclick = () => setStyle('sword');
$('style-body').onclick = () => setStyle('body');
function restart(atSafe = true) {
  if (typeof climbed !== 'undefined' && climbed) climbed = false;
  if (dummyModels.intact) { dummyModels.intact.visible = true; dummyModels.worn.visible = false; }
  enc = new Encounter(WORLD, { style });     // START is the shelter step, inside the safe radius
  $('result').hidden = true; toast('', 'info', '回到安全點');
}
$('again').onclick = () => restart(true);
$('close').onclick = () => ($('result').hidden = true);

const alias = { ArrowUp: 'KeyW', ArrowDown: 'KeyS', ArrowLeft: 'KeyA', ArrowRight: 'KeyD' };
addEventListener('keydown', e => {
  sfx.unlock();
  const k = alias[e.code] || e.code;
  if (['Space', 'KeyW', 'KeyA', 'KeyS', 'KeyD'].includes(k)) e.preventDefault();
  if (e.repeat) return;
  if (k === 'Space') act('dodge'); else if (k === 'KeyJ') act('attack'); else if (k === 'KeyQ') act('technique'); else if (k === 'KeyE') act('interact');
  else if (k === 'KeyK') act('block-on'); else if (k === 'KeyR') restart(true);
  keys.add(k);
});
addEventListener('keyup', e => { const k = alias[e.code] || e.code; keys.delete(k); if (k === 'KeyK') act('block-off'); });
addEventListener('blur', () => { keys.clear(); act('block-off'); });
document.addEventListener('visibilitychange', () => { if (document.hidden) enc.disconnect(); });   // tab hidden: the rabbit disengages
canvas.addEventListener('contextmenu', e => e.preventDefault());
let drag = null;
canvas.addEventListener('pointerdown', e => {
  sfx.unlock();
  if (e.pointerType === 'mouse' && e.button === 2) { act('block-on'); return; }
  if (e.pointerType === 'mouse' && e.button === 0 && !e.shiftKey) { drag = { id: e.pointerId, x: e.clientX, y: e.clientY, moved: 0 }; canvas.setPointerCapture(e.pointerId); return; }
  drag = { id: e.pointerId, x: e.clientX, y: e.clientY, moved: 0 }; canvas.setPointerCapture(e.pointerId);
});
canvas.addEventListener('pointermove', e => {
  if (!drag || drag.id !== e.pointerId) return;
  const dx = e.clientX - drag.x, dy = e.clientY - drag.y; drag.moved += Math.abs(dx) + Math.abs(dy);
  camYaw -= dx * 0.005; camPitch = THREE.MathUtils.clamp(camPitch + dy * 0.003, 0.05, 0.9); drag.x = e.clientX; drag.y = e.clientY;
});
canvas.addEventListener('pointerup', e => {
  if (e.pointerType === 'mouse' && e.button === 2) { act('block-off'); return; }
  if (drag && drag.moved < 6 && e.pointerType === 'mouse') act('attack');   // a click (not a drag) attacks
  drag = null;
});
{
  const el = $('stick'), knob = el.querySelector('i'); let id = null;
  const move = e => { const r = el.getBoundingClientRect(), dx = e.clientX - (r.left + r.width / 2), dy = e.clientY - (r.top + r.height / 2);
    const l = Math.min(1, Math.hypot(dx, dy) / (r.width / 2)), a = Math.atan2(dy, dx); stick = { x: Math.cos(a) * l, y: Math.sin(a) * l };
    knob.style.transform = `translate(${stick.x * 36}px, ${stick.y * 36}px)`; };
  el.addEventListener('pointerdown', e => { sfx.unlock(); id = e.pointerId; el.setPointerCapture(id); move(e); });
  el.addEventListener('pointermove', e => e.pointerId === id && move(e));
  const end = () => { id = null; stick = { x: 0, y: 0 }; knob.style.transform = ''; };
  el.addEventListener('pointerup', end); el.addEventListener('pointercancel', end);
  const hold = (btn, down, up) => { btn.addEventListener('pointerdown', e => { e.preventDefault(); sfx.unlock(); btn.classList.add('down'); btn.setPointerCapture(e.pointerId); down(); });
    for (const ev of ['pointerup', 'pointercancel']) btn.addEventListener(ev, () => { btn.classList.remove('down'); up?.(); }); };
  hold($('t-dodge'), () => act('dodge')); hold($('t-attack'), () => act('attack')); hold($('t-tech'), () => act('technique'));
  hold($('t-block'), () => act('block-on'), () => act('block-off')); hold($('t-use'), () => act('interact'));
}

/** soft lock-on: actions turn the player towards the rabbit when it is close, like most action games */
function faceRabbitIfNear() {
  const p = enc.player, r = enc.rabbit;
  if (Math.hypot(r.x - p.x, r.z - p.z) < 5 && r.state !== 'idle') enc.face(Math.atan2(r.x - p.x, r.z - p.z));
  else if (Math.hypot(DUMMY.x - p.x, DUMMY.z - p.z) < 2.4) enc.face(Math.atan2(DUMMY.x - p.x, DUMMY.z - p.z));   // practice target
}
let climbed = false;   // on the A10 watch platform deck: a safe vantage point, no movement until climbing down
function setClimbed(on) {
  climbed = on;
  const p = enc.player;
  if (on) { p.x = PLATFORM.x; p.z = PLATFORM.z; enc.world.safeZones = [{ x: PLATFORM.x, z: PLATFORM.z, r: 1.2 }]; camPitch = 0.55; }
  else { p.x = PLATFORM.ladder.x + 0.4; p.z = PLATFORM.ladder.z; enc.world.safeZones = []; camPitch = 0.32; }
  sfx.tick(on);
}
function act(kind) {
  if (kind === 'interact') {
    const p = enc.player;
    if (climbed) setClimbed(false);
    else if (Math.hypot(p.x - PLATFORM.ladder.x, p.z - PLATFORM.ladder.z) < 1.3) setClimbed(true);
    return;
  }
  if (climbed && kind !== 'block-off') return;
  if (kind === 'dodge') { if (enc.dodge()) sfx.whoosh(0.8); }
  else if (kind === 'attack' || kind === 'technique') { faceRabbitIfNear(); enc.attack(kind === 'technique' ? 'technique' : 'basic'); }
  else if (kind === 'block-on') { faceRabbitIfNear(); enc.setBlock(true); }
  else if (kind === 'block-off') enc.setBlock(false);
}

// ------------------------------------------------------------------ feedback
let toastTimer = 0;
function toast(text, kind = 'info', sub = '') {
  const t = $('toast'); if (!text && !sub) return;
  t.innerHTML = `${text}${sub ? `<small>${sub}</small>` : ''}`; t.className = `toast ${kind}`; void t.offsetWidth; t.classList.add('show');
}
function flash(kind) { const f = $('flash'); f.className = kind; clearTimeout(toastTimer); toastTimer = setTimeout(() => (f.className = ''), 160); }
let shake = 0, hitStop = 0, slowMo = 0;
const STATE_LABEL = { idle: '', alert: '警戒・豎耳踏地', windup: '預備・壓低後蹬', charge: '衝刺', stagger: '硬直・破綻', retreat: '撤退' };
const RETREAT_TEXT = { 'safe-point': '你回到安全點，山兔退回洞裡', 'left-area': '你離開了遭遇範圍，山兔回洞', 'lost-sight': '山兔看不見你了，回洞去', disconnect: '畫面中斷：山兔脫離遭遇，沒有扣血', defeated: '山兔被驅離', 'player-down': '山兔退開了' };
let alertThump = 0;
function handle(ev) {
  const r = enc.rabbit, p = enc.player;
  switch (ev.type) {
    case 'state':
      if (ev.state === 'alert') { sfx.thump(); alertThump = 0.9; }
      if (ev.state === 'windup') { sfx.scrape(); puff(r.x, groundY(r.x, r.z), r.z, 0.5); }
      if (ev.state === 'charge') sfx.whoosh(1.2);
      break;
    case 'dodged': toast('閃過', 'good', '在無敵時間內穿過衝刺'); slowMo = 0.25; break;
    case 'blocked': sfx.clack(0.8); toast('擋下', 'good', style === 'body' ? '穩架接住，破綻較長' : '架開衝勢'); shake = 0.06; break;
    case 'parry': sfx.clack(1); sfx.chime(1.4); toast(style === 'body' ? '穩架' : '精準格擋', 'good', '時機正好，山兔失衡更久'); flash('parry'); hitStop = 0.09; break;
    case 'player-hit': sfx.thud(); flash('on'); shake = 0.22; toast('受擊', 'bad', ev.reason); break;
    case 'rabbit-hit': sfx.clack(1); hitStop = 0.07; shake = 0.07; toast(ev.kind === 'technique' ? '看破綻' : '命中', 'good', ev.kind === 'technique' ? '劍式在破綻中加倍' : '趁硬直出手'); play('Hit', { once: true }); break;
    case 'whiff': toast('揮空', 'info', ev.reason); break;
    case 'guard-broken': toast('架勢散亂', 'bad', '連按防禦反而站不穩'); break;
    case 'stagger': puff(r.x, groundY(r.x, r.z), r.z, ev.cause === 'wall' ? 1.2 : 0.6); if (ev.cause === 'wall') { sfx.thud(); toast('撞上障礙', 'good', '引牠撞樹撞石，破綻最長'); } break;
    case 'retreat': $('prompt').textContent = RETREAT_TEXT[ev.reason] || '山兔撤退'; break;
    case 'dummy-hit':
      sfx.clack(0.7); shake = 0.04; puff(DUMMY.x, 1.0, DUMMY.z, 0.3, 0x9c8a4e);
      toast(ev.kind === 'technique' ? '試招' : '擊中藤靶', 'good', ev.worn ? '藤靶外皮破了，可以換新再練' : `累計 ${ev.total} 點`);
      if (ev.worn && dummyModels.worn) { dummyModels.intact.visible = false; dummyModels.worn.visible = true; }
      break;
    case 'won': showResult(true); break;
    case 'downed': showResult(false); break;
    case 'reset': break;
  }
}
function showResult(won) {
  const s = enc.snapshot().stats;
  $('result-kind').textContent = `遭遇結果 · ${style === 'sword' ? '劍・看破綻' : '體・穩架'}`;
  $('result-title').textContent = won ? '驅離山兔' : '退回安全點';
  $('result-detail').textContent = `閃過 ${s.dodged}、格擋 ${s.blocked}、精準 ${s.parried}、命中 ${s.hitsLanded}、揮空 ${s.whiffs}、受擊 ${s.hitsTaken}。` +
    (won ? '讀到預備動作就閃或擋，牠硬直時再出手。' : '先看清「壓低後蹬」，再往側面閃，或面向牠格擋。');
  setTimeout(() => { $('result').hidden = false; }, 900);
}

// ------------------------------------------------------------------ frame
function resize() { renderer.setSize(innerWidth, innerHeight, false); camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); }
const camera = new THREE.PerspectiveCamera(COARSE ? 62 : 55, 1, 0.05, 400);
addEventListener('resize', resize); resize();
let last = performance.now(), acc = 0, attackAnim = 0;
const camPos = new THREE.Vector3(), tmp = new THREE.Vector3(), tmp2 = new THREE.Vector3(), camRay = new THREE.Raycaster();

function frame(ms) {
  let dt = Math.min((ms - last) / 1000, 0.05); last = ms; wind.value = ms / 1000;
  if (hitStop > 0) { hitStop -= dt; dt = 0; }
  if (slowMo > 0) { slowMo -= dt; dt *= 0.35; }
  // input: camera-relative movement
  let f = (keys.has('KeyW') ? 1 : 0) - (keys.has('KeyS') ? 1 : 0) - stick.y, rgt = (keys.has('KeyD') ? 1 : 0) - (keys.has('KeyA') ? 1 : 0) + stick.x;
  const l = Math.hypot(f, rgt); if (l > 1) { f /= l; rgt /= l; }
  const fx = Math.sin(camYaw), fz = Math.cos(camYaw);  // camera forward on the ground; right = (-fz, fx)
  const vx = fx * f - fz * rgt, vz = fz * f + fx * rgt;
  if (autoMove) enc.move(autoMove[0], autoMove[1]); else enc.move(vx, vz);
  if (!autoMove && Math.hypot(vx, vz) > 0.1 && !enc.player.blocking && !enc.player.attackT) enc.face(Math.atan2(vx, vz));
  if (enc.player.blocking) faceRabbitIfNear();
  acc += dt;
  while (acc >= DT) { enc.step(DT); acc -= DT; }
  for (const ev of enc.drainEvents()) { handle(ev); eventLog.push(ev); if (eventLog.length > 200) eventLog.shift(); }
  const s = enc.snapshot();
  // player visual
  if (climbed) enc.move(0, 0);
  const p = s.player, py = climbed ? PLATFORM.deck : groundY(p.x, p.z);
  player.position.set(p.x, py, p.z); player.rotation.y = p.heading;
  const u = player.userData;
  u.sword.visible = style === 'sword';
  u.armL.rotation.set(p.blocking ? -1.3 : 0, 0, p.blocking ? 0.5 : 0.1);
  u.armR.rotation.set(p.blocking ? -1.3 : 0, 0, p.blocking ? -0.5 : -0.1);
  if (p.attacking) { attackAnim += dt * 9; u.armR.rotation.set(-1.6 + Math.sin(attackAnim) * 1.4, 0, -0.3); } else attackAnim = 0;
  u.body.rotation.x = p.dodging ? 0.35 : 0;
  player.scale.y = p.dodging ? 0.85 : 1;
  // rabbit visual: the five states read from pose, motion, dust and sound
  const r = s.rabbit, ry = groundY(r.x, r.z);
  rabbitRoot.position.set(r.x, ry, r.z); rabbitRoot.rotation.set(0, r.heading, 0);
  rabbit.scale.set(1, 1, 1); rabbit.rotation.set(0, 0, 0); rabbit.position.set(0, 0, 0);
  scuff.material.opacity = 0;
  if (r.state === 'idle') { play('Idle'); rabbit.position.y = -0.38; }
  else if (r.state === 'alert') { play('Idle', { speed: 1.4 }); alertThump -= dt; if (alertThump <= 0) { sfx.thump(); alertThump = 1.1; puff(r.x, ry, r.z, 0.25); } }
  else if (r.state === 'windup') {
    play('Idle', { speed: 2.2 });
    const k = Math.min(1, r.t / 0.25);
    rabbit.scale.set(1 + 0.08 * k, 1 - 0.2 * k, 1 + 0.05 * k); rabbit.rotation.x = -0.18 * k; rabbit.position.z = -0.12 * k;
    rabbit.position.x = Math.sin(ms * 0.08) * 0.015;
    scuff.position.set(r.x, ry + 0.02, r.z); scuff.rotation.y = r.heading; scuff.material.opacity = Math.min(0.85, r.t / (r.t + r.windupLeft));
  } else if (r.state === 'charge') { play('Hop', { speed: 2.6 }); rabbit.rotation.x = 0.12; }
  else if (r.state === 'stagger') { if (current !== clips.Hit || !clips.Hit.isRunning()) play('Idle', { speed: 0.6 }); rabbit.rotation.z = Math.sin(ms * 0.012) * 0.18; }
  else if (r.state === 'retreat') play('Flee', { speed: 1.3 });
  mixer.update(dt);
  tickDust(dt);
  // HUD
  const rs = $('rabbit-state'); rs.textContent = $('show-tells').checked ? (STATE_LABEL[r.state] + (r.openingLeft != null ? ` ${r.openingLeft.toFixed(1)}s` : '')) : '';
  rs.className = `rstate ${r.state}`;
  document.querySelectorAll('#hp i').forEach((el, i) => el.classList.toggle('off', i >= p.hp));
  $('dodge-cd').classList.toggle('wait', !p.dodgeReady); $('guard').classList.toggle('broken', p.guardBroken);
  $('guard').textContent = p.guardBroken ? '架勢散亂' : p.blocking ? '格擋中' : '架勢';
  const nearLadder = Math.hypot(p.x - PLATFORM.ladder.x, p.z - PLATFORM.ladder.z) < 1.3, nearDummy = Math.hypot(p.x - DUMMY.x, p.z - DUMMY.z) < 2.2;
  if (climbed) $('prompt').textContent = '觀察台上：看清兔徑、凹地與退路，山兔碰不到你。E 下來';
  else if (nearLadder && r.state === 'idle') $('prompt').textContent = 'E／互動：爬上觀察台';
  else if (nearDummy && r.state === 'idle') $('prompt').textContent = '戰前試招：對藤靶 左鍵／J 攻擊，Q 試招';
  else if (r.state === 'idle' && !s.outcome) {
    const d = Math.hypot(p.x - BURROW.x, p.z - BURROW.z);
    $('prompt').textContent = Math.hypot(p.x - SAFE.x, p.z - SAFE.z) < PARAMS.safeRadius ? '安全點：山兔不會追到這裡' : d > 9 ? '沿兔徑往林間凹地走，留意動靜' : '凹地裡有兔洞…放輕腳步，或繞到石後觀察';
  } else if (r.state === 'alert') $('prompt').textContent = '山兔發現你了：可以躲到石後，或站穩準備';
  else if (r.state === 'windup') $('prompt').textContent = '牠壓低身子後蹬：往側面閃，或面向牠格擋';
  else if (r.state === 'stagger') $('prompt').textContent = '牠失衡了：靠近出手（左鍵／J，Q 試招）';
  // camera: third person, behind and above the stand-in
  // Engaged: swing the camera so the rabbit stays in frame beside the stand-in (over-the-shoulder), never behind it.
  const engaged = ['alert', 'windup', 'charge', 'stagger'].includes(r.state) && Math.hypot(r.x - p.x, r.z - p.z) < 9;
  if (engaged && !drag) {
    const want = Math.atan2(r.x - p.x, r.z - p.z);
    camYaw += Math.atan2(Math.sin(want - camYaw), Math.cos(want - camYaw)) * Math.min(1, dt * 3);
  }
  const fwdX = Math.sin(camYaw), fwdZ = Math.cos(camYaw), rightX = -fwdZ, rightZ = fwdX;
  const dist = engaged ? 5.4 : 4.8, pitch = engaged ? Math.max(camPitch, 0.42) : camPitch;
  // camera collision: pull in along the view ray if a wall, roof or rock is between the stand-in and the camera;
  // when the right shoulder is blocked close in (e.g. between the shelter's side walls), try the left or a narrower shoulder
  const place = shoulder => {
    const t = new THREE.Vector3(p.x + rightX * shoulder, py + 1.2, p.z + rightZ * shoulder);
    if (engaged) t.lerp(new THREE.Vector3(r.x, ry + 0.4, r.z), 0.35);
    if (shoulder) {           // the shoulder point itself must not be inside a wall
      const head = new THREE.Vector3(p.x, py + 1.2, p.z), toT = t.clone().sub(head);
      camRay.set(head, toT.clone().normalize()); camRay.far = toT.length() + 0.3;
      if (camRay.intersectObjects(occluders, true).length) return { t, c: t.clone(), free: -1 };
    }
    const c = new THREE.Vector3(t.x - fwdX * dist * Math.cos(pitch), t.y + Math.sin(pitch) * dist, t.z - fwdZ * dist * Math.cos(pitch));
    camRay.set(t, tmp2.copy(c).sub(t).normalize()); camRay.far = c.distanceTo(t);
    const block = camRay.intersectObjects(occluders, true)[0];
    const free = block ? block.distance - 0.25 : dist;
    if (block) c.copy(t).addScaledVector(camRay.ray.direction, Math.max(0.15, free));
    return { t, c, free };
  };
  let view = place(0.75);
  for (const s of [-0.75, 0.35, -0.35, 0]) {
    if (view.free >= 1.2) break;
    const alt = place(s); if (alt.free > view.free + 0.05) view = alt;
  }
  const target = tmp.copy(view.t);
  camPos.copy(view.c);
  if (shake > 0) { shake = Math.max(0, shake - dt * 0.8); camPos.x += (Math.random() - 0.5) * shake; camPos.y += (Math.random() - 0.5) * shake; }
  camera.position.lerp(camPos, Math.min(1, dt * 10 || 1)); camera.lookAt(target);
  sun.position.set(p.x + SUN_DIR.x * 40, SUN_DIR.y * 40, p.z + SUN_DIR.z * 40); sun.target.position.set(p.x, 0, p.z);
  renderer.render(scene, camera);
  requestAnimationFrame(frame);
}
const R_WINDUP = PARAMS.rabbit.windup;
camera.position.set(START.x, 2.5, START.z - 4.4);
requestAnimationFrame(frame);

// Debug / capture hook (local only).
globalThis.__enc = {
  get enc() { return enc; }, act, restart, setStyle, get climbed() { return climbed; },
  autoMove(v) { autoMove = v; },
  events: () => eventLog.slice(),
  teleport(x, z, yawDeg = 0) { enc.player.x = x; enc.player.z = z; camYaw = THREE.MathUtils.degToRad(yawDeg); },
  look(yawDeg, pitch = 0.32) { camYaw = THREE.MathUtils.degToRad(yawDeg); camPitch = pitch; },
  state: () => enc.snapshot(),
};
