import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { collaboratorModels } from './scene-content.mjs';

if ('serviceWorker' in navigator) navigator.serviceWorker.register('./sw.js').catch(() => {});

const viewport = document.getElementById('scene');
const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
renderer.setSize(innerWidth, innerHeight);
renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 1.7));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.3;
viewport.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color('#b9d5cf');
scene.fog = new THREE.Fog('#b9d5cf', 30, 65);
scene.add(new THREE.HemisphereLight('#ffffff', '#719080', 2.3));
const sun = new THREE.DirectionalLight('#ffe4bb', 2.2);
sun.position.set(-7, 15, 8); scene.add(sun);
const camera = new THREE.PerspectiveCamera(60, innerWidth / innerHeight, .1, 90);
const loader = new GLTFLoader();
let previousFrame = performance.now();
const cameraBlockers = [];
const cameraRay = new THREE.Raycaster();

// Road-v13 is the authored entrance surface. A mottled ground material keeps
// the uncovered edges from reading as one flat green block.
const groundCanvas = document.createElement('canvas');
groundCanvas.width = groundCanvas.height = 256;
const groundContext = groundCanvas.getContext('2d');
groundContext.fillStyle = '#79906a'; groundContext.fillRect(0, 0, 256, 256);
let seed = 82341;
function random() { seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0; return seed / 4294967296; }
for (let i = 0; i < 4800; i++) {
  const shade = Math.floor(70 + random() * 65);
  groundContext.fillStyle = `rgba(${shade + 19},${shade + 34},${shade},${.08 + random() * .18})`;
  groundContext.fillRect(random() * 256, random() * 256, 1 + random() * 7, 1 + random() * 5);
}
const groundTexture = new THREE.CanvasTexture(groundCanvas);
groundTexture.wrapS = groundTexture.wrapT = THREE.RepeatWrapping;
groundTexture.repeat.set(5, 4);
groundTexture.colorSpace = THREE.SRGBColorSpace;
const ground = new THREE.Mesh(new THREE.PlaneGeometry(48, 35), new THREE.MeshStandardMaterial({ map: groundTexture, roughness: 1 }));
ground.rotation.x = -Math.PI / 2; ground.position.y = -.045; scene.add(ground);
const river = new THREE.Mesh(new THREE.PlaneGeometry(3.8, 35), new THREE.MeshStandardMaterial({ color: '#319ba6', transparent: true, opacity: .83, roughness: .24 }));
river.rotation.x = -Math.PI / 2; river.position.set(-9.9, .015, 0); scene.add(river);
const bank = new THREE.Mesh(new THREE.PlaneGeometry(.42, 35), new THREE.MeshStandardMaterial({ color: '#6b7760', roughness: 1 }));
bank.rotation.x = -Math.PI / 2; bank.position.set(-7.75, .025, 0); scene.add(bank);

// Normalizes an authored GLB to a readable review scale. Geometry comes from
// this repository; no third-party download is inserted into the trial.
async function placeModel(path, x, z, extent, axis = 'width', rotation = 0) {
  const gltf = await loader.loadAsync(path);
  const model = gltf.scene;
  model.updateMatrixWorld(true);
  const bounds = new THREE.Box3().setFromObject(model);
  const size = bounds.getSize(new THREE.Vector3());
  const scale = extent / Math.max(axis === 'height' ? size.y : Math.max(size.x, size.z), .001);
  model.scale.setScalar(scale);
  model.updateMatrixWorld(true);
  const fitted = new THREE.Box3().setFromObject(model);
  const center = fitted.getCenter(new THREE.Vector3());
  model.position.set(-center.x, -fitted.min.y, -center.z);
  const root = new THREE.Group(); root.position.set(x, 0, z); root.rotation.y = rotation;
  root.add(model); scene.add(root);
  return { root, gltf };
}

