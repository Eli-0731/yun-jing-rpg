// node --test tools/qingxi-waterworks-b/tests
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { CHOICES, newSession, act, undo, redo, evaluate, preview, complete, requestIdFor, placePiece } from '../src/waterworks-core.mjs';

const j = p => JSON.parse(readFileSync(new URL(p, import.meta.url), 'utf8'));
const board = j('../data/board.json'), catalog = j('../data/catalog.json'), fixture = j('../data/fixture-observations.json');
const ctx = { board, catalog };
const FULL = fixture.sets.full.observationIds;
const P = (slot, piece) => ({ type: 'place', slot, piece });
const ROUTE = {
  direct: [P('P2', 'B05'), P('P3', 'B02'), { type: 'patch', slot: 'P4', piece: 'B07' }, P('P5', 'B02'), P('P6', 'B02'), { type: 'gate', slot: 'P2', open: true }],
  bypass: [P('P2', 'B03-V04'), P('L1', 'B02'), P('L2', 'B03'), P('L3', 'B02-V03'), P('L4', 'B05'), P('L5', 'B03-V02'), P('L6', 'B02'), P('L7', 'B03-V03'), { type: 'gate', slot: 'L4', open: true }],
  desilt: [P('P2', 'B04-V02'), P('L1', 'B02'), P('L2', 'B02-V05'), P('R1', 'B05')],
};
function build(steps, obs = FULL, session) {
  let s = session ?? newSession(board, catalog, obs);
  for (const a of steps) { const r = act(ctx, s, a); assert.ok(r.ok, `${JSON.stringify(a)}: ${r.message}`); s = r.session; }
  return s;
}
const issue = (s, code) => evaluate(ctx, s.design, { obs: s.obs }).issues.find(i => i.code === code);

test('fixture lists the three upstream observation ids', () => {
  assert.deepEqual([...FULL].sort(), ['cracked_sluice', 'nursery_tracks', 'silt_buildup']);
  for (const id of FULL) assert.ok(fixture.observations[id].text);
});

test('catalog ports come from model_info and share the standard joint', () => {
  for (const id of ['B02', 'B03', 'B03-V04', 'B04-V02', 'B05']) {
    const p = catalog.pieces[id];
    assert.deepEqual(p.ports[0].pos, [0, 0]); assert.equal(p.ports[0].kind, 'in');
    assert.ok(p.cells.length > 0 && p.glb.endsWith('.glb') && p.waterGlb);
  }
  // a left bend placed facing west turns the flow north
  const g = placePiece(catalog.pieces['B03-V03'], { pos: [-0.5, 5.5], dir: [1, 0] });
  assert.deepEqual(g.ports[1].pos.map(v => Math.round(v * 100) / 100), [0, 6]);
});

test('direct route + restore_channel completes with outcomeId and supply, but sits next to the nursery', () => {
  const s = build([...ROUTE.direct, { type: 'choose', choice: 'restore_channel' }]);
  const r = complete(ctx, s, requestIdFor(s));
  assert.equal(r.ok, true, JSON.stringify(r.problems));
  assert.equal(r.outcome.outcomeId, 'wwb.restore_channel.direct');
  assert.ok(r.outcome.villageSupply > 50);
  assert.equal(r.outcome.nursery, 'risk');
  assert.equal(r.official, false);
});

test('bypass route + protect_nursery completes, keeps the nursery safe, costs more stone', () => {
  const s = build([...ROUTE.bypass, { type: 'choose', choice: 'protect_nursery' }]);
  const r = complete(ctx, s, requestIdFor(s));
  assert.equal(r.ok, true, JSON.stringify(r.problems));
  assert.equal(r.outcome.outcomeId, 'wwb.protect_nursery.bypass');
  assert.equal(r.outcome.nursery, 'safe');
  const direct = build([...ROUTE.direct, { type: 'choose', choice: 'restore_channel' }]);
  const a = preview(ctx, direct), b = preview(ctx, s);
  assert.ok(b.cost.stone > a.cost.stone, 'the bypass needs more stone');
  assert.ok(b.ev.metrics.villageSupply < a.ev.metrics.villageSupply, 'four bends lose a little water');
});

