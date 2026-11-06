import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { BreathSession, BlockSession, SIDE_LABEL, NO_ROOT_MESSAGE, WINDOW } from './practice.mjs';
import { Sfx } from './audio.mjs';

const $ = id => document.getElementById(id);
const COARSE = matchMedia('(pointer: coarse)').matches;
const EYE = 1.7;
const sfx = new Sfx();

// ------------------------------------------------------------------ renderer, sky, light
const canvas = $('world');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(devicePixelRatio, COARSE ? 1.5 : 1.75));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

const scene = new THREE.Scene();
const HORIZON = new THREE.Color('#c9d6cf');
scene.fog = new THREE.FogExp2(HORIZON, 0.0085);
const SUN_DIR = new THREE.Vector3(-0.55, 0.62, 0.56).normalize();

const sky = new THREE.Mesh(new THREE.SphereGeometry(420, 32, 16), new THREE.ShaderMaterial({
  side: THREE.BackSide, depthWrite: false, fog: false,
  uniforms: { sun: { value: SUN_DIR }, top: { value: new THREE.Color('#5f8fb0') }, hor: { value: HORIZON },
    warm: { value: new THREE.Color('#f3d9a8') } },
  vertexShader: 'varying vec3 vDir; void main(){ vDir = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
  fragmentShader: `varying vec3 vDir; uniform vec3 sun, top, hor, warm;
    void main(){ float h = clamp(vDir.y, -0.2, 1.0);
      vec3 c = mix(hor, top, pow(max(h,0.0), 0.55));
      float s = max(dot(normalize(vDir), sun), 0.0);
      c += warm * (pow(s, 6.0) * 0.35 + pow(s, 400.0) * 2.0);
      c = mix(c, hor * 0.92, smoothstep(0.0, -0.2, h));
      gl_FragColor = vec4(c, 1.0); }`,
}));
sky.renderOrder = -1;
scene.add(sky);

const hemi = new THREE.HemisphereLight(0xd6e6ee, 0x5b5232, 1.15);
scene.add(hemi);
const sun = new THREE.DirectionalLight(0xffe2b8, 3.0);
sun.position.copy(SUN_DIR).multiplyScalar(40);
sun.castShadow = true;
sun.shadow.mapSize.set(COARSE ? 1024 : 2048, COARSE ? 1024 : 2048);
Object.assign(sun.shadow.camera, { left: -16, right: 16, top: 16, bottom: -16, near: 1, far: 90 });
sun.shadow.bias = -0.0004;
sun.shadow.normalBias = 0.03;
scene.add(sun, sun.target);

// Image-based light from the same sky so PBR atlases read correctly (not just direct light).
{
  const pm = new THREE.PMREMGenerator(renderer);
  const envScene = new THREE.Scene();
  envScene.add(sky.clone());
  const ground = new THREE.Mesh(new THREE.CircleGeometry(300, 24), new THREE.MeshBasicMaterial({ color: 0x4a5236 }));
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = -2;
  envScene.add(ground);
  scene.environment = pm.fromScene(envScene, 0.04).texture;
  scene.environmentIntensity = 0.55;
}

// ------------------------------------------------------------------ ground, path, grass, backdrop
function rand(seed) { let s = seed >>> 0; return () => ((s = (1664525 * s + 1013904223) >>> 0) / 2 ** 32); }
function canvasTexture(size, paint, repeat) {
  const c = document.createElement('canvas');
  c.width = c.height = size;
  paint(c.getContext('2d'), size);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(repeat, repeat);
  t.anisotropy = 4;
  return t;
}
const grassTex = canvasTexture(256, (g, n) => {
  const r = rand(11);
  g.fillStyle = '#5d6b3a'; g.fillRect(0, 0, n, n);
  for (let i = 0; i < 2600; i++) {
    const v = r();
    g.fillStyle = v < 0.5 ? `rgba(${70 + r() * 30},${92 + r() * 30},${44 + r() * 14},.55)` : `rgba(${110 + r() * 30},${110 + r() * 20},${60 + r() * 20},.35)`;
    g.fillRect(r() * n, r() * n, 1 + r() * 3, 1 + r() * 3);
  }
}, 60);
// Ground: flat around the yard, gentle swells further out.
const groundGeo = new THREE.PlaneGeometry(320, 320, 160, 160);
groundGeo.rotateX(-Math.PI / 2);
{
  const p = groundGeo.attributes.position;
  const col = new Float32Array(p.count * 3);
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i), z = p.getZ(i), d = Math.hypot(x, z * 0.8);
    const swell = Math.min(1, Math.max(0, d - 24) / 60);
    p.setY(i, swell * swell * (3.2 + Math.sin(x * 0.07) * 1.6 + Math.cos(z * 0.05 + 1.3) * 1.2) - 0.01);
    const k = 0.85 + 0.15 * Math.sin(x * 0.21 + z * 0.17) * Math.cos(z * 0.11);
    col[i * 3] = k; col[i * 3 + 1] = k * 1.02; col[i * 3 + 2] = k * 0.95;
  }
  groundGeo.setAttribute('color', new THREE.BufferAttribute(col, 3));
  groundGeo.computeVertexNormals();
}
const ground = new THREE.Mesh(groundGeo, new THREE.MeshStandardMaterial({ map: grassTex, vertexColors: true, roughness: 1 }));
ground.receiveShadow = true;
scene.add(ground);

