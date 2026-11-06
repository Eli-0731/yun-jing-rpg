import { test } from 'node:test';
import assert from 'node:assert/strict';
import waterline from '../packages/content/waterline.json';
import {
  advanceFlow, board, buildAqueduct, catalog, core, coreCtx, creek, CreekState, cycleGate, estimateSeconds, fieldFull, gateOpen, setGate, gatesOf, isOnBeat, layoutOf, joinLeader, loadCreek, METHODS, MethodId, newCreek, checkParty,
  patch, pileMass, place, routeLength, saveCreek, scoop, siltLeft, spotAt, stonesShowing, turnWheel, wetFields, workDone, scrape,
} from '../tools/creek-repair/rules';

// 修水路 (work pack B-56h section 1): clear, join, open the wheel. Never fails.
const method = (m: MethodId) => creek.methods[m];
const names = (s: CreekState, n: string) => s.events.filter(e => e.name === n);
const dig = (s: CreekState, pile: string) => { while (s.silt[pile] > 0) assert.ok(scoop(s, pile, 1, 1).ok); };

function tasks(s: CreekState, m: MethodId): (() => void)[] {
  const d = method(m), list: (() => void)[] = [];
  for (const p of d.piles) list.push(() => dig(s, p.id));
  for (const w of d.work) list.push(() => assert.ok(place(s, w.slot, w.piece).ok));
  for (const p of d.patches) list.push(() => assert.ok(patch(s, p.slot, p.piece).ok));
  if (d.aqueduct) list.push(() => assert.ok(buildAqueduct(s).ok));
  return list;
}
function finishWork(s: CreekState) { for (const t of tasks(s, s.method)) t(); }
function finishAll(s: CreekState) {
  finishWork(s);
  while (!gateOpen(s)) turnWheel(s, 90);
  while (!s.done) advanceFlow(s, 1);
}
function permutations<T>(items: T[]): T[][] {
  if (items.length <= 1) return [items];
  return items.flatMap((x, i) => permutations([...items.slice(0, i), ...items.slice(i + 1)]).map(rest => [x, ...rest]));
}

test('workload matches waterline.json: same ids, same channel count, same stone', () => {
  assert.deepEqual([...METHODS].sort(), waterline.choices.map(c => c.id).sort());
  for (const c of waterline.choices) {
    const m = method(c.id as MethodId);
    assert.equal(m.label, c.label, c.id);
    assert.equal(m.channel, c.channel, `${c.id} channel field`);
    assert.equal(m.work.length, c.channel, `${c.id} pieces the player joins`);
    assert.equal(m.stone, c.stone, `${c.id} stone`);
    assert.equal(!!m.aqueduct, !!(c as { sanctuary?: boolean }).sanctuary, `${c.id} aqueduct only where the nursery is protected`);
  }
  const mud = (m: MethodId) => method(m).piles.reduce((a, p) => a + p.mass, 0);
  assert.ok(mud('clear_silt') > mud('restore_channel') && mud('clear_silt') > mud('protect_nursery'), 'clear_silt has the most digging');
  assert.equal(method('restore_channel').patches.length, 1, 'restore_channel also patches the crack');
});

test('finished layouts pass waterworks-core with no blocking problem', () => {
  for (const m of METHODS) {
    const s = newCreek(m); finishWork(s);
    const design = { placed: layoutOf(s), patches: s.patches, gates: gatesOf(m), choice: m };
    const ev = core.evaluate(coreCtx, design, { truth: true });
    assert.deepEqual(ev.blocking.map((i: { code: string }) => i.code), [], `${m} blocking`);
    assert.deepEqual(core.checkChoice(coreCtx, design, ev).map((p: { code: string }) => p.code), [], `${m} choice`);
  }
});