test('desilt route + clear_silt diverts mud to the drain, no field water today, then full supply later', () => {
  let s = build([...ROUTE.desilt, { type: 'choose', choice: 'clear_silt' }]);
  const r = complete(ctx, s, requestIdFor(s));
  assert.equal(r.ok, true, JSON.stringify(r.problems));
  assert.equal(r.outcome.outcomeId, 'wwb.clear_silt.diverted');
  assert.equal(r.outcome.villageSupply, 0);
  s = r.session;
  assert.equal(s.ledger.siltCleared, true);
  // after desilting, the direct route on the same ledger gets far more water
  s = build([{ type: 'clear' }, ...ROUTE.direct, { type: 'choose', choice: 'restore_channel' }], FULL, s);
  assert.ok(preview(ctx, s).ev.metrics.villageSupply > 90);
});

test('each direction checks the layout: wrong pairings are refused with a reason', () => {
  const near = preview(ctx, build([...ROUTE.direct, { type: 'choose', choice: 'protect_nursery' }]));
  assert.equal(near.ready, false); assert.ok(near.problems.some(p => p.code === 'TOO_CLOSE'));
  const old = preview(ctx, build([...ROUTE.bypass, { type: 'choose', choice: 'restore_channel' }]));
  assert.ok(old.problems.some(p => p.code === 'NOT_OLD_LINE'));
  const mud = preview(ctx, build([...ROUTE.direct, { type: 'choose', choice: 'clear_silt' }]));
  assert.ok(mud.problems.some(p => p.code === 'NO_TEE') && mud.problems.some(p => p.code === 'MUD_TO_FIELD'));
});

test('water follows the gate: closed gate keeps the field dry', () => {
  const s = build([...ROUTE.direct, { type: 'gate', slot: 'P2', open: false }, { type: 'choose', choice: 'restore_channel' }]);
  const pv = preview(ctx, s);
  assert.equal(pv.ev.metrics.villageSupply, 0);
  assert.equal(pv.ev.wet.P2, 'still'); assert.equal(pv.ev.wet.P3, undefined);
  assert.ok(pv.problems.some(p => p.code === 'NO_FIELD_WATER' && /閘板關著/.test(p.message)));
});

test('wrong tee names the broken ports and the fitting variant', () => {
  const s = build([P('P2', 'B04'), P('L1', 'B02'), P('L2', 'B02-V05'), P('R1', 'B05')]);
  const ev = evaluate(ctx, s.design, { obs: FULL });
  const open = ev.issues.filter(i => i.code === 'OPEN_PORT');
  assert.deepEqual(open.map(i => i.port).sort(), ['out_left', 'out_right']);
  assert.match(open[0].message, /差 25 cm/);
  assert.match(open[0].fix, /B04-V02/);
});

test('empty next slot, dead end, overlap and disconnected pieces are all explained', () => {
  assert.match(issue(build([P('P2', 'B05'), { type: 'gate', slot: 'P2', open: true }]), 'EMPTY_NEXT').message, /P3 還空著/);
  assert.match(issue(build([P('P2', 'B03')]), 'EMPTY_NEXT').fix, /B03-V04/);
  const ov = issue(build([P('P2', 'B04-V02'), P('P3', 'B02')]), 'OVERLAP');
  assert.match(ov.fix, /拆掉 P3/);
  assert.match(issue(build([P('P5', 'B02')]), 'NOT_CONNECTED').message, /P5/);
});

test('closed gate with an open far side is held water, not a leak', () => {
  const s = build(ROUTE.desilt);
  const ev = evaluate(ctx, s.design, { obs: FULL });
  assert.ok(ev.issues.some(i => i.code === 'GATE_END' && !i.blocking));
  assert.equal(ev.metrics.spill, 0);
  const opened = build([{ type: 'gate', slot: 'R1', open: true }], FULL, s);
  assert.ok(evaluate(ctx, opened.design, { obs: FULL }).metrics.spill > 0, 'opening it spills');
});

test('undo and redo walk the design history; a new edit drops the redo branch', () => {
  let s = build([P('P2', 'B05'), P('P3', 'B02')]);
  s = undo(s).session;
  assert.equal(s.design.placed.P3, undefined);
  s = redo(s).session;
  assert.equal(s.design.placed.P3, 'B02');
  s = undo(s).session;
  s = build([P('P3', 'B02-V04')], FULL, s);
  assert.equal(redo(s).ok, false);
  assert.equal(undo(undo(s).session).session.design.placed.P2, undefined);
  assert.equal(undo(newSession(board, catalog)).code, 'NOTHING_TO_UNDO');
});

test('fixed old troughs cannot be removed, piece stock is limited', () => {
  const s = newSession(board, catalog, FULL);
  assert.equal(act(ctx, s, { type: 'remove', slot: 'P1' }).code, 'FIXED_SLOT');
  assert.equal(act(ctx, s, P('P4', 'B02')).code, 'FIXED_SLOT');
  const two = build([P('P2', 'B05'), P('L4', 'B05')]);
  assert.equal(act(ctx, two, P('R1', 'B05')).code, 'NO_PIECE');
});