// Dirt path from the village gate to the steps (Blender -Y front == three +Z).
const PATH = [[0.3, 22], [0.9, 17], [0.4, 12], [-0.2, 8], [0, 4.4], [0, 3.05]];
const pathCurve = new THREE.CatmullRomCurve3(PATH.map(([x, z]) => new THREE.Vector3(x, 0, z)));
{
  const dirt = canvasTexture(256, (g, n) => {
    const r = rand(5);
    g.fillStyle = '#8a7656'; g.fillRect(0, 0, n, n);
    for (let i = 0; i < 1800; i++) { g.fillStyle = `rgba(${90 + r() * 70},${75 + r() * 55},${50 + r() * 40},.5)`; g.beginPath(); g.arc(r() * n, r() * n, r() * 2.5, 0, 7); g.fill(); }
  }, 1);
  const segs = 60, w = 1.9, pos = [], uv = [], idx = [];
  for (let i = 0; i <= segs; i++) {
    const t = i / segs, c = pathCurve.getPoint(t), tan = pathCurve.getTangent(t), side = new THREE.Vector3(-tan.z, 0, tan.x);
    const ww = w * (i === segs ? 1.0 : 1 + 0.12 * Math.sin(i * 1.7));
    for (const s of [-1, -0.6, 0.6, 1]) { const q = c.clone().addScaledVector(side, s * ww); pos.push(q.x, 0.006, q.z); uv.push((s + 1) / 2, t * 12); }
    if (i < segs) for (let k = 0; k < 3; k++) { const a = i * 4 + k; idx.push(a, a + 4, a + 1, a + 1, a + 4, a + 5); }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(idx); g.computeVertexNormals();
  const alpha = canvasTexture(64, (c, n) => { const gr = c.createLinearGradient(0, 0, n, 0);
    gr.addColorStop(0, 'rgba(0,0,0,0)'); gr.addColorStop(0.25, '#fff'); gr.addColorStop(0.75, '#fff'); gr.addColorStop(1, 'rgba(0,0,0,0)');
    c.fillStyle = gr; c.fillRect(0, 0, n, n); }, 1);
  alpha.colorSpace = THREE.NoColorSpace;
  const path = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ map: dirt, alphaMap: alpha, transparent: true, depthWrite: false, roughness: 1, side: THREE.DoubleSide }));
  dirt.repeat.set(1, 1);
  path.receiveShadow = true;
  scene.add(path);
}

// Shared sun-time uniform for wind.
const wind = { value: 0 };
function addWind(mat, strength, keepNormal = false) {
  mat.onBeforeCompile = sh => {
    sh.uniforms.uTime = wind;
    // Foliage cards keep their up-facing normal on both sides (no dark back faces).
    if (keepNormal) sh.fragmentShader = sh.fragmentShader.replace('#include <normal_fragment_begin>', 'vec3 normal = normalize( vNormal ); vec3 nonPerturbedNormal = normal;');
    sh.vertexShader = 'uniform float uTime;\n' + sh.vertexShader.replace('#include <begin_vertex>', `#include <begin_vertex>
      vec4 wp = instanceMatrix * vec4(0.0,0.0,0.0,1.0);
      float h = max(position.y, 0.0);
      float sway = sin(uTime*1.6 + wp.x*0.35 + wp.z*0.22) * 0.6 + sin(uTime*3.1 + wp.x*1.3) * 0.25;
      transformed.x += sway * h * h * ${strength.toFixed(3)};
      transformed.z += sway * h * h * ${(strength * 0.5).toFixed(3)};`);
  };
}

// Instanced grass clumps: three crossed alpha-tested cards with painted blades (kept off the path, plinth, slab).
{
  const tex = canvasTexture(256, (g, n) => {
    const r = rand(9);
    g.clearRect(0, 0, n, n);
    for (let i = 0; i < 42; i++) {
      const x = 14 + r() * (n - 28), h = n * (0.35 + r() * 0.6), lean = (r() - 0.5) * 70, w = 2 + r() * 3.5;
      const grd = g.createLinearGradient(0, n, 0, n - h);
      const hue = 72 + r() * 22, sat = 32 + r() * 18;
      grd.addColorStop(0, `hsl(${hue},${sat}%,${20 + r() * 6}%)`);
      grd.addColorStop(0.6, `hsl(${hue},${sat + 6}%,${34 + r() * 10}%)`);
      grd.addColorStop(1, `hsl(${hue - 14},${sat}%,${52 + r() * 14}%)`);
      g.fillStyle = grd;
      g.beginPath(); g.moveTo(x - w, n); g.quadraticCurveTo(x - w * 0.3 + lean * 0.4, n - h * 0.55, x + lean, n - h);
      g.quadraticCurveTo(x + w * 0.3 + lean * 0.4, n - h * 0.55, x + w, n); g.fill();
    }
  }, 1);
  const quad = new THREE.PlaneGeometry(0.5, 0.34, 1, 2);
  quad.translate(0, 0.17, 0);
  const parts = [0, 1, 2].map(k => quad.clone().rotateY((k * Math.PI) / 3));
  const pos = [], uv = [], idx = [];
  for (const g of parts) {
    const base = pos.length / 3;
    pos.push(...g.attributes.position.array); uv.push(...g.attributes.uv.array);
    idx.push(...Array.from(g.index.array, v => v + base));
  }
  const clump = new THREE.BufferGeometry();
  clump.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  clump.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  // Up-facing normals: cards shade like the meadow instead of flashing when seen edge-on.
  clump.setAttribute('normal', new THREE.Float32BufferAttribute(Array.from({ length: pos.length / 3 }, () => [0, 1, 0]).flat(), 3));
  clump.setIndex(idx);
  const mat = new THREE.MeshStandardMaterial({ map: tex, alphaTest: 0.45, side: THREE.DoubleSide, roughness: 0.95 });
  addWind(mat, 0.55, true);
  const N = COARSE ? 7000 : 17000;
  const mesh = new THREE.InstancedMesh(clump, mat, N);
  const r = rand(77), m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), sc = new THREE.Vector3(), p = new THREE.Vector3(), c = new THREE.Color();
  const pathPts = pathCurve.getSpacedPoints(80);
  let n = 0;
  for (let i = 0; i < N * 4 && n < N; i++) {
    const a = r() * Math.PI * 2, d = 2 + Math.sqrt(r()) * 36, x = Math.cos(a) * d, z = Math.sin(a) * d * 1.1 + 2;
    if (Math.abs(x) < 3.5 && z > -2.7 && z < 3.2) continue;
    if (Math.hypot((x + 4.6) / 1.05, (z + 0.2) / 0.88) < 1) continue;
    const dp = Math.min(...pathPts.map(pp => Math.hypot(pp.x - x, pp.z - z)));
    if (dp < 1.0 || (dp < 1.6 && r() < 0.6)) continue;
    p.set(x, 0, z);
    q.setFromAxisAngle(new THREE.Vector3(0, 1, 0), r() * Math.PI);
    const k = 0.7 + r() * 0.7;
    sc.set(k, k * (0.75 + r() * 0.6), k);
    m4.compose(p, q, sc);
    mesh.setMatrixAt(n, m4);
    c.setHSL(0.20 + r() * 0.06, 0.22 + r() * 0.2, 0.70 + r() * 0.22);
    mesh.setColorAt(n, c);
    n++;
  }
  mesh.count = n;
  mesh.receiveShadow = true;
  scene.add(mesh);
}