const assets = [
  ['../../art/exports/qingxi-road-props-v13/qingxi-road-v13.glb', 0, 7, 17, 'width'],
  ['../../art/exports/qingxi-road-props-v13/qingxi-road-v13.glb', 0, -3, 15, 'width'],
  ['../../art/exports/qingxi-entry-assets-v13/village-gate-v13.glb', 0, 8, 6.5, 'width'],
  ['../../art/exports/qingxi-riverside-house-v1/qingxi-riverside-house-v1.glb', 5.4, 2.4, 7, 'width'],
  ['../../art/exports/elder-world-tree-hero-v1/elder-world-tree-hero-v1.glb', -5, 7, 6.8, 'height'],
  ['../../art/exports/qingxi-listening-terrace-v1.glb', 14.6, 6, 9, 'width'],
];
const loading = Promise.allSettled(assets.map(async ([path, x, z, extent, axis]) => {
  const loaded = await placeModel(path, x, z, extent, axis);
  // The source tree's exposed floating-island roots extend below the trunk.
  // The village variant embeds them in terrain until the dedicated root pass.
  if (path.includes('elder-world-tree')) loaded.root.position.y -= 2.1;
  if (path.includes('village-gate') || path.includes('riverside-house')) cameraBlockers.push(loaded.root);
  return loaded;
}));
// The larger Unity town uses its own builder. This is its walkable entrance
// slice: real collaborator meshes are placed along the first village route.
const collaboratorLoading = Promise.allSettled(collaboratorModels.map(async item => {
  const { root } = await placeModel(item.path, item.x, item.z, item.size, item.axis);
  root.name = item.id;
  root.userData.author = item.owner;
  if (item.id === 'training-shelter' || item.id === 'alchemy-cabinet') cameraBlockers.push(root);
  return item.id;
}));

async function scatterExisting(path, positions, extent) {
  const first = await placeModel(path, positions[0][0], positions[0][1], extent);
  for (const [index, [x, z]] of positions.slice(1).entries()) {
    const copy = first.root.clone(true);
    copy.position.set(x, 0, z);
    copy.rotation.y = index * 2.399;
    copy.scale.setScalar(.82 + index % 4 * .10);
    scene.add(copy);
  }
}
const dressing = Promise.allSettled([
  scatterExisting('../../art/exports/qingxi-detail-props-v2/qingxi-moss-boulder-v2.glb',
    [[-5.0, 7.0], [8.7, -2.1], [17.5, -2.2], [9.1, -8.8], [18.0, -8.8], [10.1, 3.1], [18.3, 6.0],
      [-6.1, 10.2], [-4.8, 11.6], [-5.9, 2.1], [4.1, 10.9], [6.5, 9.0], [2.7, 3.1], [7.1, 5.8]], 1.8),
  scatterExisting('../../art/exports/qingxi-detail-props-v2/qingxi-fern-flower-v2.glb',
    [[10.2, -3.1], [13.4, -.8], [16.9, -4.0], [10.3, -7.8], [16.1, -9.7],
      [8.6, 4.6], [11.0, 7.6], [17.2, 8.8], [3.0, -5.4], [-5.8, 8.8], [-6.4, 4.2],
      [-2.0, 10.8], [3.5, 10.3], [5.8, 7.8], [2.9, 2.0], [-3.8, 1.4], [6.9, 4.0],
      [7.9, 2.7], [-3.1, -4.3], [4.5, -7.0]], 1.1),
]);

function beacon(x, z, color) {
  const group = new THREE.Group();
  const light = new THREE.Mesh(new THREE.SphereGeometry(.15, 10, 8), new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: 1.3 }));
  light.position.y = 1.05; group.add(light);
  const foot = new THREE.Mesh(new THREE.CylinderGeometry(.24, .30, .08, 12), new THREE.MeshStandardMaterial({ color: '#6d7d68' }));
  foot.position.y = .04; group.add(foot);
  group.position.set(x, 0, z); scene.add(group); return group;
}
const practice = beacon(0, 6.0, '#d1c28a');
const herb = beacon(12.1, -2.1, '#51c987');
const vendor = beacon(6.3, .4, '#e5a360');
const terrace = beacon(14.6, 6.1, '#7fc8d6');
const entrance = beacon(0, 10.1, '#eac978');
const returnTable = beacon(9.4, -0.8, '#d5b27f');
const workshop = beacon(15.8, 1.2, '#d96e55');
const forest = beacon(12.2, -6.0, '#8bc088');

const player = new THREE.Group(); player.position.set(0, 0, 11.4); player.rotation.y = Math.PI; scene.add(player);
let avatarMotion = null;
let rabbit;
const rabbitHome = new THREE.Vector3(12, 0, -8);
const rabbitState = { hp: 2, stun: 0, fleeAngle: 0 };

