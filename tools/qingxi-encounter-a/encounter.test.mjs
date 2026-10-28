import test from 'node:test';
import assert from 'node:assert/strict';
import { Encounter, PARAMS, NOTICE } from './encounter.mjs';

// Burrow at the origin, the village (and safe point) towards -z.
const WORLD = { burrow: { x: 0, z: 0 }, safe: { x: 0, z: -12 }, start: { x: 0, z: -9 }, cover: [{ x: 3, z: -3, r: 0.9 }], walls: [] };
const R = PARAMS.rabbit;

/** walk the player to (x, z) at normal speed, stepping the sim */
function walkTo(e, x, z, maxT = 10) {
  for (let t = 0; t < maxT; t += 1 / 60) {
    const p = e.player, dx = x - p.x, dz = z - p.z, d = Math.hypot(dx, dz);
    if (d < 0.05) { e.move(0, 0); return; }
    e.move(dx / d, dz / d); e.step(1 / 60);
  }
  e.move(0, 0);
}
function untilState(e, state, maxT = 10) {
  for (let t = 0; t < maxT; t += 1 / 60) { if (e.rabbit.state === state) return true; e.step(1 / 60); }
  return e.rabbit.state === state;
}
const faceRabbit = e => e.face(Math.atan2(e.rabbit.x - e.player.x, e.rabbit.z - e.player.z));

test('rabbit stays in its burrow until it sees the player, then shows every tell before any hit', () => {
  const e = new Encounter(WORLD);
  e.step(1);
  assert.equal(e.rabbit.state, 'idle');
  walkTo(e, 0, -3.5);
  untilState(e, 'stagger', 6);
  const ev = e.drainEvents();
  const at = s => ev.find(x => x.type === 'state' && x.state === s)?.t;
  assert.ok(at('alert') < at('windup') && at('windup') < at('charge'), JSON.stringify(ev));
  assert.ok(at('charge') - at('windup') >= PARAMS.rabbit.windup - 0.02);            // full reaction window
  const firstHit = ev.find(x => x.type === 'player-hit');
  assert.ok(!firstHit || firstHit.t >= at('charge'));                                  // never hit before the charge
});

test('standing still in the charge line gets hit; the rabbit then staggers (opening)', () => {
  const e = new Encounter(WORLD);
  walkTo(e, 0, -3.5);
  untilState(e, 'charge', 5);
  untilState(e, 'stagger', 2);
  assert.equal(e.player.hp, PARAMS.player.hp - 1);
  assert.equal(e.stats.hitsTaken, 1);
});

test('a side dodge after the direction locks makes the charge miss', () => {
  const e = new Encounter(WORLD);
  walkTo(e, 0, -3.5);
  untilState(e, 'charge', 5);
  e.move(1, 0); e.dodge(); e.step(0.4); e.move(0, 0);
  untilState(e, 'stagger', 2);
  assert.equal(e.player.hp, PARAMS.player.hp);
});

test('dodging through the rabbit inside the i-frames counts as a dodge', () => {
  const e = new Encounter(WORLD);
  walkTo(e, 0, -3.5);
  untilState(e, 'charge', 5);
  // wait until the rabbit is about to reach the player, then dash straight through it
  while (Math.hypot(e.rabbit.x - e.player.x, e.rabbit.z - e.player.z) > 1.2 && e.rabbit.state === 'charge') e.step(1 / 60);
  e.move(0, 1); e.dodge(); e.step(0.5); e.move(0, 0);
  assert.equal(e.stats.dodged, 1);
  assert.equal(e.player.hp, PARAMS.player.hp);
});

test('a block facing the rabbit stops the hit; a well-timed block is a parry with a longer opening', () => {
  for (const [lead, kind] of [[0.6, 'blocked'], [0.08, 'parry']]) {
    const e = new Encounter(WORLD, { style: 'body' });
    walkTo(e, 0, -3.5);
    untilState(e, 'charge', 5);
    faceRabbit(e);
    const eta = () => (Math.hypot(e.rabbit.x - e.player.x, e.rabbit.z - e.player.z) - R.radius - PARAMS.player.radius) / R.chargeSpeed;
    while (eta() > lead && e.rabbit.state === 'charge') e.step(1 / 60);
    e.setBlock(true);
    untilState(e, 'stagger', 2);
    assert.equal(e.player.hp, PARAMS.player.hp, kind);
    assert.ok(e.drainEvents().some(ev => ev.type === kind), kind);
    assert.equal(e.rabbit.stagger, kind === 'parry' ? R.parryStagger : R.blockedStagger);
  }
});

test('blocking with your back to the rabbit does not protect you', () => {
  const e = new Encounter(WORLD);
  walkTo(e, 0, -3.5);
  untilState(e, 'charge', 5);
  e.face(Math.PI); e.setBlock(true);
  untilState(e, 'stagger', 2);
  assert.equal(e.player.hp, PARAMS.player.hp - 1);
});