// Stylised trees and distant ridges for depth (procedural, local to this demo).
{
  const r = rand(31);
  const trunkGeo = new THREE.CylinderGeometry(0.12, 0.2, 2.4, 6); trunkGeo.translate(0, 1.2, 0);
  const crownGeo = new THREE.ConeGeometry(1.4, 3.2, 7); crownGeo.translate(0, 3.6, 0);
  const crown2 = new THREE.ConeGeometry(1.0, 2.4, 7); crown2.translate(0, 5.0, 0);
  const trunks = new THREE.InstancedMesh(trunkGeo, new THREE.MeshStandardMaterial({ color: 0x3b2a1d, roughness: 1 }), 70);
  const crowns = new THREE.InstancedMesh(crownGeo, new THREE.MeshStandardMaterial({ color: 0x2f4a2e, roughness: 0.95 }), 70);
  const crownsTop = new THREE.InstancedMesh(crown2, new THREE.MeshStandardMaterial({ color: 0x38563a, roughness: 0.95 }), 70);
  const m = new THREE.Matrix4(); let n = 0;
  for (let i = 0; i < 400 && n < 70; i++) {
    const a = r() * Math.PI * 2, d = 16 + r() * 34, x = Math.cos(a) * d, z = Math.sin(a) * d;
    if (z > 6 && Math.abs(x) < 9) continue; // keep the view from the village gate open
    const k = 0.8 + r() * 0.7;
    m.compose(new THREE.Vector3(x, 0, z), new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), r() * 6), new THREE.Vector3(k, k * (0.9 + r() * 0.4), k));
    trunks.setMatrixAt(n, m); crowns.setMatrixAt(n, m); crownsTop.setMatrixAt(n, m); n++;
  }
  for (const im of [trunks, crowns, crownsTop]) { im.count = n; im.castShadow = true; scene.add(im); }
  for (let layer = 0; layer < 3; layer++) {
    const pts = [], R = 150 + layer * 45;
    for (let i = 0; i <= 96; i++) {
      const a = (i / 96) * Math.PI * 2, h = 6 + layer * 7 + 4 * Math.sin(a * 5 + layer) + 3 * Math.sin(a * 13 + layer * 2) + 2 * Math.sin(a * 29) + (a > 4.2 && a < 5.4 ? 10 : 0);
      pts.push(Math.cos(a) * R, -3, Math.sin(a) * R, Math.cos(a) * R, h, Math.sin(a) * R);
    }
    const idx = [];
    for (let i = 0; i < 96; i++) { const k = i * 2; idx.push(k, k + 2, k + 1, k + 1, k + 2, k + 3); }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3)); g.setIndex(idx);
    // Aerial perspective: nearer ridges darker and greener, far ones dissolve into the horizon haze.
    const ridge = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ color: new THREE.Color(['#4c6352', '#6f8577', '#9aaba2'][layer]).lerp(HORIZON, 0.15 + layer * 0.2), side: THREE.DoubleSide, fog: false }));
    scene.add(ridge);
  }
}

// ------------------------------------------------------------------ yard assets
const B2T = ({ x, y, z }) => new THREE.Vector3(x, z, -y);   // Blender (Z-up, -Y front) -> three
const PLACEMENT = [
  { id: 'training-shelter', x: 0, y: 0, z: 0 },
  { id: 'qi-striking-post', x: -2.0, y: 0.9, z: 0.30 },
  { id: 'agility-post', x: 2.0, y: 0.9, z: 0.30 },
  { id: 'weapon-rack', x: 0, y: 1.5, z: 0.30 },
  { id: 'engraved-training-stone', x: -4.6, y: 0.2, z: 0, yaw: 8 },
  { id: 'training-banner', x: 2.15, y: -3.45, z: 0 },
  { id: 'training-banner', x: -2.15, y: -3.45, z: 0 },
];
const STATIONS = {
  qi: { name: '氣勁木樁', post: B2T({ x: -2.0, y: 0.9, z: 0.30 }), stand: new THREE.Vector3(-1.75, 0, 0.75), look: new THREE.Vector3(-2.15, 1.45, -0.9) },
  body: { name: '身法木樁', post: B2T({ x: 2.0, y: 0.9, z: 0.30 }), stand: new THREE.Vector3(2.0, 0, 1.75), look: new THREE.Vector3(2.0, 1.02, -0.9) },
};
// circles (x, z, r) that the walker cannot enter
const OBSTACLES = [
  ...[-2.55, 2.55].flatMap(x => [-1.75, 1.75].map(z => [x, z, 0.32])),
  [-2.0, -0.9, 0.42], [2.0, -0.9, 0.62], [-0.7, -1.5, 0.3], [0, -1.5, 0.3], [0.7, -1.5, 0.3],
  [2.15, 3.45, 0.36], [-2.15, 3.45, 0.36], [-2.13, 17, 0.5], [2.13, 17, 0.5],
];