test('the centimetre numbers in the content are what waterworks-core computes', () => {
  for (const m of METHODS) for (const w of method(m).work) {
    const slot = board.slots.find((x: { id: string }) => x.id === w.slot);
    const outs = (id: string) => core.placePiece(catalog.pieces[id], slot).ports.filter((p: { kind: string }) => p.kind !== 'in');
    const want = outs(w.piece)[0].pos;
    for (const o of w.options) {
      const gap = Math.min(...outs(o.piece).map((p: { pos: number[] }) => Math.hypot(p.pos[0] - want[0], p.pos[1] - want[1])));
      assert.equal(o.gapCm, Math.round(gap * 100), `${m} ${w.slot} ${o.piece}`);
      if (o.piece !== w.piece) assert.ok(o.message.length > 0);
      if (o.gapCm > 0) assert.ok(o.message.includes(`差 ${o.gapCm} cm`), o.message);
    }
    assert.ok(w.options.some(o => o.piece !== w.piece && o.gapCm > 0), `${m} ${w.slot} offers a piece that shows a gap`);
  }
});

test('a wrong piece says how far off it is and changes nothing', () => {
  const s = newCreek('restore_channel'), before = saveCreek(s);
  const r = place(s, 'P3', 'B03');
  assert.equal(r.ok, false); assert.equal(r.code, 'MISALIGNED'); assert.equal(r.gapCm, 79);
  assert.match(r.message, /差 79 cm/);
  assert.equal(saveCreek(s), before);
  assert.equal(place(s, 'P3', 'B02').ok, true);
  assert.equal(place(s, 'P3', 'B02').code, 'ALREADY_PLACED');
  assert.equal(place(s, 'L1', 'B02').code, 'NOT_WORK_SLOT');
  assert.equal(patch(s, 'P4', 'B07-V02').code, 'WRONG_PATCH');
  assert.equal(buildAqueduct(s).code, 'NO_AQUEDUCT');
});

test('mud is heavy: a short drag moves nothing, a snatch keeps half, stones show slowly', () => {
  const s = newCreek('clear_silt'), id = method('clear_silt').piles[0].id, total = s.silt[id];
  assert.equal(scoop(s, id, .2, 1).code, 'TOO_SHORT');
  assert.equal(s.silt[id], total);
  assert.equal(stonesShowing(s, id), 0);
  assert.equal(scoop(s, id, .9, 1).moved, 1);
  assert.equal(scoop(s, id, .9, .1).moved, .5);
  assert.equal(scoop(s, id, .45, 1).moved, .5);
  assert.equal(scoop(s, 'nope', 1, 1).code, 'NO_PILE');
  const seen = [stonesShowing(s, id)];
  while (s.silt[id] > 0) { scoop(s, id, 1, 1); seen.push(stonesShowing(s, id)); }
  assert.deepEqual(seen, [...seen].sort((a, b) => a - b), 'never hides a stone again');
  assert.equal(seen.at(-1), method('clear_silt').piles[0].stones);
  assert.equal(scoop(s, id, 1, 1).code, 'PILE_CLEAR');
});

test('five piles of clear_silt: each teaches something, and it is still the most mud of the three methods', () => {
  const piles = method('clear_silt').piles;
  assert.deepEqual(piles.map(p => p.kind), ['soft', 'hard', 'soft', 'weed', 'soft']);
  assert.deepEqual(piles.map(p => p.spots.length), [0, 0, 1, 1, 2]);
  const mud = (m: MethodId) => method(m).piles.reduce((a, p) => a + p.mass, 0);
  assert.equal(mud('clear_silt'), 34);
  assert.ok(mud('clear_silt') > mud('restore_channel') && mud('clear_silt') > mud('protect_nursery'));
  for (const m of METHODS) assert.ok(method(m).piles.some(p => p.spots.length > 0), `${m} has a weak spot`);
  for (const m of METHODS) for (const p of method(m).piles) assert.ok(p.spots.reduce((a, o) => a + o.slump, 0) < p.mass, `${m} ${p.id}: the last of it is still dug by hand`);
});

