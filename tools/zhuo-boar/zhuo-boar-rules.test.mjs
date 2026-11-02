import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { CLEANSED, ESCAPED, ZhuoBoarEncounter } from './zhuo-boar-rules.mjs';

const content = JSON.parse(readFileSync(new URL('../../packages/content/zhuo-boar-encounter-v1.json', import.meta.url), 'utf8'));
const unity = JSON.parse(readFileSync(new URL('../../apps/game/Assets/YunJing/Resources/QingxiZhuoBoar/zhuo-boar-encounter-v1.json', import.meta.url), 'utf8'));
const DT = 1 / 60;
const TREE = { id: 'D3_BoarTree_01', x: 0, z: 8, r: .175 };

/** A runner that keeps the clock and collects every event. */
function start(home = {}, autoStart = false) {
  const boar = new ZhuoBoarEncounter(content, { x: 0, z: 0, yaw: 0, ...home, autoStart });
  const run = { boar, now: 0, events: [] };
  run.play = (seconds, input) => {
    const end = run.now + seconds;
    let first = true;
    while (run.now < end - 1e-9) {
      run.now += DT;
      const r = boar.update(run.now, first ? input : { ...input, dodge: null });
      first = false;
      run.events.push(...r.events);
      if (input.until?.(boar)) break;
    }
  };
  run.playUntil = (state, input, limit = 60) => run.play(limit, { ...input, until: b => b.state === state });
  run.count = type => run.events.filter(e => e.type === type).length;
  return run;
}
const inState = state => b => b.state === state;

test('the Unity copy of the content is identical', () => assert.deepEqual(unity, content));

test('the content holds every number of the work package', () => {
  const want = { noticeRadiusM: 12, pawTelegraphSeconds: 1.2, trackTurnDegPerSecond: 90, chargeSpeedMps: 9, chargeMaxDistanceM: 14, brakeRecoverSeconds: 1.5, dazeSeconds: 2.5, cleanseHoldSeconds: 1.5, cleanseNeeded: 2, hitKnockbackM: 3, hitStaminaLoss: 15, hitsBeforeEscape: 3, retryCooldownSeconds: 30, dodgeIFrameSeconds: .35, dodgeDistanceM: 2.5 };
  for (const [k, v] of Object.entries(want)) assert.equal(content[k], v, k);
});

test('it waits for the player to come close; a script start waits for begin()', () => {
  const near = start({}, true);
  near.play(1, { player: { x: 0, z: 13 } });
  assert.equal(near.boar.state, 'idle');
  near.play(.1, { player: { x: 0, z: 11 } });
  assert.equal(near.boar.state, 'alert');

  const scripted = start();
  scripted.play(1, { player: { x: 0, z: 5 } });
  assert.equal(scripted.boar.state, 'idle');
  assert.equal(scripted.boar.begin(), true);
  assert.equal(scripted.boar.state, 'alert');
  assert.equal(scripted.boar.begin(), false);
});

test('1. it turns during the telegraph at the listed rate, and not after the charge begins', () => {
  const r = start({ yaw: 0 });
  r.boar.begin();
  // Player almost behind it: the turn is limited to 90 deg/s and stops at the charge.
  const player = { x: 1, z: -10 };
  r.playUntil('telegraph', { player });
  const before = r.boar.yaw;
  r.play(.5, { player });
  const turned = r.boar.yaw - before;
  assert.ok(Math.abs(turned - Math.PI / 4) < .03, `turned ${turned}`);

  r.playUntil('charge', { player });
  const yaw = r.boar.yaw;
  r.play(.5, { player: { x: -10, z: 5 } });
  assert.equal(r.boar.state, 'charge');
  assert.equal(r.boar.yaw, yaw);
});

test('the charge line follows while pawing and is fixed when the telegraph ends', () => {
  const r = start();
  r.boar.begin();
  r.playUntil('telegraph', { player: { x: 0, z: 10 } });
  r.play(.2, { player: { x: 0, z: 10 } });
  assert.equal(r.boar.line.fixed, false);
  assert.equal(r.boar.line.width, 1.2);
  r.playUntil('charge', { player: { x: 0, z: 10 } });
  assert.equal(r.boar.line.fixed, true);
  const y = r.boar.line.yaw;
  r.play(.3, { player: { x: 8, z: 0 } });
  assert.equal(r.boar.line.yaw, y);
});