const loader = new GLTFLoader();
const nodes = {};
let loaded = 0;
const TOTAL = 7;
function progress() { loaded++; $('load-text').textContent = `載入模型 ${loaded}/${TOTAL}`; $('load-bar').style.setProperty('--p', `${(loaded / TOTAL) * 100}%`); }
const cache = {};
async function glb(url) { return (cache[url] ||= loader.loadAsync(url)); }

await Promise.all([
  ...PLACEMENT.map(async item => {
    const g = await glb(`./assets/${item.id}.glb`);
    const root = g.scene.clone(true);
    root.position.copy(B2T(item));
    root.rotation.y = THREE.MathUtils.degToRad(item.yaw || 0);
    root.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
    scene.add(root);
    root.traverse(o => { for (const k of ['jade_disc', 'rope_band_1', 'rope_band_2', 'rope_band_3', 'arm_left', 'arm_right', 'arm_low', 'banner_cloth']) if (o.name.includes(`_${k}_`)) (nodes[k] ||= []).push(o); });
    progress();
  }),
  (async () => {
    try {
      const g = await glb('./world/village-gate-v13.glb');
      g.scene.position.set(0, 0, 17);
      g.scene.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
      scene.add(g.scene);
    } catch (e) { console.warn('village gate backdrop unavailable', e); }
  })(),
]).catch(e => { $('load-text').textContent = `模型載入失敗：${e.message}`; throw e; });
$('loading').classList.add('done');
setTimeout(() => ($('loading').hidden = true), 700);
for (const arm of ['arm_left', 'arm_right', 'arm_low']) for (const o of nodes[arm] || []) o.userData.rest = o.quaternion.clone();
for (const o of nodes.banner_cloth || []) o.userData.rest = o.quaternion.clone();

// ------------------------------------------------------------------ qi effects: band glow, disc glow, motes
const jadeGlow = new THREE.MeshBasicMaterial({ color: 0x5fe0bd, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false });
const qiBase = STATIONS.qi.post;
const bandGlows = [0.60, 0.88, 1.16].map(z => {
  const m = new THREE.Mesh(new THREE.TorusGeometry(0.215, 0.05, 8, 40), jadeGlow.clone());
  m.rotation.x = Math.PI / 2; m.position.set(qiBase.x, qiBase.y + z, qiBase.z); scene.add(m); return m;
});
const discGlow = new THREE.Mesh(new THREE.RingGeometry(0.084, 0.15, 40), jadeGlow.clone());  // halo around the jade disc
discGlow.position.set(qiBase.x, qiBase.y + 1.44, qiBase.z + 0.205);
scene.add(discGlow);
const MOTES = 140;
const moteGeo = new THREE.BufferGeometry();
const motePos = new Float32Array(MOTES * 3), moteSeed = new Float32Array(MOTES);
for (let i = 0; i < MOTES; i++) moteSeed[i] = Math.random();
moteGeo.setAttribute('position', new THREE.BufferAttribute(motePos, 3));
const moteTex = canvasTexture(64, (g, n) => { const gr = g.createRadialGradient(n / 2, n / 2, 0, n / 2, n / 2, n / 2);
  gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.3, 'rgba(160,255,220,.7)'); gr.addColorStop(1, 'rgba(0,0,0,0)'); g.fillStyle = gr; g.fillRect(0, 0, n, n); }, 1);
const motes = new THREE.Points(moteGeo, new THREE.PointsMaterial({ size: 0.045, map: moteTex, color: 0x9fffe0, transparent: true, opacity: 0,
  blending: THREE.AdditiveBlending, depthWrite: false }));
motes.frustumCulled = false;
scene.add(motes);
function updateMotes(t, strength, sync) {
  motes.material.opacity = strength;
  const c = discGlow.position;
  for (let i = 0; i < MOTES; i++) {
    const s = moteSeed[i], life = (t * (0.25 + s * 0.2) + s) % 1, k = sync > 0.6 ? life : life * 0.35;
    const ang = s * 40 + t * (0.6 + s) + life * 4, rad = (1 - k) * (0.6 + s * 0.9);
    motePos[i * 3] = c.x + Math.cos(ang) * rad;
    motePos[i * 3 + 1] = c.y + (s - 0.5) * 1.6 * (1 - k) + Math.sin(t * 2 + s * 9) * 0.05;
    motePos[i * 3 + 2] = c.z + Math.sin(ang) * rad * 0.7 + (1 - k) * 0.3;
  }
  moteGeo.attributes.position.needsUpdate = true;
}

// ------------------------------------------------------------------ block effects: sparks, approach markers
const SPARKS = 60;
const sparkGeo = new THREE.BufferGeometry();
const sparkPos = new Float32Array(SPARKS * 3), sparkVel = new Float32Array(SPARKS * 3);
sparkGeo.setAttribute('position', new THREE.BufferAttribute(sparkPos, 3));
const sparks = new THREE.Points(sparkGeo, new THREE.PointsMaterial({ size: 0.05, map: moteTex, color: 0xffd28a, transparent: true, opacity: 0,
  blending: THREE.AdditiveBlending, depthWrite: false }));