test('a weak spot brings the slope down once; missing it only means digging on', () => {
  const s = newCreek('clear_silt'), pile = method('clear_silt').piles[2], spot = pile.spots[0], total = s.silt[pile.id];
  assert.equal(spotAt(s, pile.id, spot.pos)?.id, spot.id);
  assert.equal(scoop(s, pile.id, 1, 1, { at: [spot.pos[0] + .5, spot.pos[1]] }).code, 'MOVED', 'a miss is an ordinary scoop');
  assert.equal(s.silt[pile.id], total - 1);
  const hit = scoop(s, pile.id, 1, 1, { at: spot.pos });
  assert.equal(hit.code, 'SLUMPED');
  assert.equal(hit.moved, 1 + spot.slump);
  assert.deepEqual(s.slumped, [`${pile.id}:${spot.id}`]);
  assert.equal(spotAt(s, pile.id, spot.pos), undefined);
  assert.equal(scoop(s, pile.id, 1, 1, { at: spot.pos }).code, 'MOVED', 'spent');
  assert.equal(scoop(s, pile.id, .2, 1, { at: spot.pos }).code, 'TOO_SHORT');
  const big = newCreek('clear_silt', 3), hit3 = scoop(big, pile.id, 1, 1, { at: spot.pos });
  assert.equal(hit3.moved, 1 + spot.slump * 3, 'a bigger party has a bigger slope');
  const near = newCreek('clear_silt'), last = method('clear_silt').piles[4];
  near.silt[last.id] = 1.5;
  assert.equal(scoop(near, last.id, 1, 1, { at: last.spots[1].pos }).moved, 1.5, 'never moves more mud than is left');
  assert.equal(near.silt[last.id], 0);
});

test('hard mud wants a long slow drag; weed comes away only outwards; neither can stop the work', () => {
  const s = newCreek('clear_silt'), hard = method('clear_silt').piles[1], weed = method('clear_silt').piles[3];
  assert.equal(scoop(s, hard.id, .5, 1).code, 'TOO_SHORT');
  assert.equal(scoop(s, hard.id, 1.2, .5).code, 'HURRIED');
  assert.equal(scoop(s, hard.id, 1.2, 1).moved, 1);
  const before = s.silt[weed.id], wrong = scoop(s, weed.id, .9, 1, { dir: [-weed.pull[0], -weed.pull[1]] });
  assert.equal(wrong.code, 'TANGLED');
  assert.ok(wrong.moved! > 0 && wrong.moved! < 1);
  assert.equal(s.silt[weed.id], +(before - wrong.moved!).toFixed(3));
  assert.equal(scoop(s, weed.id, .9, 1, { dir: weed.pull }).moved, 1);
  assert.equal(scoop(s, weed.id, .9, 1).moved, 1, 'no direction given (keyboard) is the right way');
  while (s.silt[weed.id] > 0) assert.ok(scoop(s, weed.id, .9, 1, { dir: [-weed.pull[0], -weed.pull[1]] }).ok, 'always the wrong way still finishes');
});

test('the chant only ever helps: on the 喲 moves more, off it moves the usual amount, a snatch earns nothing', () => {
  const c = creek.chant;
  assert.equal(isOnBeat(c.yoAtSeconds), true);
  assert.equal(isOnBeat(c.yoAtSeconds + c.cycleSeconds * 40), true);
  assert.equal(isOnBeat(c.yoAtSeconds - c.windowSeconds), true);
  assert.equal(isOnBeat(0), false);
  assert.equal(isOnBeat(-1), true);
  const id = method('clear_silt').piles[0].id;
  const on = newCreek('clear_silt'), off = newCreek('clear_silt');
  const r = scoop(on, id, .9, 1, { onBeat: true });
  assert.equal(r.onBeat, true);
  assert.equal(r.moved, creek.spade.beatKeep);
  assert.equal(scoop(off, id, .9, 1, { onBeat: false }).moved, 1);
  const snatch = scoop(newCreek('clear_silt'), id, .9, .1, { onBeat: true });
  assert.equal(snatch.moved, creek.spade.hurriedKeep);
  assert.equal(snatch.onBeat, false);
});

