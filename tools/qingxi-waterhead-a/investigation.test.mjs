import { test } from 'node:test';
import assert from 'node:assert/strict';
import { Investigation, OBSERVATION_IDS, PARAMS, polyDistance } from './investigation.mjs';

// Entrance downstream at z = 0, the stream runs towards +z.
const WORLD = {
  start: { x: 0, z: 0, heading: 0 },
  clues: [
    { id: 'cracked_sluice', x: 2, z: 8 },
    { id: 'silt_buildup', x: -1, z: 14 },
    { id: 'nursery_tracks', x: 3, z: 20 },
  ],
  hints: [{ id: 'water_gauge', x: -2, z: 4 }],
  walls: [{ x: 0, z: 3, r: 0.5 }],
  zones: [{ id: 'nursery', x: 3, z: 20, r: 4 }],
};
const DT = 1 / 60;

/** Walk straight to (x, z), stopping `stop` metres short, then face the target and look for a moment. */
function goLook(e, x, z, stop = 1.2, look = PARAMS.dwell + 0.1) {
  for (let i = 0; i < 4000; i++) {
    const p = e.player, dx = x - p.x, dz = z - p.z, d = Math.hypot(dx, dz);
    if (d <= stop) break;
    e.step(DT, { moveX: dx / d, moveZ: dz / d });
  }
  const p = e.player, h = Math.atan2(x - p.x, z - p.z);
  for (let t = 0; t < look; t += DT) e.step(DT, { heading: h });
}

test('clues can be found in any order; two are enough to discuss, three give the full picture', () => {
  for (const order of [[0, 1, 2], [2, 0, 1], [1, 2, 0]]) {
    const e = new Investigation(WORLD);
    order.forEach((i, k) => {
      const c = WORLD.clues[i];
      goLook(e, c.x, c.z);
      assert.equal(e.observe()?.id, c.id);
      assert.equal(e.verdict, k === 0 ? null : k === 1 ? 'discuss' : 'full');
    });
    assert.deepEqual(e.observationIds, OBSERVATION_IDS);
    assert.deepEqual(e.toJSON().order, order.map(i => WORLD.clues[i].id));
  }
});

test('observing the same clue again never records a second entry', () => {
  const e = new Investigation(WORLD);
  goLook(e, 2, 8);
  e.observe(); e.observe(); e.observe();
  assert.equal(e.book.length, 1);
  assert.ok(e.drainEvents().filter(ev => ev.type === 'already').length === 2);
});

test('a clue is only recorded up close, while looking at it, after a short look (no drive-by pickups)', () => {
  const e = new Investigation(WORLD);
  goLook(e, 2, 8, 4.0);                         // too far
  assert.equal(e.observe(), null);
  goLook(e, 2, 8, 1.2, 0);                      // close but has not looked yet
  assert.equal(e.observe(), null);
  for (let t = 0; t < 1; t += DT) e.step(DT, { heading: e.player.heading + Math.PI });   // turned away
  assert.equal(e.observe(), null);
  goLook(e, 2, 8, 1.2);
  assert.equal(e.observe()?.id, 'cracked_sluice');
});

test('a clue can be skipped entirely; two other clues still unlock the discussion', () => {
  const e = new Investigation(WORLD);
  goLook(e, -1, 14); e.observe();
  goLook(e, 3, 20); e.observe();
  assert.deepEqual(e.observationIds, ['silt_buildup', 'nursery_tracks']);
  assert.equal(e.verdict, 'discuss');
});

test('environment hints answer when looked at but are never recorded as an observation', () => {
  const e = new Investigation(WORLD);
  goLook(e, -2, 4);
  assert.equal(e.observe()?.kind, 'hint');
  assert.equal(e.book.length, 0);
  assert.equal(e.verdict, null);
});

test('walls block the player; returning to the entrance keeps the clue book', () => {
  const e = new Investigation(WORLD);
  for (let i = 0; i < 120; i++) e.step(DT, { moveX: 0, moveZ: 1 });
  assert.ok(Math.hypot(e.player.x - 0, e.player.z - 3) >= 0.5 + PARAMS.playerRadius - 1e-9);
  goLook(e, 2, 8); e.observe();
  e.returnToEntrance();
  assert.deepEqual([e.player.x, e.player.z], [0, 0]);
  assert.deepEqual(e.observationIds, ['cracked_sluice']);
  e.reset();
  assert.deepEqual(e.observationIds, []);
});