sparks.frustumCulled = false;
scene.add(sparks);
let sparkLife = 0;
function burst(at, color) {
  sparks.material.color.set(color);
  for (let i = 0; i < SPARKS; i++) {
    sparkPos.set([at.x, at.y, at.z], i * 3);
    const v = new THREE.Vector3(Math.random() - 0.5, Math.random() * 0.8, Math.random() - 0.2).normalize().multiplyScalar(1.5 + Math.random() * 2.5);
    sparkVel.set([v.x, v.y, v.z], i * 3);
  }
  sparkLife = 0.45;
}
function updateSparks(dt) {
  if (sparkLife <= 0) { sparks.material.opacity = 0; return; }
  sparkLife -= dt;
  for (let i = 0; i < SPARKS; i++) {
    sparkVel[i * 3 + 1] -= 6 * dt;
    for (let k = 0; k < 3; k++) sparkPos[i * 3 + k] += sparkVel[i * 3 + k] * dt;
  }
  sparks.material.opacity = Math.max(0, sparkLife / 0.45);
  sparkGeo.attributes.position.needsUpdate = true;
}
const ARM_TIP = { left: new THREE.Vector3(-0.48, 1.12 + 0.3, 0.3), right: new THREE.Vector3(0.48, 1.12 + 0.3, 0.3), low: new THREE.Vector3(0, 0.45 + 0.3, 0.52) };

// ------------------------------------------------------------------ camera + walking
const camera = new THREE.PerspectiveCamera(COARSE ? 68 : 62, 1, 0.05, 900);
const START = { x: 0.6, z: 14.5, yaw: 0 };
const player = { x: START.x, z: START.z, y: EYE, yaw: START.yaw, pitch: -0.03, vx: 0, vz: 0, bob: 0 };
const keys = new Set();
let stick = { x: 0, y: 0 };

function floorAt(x, z) {
  if (Math.abs(x) < 3.2 && z > -2.4 && z < 2.4) return 0.30;
  if (Math.abs(x) < 1.7 && z >= 2.4 && z < 2.7) return 0.20;
  if (Math.abs(x) < 1.7 && z >= 2.7 && z < 3.0) return 0.10;
  if (Math.hypot((x + 4.6) / 0.88, (z + 0.2) / 0.72) < 1) return 0.28;
  return 0;
}
function blocked(x, z) { return OBSTACLES.some(([ox, oz, r]) => Math.hypot(x - ox, z - oz) < r + 0.22) || Math.hypot(x, z - 2) > 42; }

const mode = { kind: 'walk', station: null, session: null, cam: null };
function setPose(pos, look) { camera.position.copy(pos); camera.lookAt(look); }

// ------------------------------------------------------------------ input
const alias = { ArrowUp: 'KeyW', ArrowDown: 'KeyS', ArrowLeft: 'KeyA', ArrowRight: 'KeyD' };
addEventListener('keydown', e => {
  sfx.unlock();
  if (e.target.tagName === 'INPUT') return;
  const k = alias[e.code] || e.code;
  if (['KeyW', 'KeyA', 'KeyS', 'KeyD', 'Space', 'KeyE', 'Escape'].includes(k)) e.preventDefault();
  if (mode.kind === 'qi' && k === 'Space') { holdDown(true); return; }
  if (mode.kind === 'body' && !e.repeat) {
    const side = { KeyA: 'left', KeyD: 'right', KeyS: 'low', KeyJ: 'left', KeyL: 'right', KeyK: 'low' }[k];
    if (side) { block(side, e.repeat); return; }
  }
  if (k === 'Escape') { leave(); return; }
  if (k === 'KeyE' && !e.repeat && mode.kind === 'walk') interact();
  keys.add(k);
});
addEventListener('keyup', e => {
  const k = alias[e.code] || e.code;
  keys.delete(k);
  if (k === 'Space' && mode.kind === 'qi') holdDown(false);
  document.querySelector(`.block[data-side="${{ KeyA: 'left', KeyD: 'right', KeyS: 'low' }[k]}"]`)?.classList.remove('pressed');
});
addEventListener('blur', () => { keys.clear(); if (mode.kind === 'qi') holdDown(false); });

let drag = null;
canvas.addEventListener('pointerdown', e => {
  sfx.unlock();
  if (mode.kind !== 'walk') return;
  drag = { id: e.pointerId, x: e.clientX, y: e.clientY };
  canvas.setPointerCapture(e.pointerId);
});
canvas.addEventListener('pointermove', e => {
  if (!drag || drag.id !== e.pointerId) return;
  player.yaw -= (e.clientX - drag.x) * 0.0042;
  player.pitch = THREE.MathUtils.clamp(player.pitch - (e.clientY - drag.y) * 0.0032, -0.9, 0.7);
  drag.x = e.clientX; drag.y = e.clientY;
});
canvas.addEventListener('pointerup', () => { drag = null; });
canvas.addEventListener('pointercancel', () => { drag = null; });
{
  const el = $('stick'), knob = el.querySelector('i');
  let id = null;
  const move = e => {
    const r = el.getBoundingClientRect(), dx = e.clientX - (r.left + r.width / 2), dy = e.clientY - (r.top + r.height / 2);
    const len = Math.min(1, Math.hypot(dx, dy) / (r.width / 2)), a = Math.atan2(dy, dx);
    stick = { x: Math.cos(a) * len, y: Math.sin(a) * len };
    knob.style.transform = `translate(${stick.x * 36}px, ${stick.y * 36}px)`;
  };
  el.addEventListener('pointerdown', e => { sfx.unlock(); id = e.pointerId; el.setPointerCapture(id); move(e); });
  el.addEventListener('pointermove', e => { if (e.pointerId === id) move(e); });
  const end = () => { id = null; stick = { x: 0, y: 0 }; knob.style.transform = ''; };
  el.addEventListener('pointerup', end); el.addEventListener('pointercancel', end);
}
$('interact').addEventListener('click', () => { sfx.unlock(); interact(); });