test('a skilled run is shorter than a new one, and every stroke style reaches the same finish', () => {
  for (const m of METHODS) {
    const plain = newCreek(m), skilled = newCreek(m);
    let plainN = 0, skilledN = 0;
    for (const p of method(m).piles) {
      while (plain.silt[p.id] > 0) { scoop(plain, p.id, 2, 1); plainN++; }
      for (const o of p.spots) { scoop(skilled, p.id, 2, 1, { at: o.pos, onBeat: true }); skilledN++; }
      while (skilled.silt[p.id] > 0) { scoop(skilled, p.id, 2, 1, { dir: p.pull, onBeat: true }); skilledN++; }
    }
    assert.ok(skilledN < plainN, `${m}: ${skilledN} < ${plainN}`);
    assert.equal(siltLeft(plain), 0);
    assert.equal(siltLeft(skilled), 0);
    finishWork(plain); finishWork(skilled);
    assert.deepEqual(layoutOf(plain), layoutOf(skilled), 'skill never changes the result');
    assert.equal(names(skilled, 'creek.workCompleted').length, 1);
  }
});

test('any order of the work finishes, and the event fires once at the end', () => {
  for (const m of METHODS) {
    const count = tasks(newCreek(m), m).length;
    for (const order of permutations([...Array(count).keys()])) {
      const s = newCreek(m), list = tasks(s, m);
      order.forEach((i, k) => {
        assert.equal(names(s, 'creek.workCompleted').length, 0, 'not before the last task');
        list[i]();
        if (k < count - 1) assert.equal(workDone(s), false);
      });
      assert.equal(workDone(s), true);
      const e = names(s, 'creek.workCompleted');
      assert.equal(e.length, 1);
      assert.deepEqual(e[0].data, { method: m, layout: layoutOf(s), patches: s.patches });
    }
  }
});

test('the wheel waits for the work, explains why, then the water walks the route', () => {
  for (const m of METHODS) {
    const s = newCreek(m);
    const blocked = turnWheel(s, 90);
    assert.equal(blocked.ok, false); assert.equal(blocked.code, 'WORK_PENDING'); assert.ok(blocked.message.length > 0);
    assert.equal(turnWheel(s, -90).code, 'WORK_PENDING');
    advanceFlow(s, 60); assert.equal(s.flowM, 0, 'no water before the gate is open');
    finishWork(s);
    assert.equal(turnWheel(s, -90).code, 'WRONG_WAY');
    while (!gateOpen(s)) { advanceFlow(s, 5); assert.equal(s.flowM, 0); turnWheel(s, 90); }
    assert.deepEqual(wetFields(s), []);
    const route = method(m).route.map(n => n.id);
    while (!s.done) advanceFlow(s, .5);
    assert.deepEqual(s.reached.slice(0, route.length), route, 'every node once, in order, then the fields');
    assert.equal(new Set(s.reached).size, route.length + 3);
    assert.deepEqual(names(s, 'creek.flowReached').map(e => e.data.nodeId), s.reached);
    assert.equal(names(s, 'creek.flowCompleted').length, 1);
    assert.deepEqual(names(s, 'creek.flowCompleted')[0].data, { method: m });
    assert.equal(wetFields(s).length, 3, 'several fields get wet');
    assert.equal(s.flowM, routeLength(m));
  }
});

test('events never repeat, even if the player keeps going after the end', () => {
  const s = newCreek('protect_nursery'); finishAll(s);
  const n = s.events.length;
  advanceFlow(s, 100); turnWheel(s, 720);
  scoop(s, method('protect_nursery').piles[0].id, 1, 1);
  assert.equal(buildAqueduct(s).code, 'ALREADY_PLACED');
  assert.equal(s.events.length, n);
  assert.equal(new Set(s.events.map(e => JSON.stringify(e))).size, n);
});