test('pressing complete again replays the receipt and never deducts twice', () => {
  const s = build([...ROUTE.direct, { type: 'choose', choice: 'restore_channel' }]);
  const id = requestIdFor(s);
  const first = complete(ctx, s, id);
  const stone = first.session.ledger.stock.stone;
  assert.equal(stone, board.materialStock.stone - first.consumed.stone);
  assert.equal(requestIdFor(first.session), id, 'unchanged design keeps the same request id');
  const again = complete(ctx, first.session, id);
  assert.equal(again.replayed, true);
  assert.deepEqual(again.session.ledger, first.session.ledger);
  assert.equal(again.session.ledger.completed.length, 1);
  // same id, different design -> conflict, nothing changes
  const changed = build([{ type: 'choose', choice: 'protect_nursery' }], FULL, first.session);
  const c = complete(ctx, changed, id);
  assert.equal(c.code, 'IDEMPOTENCY_CONFLICT');
  assert.deepEqual(c.session.ledger, first.session.ledger);
});

test('rebuilding the same layout after another completion is a new request, not a replay', () => {
  let s = build([...ROUTE.direct, { type: 'choose', choice: 'restore_channel' }]);
  const first = complete(ctx, s, requestIdFor(s));
  s = build([{ type: 'clear' }, ...ROUTE.desilt, { type: 'choose', choice: 'clear_silt' }], FULL, first.session);
  s = complete(ctx, s, requestIdFor(s)).session;
  s = build([{ type: 'clear' }, ...ROUTE.direct, { type: 'choose', choice: 'restore_channel' }], FULL, s);
  const id = requestIdFor(s);
  assert.notEqual(id, first.requestId);
  const again = complete(ctx, s, id);
  assert.equal(again.replayed, false);
  assert.ok(again.outcome.villageSupply > first.outcome.villageSupply, 'desilted channel carries more water');
  assert.equal(again.session.ledger.completed.length, 3);
});

test('undo after completing does not refund or re-deduct materials', () => {
  const s = build([...ROUTE.direct, { type: 'choose', choice: 'restore_channel' }]);
  const done = complete(ctx, s, requestIdFor(s)).session;
  const back = undo(done).session;
  assert.deepEqual(back.ledger, done.ledger);
});

test('missing clues still allow trying; the preview names the unknown risk and the result reveals it', () => {
  const s = build([...ROUTE.direct, { type: 'choose', choice: 'restore_channel' }], []);
  const pv = preview(ctx, s);
  assert.deepEqual(pv.ev.unknowns.map(u => u.id).sort(), ['crack', 'nursery', 'silt']);
  assert.equal(pv.ev.metrics.nursery.level, 'unknown');
  const r = complete(ctx, s, requestIdFor(s));
  assert.equal(r.ok, true);
  assert.equal(r.outcome.nursery, 'risk');
  assert.ok(r.outcome.discovered.length >= 2, JSON.stringify(r.outcome.discovered));
  // with the patch but no crack clue the patch still holds; without the patch the hidden crack leaks
  const noPatch = build([P('P2', 'B05'), P('P3', 'B02'), P('P5', 'B02'), P('P6', 'B02'), { type: 'gate', slot: 'P2', open: true }, { type: 'choose', choice: 'restore_channel' }], ['silt_buildup', 'nursery_tracks']);
  const leak = complete(ctx, noPatch, requestIdFor(noPatch));
  assert.equal(leak.outcome.crack, 'leaking');
  assert.ok(leak.outcome.villageSupply < r.outcome.villageSupply);
});

test('same inputs give the same evaluation (no lottery, no clock)', () => {
  const s = build([...ROUTE.bypass, { type: 'choose', choice: 'protect_nursery' }]);
  assert.deepEqual(complete(ctx, s, 'x').outcome, complete(ctx, s, 'x').outcome);
  const src = readFileSync(new URL('../src/waterworks-core.mjs', import.meta.url), 'utf8').replace(/^\s*\/\/.*$/gm, '');
  assert.doesNotMatch(src, /Math\.random|Date\.now|new Date|setTimeout|performance\.now|document\.|window\./);
  assert.deepEqual(Object.values(CHOICES).map(c => c.outcomeId), ['wwb.clear_silt.diverted', 'wwb.restore_channel.direct', 'wwb.protect_nursery.bypass']);
});
