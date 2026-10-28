// In-world state props for the demo: material piles (raw / sliced / ground / soaked), B05 drawers that slide out with
// their contents and labels, B04 tray loads, and vent steam over the heated B02 lid.
// Material piles are simple three.js stand-ins for PR #31's harvested items (not delivery art).
// Coordinates: Blender model space (x, y, z-up, front -Y) is converted with bl() = (x, z, -y), as in main.js.
import * as THREE from 'three';

const bl = (x, y, z) => new THREE.Vector3(x, z, -y);
const std = (color, o = {}) => new THREE.MeshStandardMaterial({ color, roughness: 0.6, ...o });
const LOOK = {
  'qinglan-stem': { stem: '#7f9f48', tip: '#d7e6d2', speck: '#8a4f7a', powder: '#7d8a4c', name: '青溪蘭' },
  'chilu-berry': { stem: '#9c1d16', tip: '#d8541e', speck: '#3f5a2a', powder: '#6e1d14', name: '赤露參' },
  'yumai-crystal': { stem: '#8fc9b2', tip: '#d9f2e6', speck: '#5f8f7e', powder: '#b9d8cb', name: '玉脈晶' },
};
const MAT = {}, mat = (k, c, o) => (MAT[k] ??= std(c, o));

function rng(seed) { let s = seed >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 2 ** 32); }

// A pile of one material in a given processing form, centred on the origin, resting on y = 0, about `size` across.
export function materialPile(material, form = 'raw', size = 0.16, seed = 1) {
  const L = LOOK[material], g = new THREE.Group(), r = rng(seed), add = m => (m.castShadow = true, g.add(m), m);
  if (form === 'slice' && material === 'yumai-crystal') form = 'raw';   // crystal cannot be cut (alchemy-core rule)
  if (form === 'soak') {
    add(new THREE.Mesh(new THREE.CylinderGeometry(size * 0.55, size * 0.45, size * 0.16, 28), mat('dish', '#b9cbbf', { roughness: 0.3 }))).position.y = size * 0.08;
    const water = add(new THREE.Mesh(new THREE.CircleGeometry(size * 0.5, 28), mat('water', '#6f8f86', { roughness: 0.05, metalness: 0.1, transparent: true, opacity: 0.75 })));
    water.rotation.x = -Math.PI / 2; water.position.y = size * 0.15; water.castShadow = false;
    const inner = materialPile(material, 'raw', size * 0.62, seed + 7); inner.position.y = size * 0.06; inner.traverse(m => m.isMesh && (m.material = m.material.clone(), m.material.color.multiplyScalar(0.7)));
    g.add(inner); return g;
  }
  if (form === 'grind') {
    const mound = add(new THREE.Mesh(new THREE.SphereGeometry(size * 0.42, 24, 12, 0, Math.PI * 2, 0, Math.PI / 2), mat(material + 'p', L.powder, { roughness: 0.95 })));
    mound.scale.y = 0.42;
    if (material === 'yumai-crystal') mound.material = std(L.powder, { roughness: 0.6, emissive: '#3f8f74', emissiveIntensity: 0.25 });
    return g;
  }
  if (material === 'qinglan-stem') {
    const n = form === 'slice' ? 11 : 3;
    for (let i = 0; i < n; i++) {
      const len = form === 'slice' ? size * 0.16 : size * (0.85 + r() * 0.2);
      const s = add(new THREE.Mesh(new THREE.CylinderGeometry(size * 0.034, size * 0.04, len, 8), mat('qs', L.stem)));
      s.rotation.z = Math.PI / 2; s.rotation.y = r() * Math.PI; s.position.set((r() - 0.5) * size * 0.6, size * 0.03 + i * 0.002, (r() - 0.5) * size * 0.5);
      if (form !== 'slice') for (let k = 0; k < 4; k++) {
        const f = add(new THREE.Mesh(new THREE.SphereGeometry(size * 0.05, 10, 8), mat('qf', L.tip, { roughness: 0.4 })));
        const t = len * (0.18 + k * 0.08); f.position.copy(s.position).add(new THREE.Vector3(Math.cos(s.rotation.y) * t, size * 0.03, -Math.sin(s.rotation.y) * t));
        f.scale.set(1, 0.6, 1.2);
      }
    }
  } else if (material === 'chilu-berry') {
    const n = form === 'slice' ? 10 : 12;
    for (let i = 0; i < n; i++) {
      const rad = size * (0.075 + r() * 0.02);
      const geo = form === 'slice' ? new THREE.SphereGeometry(rad, 14, 8, 0, Math.PI * 2, 0, Math.PI / 2) : new THREE.SphereGeometry(rad, 14, 10);
      const b = add(new THREE.Mesh(geo, mat('cb', L.stem, { roughness: 0.25 })));
      const a = r() * Math.PI * 2, d = Math.sqrt(r()) * size * 0.32;
      b.position.set(Math.cos(a) * d, form === 'slice' ? 0 : rad * (0.9 + (i > 7 ? 1.4 : 0)), Math.sin(a) * d);
      if (form === 'slice') { b.rotation.x = Math.PI; b.position.y = rad * 0.02; const cut = add(new THREE.Mesh(new THREE.CircleGeometry(rad * 0.92, 14), mat('cc', L.tip))); cut.rotation.x = -Math.PI / 2; cut.position.copy(b.position).setY(rad * 0.03); }
    }
    for (let i = 0; i < 2; i++) { const lf = add(new THREE.Mesh(new THREE.CircleGeometry(size * 0.16, 5), mat('cl', L.speck, { side: THREE.DoubleSide }))); lf.rotation.x = -Math.PI / 2; lf.scale.set(1, 0.45, 1); lf.position.set((i - 0.5) * size * 0.5, 0.002, size * 0.3); }
  } else {
    for (let i = 0; i < 4; i++) {
      const h = size * (0.32 + r() * 0.22), w = size * 0.07;
      const c = add(new THREE.Mesh(new THREE.CylinderGeometry(w, w, h, 6), std(L.stem, { roughness: 0.15, transparent: true, opacity: 0.88, emissive: '#3a8f70', emissiveIntensity: 0.35 })));
      const tip = new THREE.Mesh(new THREE.ConeGeometry(w, h * 0.35, 6), c.material); tip.position.y = h * 0.67; c.add(tip);
      c.position.set((r() - 0.5) * size * 0.4, h / 2 * 0.8, (r() - 0.5) * size * 0.3); c.rotation.set((r() - 0.5) * 0.9, r() * 3, (r() - 0.5) * 1.6);
    }
  }
  return g;
}