test('saving at any point and reloading gives the same run, with no repeated events', () => {
  for (const m of METHODS) {
    const reference = newCreek(m); finishAll(reference);
    const s0 = newCreek(m), list = tasks(s0, m);
    let s = loadCreek(saveCreek(s0));
    for (let i = 0; i < list.length; i++) { s = loadCreek(saveCreek(s)); tasks(s, m)[i](); }
    while (!gateOpen(s)) { s = loadCreek(saveCreek(s)); turnWheel(s, 90); }
    while (!s.done) { s = loadCreek(saveCreek(s)); advanceFlow(s, 1); }
    assert.deepEqual(s.reached, reference.reached);
    assert.deepEqual(layoutOf(s), layoutOf(reference));
    assert.equal(names(s, 'creek.workCompleted').length, 1);
    assert.equal(names(s, 'creek.flowCompleted').length, 1);
    assert.equal(names(s, 'creek.flowReached').length, method(m).route.length + 3);
  }
  assert.throws(() => loadCreek(JSON.stringify({ ...newCreek('clear_silt'), version: 'old' })), (e: any) => e.code === 'SAVE_VERSION');
  assert.throws(() => loadCreek(JSON.stringify({ ...newCreek('clear_silt'), method: 'x' })), (e: any) => e.code === 'METHOD');
});

test('partySize 1 to 4: the total grows with the party, each person spends about the same time, the layout stays', () => {
  for (const m of METHODS) {
    const solo = siltLeft(newCreek(m));
    for (const size of [1, 2, 3, 4]) {
      const s = newCreek(m, size);
      assert.equal(siltLeft(s), solo * size, `${m} ${size}: one carries 10, three carry 30`);
      assert.equal(siltLeft(s) / size, solo, 'digging per person is unchanged');
      assert.equal(estimateSeconds(m, size), estimateSeconds(m), 'each person spends about the same time');
      finishAll(s);
      assert.equal(s.done, true);
      assert.equal(s.partySize, size);
      assert.equal(names(s, 'creek.workCompleted').length, 1);
      assert.deepEqual(layoutOf(s), layoutOf((() => { const a = newCreek(m); finishWork(a); return a; })()));
      for (const p of method(m).piles) assert.equal(stonesShowing(s, p.id), p.stones);
    }
  }
  for (const bad of [0, 5, 1.5]) assert.throws(() => checkParty(bad), (e: any) => e.code === 'PARTY_SIZE');
  assert.throws(() => newCreek('clear_silt', 9), (e: any) => e.code === 'PARTY_SIZE');
});

test('a party: a dry member follows the leader and fires each event once; a repaired helper keeps their own creek', () => {
  const leader = newCreek('restore_channel', 3); finishAll(leader);
  const dry = newCreek('restore_channel', 3);
  assert.equal(joinLeader(dry, leader).code, 'JOINED');
  assert.equal(dry.done, true);
  assert.equal(names(dry, 'creek.workCompleted').length, 1);
  assert.equal(names(dry, 'creek.flowCompleted').length, 1);
  assert.equal(names(dry, 'creek.flowReached').length, method('restore_channel').route.length + 3);
  joinLeader(dry, leader);
  assert.equal(names(dry, 'creek.flowCompleted').length, 1, 'joining again repeats nothing');
  const helper = newCreek('clear_silt'); finishAll(helper); const kept = saveCreek(helper);
  assert.equal(joinLeader(helper, newCreek('protect_nursery', 2)).code, 'ALREADY_REPAIRED');
  assert.equal(saveCreek(helper), kept);
});

test('a solo run is planned at 5 to 8 minutes for every method', () => {
  for (const m of METHODS) {
    const t = estimateSeconds(m);
    assert.ok(t >= 300 && t <= 480, `${m} ${Math.round(t)} s`);
  }
});

test('water width differs by method, and it is the only thing besides looks that does', () => {
  const widths = METHODS.map(m => method(m).waterWidthM);
  assert.equal(new Set(widths).size, 3);
  for (const m of METHODS) { const s = newCreek(m); finishAll(s); assert.equal(wetFields(s).length, 3, `${m} waters the fields`); }
});

