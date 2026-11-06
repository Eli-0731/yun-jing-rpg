// Copies the combat content to where Unity can load it, and records scripted runs from basic-combat-rules.mjs for the C# port
// (QingxiBasicCombatRules). QingxiBasicCombatSmoke replays the same inputs and must produce the same events and positions.
//   node tools/basic-combat/parity.mjs
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { BasicCombat } from './basic-combat-rules.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const raw = readFileSync(resolve(root, 'packages/content/basic-combat-v1.json'), 'utf8');
const content = JSON.parse(raw);
const r6 = v => Math.round(v * 1e6) / 1e6;

/** schedule: [{at, attack?, heavyHeld?, dodge?, mx?, mz?}] — heavyHeld/mx/mz persist until changed; attack/dodge are one-frame presses. */
function run(name, step, seconds, targets, schedule) {
  const f = new BasicCombat(content, { x: 0, z: 0, yaw: 0 });
  const frames = [], log = [];
  let held = false, mx = 0, mz = 0, k = 0;
  for (let frame = 1, now = 0; now < seconds; frame++) {
    now = r6(frame * step);
    let attack = false, dodge = false, changed = false;
    while (k < schedule.length && schedule[k].at <= now + 1e-9) {
      const s = schedule[k++];
      if (s.attack) attack = true;
      if (s.dodge) dodge = true;
      if (s.heavyHeld !== undefined) held = s.heavyHeld;
      if (s.mx !== undefined) { mx = s.mx; mz = s.mz; }
      changed = true;
    }
    if (changed) frames.push({ frame, attack, dodge, held, mx, mz });
    const evs = f.update(now, { attack, dodge, heavyHeld: held, move: { x: mx, z: mz } }, targets);
    for (const e of evs) log.push(`${r6(e.t)}:${e.type}${e.attackId ? ':' + e.attackId : ''}${e.targetId ? ':' + e.targetId : ''}${e.damage !== undefined ? ':' + e.damage : ''}`);
  }
  return { name, step, seconds, targets, frames, log, state: f.state, x: r6(f.x), z: r6(f.z), yaw: r6(f.yaw), heavyCooldown: r6(f.heavyCooldown) };
}

const post = [{ id: 'A12_VineDummy', x: 0.3, z: 1.4, radius: 0.35 }];
const ring = [{ id: 'rabbit', x: -1.2, z: 1.0, radius: 0.25 }, { id: 'boar', x: 2.6, z: 1.8, radius: 0.6 }, { id: 'far', x: 6, z: 0, radius: 0.3 }];
const runs = [
  run('chain-three', 1 / 60, 2.2, post, [
    { at: 0.1, attack: true }, { at: 0.15, attack: true }, { at: 0.48, attack: true }, { at: 0.93, attack: true }, { at: 1.5, attack: true },
  ]),
  run('heavy-and-cooldown', 1 / 50, 6.5, post, [
    { at: 0.1, heavyHeld: true }, { at: 0.3, heavyHeld: false }, { at: 0.5, heavyHeld: true }, { at: 1.3, heavyHeld: false },
    { at: 2.4, heavyHeld: true }, { at: 2.6, heavyHeld: false }, { at: 5.0, heavyHeld: true }, { at: 6.4, heavyHeld: false },
  ]),
  run('dodge-cancel', 1 / 60, 2.4, ring, [
    { at: 0.1, attack: true }, { at: 0.18, dodge: true, mx: 1, mz: 0 }, { at: 0.5, dodge: true }, { at: 0.55, mx: 0, mz: 0 },
    { at: 0.9, heavyHeld: true }, { at: 1.0, dodge: true, mx: -1, mz: 0.3 }, { at: 1.05, heavyHeld: false }, { at: 1.6, attack: true },
  ]),
  run('turn-to-nearest', 1 / 30, 1.5, ring, [{ at: 0.2, attack: true }, { at: 0.75, attack: true }]),
];

const out = { content: 'basic-combat-v1', runs };
mkdirSync(resolve(root, 'apps/game/Assets/YunJing/Data'), { recursive: true });
writeFileSync(resolve(root, 'apps/game/Assets/YunJing/Data/QingxiBasicCombatParity.json'), JSON.stringify(out, null, 1) + '\n');
mkdirSync(resolve(root, 'apps/game/Assets/YunJing/Resources/BasicCombat'), { recursive: true });
writeFileSync(resolve(root, 'apps/game/Assets/YunJing/Resources/BasicCombat/basic-combat-v1.json'), raw);
for (const r of runs) console.log(r.name, r.log.length, 'events', r.state, r.x, r.z);