// identity
let hasRoots = true;
function setRoots(v) {
  hasRoots = v;
  $('root-yes').classList.toggle('on', v); $('root-no').classList.toggle('on', !v);
  $('root-yes').setAttribute('aria-pressed', v); $('root-no').setAttribute('aria-pressed', !v);
  if (mode.kind === 'qi') leave();
  if (!$('chooser').hidden) openChooser(mode.near || 'body');
}
$('root-yes').onclick = () => setRoots(true);
$('root-no').onclick = () => setRoots(false);
$('reset').onclick = () => { leave(); Object.assign(player, { x: START.x, z: START.z, yaw: START.yaw, pitch: -0.03 }); };

// ------------------------------------------------------------------ stations
function nearestStation() {
  let best = null;
  for (const [k, s] of Object.entries(STATIONS)) {
    const d = Math.hypot(player.x - s.post.x, player.z - s.post.z);
    if (d < 2.2 && (!best || d < best.d)) best = { k, d };
  }
  return best?.k || null;
}
function interact() {
  const k = nearestStation();
  if (k) openChooser(k);
}
function openChooser(k) {
  mode.near = k;
  $('chooser').hidden = false;
  $('chooser-title').textContent = `${STATIONS[k].name} · 選擇練功`;
  $('pick-qi').classList.toggle('recommended', k === 'qi');
  $('pick-body').classList.toggle('recommended', k === 'body');
  $('pick-qi').disabled = !hasRoots;
  $('qi-lock').textContent = hasRoots ? '已感應靈氣，可修習' : NO_ROOT_MESSAGE;
  $('prompt').hidden = true;
  document.body.classList.add('practicing');
}
$('pick-qi').onclick = () => start('qi');
$('pick-body').onclick = () => start('body');
document.querySelectorAll('[data-close]').forEach(b => b.addEventListener('click', leave));
$('again').onclick = () => start(mode.last);
$('switch').onclick = () => (mode.last === 'qi' || !hasRoots ? start('body') : start('qi'));

const now = () => performance.now() / 1000;
function start(kind) {
  if (kind === 'qi' && !hasRoots) return;
  sfx.unlock();
  $('chooser').hidden = true; $('result').hidden = true;
  $('qi-hud').hidden = kind !== 'qi'; $('body-hud').hidden = kind !== 'body';
  $('prompt').hidden = true;
  document.body.classList.add('practicing');
  mode.kind = kind; mode.last = kind; mode.station = STATIONS[kind];
  mode.session = kind === 'qi' ? new BreathSession({ hasRoots, start: now() }) : new BlockSession({ seed: 7 + Math.floor(Math.random() * 5), start: now() });
  mode.lastJudged = 0; mode.ticked = -1; mode.cycleSeen = 0; mode.hitStop = 0; mode.shake = 0;
  // glide the camera to the station's practice pose
  const st = mode.station;
  mode.cam = { from: camera.position.clone(), fromQ: camera.quaternion.clone(), t: 0,
    to: new THREE.Vector3(st.stand.x, floorAt(st.stand.x, st.stand.z) + EYE - 0.06, st.stand.z), look: st.look };
  Object.assign(player, { x: st.stand.x, z: st.stand.z });
  if (kind === 'qi') { sfx.breathStart(); $('vignette').className = 'qi'; }
  document.querySelectorAll('.cycles i').forEach(i => (i.className = ''));
}
function leave() {
  if (mode.kind === 'qi') sfx.breathStop();
  mode.kind = 'walk'; mode.session = null; mode.cam = null;
  for (const id of ['chooser', 'qi-hud', 'body-hud', 'result']) $(id).hidden = true;
  $('prompt').hidden = false; $('vignette').className = '';
  document.body.classList.remove('practicing');
  const look = new THREE.Vector3(); camera.getWorldDirection(look);
  player.yaw = Math.atan2(-look.x, -look.z); player.pitch = Math.asin(THREE.MathUtils.clamp(look.y, -1, 1));
  for (const g of [...bandGlows, discGlow]) g.material.opacity = 0;
  motes.material.opacity = 0;
  restArms();
}
function finish(state) {
  const card = $('result');
  if (state.mode === 'qi') {
    sfx.breathStop();
    const grades = state.cycleGrades.map(g => g.label).join('・');
    $('result-kind').textContent = '引氣呼吸 · 氣勁木樁';
    $('result-grade').textContent = state.harmonised === 3 ? '三息調和' : state.harmonised ? `${state.harmonised} 息調和` : '氣息未定';
    $('result-detail').textContent = `三息：${grades}。繩圈亮起代表該息跟上節奏；跟不上可再練一次。`;
  } else {
    $('result-kind').textContent = '武技格擋 · 身法木樁';
    $('result-grade').textContent = state.grade;
    $('result-detail').textContent = `擋下 ${state.blocked}/${state.total}（精準 ${state.perfect}），最高連擋 ${state.bestCombo}，散架 ${state.flinches} 次。`;
  }
  $('switch').textContent = state.mode === 'qi' ? '改練武技' : hasRoots ? '改練引氣' : '再練武技';
  $('qi-hud').hidden = true; $('body-hud').hidden = true;
  card.hidden = false;
  mode.kind = 'result';
}