test('2. an obstacle on the line stops the charge in daze; none runs the full distance to brake', () => {
  const hit = start();
  hit.boar.begin();
  const side = { player: { x: 4, z: 8 }, obstacles: [TREE] };
  hit.playUntil('telegraph', { player: { x: 0, z: 8 }, obstacles: [TREE] });
  hit.playUntil('charge', { player: { x: 0, z: 8 }, obstacles: [TREE] });
  hit.playUntil('daze', side);
  assert.equal(hit.boar.state, 'daze');
  assert.ok(Math.abs(hit.boar.z - 8) < 1.1, `stopped at ${hit.boar.z}`);
  assert.equal(hit.events.find(e => e.type === 'daze').obstacle, TREE.id);

  const miss = start();
  miss.boar.begin();
  miss.playUntil('charge', { player: { x: 0, z: 8 } });
  const from = miss.boar.z;
  miss.playUntil('brake', { player: { x: 4, z: 0 } });
  assert.equal(miss.boar.state, 'brake');
  assert.ok(Math.abs(miss.boar.z - from - 14) < .15, `ran ${miss.boar.z - from}`);
  miss.play(1.4, { player: { x: 4, z: 0 } });
  assert.equal(miss.boar.state, 'brake');
  miss.play(.2, { player: { x: 4, z: 0 } });
  assert.equal(miss.boar.state, 'alert');
});

test('an obstacle beside the line is passed, one behind does not catch it', () => {
  const r = start();
  r.boar.begin();
  r.playUntil('charge', { player: { x: 0, z: 8 } });
  r.playUntil('brake', { player: { x: 4, z: 0 }, obstacles: [{ id: 'side', x: 1.2, z: 8, r: .175 }, { id: 'back', x: 0, z: -1, r: .5 }] });
  assert.equal(r.boar.state, 'brake');
});

test('the charge stops at the bounds without a daze', () => {
  const r = start();
  r.boar.begin();
  const bounds = { minX: -10, maxX: 10, minZ: -10, maxZ: 10 };
  r.playUntil('charge', { player: { x: 0, z: 8 }, bounds });
  r.playUntil('brake', { player: { x: 4, z: 0 }, bounds });
  assert.equal(r.boar.state, 'brake');
  assert.ok(r.boar.z < 10, `stopped at ${r.boar.z}`);
  assert.equal(r.count('daze'), 0);
});

/** Up to the point it stands dazed against the tree, with the player beside it. */
function dazed(run) {
  const player = { x: 1.4, z: 7 };
  run.boar.begin();
  const line = { player: { x: 0, z: 8 }, obstacles: [TREE] };
  run.playUntil('charge', line);
  run.playUntil('daze', { player, obstacles: [TREE] });
  assert.equal(run.boar.state, 'daze');
  return { player, obstacles: [TREE] };
}

test('3. holding for 1.5 s in daze counts once; letting go starts over; the end of the daze cancels', () => {
  const r = start();
  const near = dazed(r);
  r.play(1, { ...near, cleanseHeld: true });
  assert.ok(r.boar.cleanseProgress > .6);
  r.play(.05, { ...near, cleanseHeld: false });
  assert.equal(r.boar.cleanseProgress, 0);
  r.play(1.4, { ...near, cleanseHeld: true });
  // 1 + .05 + 1.4 = 2.45 s into the daze: not enough held since letting go.
  assert.equal(r.boar.cleanses, 0);
  r.play(.1, { ...near, cleanseHeld: true });
  assert.equal(r.boar.state, 'reposition');
  assert.equal(r.boar.cleanses, 0);
  assert.equal(r.boar.cleanseProgress, 0);

  const one = start();
  const beside = dazed(one);
  one.play(1.5, { ...beside, cleanseHeld: true });
  assert.equal(one.boar.cleanses, 1);
  assert.equal(one.count('cleanse'), 1);
  assert.equal(one.boar.state, 'daze');
  assert.equal(one.boar.zhuo, .5);
});

test('3b. only within 2 m, and only in daze', () => {
  const far = start();
  dazed(far);
  far.play(2, { player: { x: 2.1, z: 7 }, obstacles: [TREE], cleanseHeld: true });
  assert.equal(far.boar.cleanses, 0);

  const walk = start();
  walk.boar.begin();
  walk.play(.5, { player: { x: .5, z: .5 }, cleanseHeld: true });
  assert.equal(walk.boar.state, 'alert');
  assert.equal(walk.boar.cleanseProgress, 0);
});