test('scraping takes what the blade carried off, and nothing can go wrong with it', () => {
  const s = newCreek('clear_silt'); const soft = 'silt_1', weed = 'silt_4'; const start = s.silt[soft];
  assert.equal(scrape(s, soft, 0).code, 'NOTHING_MOVED'); assert.equal(s.silt[soft], start);
  const r = scrape(s, soft, .37); assert.equal(r.code, 'MOVED'); assert.equal(r.moved, .37); assert.equal(s.silt[soft], +(start - .37).toFixed(3));
  assert.equal(scrape(s, soft, 99).moved, +(start - .37).toFixed(3), 'never moves more than is left'); assert.equal(s.silt[soft], 0);
  assert.equal(scrape(s, soft, 1).code, 'PILE_CLEAR');
  const left = s.silt[weed]; assert.equal(scrape(s, weed, 2).code, 'USE_DRAG'); assert.equal(s.silt[weed], left);
  assert.equal(scrape(s, 'nope', 1).code, 'NO_PILE');
});

test('a scrape through a weak spot brings it down once, even with no mud of its own, and the beat changes no amounts', () => {
  const s = newCreek('clear_silt'); const pile = method('clear_silt').piles[2]; const at = pile.spots[0].pos; const start = s.silt[pile.id];
  const slump = scrape(s, pile.id, 0, { at }); assert.equal(slump.code, 'SLUMPED'); assert.equal(slump.moved, pile.spots[0].slump);
  assert.equal(scrape(s, pile.id, 0, { at }).code, 'NOTHING_MOVED', 'spent');
  const onBeat = scrape(s, pile.id, .5, { onBeat: true }); assert.equal(onBeat.onBeat, true); assert.equal(onBeat.moved, .5);
  assert.equal(s.silt[pile.id], start - pile.spots[0].slump - .5);
  const big = newCreek('clear_silt', 3); assert.equal(scrape(big, pile.id, 0, { at }).moved, pile.spots[0].slump * 3);
});

// ---- gates: the fields share the water, set before it comes or while it runs. Nothing here can fail.
const G = creek.distribution, canal = (s: CreekState) => { finishWork(s); while (!gateOpen(s)) turnWheel(s, 180); };
const toCrossing = (s: CreekState) => { while (s.flowM < routeLength(s.method)) advanceFlow(s, .5); };
const fills = (s: CreekState) => G.gates.map(g => s.gates[g.id].fill);

test('gates can be set before the water, and a press goes shut, half, full, shut', () => {
  const s = newCreek('clear_silt');
  assert.equal(cycleGate(s, 'gate_a').code, 'GATE_SET'); assert.equal(s.gates.gate_a.level, .5);
  cycleGate(s, 'gate_a'); assert.equal(s.gates.gate_a.level, 1);
  cycleGate(s, 'gate_a'); assert.equal(s.gates.gate_a.level, 0);
  assert.equal(setGate(s, 'nope', 1).code, 'NO_GATE');
  assert.equal(setGate(s, 'gate_a', .3).code, 'BAD_LEVEL');
  assert.equal(setGate(s, 'gate_a', 0).code, 'SAME_LEVEL');
  assert.deepEqual(s.gateLog.map(m => m.by), ['player', 'player', 'player']);
  assert.equal(s.flowM, 0, 'setting a gate moves no water');
  setGate(s, 'gate_b', 1); assert.deepEqual(loadCreek(saveCreek(s)).gates, s.gates, 'gates survive a save');
});

test('following the sign fills all three together; any other setting takes the same water and still fills them', () => {
  assert.equal(G.gates.reduce((a, g) => a + g.fieldM, 0), 10);
  const plan = newCreek('clear_silt'); canal(plan); for (const g of G.gates) setGate(plan, g.id, g.planLevel);
  toCrossing(plan); let ticks = 0;
  while (!plan.done) { advanceFlow(plan, .5); ticks++; }
  assert.equal(plan.together, true, 'the sign plan fills them at once');
  assert.equal(wetFields(plan).length, 3);
  const uneven = newCreek('clear_silt'); canal(uneven); setGate(uneven, 'gate_b', 1); setGate(uneven, 'gate_a', .5);
  toCrossing(uneven); let ticks2 = 0;
  while (!uneven.done) { advanceFlow(uneven, .5); ticks2++; }
  assert.equal(uneven.together, false, 'no prize and no penalty, only a different order');
  assert.deepEqual(fills(uneven), fills(plan));
  assert.ok(Math.abs(ticks - ticks2) <= (G.villagerDelaySeconds + 2) / .5, `same water; at most the wait for a gate to lift: ${ticks} / ${ticks2}`);
});

