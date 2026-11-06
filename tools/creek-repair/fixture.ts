import { writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { advanceFlow, buildAqueduct, creek, CreekState, cycleGate, gateOpen, setGate, isOnBeat, layoutOf, METHODS, newCreek, patch, place, scoop, siltLeft, stonesShowing, turnWheel, workLeft, scrape } from './rules';

// npm run build && node dist/tools/creek-repair/fixture.js — rewrites the replay fixture Unity checks CreekRepairSim.cs against.
const snap = (s: CreekState) => ({
  silt: siltLeft(s), work: workLeft(s), wheel: s.wheelDegrees, flow: +s.flowM.toFixed(4), reached: s.reached.length, done: s.done, events: s.events.length,
  layout: Object.entries(layoutOf(s)).map(([k, v]) => k + '=' + v).join(','),
  stones: creek.methods[s.method].piles.map(p => stonesShowing(s, p.id)).join(','), slumped: s.slumped.join(','),
  levels: creek.distribution.gates.map(g => s.gates[g.id].level).join(','), fill: +creek.distribution.gates.reduce((a, g) => a + s.gates[g.id].fill, 0).toFixed(4), moves: s.gateLog.length, lastBy: s.gateLog.at(-1)?.by ?? '', together: s.together,
});
const cases = METHODS.flatMap(method => [1, 2, 3, 4].map(partySize => {
  const s = newCreek(method, partySize), m = creek.methods[method], steps: unknown[] = [];
  const log = (op: string, a: string, b: string, n: number, n2: number, r: { code: string; gapCm?: number }) => steps.push({ op, a, b, n, m: n2, code: r.code, gapCm: r.gapCm ?? 0, after: snap(s) });
  log('wheel', '', '', 90, 0, turnWheel(s, 90));
  log('scoop', m.piles[0].id, '', .2, 1, scoop(s, m.piles[0].id, .2, 1));
  log('scoop', m.piles[0].id, '', .9, .1, scoop(s, m.piles[0].id, .9, .1));
  log('scoop', m.piles[0].id, '', .45, 1, scoop(s, m.piles[0].id, .45, 1));
  // every kind of stroke on every pile: on the beat, wrong way, right way, missing a spot, then each weak spot twice
  const stroke = (id: string, n: number, sec: number, h: { at?: readonly number[]; dir?: readonly number[]; onBeat?: boolean }) => {
    const r = scoop(s, id, n, sec, h);
    steps.push({ op: 'stroke', a: id, b: '', n, m: sec, x: h.at ? h.at[0] : 0, z: h.at ? h.at[1] : 0, hasAt: !!h.at, dx: h.dir ? h.dir[0] : 0, dz: h.dir ? h.dir[1] : 0, hasDir: !!h.dir, beat: !!h.onBeat, code: r.code, gapCm: 0, after: snap(s) });
  };
  const scraped = (id: string, n: number, h: { at?: readonly number[]; onBeat?: boolean }) => {
    const r = scrape(s, id, n, h);
    steps.push({ op: 'scrape', a: id, b: '', n, m: 0, x: h.at ? h.at[0] : 0, z: h.at ? h.at[1] : 0, hasAt: !!h.at, dx: 0, dz: 0, hasDir: false, beat: !!h.onBeat, code: r.code, gapCm: r.gapCm ?? 0, after: snap(s) });
  };
  for (const p of m.piles) {
    if (s.silt[p.id] <= 0) continue;
    scraped(p.id, 0, {}); scraped(p.id, .137, {}); scraped(p.id, .5, { onBeat: true }); scraped(p.id, .25, { at: [9, 9] });
    if (p.spots[0] && p.kind !== 'weed') { scraped(p.id, 0, { at: p.spots[0].pos }); scraped(p.id, 0, { at: p.spots[0].pos }); }
  }
  for (const p of m.piles) {
    if (s.silt[p.id] <= 0) continue;
    stroke(p.id, .4, 1, {});
    stroke(p.id, 1, 1, { onBeat: true });
    stroke(p.id, 1, .1, { onBeat: true });
    stroke(p.id, 1, 1, { dir: [-p.pull[0], -p.pull[1]] });
    stroke(p.id, 1, 1, { dir: p.pull, onBeat: true });
    stroke(p.id, 1, 1, { at: [9, 9] });
    for (const o of p.spots) if (s.silt[p.id] > 0) { stroke(p.id, 1, 1, { at: o.pos }); if (s.silt[p.id] > 0) stroke(p.id, 1, 1, { at: o.pos }); }
  }
  for (const t of [0, .69, .7, 1, 1.3, 1.31, 2, 2.7, 3.3, 3.31, -1]) steps.push({ op: 'beat', a: '', b: '', n: t, m: 0, beat: isOnBeat(t), code: '', gapCm: 0, after: snap(s) });
  for (const w of m.work) {
    for (const o of w.options) if (o.piece !== w.piece) log('place', w.slot, o.piece, 0, 0, place(s, w.slot, o.piece));
    log('place', w.slot, w.piece, 0, 0, place(s, w.slot, w.piece));
  }
  for (const p of m.patches) { log('patch', p.slot, p.wrong, 0, 0, patch(s, p.slot, p.wrong)); log('patch', p.slot, p.piece, 0, 0, patch(s, p.slot, p.piece)); }
  log('aqueduct', '', '', 0, 0, buildAqueduct(s));
  for (const p of m.piles) while (s.silt[p.id] > 0) log('scoop', p.id, '', 1, 1, scoop(s, p.id, 1, 1));
  log('wheel', '', '', -90, 0, turnWheel(s, -90));
  while (!gateOpen(s)) log('wheel', '', '', 180, 0, turnWheel(s, 180));
  const gate = (id: string, level: number) => log('gate', id, 'player', level, 0, setGate(s, id, level));
  const cycle = (id: string) => log('cycle', id, 'player', 0, 0, cycleGate(s, id));
  gate('nope', 1); gate('gate_a', .3); gate('gate_a', 0);
  // every party size plays the gates differently: the sign's plan, nothing at all, changing their mind, and shutting everything
  if (partySize === 1) { cycle('gate_a'); cycle('gate_a'); cycle('gate_b'); cycle('gate_c'); } else if (partySize === 3) gate('gate_b', 1);
  let ticks = 0;
  while (!s.done) {
    advanceFlow(s, 2.5); steps.push({ op: 'flow', a: '', b: '', n: 2.5, m: 0, code: '', gapCm: 0, after: snap(s) }); ticks++;
    if (partySize === 3 && ticks === 40) { gate('gate_c', .5); cycle('gate_c'); gate('gate_b', 0); }
    if (partySize === 4 && ticks % 9 === 0) for (const g of creek.distribution.gates) gate(g.id, 0);
    if (s.done) { gate('gate_a', 1); cycle('gate_a'); }
  }
  return { method, partySize, steps };
}));
const file = join(__dirname, '..', '..', '..', 'tests', 'fixtures', 'creek-repair-trace.json');
writeFileSync(file, JSON.stringify({ cases }) + '\n');
console.log('wrote', file);