test('4. two cleanses end it and raise the event once', () => {
  const r = start();
  const near = dazed(r);
  r.play(1.6, { ...near, cleanseHeld: true });
  r.playUntil('charge', { player: { x: 1, z: 2 }, obstacles: [TREE] });
  // Lines the boar up with the tree again from wherever it stands.
  const line = r.boar.line;
  const ahead = { id: 'again', x: line.x + Math.sin(line.yaw) * 4, z: line.z + Math.cos(line.yaw) * 4, r: .175 };
  r.playUntil('daze', { player: { x: line.x + 3, z: line.z }, obstacles: [ahead] });
  assert.equal(r.boar.state, 'daze');
  const stand = { player: { x: r.boar.x + 1.2, z: r.boar.z }, obstacles: [ahead] };
  r.play(1.6, { ...stand, cleanseHeld: true });
  assert.equal(r.boar.state, 'cleansed');
  assert.equal(r.boar.zhuo, 0);
  r.play(10, stand);
  const raised = r.events.filter(e => e.type === CLEANSED);
  assert.equal(raised.length, 1);
  assert.ok(raised[0].durationSeconds > 3);
  assert.equal(raised[0].hitsTaken, 0);
  assert.equal(r.boar.begin(), false);
  assert.equal(r.boar.visible, false);
});

test('after the cleanse it stands a while, then runs away from the player', () => {
  const r = start();
  const near = dazed(r);
  r.boar.cleanses = content.cleanseNeeded - 1;
  r.play(1.6, { ...near, cleanseHeld: true });
  const at = { x: r.boar.x, z: r.boar.z };
  r.play(1.8, near);
  assert.deepEqual({ x: r.boar.x, z: r.boar.z }, at);
  const before = Math.hypot(r.boar.x - near.player.x, r.boar.z - near.player.z);
  r.play(1.5, near);
  assert.ok(Math.hypot(r.boar.x - near.player.x, r.boar.z - near.player.z) > before + 4);
});

test('5. i-frames from a dodge prevent the hit; once they run out it counts', () => {
  const safe = start();
  safe.boar.begin();
  const player = { x: 0, z: 2 };
  safe.playUntil('charge', { player });
  const contact = (2 - .8 - .15 - .45) / 9;   // seconds to reach the player
  safe.play(Math.max(0, contact - .1), { player });
  safe.play(.3, { player, dodge: { x: 1, z: 0 } });
  assert.equal(safe.count('dodge'), 1);
  assert.equal(safe.count('hit'), 0);

  const hurt = start();
  hurt.boar.begin();
  const far = { x: 0, z: 6 };
  hurt.playUntil('charge', { player: far });
  hurt.play(.05, { player: far, dodge: { x: 1, z: 0 } });
  hurt.play(1, { player: far });
  assert.equal(hurt.count('dodge'), 1);
  assert.equal(hurt.count('hit'), 1, 'the i-frames were gone when it arrived');
});

test('a dodge has the listed distance, needs a direction and has a cooldown', () => {
  const r = start();
  r.boar.begin();
  r.play(.1, { player: { x: 0, z: 5 }, dodge: { x: 0, z: 0 } });
  assert.equal(r.count('dodge'), 0);
  r.play(.1, { player: { x: 0, z: 5 }, dodge: { x: 3, z: 4 } });
  const d = r.events.find(e => e.type === 'dodge');
  assert.ok(Math.abs(Math.hypot(d.x, d.z) - 2.5) < 1e-9);
  r.play(.1, { player: { x: 0, z: 5 }, dodge: { x: 1, z: 0 } });
  assert.equal(r.count('dodge'), 1);
  r.play(1, { player: { x: 0, z: 5 } });
  r.play(.1, { player: { x: 0, z: 5 }, dodge: { x: 1, z: 0 } });
  assert.equal(r.count('dodge'), 2);
});

/** Stands in the way of charges until it has been hit `count` times. */
function takeHits(run, count) {
  run.boar.begin();
  for (let i = 0; i < count && run.boar.state !== 'escaped'; i++) {
    run.playUntil('charge', { player: { x: run.boar.x, z: run.boar.z + 3 } });
    const ahead = { x: run.boar.x + Math.sin(run.boar.yaw) * 3, z: run.boar.z + Math.cos(run.boar.yaw) * 3 };
    run.play(60, { player: ahead, until: b => b.state !== 'charge' });
  }
}

