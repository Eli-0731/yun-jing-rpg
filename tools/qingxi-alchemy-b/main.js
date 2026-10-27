// Workshop demo: walk between the B01-B12 stations and run 辨材 -> 配伍 -> 煉製 -> 領成品 on the local rules core.
// Everything here is a local demo; results never reach an official inventory (see CONTRACT.md).
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MATERIALS, demoBag } from './src/materials-adapter.mjs';
import { RECIPES, PROCESS, FIRE, COLLECT, newState, identify, checkCompound, preview, brew, claimLocal } from './src/alchemy-core.mjs';
import { makeCabinet, makeTrays, makeSteam } from './props.js';

const $ = id => document.getElementById(id);
const WALK = new URLSearchParams(location.search).has('walk');
const layout = await (await fetch('data/layout.json')).json();
const ROOT = '../../';

// ---------------------------------------------------------------- scene
const canvas = $('view');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: WALK });
renderer.setPixelRatio(WALK ? 1 : Math.min(devicePixelRatio, 2)); renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace; renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;
const scene = new THREE.Scene(); scene.background = new THREE.Color('#9fb3ab'); scene.fog = new THREE.Fog('#9fb3ab', 9, 22);
const camera = new THREE.PerspectiveCamera(50, 1, 0.05, 60);
scene.add(new THREE.HemisphereLight('#e8efe6', '#4a4035', 1.1));
const sun = new THREE.DirectionalLight('#ffe7c8', 2.4); sun.position.set(-3.5, 6, 3); sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048); Object.assign(sun.shadow.camera, { left: -5, right: 5, top: 5, bottom: -5, near: 0.5, far: 20 }); sun.shadow.bias = -0.0004;
scene.add(sun);

// Blender (x, y, z-up, front -Y) -> three (x, y-up, z): (x, z, -y)
const b2t = ([x, y, z]) => new THREE.Vector3(x, z, -y);
const mat = (c, r = 0.9) => new THREE.MeshStandardMaterial({ color: c, roughness: r });
function boxAt(size, pos, color) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(size[0], size[2], size[1]), mat(color)); m.position.copy(b2t(pos)); m.castShadow = m.receiveShadow = true; scene.add(m); return m;
}
// layout placeholders (same as layout.py): floor, shed posts, back wall, bench
boxAt([4.6, 3.6, 0.06], [0.30, 0.30, -0.03], '#57524a');
const ground = new THREE.Mesh(new THREE.PlaneGeometry(60, 60), mat('#55604f', 1)); ground.rotation.x = -Math.PI / 2; ground.position.y = -0.065; ground.receiveShadow = true; scene.add(ground);
for (const x of [-1.95, 2.55]) for (const y of [-1.45, 1.75]) boxAt([0.14, 0.14, 2.7], [x, y, 1.35], '#4a3523');
boxAt([4.5, 0.06, 1.25], [0.30, 1.75, 0.625], '#4a3523');
boxAt([1.30, 0.50, 0.05], [1.02, -0.46, 0.395], '#5b4029');
for (const x of [0.45, 1.59]) boxAt([0.08, 0.42, 0.37], [x, -0.46, 0.185], '#5b4029');

