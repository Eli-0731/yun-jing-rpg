import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { BasicCombat, HIT } from './basic-combat-rules.mjs';

const content = JSON.parse(readFileSync(new URL('../../packages/content/basic-combat-v1.json', import.meta.url)));
const [p1, p2, p3] = content.light;
const H = content.heavy, D = content.dodge;

// a fighter at the origin facing +z, plus a helper that advances time with a fixed input
function fighter(at) { return new BasicCombat(content, at); }
function at(f, t, input = {}, targets = []) { return f.update(t, input, targets); }
const types = evs => evs.map(e => e.type);
const recoveryStart = a => a.windup + a.active;

test('light chain only continues when the press lands in recovery after chainFrom', () => {
  const f = fighter();
  at(f, 0);
  assert.deepEqual(types(at(f, 0.001, { attack: true })), ['attack.start']);
  assert.equal(f.attack.id, 'palm1');
  // pressing during windup or active is dropped, not buffered
  assert.ok(types(at(f, 0.06, { attack: true })).includes('input.ignored'));
  assert.ok(types(at(f, 0.15, { attack: true })).includes('input.ignored'));
  assert.equal(f.attack.id, 'palm1');
  // in recovery but before chainFrom: still dropped
  const r1 = 0.001 + recoveryStart(p1);
  at(f, r1 + 0.01);
  assert.ok(types(at(f, r1 + 0.02, { attack: true })).includes('input.ignored'));
  // after chainFrom: chains into palm2, then palm3
  at(f, r1 + p1.chainFrom + 0.02, { attack: true });
  assert.equal(f.attack.id, 'palm2');
  const t2 = f.time;
  at(f, t2 + recoveryStart(p2) + p2.chainFrom + 0.02, { attack: true });
  assert.equal(f.attack.id, 'palm3');
  // no fourth hit: pressing in palm3's recovery is ignored
  const t3 = f.time;
  assert.ok(types(at(f, t3 + recoveryStart(p3) + 0.05, { attack: true })).includes('input.ignored'));
  assert.equal(f.attack.id, 'palm3');
});

test('a press after recovery has finished starts the chain over at palm1', () => {
  const f = fighter();
  at(f, 0);
  at(f, 0.001, { attack: true });
  at(f, 0.001 + recoveryStart(p1) + p1.recovery + 0.05);
  assert.equal(f.state, 'idle');
  at(f, f.time + 0.01, { attack: true });
  assert.equal(f.attack.id, 'palm1');
});

test('heavy: short taps cancel without cooldown; damage and knockback scale with charge', () => {
  const f = fighter();
  const dummy = [{ id: 'dummy', x: 0, z: 1.2 }];
  at(f, 0);
  at(f, 0.01, { heavyHeld: true });
  assert.equal(f.state, 'charging');
  assert.ok(types(at(f, 0.01 + H.chargeMin - 0.1, { heavyHeld: false })).includes('heavy.cancelled'));
  assert.equal(f.heavyCooldown, 0);
  // half charge
  const start = f.time + 0.01;
  at(f, start, { heavyHeld: true }, dummy);
  const half = (H.chargeMin + H.chargeMax) / 2;
  at(f, start + half, { heavyHeld: true }, dummy);
  at(f, start + half + 1e-3, { heavyHeld: false }, dummy);
  assert.equal(f.state, 'heavy');
  const evs = at(f, f.time + H.windup + H.active, {}, dummy).filter(e => e.type === HIT);
  assert.equal(evs.length, 1);
  assert.ok(Math.abs(evs[0].damage - (H.damageMin + H.damageMax) / 2) <= 1, `damage ${evs[0].damage}`);
  assert.ok(evs[0].knockback > H.knockbackMin && evs[0].knockback < H.knockbackMax);
});

test('heavy: holding past chargeMax fires at full power; cooldown blocks the next charge until it expires', () => {
  const f = fighter();
  const dummy = [{ id: 'dummy', x: 0, z: 1.2 }];
  at(f, 0);
  at(f, 0.01, { heavyHeld: true }, dummy);
  const evs = at(f, 0.01 + H.chargeMax + H.windup + H.active + 0.02, { heavyHeld: true }, dummy);
  const hit = evs.find(e => e.type === HIT);
  assert.equal(hit.damage, H.damageMax);
  assert.equal(hit.knockback, H.knockbackMax);
  at(f, f.time + H.recovery + 0.05, { heavyHeld: false });
  assert.equal(f.state, 'idle');
  assert.ok(types(at(f, f.time + 0.01, { heavyHeld: true })).includes('heavy.cooldown'));
  assert.equal(f.state, 'idle');
  const fired = 0.01 + H.chargeMax;
  at(f, fired + H.cooldown + 0.05, { heavyHeld: false });
  at(f, f.time + 0.01, { heavyHeld: true });
  assert.equal(f.state, 'charging');
});

