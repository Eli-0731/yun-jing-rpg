// Writes apps/game/Assets/YunJing/Data/QingxiAbcZones.json for the Unity main-scene builder:
// the A/B/C zone layouts plus parity scenarios recorded from A's original encounter.mjs.
// QingxiForestEncounterSmoke replays the same inputs on the C# port and must emit the same events.
//   node tools/qingxi-main-scene/build-data.mjs
import { writeFileSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { Encounter } from '../qingxi-encounter-a/encounter.mjs';
import { forestLayout, forestWorld, platform, alchemyLayout, alchemyTable, alchemyDoor, returnLayout, returnTable } from './zones.mjs';

const DT = 1 / 60;
const round = v => Math.round(v * 1000) / 1000;

// A scripted player: decisions read the simulation, every input is recorded with its tick so the
// C# port can replay the identical input stream without needing the same decision code.
function record(name, style, maxSeconds, decide, faceRabbit = true) {
  const e = new Encounter(forestWorld, { style });
  const commands = [], events = [];
  const memo = {};
  for (let tick = 0; tick < Math.round(maxSeconds / DT) && !memo.done; tick++) {
    const cmd = decide(e, memo, tick) || {};
    if (cmd.move) e.move(...cmd.move);
    if (cmd.face !== undefined) e.face(cmd.face);
    if (cmd.block !== undefined) e.setBlock(cmd.block);
    if (cmd.attack) e.attack(cmd.attack);
    if (cmd.dodge) e.dodge();
    if (cmd.reset) e.resetAtSafePoint();
    // Fixed shape for Unity's JsonUtility: empty arrays / strings mean "not sent this tick".
    if (Object.keys(cmd).length) commands.push({ tick, m: cmd.move || [], f: cmd.face === undefined ? [] : [cmd.face],
      b: cmd.block === undefined ? [] : [cmd.block ? 1 : 0], a: cmd.attack || '', d: !!cmd.dodge, r: !!cmd.reset });
    if (faceRabbit) e.face(Math.atan2(e.rabbit.x - e.player.x, e.rabbit.z - e.player.z));
    e.step(DT);
    for (const ev of e.drainEvents()) {
      events.push({ t: ev.t, type: ev.type, state: ev.state || '', reason: ev.reason || '', kind: ev.kind || '', hp: ev.hp ?? -1 });
      if (ev.type === 'won' || ev.type === 'downed') memo.done = memo.done || ev.type;
    }
  }
  const p = e.player, r = e.rabbit;
  return { name, style, faceRabbit, ticks: Math.round(e.time / DT), commands, events,
    final: { outcome: e.outcome || '', playerX: round(p.x), playerZ: round(p.z), playerHp: p.hp, rabbitHp: r.hp, rabbitState: r.state } };
}

const towardBurrow = (e, speed = 1) => [0, Math.sign(forestWorld.burrow.z - e.player.z) * speed];

const scenarios = [
  // Read the tell, parry the charge, punish the opening with 看破綻 until the rabbit is driven off.
  record('parry-and-punish', 'sword', 25, (e, m) => {
    const s = e.rabbit.state;
    if (!m.stopped && e.player.z < -3) return { move: towardBurrow(e) };
    if (!m.stopped) { m.stopped = true; return { move: [0, 0] }; }
    if (s === 'charge' && !e.player.blocking) return { block: true };
    if (s === 'stagger' && e.player.blocking) return { block: false };
    if (s === 'stagger' && !e.player.blocking && e.player.attackT === 0 && Math.hypot(e.rabbit.x - e.player.x, e.rabbit.z - e.player.z) > 1.7) {
      return { move: [Math.sign(e.rabbit.x - e.player.x) * 0.6, Math.sign(e.rabbit.z - e.player.z)] };
    }
    if (s === 'stagger' && e.player.attackT === 0) return { move: [0, 0], attack: 'technique' };
    if (s !== 'stagger' && (e.player.moveX || e.player.moveZ)) return { move: [0, 0] };
  }),
  // Body style that never defends: three hits put the player down and the rabbit withdraws.
  record('stand-and-get-hit', 'body', 25, (e, m) => {
    if (!m.stopped && e.player.z < -3.2) return { move: towardBurrow(e) };
    if (!m.stopped) { m.stopped = true; return { move: [0, 0] }; }
  }),
  // Warm up on the A12 dummy, then side-dodge through charges and retreat to the shelter.
  record('dummy-dodge-retreat', 'sword', 25, (e, m, tick) => {
    const p = e.player;
    // Step off the shelter posts, walk along the inside of the fence to the A12 dummy.
    if (!m.phase) { m.phase = 'up'; return { move: [0, 1] }; }
    if (m.phase === 'up' && p.z >= -9.7) { m.phase = 'east'; return { move: [1, 0] }; }
    if (m.phase === 'east' && p.x >= 2.6) { m.phase = 'swing'; return { move: [0, 0], face: Math.atan2(3.4 - p.x, -10.6 - p.z) }; }
    if (m.phase === 'swing' && (m.swings || 0) < 5 && p.attackT === 0) { m.swings = (m.swings || 0) + 1; return { attack: m.swings % 2 ? 'technique' : 'basic' }; }
    // Back through the gap between the A08 fences and up the rabbit trail.
    if (m.phase === 'swing' && m.swings >= 5 && p.attackT === 0) { m.phase = 'west'; return { move: [-1, 0] }; }
    if (m.phase === 'west' && p.x <= 0) { m.phase = 'trail'; m.walking = true; return { move: [0, 1], face: 0 }; }
    if (m.phase === 'trail' && !m.stopped && p.z > -3) { m.stopped = true; return { move: [0, 0] }; }
    if (m.stopped && e.rabbit.state === 'charge' && !m.dodged) { m.dodged = tick; return { move: [1, 0], dodge: true }; }
    if (m.dodged && tick === m.dodged + 25) return { move: [0, 0] };
    if (m.dodged && tick === m.dodged + 140) return { move: [0, -1] };
    if (m.dodged && e.inSafeZone() && !m.safe) { m.safe = true; return { move: [0, 0] }; }
    if (m.safe && e.rabbit.state === 'idle') m.done = true;
  }, false),
];

const out = {
  generatedBy: 'tools/qingxi-main-scene/build-data.mjs',
  note: '本機整合資料：林地遭遇規則與擺位來自 Johnnnny0823 的 tools/qingxi-encounter-a；丹房擺位來自 joshsu54 的 AlchemyRoomBuilder；回村角擺位來自 Eli-0731 的 batch2-manifest.json。',
  forest: {
    layout: forestLayout.map(it => ({ ...it, rot: round(it.rot) })),
    platform,
    world: forestWorld,
    parity: scenarios,
  },
  alchemy: { layout: alchemyLayout, table: alchemyTable, door: alchemyDoor },
  ret: { layout: returnLayout, table: returnTable },
};
const target = resolve(import.meta.dirname, '../../apps/game/Assets/YunJing/Data/QingxiAbcZones.json');
mkdirSync(dirname(target), { recursive: true });
writeFileSync(target, JSON.stringify(out, null, 1) + '\n');
for (const s of scenarios) console.log(`${s.name}: ${s.events.length} events, ${s.commands.length} inputs, outcome=${s.final.outcome}, rabbit=${s.final.rabbitState}/${s.final.rabbitHp}hp, player hp=${s.final.playerHp}`);
console.log('QINGXI_ABC_DATA_OK', target);