const loader = new GLTFLoader();
const inst = [];   // { id, role, glb, obj }
await Promise.all(layout.instances.map(async it => {
  const g = await loader.loadAsync(ROOT + 'art/exports/qingxi-alchemy-b/' + it.glb);
  const o = g.scene; o.position.copy(b2t(it.position)); o.rotation.y = THREE.MathUtils.degToRad(it.yawDeg);
  o.traverse(m => { if (m.isMesh) { m.castShadow = true; m.receiveShadow = true; if (m.material.transparent) m.castShadow = false; } });
  scene.add(o); inst.push({ ...it, obj: o });
}));
// furnace states: heating copy loaded beside the layout's heating furnace, cold shown until the fire is lit
const heatingFurnace = inst.find(i => i.glb.includes('B01_BronzeFurnace_heating')).obj;
const coldFurnace = (await loader.loadAsync(ROOT + 'art/exports/qingxi-alchemy-b/B01_BronzeFurnace/v001/B01_BronzeFurnace_cold.glb')).scene;
coldFurnace.position.copy(heatingFurnace.position); coldFurnace.traverse(m => { if (m.isMesh) m.castShadow = m.receiveShadow = true; }); scene.add(coldFurnace);
// lid states: the layout seats the heated lid; the cold lid is loaded beside it and shown while the fire is out
const hotLid = inst.find(i => i.id === 'B02').obj, lidSeat = hotLid.position.clone(), lidOpen = b2t([0.62, 0.42, 0.0]);
const coldLid = (await loader.loadAsync(ROOT + 'art/exports/qingxi-alchemy-b/B02_FurnaceLid/v001/B02_FurnaceLid.glb')).scene;
coldLid.traverse(m => { if (m.isMesh) m.castShadow = m.receiveShadow = true; }); scene.add(coldLid);
const lids = [hotLid, coldLid], VENT_TOP = b2t([0.09, 0.165, 0.175]);   // vent mouth in lid space (Blender coords)
const filledBottles = inst.filter(i => i.glb.includes('_filled')).map(i => i.obj);
const fireLight = new THREE.PointLight('#ff8a3a', 0, 2.2, 2); fireLight.position.copy(b2t([0, 0.30, 0.3])); scene.add(fireLight);

// player (1.70 m capsule figure, same proportions as the layout scale figure)
const player = new THREE.Group();
const robe = new THREE.Mesh(new THREE.CapsuleGeometry(0.17, 1.0, 6, 16), mat('#2f5a55', 0.8)); robe.position.y = 0.70;
const head = new THREE.Mesh(new THREE.SphereGeometry(0.11, 20, 14), mat('#d9b896', 0.7)); head.position.y = 1.585;
const nose = new THREE.Mesh(new THREE.ConeGeometry(0.03, 0.08, 8), mat('#b39a62')); nose.rotation.x = -Math.PI / 2; nose.position.set(0, 1.58, -0.12);
[robe, head, nose].forEach(m => { m.castShadow = true; player.add(m); }); scene.add(player);
const figureMats = [robe, head, nose].map(m => Object.assign(m.material, { transparent: true }));   // compiled transparent so opacity can fade
player.position.copy(b2t(layout.entrance)); player.rotation.y = 0;

// ---------------------------------------------------------------- game state
const S = newState(demoBag());
let plan, round, last, claimRequest;
function newRound() { plan = { recipe: 'body-bath', picks: {}, process: {}, fire: null, collect: null }; round = { locked: false, water: false, fuel: false, brewed: false, claimed: false }; last = null; claimRequest = null; }
newRound();
const STATION = Object.fromEntries(layout.stations.map(s => [s.role, s]));
const STEPS = [
  ['辨材', '藥櫃 B05', () => plan.picks.main && plan.picks.aux ? [plan.picks.main, plan.picks.aux].every(b => S.identified.includes(b)) : S.identified.length >= 2],
  ['配伍', '配方竹簡 B11', () => round.locked],
  ['處理材料', '石臼 B03（浸泡用陶甕 B06 的水）', () => RECIPES[plan.recipe].slots.every(s => plan.process[s.role])],
  ['控火', '添柴 B07 → 丹爐 B01', () => !!plan.fire],
  ['收取', '濾渣架 B09', () => round.brewed],
  ['領成品', '長凳藥瓶 B10', () => round.claimed || (round.brewed && !last?.success)],
];