// qi input
function holdDown(v) {
  if (mode.kind !== 'qi' || !mode.session) return;
  mode.session.setHeld(v);
  $('hold').classList.toggle('down', v);
}
{
  const h = $('hold');
  h.addEventListener('pointerdown', e => { e.preventDefault(); h.setPointerCapture(e.pointerId); holdDown(true); });
  for (const ev of ['pointerup', 'pointercancel', 'lostpointercapture']) h.addEventListener(ev, () => holdDown(false));
}

// block input
function block(side) {
  if (mode.kind !== 'body' || !mode.session) return;
  const btn = document.querySelector(`.block[data-side="${side}"]`);
  btn?.classList.add('pressed');
  setTimeout(() => btn?.classList.remove('pressed'), 120);
  const { judged } = mode.session.input(side, now());
  if (judged) showJudge(judged);
}
document.querySelectorAll('.block').forEach(b => b.addEventListener('pointerdown', e => { e.preventDefault(); block(b.dataset.side); }));
function showJudge(j) {
  const el = $('judge');
  const text = { perfect: '精準', good: '擋下', hit: '中招', flinch: '散架' }[j.result];
  el.textContent = j.result === 'hit' && j.reason ? `中招` : text;
  el.className = `judge ${j.result}`;
  void el.offsetWidth; el.classList.add('show');
  const tip = mode.station.post.clone().add(ARM_TIP[mode.session.snapshot().last?.side || 'left']);
  if (j.result === 'perfect' || j.result === 'good') {
    sfx.clack(j.result === 'perfect' ? 1 : 0.7);
    if (j.result === 'perfect') sfx.chime(1.5);
    burst(tip, j.result === 'perfect' ? 0xffe0a0 : 0xfff2dc);
    mode.hitStop = 0.07; mode.shake = 0.05;
  } else if (j.result === 'hit') {
    sfx.thud(); mode.shake = 0.14;
    const v = $('vignette'); v.className = 'hit'; setTimeout(() => (v.className = ''), 160);
  } else { sfx.tick(false); mode.shake = 0.03; }
  $('body-tip').textContent = j.result === 'hit' ? (j.reason || '中招，看清木臂後擺的方向') : j.result === 'flinch' ? '沒有來勢時別出手，架勢會散' : '保持節奏';
}

// ------------------------------------------------------------------ arm animation
function restArms() { for (const k of ['arm_left', 'arm_right', 'arm_low']) for (const o of nodes[k] || []) o.quaternion.copy(o.userData.rest); }
const Y_AXIS = new THREE.Vector3(0, 1, 0), X_AXIS = new THREE.Vector3(1, 0, 0), Z_AXIS = new THREE.Vector3(0, 0, 1);
function armPose(side, eta) {
  // eta: seconds until impact. Wind back from 0.65 s, swing through at 0, recover by -0.35 s.
  let a;
  if (eta > 0.65) a = 0;
  else if (eta > 0.12) a = THREE.MathUtils.smoothstep(0.65 - eta, 0, 0.53);
  else if (eta > 0) a = 1 - 1.8 * (1 - eta / 0.12);
  else a = THREE.MathUtils.lerp(-0.8, 0, THREE.MathUtils.clamp(-eta / 0.35, 0, 1));
  const node = nodes[`arm_${side}`]?.[0];
  if (!node) return;
  // Side arms lift (wind-up) and chop down through the block in the screen plane; the low arm pulls back and thrusts.
  const q = side === 'low' ? new THREE.Quaternion().setFromAxisAngle(X_AXIS, -0.5 * a) :
    new THREE.Quaternion().setFromAxisAngle(Z_AXIS, (side === 'left' ? -1 : 1) * 0.7 * a);
  node.quaternion.copy(node.userData.rest).premultiply(q);
}

// ------------------------------------------------------------------ frame loop
function resize() { renderer.setSize(innerWidth, innerHeight, false); camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); }
addEventListener('resize', resize);
resize();
let last = performance.now();
const tmp = new THREE.Vector3();

function frame(ms) {
  const dt = Math.min((ms - last) / 1000, 0.05);
  last = ms;
  const t = ms / 1000;
  wind.value = t;
  for (const o of nodes.banner_cloth || []) o.quaternion.copy(o.userData.rest).multiply(new THREE.Quaternion().setFromEuler(new THREE.Euler(0.05 * Math.sin(t * 1.3 + o.id), 0, 0.03 * Math.sin(t * 0.9 + o.id * 2))));

  if (mode.kind === 'walk' || mode.kind === 'result' || (mode.kind !== 'qi' && mode.kind !== 'body')) {
    if (mode.kind === 'walk' && $('chooser').hidden) {
      let f = (keys.has('KeyW') ? 1 : 0) - (keys.has('KeyS') ? 1 : 0) - stick.y;
      let r = (keys.has('KeyD') ? 1 : 0) - (keys.has('KeyA') ? 1 : 0) + stick.x;
      const len = Math.hypot(f, r);
      if (len > 1) { f /= len; r /= len; }
      const speed = keys.has('ShiftLeft') ? 4.2 : 2.6;
      const tx = (-Math.sin(player.yaw) * f + Math.cos(player.yaw) * r) * speed, tz = (-Math.cos(player.yaw) * f - Math.sin(player.yaw) * r) * speed;
      player.vx += (tx - player.vx) * Math.min(1, dt * 10); player.vz += (tz - player.vz) * Math.min(1, dt * 10);
      const nx = player.x + player.vx * dt, nz = player.z + player.vz * dt;
      if (!blocked(nx, player.z)) player.x = nx; else player.vx = 0;
      if (!blocked(player.x, nz)) player.z = nz; else player.vz = 0;
      const moving = Math.hypot(player.vx, player.vz);
      player.bob += moving * dt * 2.4;
      const targetY = floorAt(player.x, player.z) + EYE + Math.sin(player.bob * 2) * 0.025 * Math.min(1, moving / 2.6);
      player.y += (targetY - player.y) * Math.min(1, dt * 12);
      camera.position.set(player.x, player.y, player.z);
      camera.rotation.set(player.pitch, player.yaw, 0, 'YXZ');
      const near = nearestStation();
      const p = $('prompt');
      p.textContent = near ? `${STATIONS[near].name} · 按 E／互動 選擇練功` : player.z > 6 ? '沿土路走向演武棚' : '走近木樁開始練功';
      p.classList.toggle('ready', !!near);
    }
  } else {
    // practice camera: glide in, then hold with a tiny breathing drift
    const c = mode.cam;
    c.t = Math.min(1, c.t + dt / 0.9);
    const e = c.t * c.t * (3 - 2 * c.t);
    camera.position.lerpVectors(c.from, c.to, e);
    const look = new THREE.Matrix4().lookAt(c.to, c.look, Y_AXIS);
    camera.quaternion.slerpQuaternions(c.fromQ, new THREE.Quaternion().setFromRotationMatrix(look), e);
    if (mode.shake > 0) {
      mode.shake = Math.max(0, mode.shake - dt * 0.6);
      camera.position.add(tmp.set((Math.random() - 0.5) * mode.shake, (Math.random() - 0.5) * mode.shake, 0));
    }
    if (mode.kind === 'qi') updateQi(t, dt);
    else updateBlock(t, dt);
  }
  updateSparks(dt);
  renderer.render(scene, camera);
  requestAnimationFrame(frame);
}