function labelTexture(text, sub) {
  const c = document.createElement('canvas'); c.width = 256; c.height = 128; const g = c.getContext('2d');
  g.fillStyle = '#e6e4da'; g.fillRect(0, 0, 256, 128);
  if (!text) { g.fillStyle = '#9a978d'; g.font = 'bold 72px serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('？', 128, 66); }
  else {
    g.fillStyle = '#23211d'; g.font = 'bold 54px "Microsoft JhengHei", "Noto Serif TC", serif'; g.textBaseline = 'middle'; g.fillText(text, 14, 50, 176);
    g.font = '30px "Microsoft JhengHei", serif'; g.fillStyle = '#4a463e'; g.fillText(sub, 16, 100);
    g.fillStyle = '#a3291d'; g.fillRect(196, 70, 46, 46); g.fillStyle = '#e6e4da'; g.font = 'bold 30px serif'; g.fillText('辨', 204, 94);
  }
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}

// B05: drawers are glTF nodes *Drawer1/2/3* (bottom to top). While the B05 card is open the drawer of the batch in
// focus slides fully out (the others stay shut, so nothing hides its contents). Each drawer holds one bag batch; its porcelain
// label shows "？" until that batch is identified, then the name, element / nature and a red 辨 seal.
const DRAWER_Z = [0.205, 0.455, 0.700], DRAWER_OPEN = 0.28, LABEL = { x: 0.13, y: -0.2248, w: 0.064, h: 0.032 };
export function makeCabinet(cabinet, bag, materials) {
  const drawers = [1, 2, 3].map(i => { let n; cabinet.traverse(o => { if (!n && /Drawer\d/.test(o.name) && o.name.includes(`Drawer${i}`)) n = o; }); return n; });
  const top = drawers.slice().reverse();   // bag[0] -> top drawer
  const slots = bag.map((b, k) => {
    const node = top[k], zc = DRAWER_Z[2 - k]; if (!node) return null;
    const base = node.position.clone();
    const pile = materialPile(b.material, 'raw', 0.22, 11 + k); pile.position.copy(bl(0.02, -0.04, zc - 0.095));   // middle of the pulled-out part
    const label = new THREE.Mesh(new THREE.PlaneGeometry(LABEL.w, LABEL.h), new THREE.MeshStandardMaterial({ map: labelTexture(), roughness: 0.4 }));
    label.position.copy(bl(LABEL.x, LABEL.y, zc));
    cabinet.add(pile, label); cabinet.updateMatrixWorld(true); node.attach(pile); node.attach(label);
    return { batch: b.batchId, material: b.material, node, base, t: 0, label, seen: false };
  }).filter(Boolean);
  return {
    // open: whether the B05 card is up; identified: batch ids already identified; focus: batch whose drawer is pulled
    update(dt, open, identified, focus) {
      for (const s of slots) {
        const want = open && s.batch === focus ? 1 : 0; s.t += (want - s.t) * (1 - Math.exp(-dt * 6));
        s.node.position.copy(s.base).add(new THREE.Vector3(0, 0, DRAWER_OPEN * s.t));
        const seen = identified.includes(s.batch);
        if (seen !== s.seen) { const m = materials[s.material]; s.label.material.map.dispose(); s.label.material.map = labelTexture(seen ? m.name : null, `${m.element}・${m.nature}`); s.label.material.needsUpdate = true; s.seen = seen; }
      }
    },
  };
}

// B04: upper tray = main ingredient, lower tray = auxiliary, each shown in its current processing form.
const TRAY = { main: 0.47, aux: 0.215 }, TILT = THREE.MathUtils.degToRad(-9);
export function makeTrays(rack) {
  const holders = {}, cur = {};
  for (const [role, z] of Object.entries(TRAY)) {
    const h = new THREE.Group(); h.position.copy(bl(0, 0, z + 0.008)); h.rotation.x = TILT; rack.add(h); holders[role] = h;
  }
  return {
    // loads: { main: { material, form } | null, aux: ... }
    set(loads) {
      for (const role of Object.keys(TRAY)) {
        const l = loads[role], key = l ? `${l.material}:${l.form}` : '';
        if (cur[role] === key) continue; cur[role] = key; holders[role].clear();
        if (!l) continue;
        for (const [i, x] of [[0, -0.12], [1, 0.11]]) { const p = materialPile(l.material, l.form, 0.17, 30 + i + (role === 'aux' ? 9 : 0)); p.position.x = x; p.rotation.y = i * 1.3; holders[role].add(p); }
      }
    },
  };
}

// Steam puffs rising from the heated lid's vent (a world-space point supplied each frame).
export function makeSteam(scene) {
  const c = document.createElement('canvas'); c.width = c.height = 64; const g = c.getContext('2d');
  const grd = g.createRadialGradient(32, 32, 0, 32, 32, 32); grd.addColorStop(0, 'rgba(255,255,255,0.9)'); grd.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = grd; g.fillRect(0, 0, 64, 64);
  const tex = new THREE.CanvasTexture(c), puffs = [];
  for (let i = 0; i < 10; i++) {
    const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, depthWrite: false, opacity: 0 }));
    s.userData.age = i / 10; scene.add(s); puffs.push(s);
  }
  return {
    update(dt, on, origin) {
      for (const s of puffs) {
        s.userData.age = (s.userData.age + dt / 2.2) % 1; const a = s.userData.age;
        s.position.copy(origin).add(new THREE.Vector3(Math.sin(a * 5 + s.id) * 0.03 + a * 0.05, a * 0.55, Math.cos(a * 4 + s.id) * 0.03));
        const k = 0.07 + a * 0.28; s.scale.set(k, k, k);
        s.material.opacity = on ? Math.sin(a * Math.PI) * 0.6 : 0;
      }
    },
  };
}
