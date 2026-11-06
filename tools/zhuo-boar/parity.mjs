// Copies the encounter content to where Unity can load it, and records runs from zhuo-boar-rules.mjs for the C# port
// (QingxiZhuoBoarRules). QingxiZhuoBoarSmoke replays the same inputs and must match.
//   node tools/zhuo-boar/parity.mjs
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { ZhuoBoarEncounter } from './zhuo-boar-rules.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const raw = readFileSync(resolve(root, 'packages/content/zhuo-boar-encounter-v1.json'), 'utf8');
const content = JSON.parse(raw);
const r6 = v => Math.round(v * 1e6) / 1e6;
const OBSTACLES = [
  { id: 'D3_BoarTree_01', x: -4, z: 2, r: .175 },
  { id: 'D3_BoarTree_02', x: 4, z: 3, r: .175 },
  { id: 'D3_BoarTree_03', x: 0, z: -4, r: .175 },
  { id: 'Stone_01', x: 5, z: -5, r: .8 },
  { id: 'Stone_02', x: -6, z: -3, r: .7 },
];
const BOUNDS = { minX: -10, maxX: 10, minZ: -10, maxZ: 10 };

/** Plays at a fixed step. `policy(boar, state)` returns the wanted player position, held key and dodge for this frame. */
function run(name, step, seconds, policy) {
  const boar = new ZhuoBoarEncounter(content, { x: 0, z: 7, yaw: Math.PI, stamina: 40 });
  boar.begin();
  const inputs = [], log = [];
  let now = 0, frame = 0, last = '';
  const memo = {};
  while (now < seconds) {
    now += step; frame++;
    const want = policy(boar, memo);
    const stamp = `${want.player.x}|${want.player.z}|${want.held ? 1 : 0}|${want.dodge?.x ?? ''}|${want.dodge?.z ?? ''}`;
    if (stamp !== last) {
      inputs.push({ frame, px: r6(want.player.x), pz: r6(want.player.z), held: !!want.held, hasDodge: !!want.dodge, dx: want.dodge?.x ?? 0, dz: want.dodge?.z ?? 0 });
      last = stamp;
      // The C# run sees the rounded position, so this one does too.
      want.player = { x: r6(want.player.x), z: r6(want.player.z) };
    } else want.player = { x: inputs.at(-1).px, z: inputs.at(-1).pz };
    const r = boar.update(now, { player: want.player, obstacles: OBSTACLES, bounds: BOUNDS, cleanseHeld: want.held, dodge: want.dodge ?? null });
    for (const e of r.events) log.push(`${r6(boar.time)}:${e.type}${e.obstacle ? ':' + e.obstacle : ''}${e.hits ? ':' + e.hits : ''}${e.count ? ':' + e.count : ''}`);
  }
  return { name, step, frames: frame, inputs, log, state: boar.state, x: r6(boar.x), z: r6(boar.z), yaw: r6(boar.yaw), hits: boar.hits, cleanses: boar.cleanses, stamina: boar.stamina };
}

/** Stands behind a tree on the boar's far side, walks up and holds through each daze. */
function clean(boar, memo) {
  if (boar.state === 'daze') return { player: { x: boar.x + 1, z: boar.z }, held: true };
  if (boar.state === 'alert' || !memo.spot) {
    const tree = OBSTACLES[memo.turn = ((memo.turn ?? -1) + (memo.wasDaze ? 1 : 0)) % 3 < 0 ? 0 : ((memo.turn ?? 0) + (memo.wasDaze ? 1 : 0)) % 3];
    const dx = tree.x - boar.x, dz = tree.z - boar.z, m = Math.hypot(dx, dz) || 1;
    memo.spot = { x: tree.x + dx / m * 1.5, z: tree.z + dz / m * 1.5 };
    memo.wasDaze = false;
  }
  if (boar.state === 'charge') memo.wasDaze = true;
  return { player: memo.spot };
}

/** Stands still on the charge line each time. */
function stand(boar, memo) {
  if (boar.state !== 'charge') memo.spot = { x: boar.x + Math.sin(boar.yaw) * 3, z: boar.z + Math.cos(boar.yaw) * 3 };
  return { player: memo.spot };
}

/** Pressed into a corner, so it keeps having to move. */
function corner(boar, memo) {
  return { player: { x: 9.2, z: 9.2 } };
}

/** Dodges every charge once it is close, and stays in the open. */
function dodging(boar, memo) {
  const player = { x: 0, z: 0 };
  const near = Math.hypot(boar.x, boar.z) < 2.5;
  return { player, dodge: boar.state === 'charge' && near ? { x: 1, z: 0 } : null };
}

const data = {
  source: 'tools/zhuo-boar/zhuo-boar-rules.mjs (Johnnnny0823)',
  runs: [
    run('cleanse-60fps', 1 / 60, 40, clean),
    run('cleanse-30fps', 1 / 30, 40, clean),
    run('three-hits-then-return', 1 / 60, 50, stand),
    run('dodging', 1 / 45, 20, dodging),
    run('cornered', 1 / 60, 30, corner),
  ],
};
const unity = resolve(root, 'apps/game/Assets/YunJing/Resources/QingxiZhuoBoar');
mkdirSync(unity, { recursive: true });
writeFileSync(resolve(unity, 'zhuo-boar-encounter-v1.json'), raw);
writeFileSync(resolve(root, 'apps/game/Assets/YunJing/Data/QingxiZhuoBoarParity.json'), JSON.stringify(data, null, 1) + '\n');
console.log('wrote', data.runs.map(r => `${r.name}:${r.state} hits=${r.hits} cleanses=${r.cleanses} stamina=${r.stamina} events=${r.log.length}`).join('\n      '));