// ---------------------------------------------------------------- UI
let toastT = 0;
function toast(text, bad = false) { const t = $('toast'); t.textContent = text; t.className = bad ? 'bad' : ''; t.hidden = false; toastT = 4.5; }
function renderSteps() {
  const firstOpen = STEPS.findIndex(s => !s[2]());
  $('steps').innerHTML = `<h2>${RECIPES[plan.recipe].label}</h2><ol>${STEPS.map(([n, w, f], i) => `<li class="${f() ? 'done' : i === firstOpen ? 'now' : ''}">${i + 1}. ${n}${f() ? ' ✓' : ''}<br><span class="dim">${w}</span></li>`).join('')}</ol>`;
}
function renderPreview() {
  const p = preview(S, plan), r = RECIPES[plan.recipe];
  const bag = S.bag.map(b => `${MATERIALS[b.material].name} ×${b.qty}`).join('、');
  const prod = S.products.map(x => `${x.label}（${x.grade}）`).join('、') || '尚無';
  $('preview').innerHTML = `<h2>預估結果</h2>藥效 ${p.potency}<div class="meter pot"><i style="width:${p.potency}%"></i></div>
    穩定度 ${p.stability}（${p.grade}）<div class="meter"><i style="width:${p.stability}%"></i></div>
    ${p.warnings.map(w => `<p class="warn">⚠ ${w}</p>`).join('')}
    <p class="dim">${r.kind === 'known' ? '已知配方：材料正確必定成功' : '研究變體：可能失敗，失敗會說明原因並退回部分材料'}</p>
    <p class="dim">背包：${bag}</p><p class="dim">演示成品：${prod}</p>`;
}
const opts = (obj, cur, act, slot = '') => Object.entries(obj).map(([k, v]) => `<button data-act="${act}" data-slot="${slot}" data-v="${k}" class="${cur === k ? 'on' : ''}">${v}</button>`).join('');
let openRole = null;
function card(role) {
  openRole = role; const c = $('card'); c.hidden = false; const r = RECIPES[plan.recipe]; let h = '';
  const slotName = role => r.slots.find(s => s.role === role)?.label ?? role;
  if (role === 'identify') {
    h = `<h2>藥櫃 B05 · 辨材</h2><p class="dim">拉開抽屜看清屬性、藥性、純度與穩定度；辨識過的抽屜標籤寫上名稱並蓋紅印。</p><table>${S.bag.map(b => {
      const m = MATERIALS[b.material], seen = S.identified.includes(b.batchId);
      return `<tr><td>${m.name} ×${b.qty}</td><td>${seen ? `${m.element}屬・性${m.nature}・純度 ${b.purity}・穩定 ${b.stability}` : '<span class="dim">未辨識</span>'}</td><td>${seen ? '' : `<button data-act="identify" data-v="${b.batchId}">辨識</button>`}</td></tr>`; }).join('')}</table>`;
  } else if (role === 'recipe') {
    h = `<h2>配方竹簡 B11 · 配伍</h2><div class="row">${Object.values(RECIPES).map(x => `<button data-act="recipe" data-v="${x.id}" class="${plan.recipe === x.id ? 'on' : ''}" ${round.locked ? 'disabled' : ''}>${x.label}</button>`).join('')}</div>
      <p class="dim">${r.summary}</p>` + r.slots.map(s => `<div class="row"><b>${s.label}</b><span class="dim">需 ${s.element}屬・${s.nature}性 ×${s.qty}</span>${S.bag.map(b => `<button data-act="pick" data-slot="${s.role}" data-v="${b.batchId}" class="${plan.picks[s.role] === b.batchId ? 'on' : ''}" ${round.locked ? 'disabled' : ''}>${MATERIALS[b.material].name}</button>`).join('')}</div>`).join('') +
      (round.locked ? '<div class="ok">配伍已確認，到石臼處理材料。</div>' : '<div class="row"><button class="go" data-act="lock">確認配伍</button></div>');
  } else if (role === 'process') {
    h = `<h2>石臼 B03 · 處理材料</h2>` + (!round.locked ? '<div class="fb">先到配方竹簡確認配伍。</div>' :
      r.slots.map(s => `<div class="row"><b>${s.label}・${MATERIALS[S.bag.find(b => b.batchId === plan.picks[s.role]).material].name}</b>${opts(PROCESS, plan.process[s.role], 'process', s.role)}</div>`).join('') +
      `<p class="dim">${round.water ? '已從陶甕取水，可以浸泡。' : '浸泡要先到陶甕 B06 取水。'}</p>`);
  } else if (role === 'water') {
    h = `<h2>陶甕 B06 · 取水</h2><p>${round.water ? '水已取好。' : '舀一瓢溪水，給浸泡用。'}</p>${round.water ? '' : '<div class="row"><button class="go" data-act="water">取水</button></div>'}`;
  } else if (role === 'fuel') {
    h = `<h2>燃料箱 B07 · 添柴</h2><p>${round.fuel ? '爐下已添柴。' : '抱兩段劈柴送進爐口。'}</p>${round.fuel ? '' : '<div class="row"><button class="go" data-act="fuel">添柴</button></div>'}`;
  } else if (role === 'refine') {
    const ready = round.locked && r.slots.every(s => plan.process[s.role]);
    h = `<h2>青銅丹爐 B01 · 控火</h2>` + (!ready ? '<div class="fb">材料還沒配伍、處理好。</div>' : !round.fuel ? '<div class="fb">爐下沒柴，先到燃料箱 B07 添柴。</div>' :
      `<p class="dim">火候會改變藥效與穩定度，右側預估即時更新。</p><div class="row">${opts(FIRE, plan.fire, 'fire')}</div>`);
  } else if (role === 'filter') {
    h = `<h2>濾渣布架 B09 · 收取</h2>` + (round.brewed ? resultHtml() : !plan.fire ? '<div class="fb">丹爐還沒起火。</div>' :
      `<div class="row">${opts(COLLECT, plan.collect, 'collect')}</div><div class="row"><button class="go" data-act="brew" ${plan.collect ? '' : 'disabled'}>開爐收藥</button></div>`);
  } else if (role === 'collect') {
    h = `<h2>長凳藥瓶 B10 · 領成品</h2>` + (!round.brewed ? '<div class="fb">這爐還沒收取。</div>' : !last.success ? `<div class="fb">這爐沒有成品可領。${last.reason}</div><div class="row"><button class="go" data-act="again">再煉一爐</button></div>` :
      `<p>${last.label} ×${last.product.quantity}（藥效 ${last.product.potency}・穩定 ${last.product.stability}・${last.product.grade}${last.product.bound ? '・綁定' : ''}）</p>
       <p class="dim">本機演示領取：請求編號 ${claimRequest.slice(0, 8)}…，重複按不會增加。正式領取由伺服器決定（CONTRACT.md）。</p>
       <div class="row"><button class="go" data-act="claim">本機演示領取</button>${round.claimed ? '<button data-act="again">再煉一爐</button>' : ''}</div>`);
  } else {
    const flavour = { dry: '晾藥筐 B08：曬好的藥材攤在這裡透氣。', sort: '分料盤 B04：配伍確認後，上層放主藥、下層放輔藥，處理過的樣子會留在盤上，開爐後用掉。', exhaust: '排煙矮煙囪 B12：丹爐的煙從這裡排出。' };
    h = `<h2>${STATION[role].label}</h2><p>${flavour[role] ?? ''}</p>`;
  }
  c.innerHTML = '<button class="x" data-act="close">×</button>' + h;
}
function resultHtml() {
  if (last.success) return `<div class="ok">成功：${last.label}（藥效 ${last.product.potency}・穩定 ${last.product.stability}・${last.product.grade}）。到長凳藥瓶處領取。</div>`;
  return `<div class="fb">失敗（${{ process: '處理', fire: '控火', collect: '收取' }[last.stage]}階段）：${last.reason}</div>
    <p>退回：${last.returned.map(x => `${MATERIALS[x.material].name} ×${x.qty}`).join('、') || '無'}</p><p class="dim">原因已記入研究筆記，下次預估會提醒。</p>`;
}
function act(a, v, slot) {
  if (a === 'close') { $('card').hidden = true; openRole = null; return; }
  if (a === 'identify') { const r = identify(S, v); toast(r.text); drawerFocus = v; }
  if (a === 'recipe') { plan.recipe = v; plan.picks = {}; plan.process = {}; }
  if (a === 'pick') plan.picks[slot] = v;
  if (a === 'lock') {
    const p = checkCompound(S, plan.recipe, plan.picks);
    if (p.length) toast(p.map(x => x.message).join('\n'), true); else { round.locked = true; toast('配伍正確。'); }
  }
  if (a === 'process') {
    if (v === 'soak' && !round.water) { toast('浸泡要先到陶甕 B06 取水', true); return; }
    plan.process[slot] = v;
  }
  if (a === 'water') { round.water = true; toast('取了一瓢溪水'); }
  if (a === 'fuel') { round.fuel = true; toast('爐下添了柴'); }
  if (a === 'fire') { plan.fire = v; setFurnace(true); toast(`${FIRE[v]}起爐`); }
  if (a === 'collect') plan.collect = v;
  if (a === 'brew') {
    last = brew(S, plan); round.brewed = true; claimRequest = crypto.randomUUID();
    if (!last.ok) { round.brewed = false; toast(last.problems.map(x => x.message).join('\n'), true); }
    else { setFurnace(false, true); toast(last.success ? `成功：${last.label}` : `失敗：${last.reason}`, !last.success); }
  }
  if (a === 'claim') {
    const r = claimLocal(S, last, claimRequest);
    if (!r.ok) toast(r.message, true);
    else if (r.replayed) toast('已領過：同一請求重送，結果不增加');
    else { round.claimed = true; filledBottles.forEach(o => (o.visible = true)); toast(`本機演示領得 ${r.granted.label} ×${r.granted.quantity}（非正式）`); }
  }
  if (a === 'again') { newRound(); setFurnace(false); filledBottles.forEach(o => (o.visible = false)); }
  renderSteps(); renderPreview(); if (openRole) card(openRole);
}
$('card').addEventListener('click', e => { const b = e.target.closest('button'); if (b && !b.disabled) act(b.dataset.act, b.dataset.v, b.dataset.slot); });
function setFurnace(hot, open = false) {
  heatingFurnace.visible = hot; coldFurnace.visible = !hot; fireLight.intensity = hot ? 2.2 : 0;
  hotLid.visible = hot; coldLid.visible = !hot; lids.forEach(l => l.position.copy(open ? lidOpen : lidSeat));
}
setFurnace(false); filledBottles.forEach(o => (o.visible = false));