function fallbackCharacter() {
  const body = new THREE.Mesh(new THREE.CapsuleGeometry(.28, 1.15, 4, 8), new THREE.MeshStandardMaterial({ color: '#315a63' }));
  body.position.y = 1.0; player.add(body);
}
placeModel('../../art/exports/qingxi-entry-assets-v13/novice-cultivator-v13.glb', 0, 0, 1.75, 'height')
  .then(({ root }) => {
    scene.remove(root); root.position.set(0, 0, 0); player.add(root);
    const parts = [];
    root.traverse(object => {
      if (!object.isMesh) return;
      const name = object.name;
      const swing = /_(Leg|UpperArm|Forearm|Sleeve)_/.exec(name);
      const hair = name.includes('BackHair') || name.includes('TempleHair');
      const skirt = name.includes('SkirtLayer');
      if (!swing && !hair && !skirt) return;
      parts.push({ object, base: object.rotation.clone(), swing: swing?.[1],
        side: name.endsWith('_-1') ? -1 : 1, hair, skirt });
    });
    avatarMotion = { root, parts, phase: 0, amount: 0 };
    document.getElementById('avatar').textContent = '原創修行者試模：可步行、轉向、出招';
  })
  .catch(() => fallbackCharacter());
placeModel('../../art/exports/qingxi-mountain-rabbit-v003/QingxiMountainRabbit_v003.glb', rabbitHome.x, rabbitHome.z, .75, 'height')
  .then(({ root, gltf }) => {
    rabbit = root;
    if (gltf.animations.length) {
      const mixer = new THREE.AnimationMixer(root);
      mixer.clipAction(gltf.animations[0]).play(); rabbitState.mixer = mixer;
    }
  }).catch(() => {
    rabbit = new THREE.Mesh(new THREE.SphereGeometry(.35, 12, 8), new THREE.MeshStandardMaterial({ color: '#9b8a73' }));
    rabbit.position.copy(rabbitHome); rabbit.position.y = .35; scene.add(rabbit);
  });

const state = { training: false, herb: false, rabbit: false, delivered: false, started: false,
  yaw: 0, attackCooldown: 0, lastToast: 0 };
const held = new Set();
const status = document.getElementById('progress');
const nearby = document.getElementById('nearby');
const notice = document.getElementById('notice');
const intro = document.getElementById('intro');
const activity = document.getElementById('activity');
const activityFrame = document.getElementById('activity-frame');
function say(message) { notice.textContent = message; state.lastToast = performance.now(); }
function openActivity(title, path) {
  held.clear();
  document.getElementById('activity-title').textContent = title + ' · 本機試玩';
  activityFrame.src = path;
  activity.showModal();
  say(`${title}已開啟；完成後按「返回場景」繼續走。此處資料不會寫入正式角色。`);
}
document.getElementById('activity-close').addEventListener('click', () => activity.close());
activity.addEventListener('close', () => { activityFrame.src = 'about:blank'; held.clear(); });
function refresh() {
  status.textContent = `練功 ${+state.training}/1 · 靈草 ${+state.herb}/1 · 山兔 ${+state.rabbit}/1`;
  if (state.delivered) status.classList.add('done');
}
function distance(object) { return Math.hypot(player.position.x - object.position.x, player.position.z - object.position.z); }
function nearest() {
  return [['青溪入口告示', entrance], ['村門演武', practice], ['青溪靈草', herb],
    ['回村分揀桌', returnTable], ['溪畔煉製工坊', workshop], ['山兔林地遭遇', forest],
    ['客舍商販', vendor], ['聽風台', terrace]]
    .map(([name, object]) => ({ name, object, d: distance(object) })).sort((a, b) => a.d - b.d)[0];
}
function interact() {
  if (!state.started || activity.open) return;
  const target = nearest();
  if (target.d > 2.7) { say('再靠近一點，才能互動。'); return; }
  if (target.object === entrance) {
    openActivity('村口告示與三條線索', '../novice-field-guide/');
  } else if (target.object === practice) {
    openActivity('公共演武區 · 調息與格擋', '../training-yard-demo/');
  } else if (target.object === herb) {
    if (!state.herb) { state.herb = true; herb.visible = false; say('採到一株青溪靈草。這是本機試玩道具，未寫入遊戲背包。'); }
    else say('這株靈草已在本次試玩採過。');
  } else if (target.object === returnTable) {
    openActivity('回村樣本整理', '../qingxi-return-c/');
  } else if (target.object === workshop) {
    openActivity('溪畔煉製工坊', '../qingxi-alchemy-b/');
  } else if (target.object === forest) {
    openActivity('山兔林地 · 閃避與看破綻', '../qingxi-encounter-a/');
  } else if (target.object === vendor) {
    if (state.herb && state.rabbit) { state.delivered = true; say('商販確認了靈草與山兔材料。小循環完成；正式交易仍須服務端結算。'); }
    else say('商販說：先自由走走；找到靈草、追上山兔，再回來聊聊。');
  } else say('青溪聽風台：可坐望河谷。此處正在精修，沒有強制任務。');
  refresh();
}
function attack() {
  if (!state.started || activity.open || state.attackCooldown > 0) return;
  state.attackCooldown = .55;
  if (!rabbit || state.rabbit || distance(rabbit) > 2.6) { say('招式落空。靠近山兔，觀察牠的逃跑路線。'); return; }
  rabbitState.hp--;
  rabbitState.stun = .55;
  if (rabbitState.hp <= 0) { state.rabbit = true; rabbit.visible = false; say('山兔遭擊倒；本機試玩記錄一份材料，沒有正式掉落。'); refresh(); }
  else say('擊中了山兔！牠正在轉向逃跑。');
}