test('collision-hull polygons block at their real outline, not a circle', () => {
  const box = [[-1, 2.8], [1, 2.8], [1, 3.2], [-1, 3.2]];          // a trough lying across the path
  assert.equal(polyDistance(box, 0, 3), 0);
  assert.ok(Math.abs(polyDistance(box, 0, 2) - 0.8) < 1e-9);
  assert.ok(Math.abs(polyDistance([...box].reverse(), 2, 3) - 1) < 1e-9);
  const e = new Investigation({ ...WORLD, walls: [{ poly: box }] });
  for (let i = 0; i < 120; i++) e.step(DT, { moveX: 0, moveZ: 1 });
  assert.ok(e.player.z <= 2.8 - PARAMS.playerRadius + 1e-6 && e.player.z > 2.8 - PARAMS.playerRadius - 0.1);
  const f = new Investigation({ ...WORLD, walls: [{ poly: box }] });           // past the end of the trough the way is open
  f.player.x = 1.6;
  for (let i = 0; i < 120; i++) f.step(DT, { moveX: 0, moveZ: 1 });
  assert.ok(f.player.z > 3.5);
});

test('walkable() keeps the player out of the deep channel', () => {
  const e = new Investigation({ ...WORLD, walls: [], walkable: (x) => x < 1 });
  for (let i = 0; i < 300; i++) e.step(DT, { moveX: 1, moveZ: 0 });
  assert.ok(e.player.x < 1);
});

test('entering the nursery side raises a warning event, never damage', () => {
  const e = new Investigation(WORLD);
  goLook(e, 3, 20, 2.0);
  const ev = e.drainEvents();
  assert.ok(ev.some(x => x.type === 'enter-zone' && x.id === 'nursery'));
  assert.equal(Object.keys(e.snapshot()).includes('hp'), false);
});

test('the handoff JSON only carries observation ids and the verdict', () => {
  const e = new Investigation(WORLD);
  goLook(e, 2, 8); e.observe();
  goLook(e, -1, 14); e.observe();
  assert.deepEqual(e.toJSON(), {
    schema: 'qingxi-waterhead-a/observations@1',
    observationIds: ['cracked_sluice', 'silt_buildup'], order: ['cracked_sluice', 'silt_buildup'], verdict: 'discuss',
  });
});

test('the silt can only be raked open after it was looked at, from beside it, once', () => {
  const e = new Investigation(WORLD);
  assert.equal(e.clearSilt(), false);                       // not looked at yet
  goLook(e, -1, 14); e.observe();
  for (let i = 0; i < 400; i++) e.step(DT, { moveX: 0, moveZ: -1 });   // walk away
  assert.equal(e.clearSilt(), false);                       // too far
  goLook(e, -1, 14);
  assert.equal(e.clearSilt(), true);
  assert.equal(e.snapshot().siltCleared, true);
  assert.equal(e.clearSilt(), false);                       // already cleared
  const ev = e.drainEvents().map(x => x.type);
  assert.ok(ev.includes('look-first') && ev.includes('too-far') && ev.includes('silt-cleared') && ev.includes('already-cleared'));
  assert.deepEqual(e.toJSON().observationIds, ['silt_buildup']);   // the scene change is not part of the handoff
  e.reset();
  assert.equal(e.siltCleared, false);
});

test('walking into the nursery side warns once on entry and once on leaving, and never ends the run', () => {
  const e = new Investigation(WORLD);
  goLook(e, 3, 20, 1.0);
  for (let i = 0; i < 300; i++) e.step(DT, { moveX: 0, moveZ: -1 });
  const ev = e.drainEvents().filter(x => x.type.endsWith('-zone'));
  assert.deepEqual(ev.map(x => x.type), ['enter-zone', 'leave-zone']);
  assert.equal(e.verdict, null);
});

test('all three clues in any order give the full picture; the nursery tracks count like the others', () => {
  const e = new Investigation(WORLD);
  goLook(e, 3, 20); e.observe();
  goLook(e, 2, 8); e.observe();
  goLook(e, -1, 14); e.observe();
  assert.equal(e.verdict, 'full');
  assert.deepEqual(e.toJSON().order, ['nursery_tracks', 'cracked_sluice', 'silt_buildup']);
});

test('a hint right in front of you wins over a clue that is only at the edge of view', () => {
  const e = new Investigation({ ...WORLD, hints: [{ id: 'water_gauge', x: 0, z: 2 }], clues: [{ id: 'cracked_sluice', x: 1.6, z: 1.2 }], walls: [] });
  e.player.heading = 0;                                  // looking straight at the gauge (+z); the sluice is off to the side
  assert.equal(e.inReach().id, 'water_gauge');
  e.player.heading = Math.atan2(1.6, 1.2);               // turn to the sluice
  assert.equal(e.inReach().id, 'cracked_sluice');
});