test('dodge: i-frames last exactly the configured time, distance matches, and cooldown applies', () => {
  const f = fighter();
  at(f, 0);
  at(f, 0.01, { dodge: true, move: { x: 1, z: 0 } });
  assert.equal(f.state, 'dodge');
  at(f, 0.01 + D.iframes - 0.02);
  assert.equal(f.receive(), 'dodged');
  at(f, 0.01 + D.iframes + 0.02);
  assert.equal(f.receive(), 'hit');
  at(f, 0.01 + D.duration + 0.02);
  assert.ok(Math.abs(f.x - D.distance) < 0.05, `travelled ${f.x}`);
  assert.equal(f.state, 'idle');
  assert.ok(types(at(f, f.time + 0.01, { dodge: true })).includes('input.ignored'));
  at(f, 0.01 + D.duration + D.cooldown + 0.02, { dodge: true });
  assert.equal(f.state, 'dodge');
});

test('dodge cancels recovery and charging but never windup or active', () => {
  const f = fighter();
  at(f, 0);
  at(f, 0.001, { attack: true });
  assert.ok(types(at(f, 0.05, { dodge: true })).includes('input.ignored'));   // windup
  assert.ok(types(at(f, 0.001 + p1.windup + 0.02, { dodge: true })).includes('input.ignored'));   // active
  const evs = at(f, 0.001 + recoveryStart(p1) + 0.05, { dodge: true });
  assert.deepEqual(evs.find(e => e.type === 'dodge.start'), { type: 'dodge.start', t: evs.find(e => e.type === 'dodge.start').t, cancelled: true });
  const g = fighter();
  at(g, 0);
  at(g, 0.01, { heavyHeld: true });
  const ev2 = at(g, 0.2, { heavyHeld: true, dodge: true });
  assert.ok(types(ev2).includes('heavy.cancelled') && types(ev2).includes('dodge.start'));
});

test('one swing hits each target once, and every target in the arc gets its own hit', () => {
  const f = fighter();
  const targets = [{ id: 'a', x: 0, z: 1.2 }, { id: 'b', x: 0.5, z: 1.3 }, { id: 'behind', x: 0, z: -1.2 }];
  at(f, 0, {}, targets);
  at(f, 0.001, { attack: true }, targets);
  const evs = [];
  for (let t = 0.01; t < 0.6; t += 1 / 60) evs.push(...at(f, t, {}, targets));
  const hits = evs.filter(e => e.type === HIT);
  assert.deepEqual(hits.map(h => h.targetId).sort(), ['a', 'b']);
  assert.ok(hits.every(h => h.attackId === 'palm1' && h.damage === p1.damage));
});

test('attacks turn to the nearest target within 4 m, never further', () => {
  const f = fighter();
  at(f, 0);
  at(f, 0.001, { attack: true }, [{ id: 'side', x: 3.5, z: 0 }]);
  assert.ok(Math.abs(f.yaw - Math.PI / 2) < 1e-6);
  const g = fighter();
  at(g, 0);
  at(g, 0.001, { attack: true }, [{ id: 'far', x: 4.5, z: 0 }]);
  assert.equal(g.yaw, 0);
  const h = fighter();
  at(h, 0);
  at(h, 0.001, { attack: true }, [{ id: 'far', x: 3.9, z: 0 }, { id: 'near', x: 0, z: -2 }]);
  assert.ok(Math.abs(Math.abs(h.yaw) - Math.PI) < 1e-6);
});

test('dead targets are ignored for both facing and hits', () => {
  const f = fighter();
  const targets = [{ id: 'gone', x: 0, z: 1, alive: false }];
  at(f, 0);
  at(f, 0.001, { attack: true }, targets);
  const evs = at(f, 0.5, {}, targets);
  assert.equal(evs.filter(e => e.type === HIT).length, 0);
});