// ---------------------------------------------------------------- movement + interaction
const keys = new Set(); let target = null, near = null;
addEventListener('keydown', e => { keys.add(e.key.toLowerCase()); if (e.key.toLowerCase() === 'e' && near) card(near.role); if (e.key === 'Escape') act('close'); });
addEventListener('keyup', e => keys.delete(e.key.toLowerCase()));
const ray = new THREE.Raycaster(), floorPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
canvas.addEventListener('pointerdown', e => {
  ray.setFromCamera(new THREE.Vector2(e.clientX / innerWidth * 2 - 1, -e.clientY / innerHeight * 2 + 1), camera);
  const p = new THREE.Vector3(); if (ray.ray.intersectPlane(floorPlane, p)) target = p;
});
$('prompt').addEventListener('click', () => near && card(near.role));
const obstacles = layout.stations.filter(s => s.position[2] === 0).map(s => ({ p: b2t(s.position), r: s.role === 'exhaust' ? 0.45 : s.role === 'refine' ? 0.42 : 0.32 }))
  .concat([0.6, 1.0, 1.45].map(x => ({ p: b2t([x, -0.46, 0]), r: 0.3 })));
function move(dt) {
  const dir = new THREE.Vector3();
  if (keys.has('w') || keys.has('arrowup')) dir.z -= 1; if (keys.has('s') || keys.has('arrowdown')) dir.z += 1;
  if (keys.has('a') || keys.has('arrowleft')) dir.x -= 1; if (keys.has('d') || keys.has('arrowright')) dir.x += 1;
  let step = 1.7 * dt;
  if (dir.lengthSq()) target = null;
  else if (target) {   // the last step stops on the target instead of overshooting (large dt would oscillate round it)
    dir.subVectors(target, player.position).setY(0); step = Math.min(step, dir.length());
    if (dir.length() < 0.06) { target = null; dir.set(0, 0, 0); }
  }
  if (dir.lengthSq()) {
    dir.normalize(); const next = player.position.clone().addScaledVector(dir, step);
    for (const o of obstacles) { const d = next.clone().sub(o.p).setY(0), min = o.r + 0.2; if (d.length() < min) next.add(d.setLength(min - d.length())); }
    next.x = THREE.MathUtils.clamp(next.x, -1.85, 2.45); next.z = THREE.MathUtils.clamp(next.z, -1.65, 2.35);
    player.position.copy(next); player.rotation.y = Math.atan2(-dir.x, -dir.z);
  }
  near = null; let best = 0.7;   // nearest approach point wins (B05/B11 share a footprint, so positions alone are ambiguous)
  for (const s of layout.stations) { const d = b2t(s.approach).setY(0).distanceTo(player.position.clone().setY(0)); if (d < best) { best = d; near = s; } }
  const pr = $('prompt'); pr.hidden = !near || openRole === near?.role; if (near) pr.textContent = `E：${near.label}（${near.id}）`;
  if (openRole && STATION[openRole] && b2t(STATION[openRole].approach).setY(0).distanceTo(player.position.clone().setY(0)) > 1.2) act('close');
}
// follow camera; while a station card is open it rises to look down on that station from the side away from the
// player (or toward the room centre when the player stands square in front), so the figure and the shed posts do not
// hide drawers, trays or the furnace mouth
const look = new THREE.Vector3();
function frameCamera(dt, snap = false) {
  const st = openRole && STATION[openRole];
  let want, at;
  if (st) {
    const f = b2t(st.position), dx = player.position.x - f.x, side = Math.abs(dx) > 0.1 ? -Math.sign(dx) : f.x > 0.3 ? -1 : 1;
    want = f.clone().add(new THREE.Vector3(side * 1.0, 2.4, 2.2)); at = f.clone().add(new THREE.Vector3(0, -0.1, 0));   // aim low: station sits above the card
  } else {
    want = player.position.clone().add(new THREE.Vector3(0.3, 3.0, 3.7)); at = player.position.clone().add(new THREE.Vector3(0, 0.5, -1.3));
  }
  const k = snap ? 1 : 1 - Math.exp(-dt * 4);
  camera.position.lerp(want, k); look.lerp(at, k); camera.lookAt(look);
  const fade = THREE.MathUtils.lerp(figureMats[0].opacity, st ? 0.3 : 1, k);   // figure ghosts while framing a station
  for (const m of figureMats) { m.opacity = fade; m.depthWrite = fade >= 0.99; }
}
function resize() { const w = WALK ? 1280 : innerWidth, h = WALK ? 720 : innerHeight; renderer.setSize(w, h, !WALK); camera.aspect = w / h; camera.updateProjectionMatrix(); }
addEventListener('resize', resize); resize();
frameCamera(0, true);
renderSteps(); renderPreview();