test('5b. three hits and it runs off with one event; no restart for 30 s, and it comes back to where it was', () => {
  const r = start({ x: 2, z: -3 });
  takeHits(r, 3);
  assert.equal(r.boar.state, 'escaped');
  const raised = r.events.filter(e => e.type === ESCAPED);
  assert.equal(raised.length, 1);
  assert.equal(raised[0].hitsTaken, 3);
  r.play(29, { player: { x: 2, z: -3 } });
  assert.equal(r.boar.state, 'escaped');
  assert.equal(r.boar.begin(), false);
  assert.ok(r.boar.retryIn < 1.1 && r.boar.retryIn > 0);
  r.play(1.2, { player: { x: 100, z: 100 } });
  assert.equal(r.boar.state, 'idle');
  assert.deepEqual([r.boar.x, r.boar.z], [2, -3]);
  assert.equal(r.boar.hits, 0);
  assert.equal(r.boar.visible, true);
  assert.equal(r.count('returned'), 1);
  r.play(.1, { player: { x: 2, z: 0 } });
  assert.equal(r.boar.state, 'alert', 'met again at the same place without another script start');
});

test('one charge hits once, and only a charge hits', () => {
  const r = start();
  r.boar.begin();
  r.play(1, { player: { x: .1, z: .1 } });
  assert.equal(r.count('hit'), 0);
  r.playUntil('charge', { player: { x: 0, z: 3 } });
  r.playUntil('brake', { player: { x: 0, z: 3 } });
  assert.equal(r.count('hit'), 1);
});

test('6. a hit costs 15 stamina and never goes below 1', () => {
  const r = start();
  r.boar.stamina = 20;
  takeHits(r, 2);
  const hits = r.events.filter(e => e.type === 'hit');
  assert.equal(hits[0].staminaLost, 15);
  assert.equal(hits[0].stamina, 5);
  assert.equal(hits[1].staminaLost, 4);
  assert.equal(hits[1].stamina, 1);
  assert.equal(Math.round(Math.hypot(hits[0].x, hits[0].z) * 1e6) / 1e6, 3);
});

test('a slow phone and a fast desktop get the same fight', () => {
  const play = dt => {
    const boar = new ZhuoBoarEncounter(content, { x: 0, z: 0 });
    boar.begin();
    let now = 0;
    while (boar.state !== 'daze' && now < 10) {
      now += dt;
      boar.update(now, { player: { x: 3, z: 6 }, obstacles: [{ id: 't', x: 3, z: 6, r: .3 }] });
    }
    return { x: boar.x, z: boar.z, time: boar.time };
  };
  const fast = play(1 / 144), slow = play(1 / 30);
  assert.ok(Math.hypot(fast.x - slow.x, fast.z - slow.z) < .01, JSON.stringify({ fast, slow }));
  assert.ok(Math.abs(fast.time - slow.time) < .02);
});

const BOUNDS = { minX: -10, maxX: 10, minZ: -10, maxZ: 10 };

test('after running into the bounds it moves somewhere with room, then comes again', () => {
  const r = start({ x: 0, z: 2 });
  r.boar.begin();
  const player = { x: 0, z: 9.3 };   // pressed against the wall
  r.playUntil('charge', { player, bounds: BOUNDS });
  r.playUntil('brake', { player, bounds: BOUNDS });
  assert.equal(r.boar.state, 'brake');
  const hit = { x: r.boar.x, z: r.boar.z };
  r.playUntil('reposition', { player, bounds: BOUNDS });
  assert.equal(r.boar.state, 'reposition');
  r.playUntil('alert', { player, bounds: BOUNDS });
  assert.equal(r.boar.state, 'alert');
  assert.ok(Math.hypot(r.boar.x - hit.x, r.boar.z - hit.z) > 2, 'it moved away from the wall');
  r.playUntil('charge', { player, bounds: BOUNDS });
  const room = r.boar.line.length;
  assert.ok(room >= content.tuning.minChargeRunM, `room ${room}`);
});