test('more gates open means each field fills slower; a closed gate takes nothing', () => {
  const s = newCreek('clear_silt'); canal(s); toCrossing(s); s.idleSeconds = 0;
  setGate(s, 'gate_b', 1); const b0 = s.gates.gate_b.fill; advanceFlow(s, 1);
  const alone = s.gates.gate_b.fill - b0; assert.ok(Math.abs(alone - creek.flow.speedMps) < 1e-9);
  assert.equal(s.gates.gate_c.fill, 0);
  setGate(s, 'gate_c', 1); const b1 = s.gates.gate_b.fill; advanceFlow(s, 1);
  assert.ok(Math.abs(s.gates.gate_b.fill - b1 - alone / 2) < 1e-9);
  assert.ok(Math.abs(s.gates.gate_c.fill - alone / 2) < 1e-9);
});

test('with nothing open another gate lifts by itself, and never the one a player just shut unless it is last', () => {
  const s = newCreek('protect_nursery'); canal(s); toCrossing(s);
  setGate(s, 'gate_a', 1); setGate(s, 'gate_a', 0);
  for (let t = 0; t < G.villagerDelaySeconds + 1; t++) advanceFlow(s, 1);
  assert.deepEqual(s.gateLog.at(-1), { gate: 'gate_b', level: .5, by: 'villager' });
  const idle = newCreek('clear_silt'); idle.wheelDegrees = 0; advanceFlow(idle, 60);
  assert.equal(idle.gateLog.length, 0, 'nobody moves a gate before the water comes');
  const last = newCreek('clear_silt'); canal(last); toCrossing(last);
  last.gates.gate_b.fill = G.gates[1].fieldM; last.gates.gate_c.fill = G.gates[2].fieldM; last.lastClosed = 'gate_a';
  for (let t = 0; t < G.villagerDelaySeconds + 1; t++) advanceFlow(last, 1);
  assert.ok(last.gates.gate_a.level > 0, 'the last field still gets its water');
});

test('a full field closes its gate and refuses more; shutting everything over and over still finishes', () => {
  const s = newCreek('restore_channel'); canal(s); toCrossing(s); setGate(s, 'gate_c', 1);
  while (!fieldFull(s, 'gate_c')) advanceFlow(s, 1);
  assert.equal(s.gates.gate_c.level, 0); assert.equal(s.gateLog.at(-1)!.by, 'villager');
  assert.equal(setGate(s, 'gate_c', 1).code, 'FIELD_FULL');
  assert.equal(cycleGate(s, 'gate_c').code, 'SAME_LEVEL');
  const stubborn = newCreek('clear_silt'); canal(stubborn); toCrossing(stubborn); let n = 0;
  while (!stubborn.done) { advanceFlow(stubborn, 1); if (++n % 20 === 0) for (const g of G.gates) setGate(stubborn, g.id, 0); assert.ok(n < 2000, 'never stuck'); }
  assert.equal(names(stubborn, 'creek.flowCompleted').length, 1);
  assert.equal(names(stubborn, 'creek.flowReached').filter(e => String(e.data.nodeId).startsWith('field')).length, 3, 'each field once, however often its gate moved');
});

test('a gate move names who made it, so a server can pass real player ids later', () => {
  const s = newCreek('clear_silt', 2); setGate(s, 'gate_a', 1, 'player:2'); cycleGate(s, 'gate_b', 'player:1');
  assert.deepEqual(s.gateLog.map(m => m.by), ['player:2', 'player:1']);
});