document.getElementById('start').addEventListener('click', async () => {
  if (screen.orientation?.lock) { try { await screen.orientation.lock('landscape'); } catch { /* browser tabs may not grant this */ } }
  state.started = true; intro.remove(); say('方向鍵或 WASD 移動，右側滑動可轉視角。先自由探索。');
});
document.getElementById('interact').addEventListener('click', interact);
document.getElementById('attack').addEventListener('click', attack);
addEventListener('keydown', e => {
  if (activity.open) return;
  const k = e.key.toLowerCase();
  if (['w','a','s','d','arrowup','arrowdown','arrowleft','arrowright','e',' '].includes(k)) e.preventDefault();
  held.add(k); if (k === 'e' && !e.repeat) interact(); if (k === ' ' && !e.repeat) attack();
});
addEventListener('keyup', e => held.delete(e.key.toLowerCase()));
addEventListener('blur', () => held.clear());
document.querySelectorAll('[data-move]').forEach(button => {
  const key = button.dataset.move;
  button.addEventListener('pointerdown', e => { e.preventDefault(); held.add(key); button.setPointerCapture(e.pointerId); });
  button.addEventListener('pointerup', () => held.delete(key));
  button.addEventListener('pointercancel', () => held.delete(key));
});
let dragX = null;
renderer.domElement.addEventListener('pointerdown', e => { if (e.button === 2 || e.pointerType === 'touch' && e.clientX > innerWidth * .45) { dragX = e.clientX; renderer.domElement.setPointerCapture(e.pointerId); } });
renderer.domElement.addEventListener('pointermove', e => { if (dragX !== null) { state.yaw -= (e.clientX - dragX) * .005; dragX = e.clientX; } });
renderer.domElement.addEventListener('pointerup', () => { dragX = null; });
renderer.domElement.addEventListener('contextmenu', e => e.preventDefault());
addEventListener('resize', () => { camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); renderer.setSize(innerWidth, innerHeight); });