test('mashing block breaks the guard instead of making you safer', () => {
  const e = new Encounter(WORLD);
  for (let i = 0; i < PARAMS.player.block.spamLimit + 1; i++) { e.setBlock(true); e.step(0.05); e.setBlock(false); e.step(0.05); }
  assert.ok(e.drainEvents().some(ev => ev.type === 'guard-broken'));
  assert.equal(e.setBlock(true), false);
  assert.equal(e.snapshot().player.guardBroken, true);
  e.step(PARAMS.player.block.breakTime + 0.1);
  assert.equal(e.setBlock(true), true);
});

test('attacks only land inside the opening, in range and aimed; sword technique deals more there', () => {
  const e = new Encounter(WORLD, { style: 'sword' });
  walkTo(e, 0, -3.5);
  untilState(e, 'alert', 3);
  faceRabbit(e); e.attack(); e.step(0.6);           // too far and not an opening
  assert.equal(e.stats.hitsLanded, 0);
  untilState(e, 'charge', 5);
  e.move(1, 0); e.dodge(); e.step(0.4); e.move(0, 0);
  untilState(e, 'stagger', 2);
  walkTo(e, e.rabbit.x + 0.9, e.rabbit.z - 0.9, 1);
  faceRabbit(e);
  e.attack('technique'); e.step(0.6);
  assert.equal(e.stats.hitsLanded, 1);
  assert.equal(e.rabbit.hp, R.hp - 2);
});

test('the full loop: read, dodge, punish until the rabbit is driven off (local only, no drops)', () => {
  const e = new Encounter(WORLD, { style: 'sword' });
  walkTo(e, 0, -3.5);
  for (let round = 0; round < 6 && !e.outcome; round++) {
    if (!untilState(e, 'charge', 8)) break;
    e.move(1, 0); e.dodge(); e.step(0.4); e.move(0, 0);
    if (!untilState(e, 'stagger', 2)) continue;
    walkTo(e, e.rabbit.x + 0.8, e.rabbit.z - 0.8, 0.6);
    faceRabbit(e); e.attack('technique'); e.step(0.6);
  }
  assert.equal(e.outcome, 'won');
  assert.equal(e.rabbit.state, 'retreat');
  assert.equal(e.snapshot().notice, NOTICE);
  assert.ok(!('drops' in e.snapshot()));
});

test('leaving the encounter area makes the rabbit disengage and go home', () => {
  const e = new Encounter(WORLD);
  walkTo(e, 0, -3.5);
  untilState(e, 'alert', 2);
  walkTo(e, 0, -14, 8);    // far beyond the leash
  assert.ok(e.drainEvents().some(ev => ev.type === 'retreat' && (ev.reason === 'left-area' || ev.reason === 'safe-point' || ev.reason === 'lost-sight')));
  untilState(e, 'idle', 5);
  assert.deepEqual([e.rabbit.x, e.rabbit.z], [0, 0]);
});

test('reaching the safe point calls the rabbit off; it will not re-engage there', () => {
  const e = new Encounter({ ...WORLD, safe: { x: 0, z: -4 } });
  walkTo(e, 0, -8.5, 1);
  e.player.x = 0; e.player.z = -4;   // standing on the safe point
  e.step(3);
  assert.notEqual(e.rabbit.state, 'charge');
  assert.notEqual(e.rabbit.state, 'windup');
});

test('cover blocks the rabbit sight line', () => {
  const e = new Encounter({ ...WORLD, cover: [{ x: 0, z: -2, r: 0.9 }] });
  walkTo(e, 0, -3.5);
  e.step(2);
  assert.equal(e.rabbit.state, 'idle');
});

test('disconnect / tab hidden during a charge: the rabbit disengages, no damage is applied', () => {
  const e = new Encounter(WORLD);
  walkTo(e, 0, -3.5);
  untilState(e, 'charge', 5);
  e.disconnect();
  e.step(2);
  assert.equal(e.player.hp, PARAMS.player.hp);
  assert.ok(['retreat', 'idle'].includes(e.rabbit.state));
});

test('falling to 0 HP retreats the rabbit and the player restarts at the safe point with nothing lost', () => {
  const e = new Encounter(WORLD);
  walkTo(e, 0, -3.5);
  for (let i = 0; i < 6 && !e.outcome; i++) { untilState(e, 'charge', 8); untilState(e, 'stagger', 2); }
  assert.equal(e.outcome, 'downed');
  e.resetAtSafePoint();
  const s = e.snapshot();
  assert.equal(s.player.hp, PARAMS.player.hp);
  assert.deepEqual([s.player.x, s.player.z], [WORLD.safe.x, WORLD.safe.z]);
  assert.equal(s.outcome, null);
});

test('qi (法) is not playable yet and says so', () => {
  assert.throws(() => new Encounter(WORLD, { style: 'qi' }), /next version/);
});