let t0 = performance.now(), flicker = 0;
// in-world material and product states: B05 drawers + labels, B04 tray loads, steam from the heated lid's vent
const cabinet = makeCabinet(inst.find(i => i.id === 'B05').obj, S.bag, MATERIALS);
const trays = makeTrays(inst.find(i => i.id === 'B04').obj);
const steam = makeSteam(scene);
let drawerFocus = null;   // last batch identified at B05; its drawer is the one pulled out
function trayLoads() {   // after 配伍 the picked batches sit on B04 (main up, aux down) until the brew consumes them
  if (!round.locked || round.brewed) return {};
  return Object.fromEntries(RECIPES[plan.recipe].slots.map(s => [s.role, { material: S.bag.find(b => b.batchId === plan.picks[s.role]).material, form: plan.process[s.role] ?? 'raw' }]));
}
function tick(dt) {
  move(dt); frameCamera(dt); flicker += dt;
  cabinet.update(dt, openRole === 'identify', S.identified, drawerFocus ?? S.bag.find(b => !S.identified.includes(b.batchId))?.batchId);
  trays.set(trayLoads());
  steam.update(dt, hotLid.visible && hotLid.position.equals(lidSeat), hotLid.localToWorld(VENT_TOP.clone()));
  if (heatingFurnace.visible) fireLight.intensity = 2.0 + Math.sin(flicker * 9) * 0.25 + Math.sin(flicker * 23) * 0.12;
  if (toastT > 0 && (toastT -= dt) <= 0) $('toast').hidden = true;
  renderer.render(scene, camera);
}
if (!WALK) renderer.setAnimationLoop(() => { const now = performance.now(); tick(Math.min(0.05, (now - t0) / 1000)); t0 = now; });

// ---------------------------------------------------------------- scripted walkthrough (?walk) for the recording
window.demo = { S, get plan() { return plan; }, get last() { return last; }, act, card, layout, scene, camera, player, tick };
if (WALK) {
  const { runWalkthrough } = await import('./walkthrough.js');
  runWalkthrough({ tick, act, card, player, layout, b2t, S, get plan() { return plan; }, get last() { return last; }, get target() { return target; }, set target(v) { target = v; }, canvas });
}