function updateQi(t, dt) {
  const s = mode.session.update(now());
  const R = 26 + 62 * s.guide, Q = 18 + 70 * s.qi;
  $('guide').setAttribute('r', R.toFixed(1));
  $('qi-ring').setAttribute('r', Q.toFixed(1));
  $('phase').textContent = s.label;
  $('sync').firstElementChild.style.width = `${(s.sync * 100).toFixed(0)}%`;
  const cells = document.querySelectorAll('.cycles i');
  cells.forEach((el, i) => { el.classList.toggle('now', i === s.cycle && !s.done); });
  s.cycleGrades.forEach((g, i) => { cells[i].className = g.key; });
  if (s.cycleGrades.length > mode.cycleSeen) {
    const g = s.cycleGrades.at(-1);
    if (g.key !== 'scattered') sfx.chime(1 + mode.cycleSeen * 0.12);
    mode.cycleSeen = s.cycleGrades.length;
  }
  // 3D feedback: completed bands stay lit, the current one breathes with qi; disc glows with sync.
  bandGlows.forEach((m, i) => {
    const g = s.cycleGrades[i];
    const target = g ? (g.key === 'scattered' ? 0.08 : g.key === 'smooth' ? 0.75 : 0.45) : i === s.cycle ? s.qi * 0.4 : 0;
    m.material.opacity += (target - m.material.opacity) * Math.min(1, dt * 6);
  });
  discGlow.material.opacity = 0.15 + 0.6 * s.qi * s.sync;
  discGlow.scale.setScalar(0.85 + 0.35 * s.qi);
  updateMotes(t, 0.35 + 0.6 * s.qi, s.sync);
  sfx.breathSet(s.qi, s.sync);
  $('qi-tip').textContent = s.phase === 'ready' ? '凝神。金圈開始擴張時按住。' : s.phase === 'inhale' ? '吸——按住，讓玉圈跟著金圈長大' :
    s.phase === 'hold' ? '停——繼續按住' : s.phase === 'exhale' ? '呼——放開，讓氣緩緩散回' : '歇——放鬆，準備下一息';
  if (s.done) finish(s);
}

function updateBlock(t, dt) {
  if (mode.hitStop > 0) { mode.hitStop -= dt; return; }   // freeze frames on a clean block
  const s = mode.session.update(now());
  if (s.judged > mode.lastJudged) {
    if (s.last.result === 'hit' && s.last.reason === '來不及格擋') showJudge(s.last);
    mode.lastJudged = s.judged;
  } else if (mode.lastJudged < s.judged) mode.lastJudged = s.judged;
  $('combo').textContent = s.combo;
  restArms();
  const posed = new Set();  // only the nearest strike per side drives that arm
  for (const up of s.upcoming) if (!posed.has(up.side)) { posed.add(up.side); armPose(up.side, up.eta); }
  // rhythm tick 0.6 s before impact, ring approach on the matching button
  document.querySelectorAll('.block').forEach(b => {
    const up = s.upcoming.find(u => u.side === b.dataset.side && u.eta < 0.9 && u.eta > -WINDOW.good);
    const ring = b.querySelector('i');
    if (up) {
      const k = Math.max(0, up.eta) / 0.9;
      ring.style.opacity = String(1 - k * 0.6);
      ring.style.transform = `scale(${1 + k * 0.9})`;
      b.classList.add('armed');
    } else { ring.style.opacity = '0'; b.classList.remove('armed'); }
  });
  if (s.next && s.next.eta < 0.6 && mode.ticked !== s.judged) { sfx.tick(s.next.side === 'low'); mode.ticked = s.judged; }
  if (s.done) { setTimeout(() => mode.session && finish(mode.session.snapshot()), 500); mode.kind = 'ending'; }
}

requestAnimationFrame(frame);

// Debug/test hook (no game state leaves the page).
globalThis.__yard = {
  teleport(x, z, yawDeg = 0, pitch = -0.03) { leave(); Object.assign(player, { x, z, yaw: THREE.MathUtils.degToRad(yawDeg), pitch }); },
  start, leave, setRoots, block, holdDown, interact,
  state: () => ({ mode: mode.kind, session: mode.session?.snapshot(), player: { ...player }, near: nearestStation() }),
};