test('a charge that merely reaches its full distance does not make it move', () => {
  const r = start({ x: -7, z: 0 });
  r.boar.begin();
  r.playUntil('charge', { player: { x: 7, z: 0 } });
  r.playUntil('brake', { player: { x: 7, z: 5 } });
  r.playUntil('alert', { player: { x: 7, z: 5 } });
  assert.equal(r.count('reposition'), 0);
});

test('with no room to run it moves instead of butting the same wall or trunk', () => {
  const wall = start({ x: 0, z: 9, yaw: 0 });
  wall.boar.begin();
  // The player is beyond the wall side, so it faces the wall.
  wall.play(3, { player: { x: 0, z: 9.5 }, bounds: BOUNDS });
  assert.equal(wall.count('charge'), 0);
  assert.equal(wall.count('reposition'), 1);

  const trunk = start({ x: 0, z: 0, yaw: 0 });
  trunk.boar.begin();
  const tree = { id: 'tree', x: 0, z: 1.2, r: .175 };
  trunk.play(3, { player: { x: 0, z: 2.5 }, obstacles: [tree] });
  assert.equal(trunk.count('daze'), 0, 'hiding behind a trunk at point blank does not stun it for free');
  assert.equal(trunk.count('reposition'), 1);
});

test('while moving it cannot be cleansed and does not hit', () => {
  const r = start({ x: 0, z: 9 });
  r.boar.begin();
  r.playUntil('reposition', { player: { x: 0, z: 9.5 }, bounds: BOUNDS });
  r.play(.4, { player: { x: r.boar.x + .5, z: r.boar.z }, bounds: BOUNDS, cleanseHeld: true });
  assert.equal(r.boar.state, 'reposition');
  assert.equal(r.boar.cleanseProgress, 0);
  assert.equal(r.count('hit'), 0);
});

test('in a corner with nowhere to go it still charges, and never circles for ever', () => {
  const tiny = { minX: -1.5, maxX: 1.5, minZ: -1.5, maxZ: 1.5 };
  const r = start({ x: 0, z: 0 });
  r.boar.begin();
  r.play(10, { player: { x: 0, z: 1 }, bounds: tiny });
  assert.ok(r.count('charge') > 0);
});

test('standing behind the same tree works only once: after the daze it comes round the tree', () => {
  const tree = { id: 'tree', x: 0, z: 5, r: .175 };
  const hide = { x: 0, z: 6.4 };   // right behind the trunk, and never moving
  const r = start({ x: 0, z: 0 });
  r.boar.begin();
  r.play(60, { player: hide, obstacles: [tree], until: b => b.hits > 0 });
  const stuns = r.count('daze');
  assert.equal(stuns, 1, 'one stun from that tree');
  assert.equal(r.boar.hits, 1, 'then it reached the player who stayed put');
});

test('moving again to put a tree in the way still works', () => {
  const tree = { id: 'tree', x: 0, z: 5, r: .175 };
  const r = start({ x: 0, z: 0 });
  r.boar.begin();
  // A player who keeps the trunk between them and the boar, as a person would.
  for (let i = 0; i < 400 && r.count('daze') < 2; i++) {
    const away = { x: tree.x - r.boar.x, z: tree.z - r.boar.z }, m = Math.hypot(away.x, away.z) || 1;
    const spot = { x: tree.x + away.x / m * 1.4, z: tree.z + away.z / m * 1.4 };
    r.play(.1, { player: r.boar.state === 'charge' ? r.held : (r.held = spot), obstacles: [tree] });
  }
  assert.equal(r.count('daze'), 2);
});

test('it never walks into an obstacle while moving', () => {
  const trees = [{ id: 'a', x: 2, z: 7, r: .175 }, { id: 'b', x: -2, z: 6, r: .175 }, { id: 'c', x: 0, z: 4.5, r: .8 }];
  const r = start({ x: 0, z: 9 });
  r.boar.begin();
  const input = { player: { x: 0, z: 9.6 }, bounds: BOUNDS, obstacles: trees };
  r.playUntil('reposition', input);
  while (r.boar.state === 'reposition') {
    r.play(.05, input);
    for (const t of trees) assert.ok(Math.hypot(t.x - r.boar.x, t.z - r.boar.z) > t.r + .4, `near ${t.id}`);
  }
});

test('a player who ran far away is not charged', () => {
  const r = start();
  r.boar.begin();
  r.play(3, { player: { x: 0, z: 40 } });
  assert.equal(r.boar.state, 'alert');
  assert.equal(r.count('charge'), 0);
});