function tick(now = performance.now()) {
  const dt = Math.min((now - previousFrame) / 1000, .05);
  previousFrame = now;
  state.attackCooldown = Math.max(0, state.attackCooldown - dt);
  rabbitState.mixer?.update(dt);
  if (state.started && !activity.open) {
    const forward = Number(held.has('w') || held.has('arrowup')) - Number(held.has('s') || held.has('arrowdown'));
    const sideways = Number(held.has('d') || held.has('arrowright')) - Number(held.has('a') || held.has('arrowleft'));
    const length = Math.hypot(forward, sideways) || 1;
    const fx = -Math.sin(state.yaw), fz = -Math.cos(state.yaw);
    const dx = (fx * forward + -fz * sideways) / length * 4.6 * dt;
    const dz = (fz * forward + fx * sideways) / length * 4.6 * dt;
    const nextX = THREE.MathUtils.clamp(player.position.x + dx, -7.4, 20);
    const nextZ = THREE.MathUtils.clamp(player.position.z + dz, -12, 12);
    // Coarse prototype collision: keep an opening around the house and
    // prevent wading into the river; formal game collision belongs in Unity.
    if (!(nextX > 2.7 && nextX < 8.2 && nextZ > .9 && nextZ < 4.4)) {
      player.position.x = nextX; player.position.z = nextZ;
    }
    const moving = Boolean(forward || sideways);
    if (moving) player.rotation.y = Math.atan2(dx, dz);
    if (avatarMotion) {
      avatarMotion.amount = THREE.MathUtils.damp(avatarMotion.amount, moving ? 1 : 0, 9, dt);
      avatarMotion.phase += dt * (moving ? 9.8 : 1.8);
      const stride = Math.sin(avatarMotion.phase) * avatarMotion.amount;
      const casting = state.attackCooldown > .30 ? 1 : 0;
      avatarMotion.root.position.y = Math.abs(Math.sin(avatarMotion.phase)) * .045 * avatarMotion.amount
        + Math.sin(now * .002) * .008;
      for (const part of avatarMotion.parts) {
        let angle = 0;
        if (part.swing === 'Leg') angle = stride * .23 * part.side;
        else if (part.swing) angle = -stride * .15 * part.side + casting * .28;
        else if (part.hair) angle = Math.sin(now * .003 + part.side) * .025 + stride * .018;
        else if (part.skirt) angle = -stride * .035;
        part.object.rotation.x = part.base.x + angle;
      }
    }
    if (rabbit && !state.rabbit && rabbitState.stun <= 0 && distance(rabbit) < 5.8) {
      const away = new THREE.Vector3(rabbit.position.x - player.position.x, 0, rabbit.position.z - player.position.z).normalize();
      rabbit.position.x = THREE.MathUtils.clamp(rabbit.position.x + away.x * 1.9 * dt, 8, 20);
      rabbit.position.z = THREE.MathUtils.clamp(rabbit.position.z + away.z * 1.9 * dt, -12, -3);
      rabbit.rotation.y = Math.atan2(away.x, away.z);
    }
    rabbitState.stun = Math.max(0, rabbitState.stun - dt);
    const target = nearest();
    const rabbitDistance = rabbit && !state.rabbit ? distance(rabbit) : Infinity;
    nearby.textContent = rabbitDistance < 3.4 && rabbitDistance < target.d
      ? '山兔 · 靠近後按空白鍵／出招'
      : target.d < 2.7 ? `${target.name} · 按 E／互動` : '走近地標可互動';
    if (performance.now() - state.lastToast > 8000 && !state.delivered) notice.textContent = '可自由練功、採草、追兔；沒有每日時長要求。';
  }
  const portrait = innerWidth / innerHeight < .7;
  const distanceBehind = portrait ? 8.1 : 5.8;
  const focus = new THREE.Vector3(player.position.x, 1.3, player.position.z);
  const desired = new THREE.Vector3(player.position.x + Math.sin(state.yaw) * distanceBehind,
    portrait ? 4.7 : 3.6, player.position.z + Math.cos(state.yaw) * distanceBehind);
  const cameraPath = desired.clone().sub(focus);
  cameraRay.set(focus, cameraPath.clone().normalize());
  cameraRay.far = cameraPath.length();
  const firstObstacle = cameraBlockers.length ? cameraRay.intersectObjects(cameraBlockers, true)[0] : null;
  if (firstObstacle) {
    camera.position.copy(focus).addScaledVector(cameraPath.normalize(), Math.max(.55, firstObstacle.distance - .35));
  } else camera.position.lerp(desired, Math.min(1, dt * 7));
  camera.lookAt(focus);
  renderer.render(scene, camera); requestAnimationFrame(tick);
}
loading.then(results => {
  const failed = results.filter(result => result.status === 'rejected').length;
  if (failed) say(`${failed} 件場景模型載入失敗，仍可試走基本玩法。`);
});
collaboratorLoading.then(results => {
  const failed = results.filter(result => result.status === 'rejected');
  const count = results.length - failed.length;
  document.getElementById('models').textContent = `協作者場景模型 ${count}/${results.length} 件已載入`;
  if (failed.length) say(`${failed.length} 件協作者模型載入失敗；請從本機伺服器開啟並確認 Git LFS 素材。`);
});
tick();
