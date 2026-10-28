/**
 * Qingxi forest rabbit encounter rules. Pure, fixed-step, no DOM / network / storage.
 * Units: metres, seconds, radians. Ground plane is (x, z); +z points from the village towards the forest.
 *
 * Rabbit states (all observable): idle (burrow) -> alert -> windup -> charge -> stagger -> retreat.
 * The player can walk, dodge (short dash with i-frames), block (hold), attack, and use one chosen
 * technique: sword "看破綻" (bonus damage only inside the stagger window) or body "穩架" (perfect block
 * staggers the rabbit longer). Qi technique is listed for the next version and is not playable.
 *
 * Nothing here is a real reward: results are local demo feedback. Real drops only come from the server's
 * internal hunt death endpoint after a region process validated the fight (see CONTRACT.md).
 */
export const NOTICE = '本機展示・刷新重置・不發正式掉落或靈石';

export const PARAMS = Object.freeze({
  dt: 1 / 60,
  player: { radius: 0.35, speed: 3.2, hp: 3, dodge: { distance: 2.6, time: 0.32, iframes: 0.26, cooldown: 0.75 },
    attack: { range: 1.55, arc: Math.PI * 0.45, windup: 0.18, recover: 0.32 },
    block: { arc: Math.PI * 0.6, perfect: 0.18, spamLimit: 4, spamWindow: 1.5, breakTime: 1.2 } },
  rabbit: { radius: 0.38, hp: 3, alertRadius: 7.5, engageRadius: 5.0, leashRadius: 13, alertTime: 1.1,
    windup: 0.85, chargeSpeed: 9.5, chargeMax: 5.0, staggerTime: 1.3, blockedStagger: 1.9, parryStagger: 2.6,
    wallStagger: 2.2, retreatSpeed: 5.5, cooldownAfterRetreat: 2.5 },
  safeRadius: 1.4,
});

const len = (x, z) => Math.hypot(x, z);
const angleDiff = (a, b) => Math.atan2(Math.sin(a - b), Math.cos(a - b));
/** heading convention: 0 = +z, positive = towards +x */
const headingTo = (fx, fz, tx, tz) => Math.atan2(tx - fx, tz - fz);

/**
 * world: { burrow:{x,z}, safe:{x,z}, start:{x,z}, cover:[{x,z,r}], walls:[{x,z,r}],
 *          safeZones?:[{x,z,r}] (e.g. the watch platform), dummies?:[{x,z,r,wearAt}] (A12 practice targets) }
 * cover circles block the rabbit's sight line; walls stop a charge (rabbit stuns itself) and the player.
 */
export class Encounter {
  constructor(world, { style = 'sword', params = PARAMS } = {}) {
    if (!['sword', 'body'].includes(style)) throw new Error('style must be sword or body (qi is next version)');
    this.P = params;
    this.world = world;
    this.style = style;
    this.time = 0;
    this.events = [];
    this.player = { x: world.start.x, z: world.start.z, heading: 0, hp: params.player.hp, moveX: 0, moveZ: 0,
      dodgeT: 0, dodgeCd: 0, dodgeDir: [0, 0], blocking: false, blockSince: -1, blockPresses: [], guardBroken: 0,
      attackT: 0, attackKind: null, attackHit: false, downed: false };
    this.rabbit = { x: world.burrow.x, z: world.burrow.z, heading: Math.PI, hp: params.rabbit.hp, state: 'idle',
      t: 0, seen: 0, dir: 0, travelled: 0, hitThisCharge: false, cooldown: 0, stagger: 0 };
    this.stats = { dodged: 0, blocked: 0, parried: 0, hitsTaken: 0, hitsLanded: 0, whiffs: 0, retreats: 0 };
    this.outcome = null; // 'won' | 'downed' | null
    this.dummyHits = [];
  }

  // ------------------------------------------------------------ inputs (all validated by state)
  move(x, z) { const l = len(x, z); this.player.moveX = l > 1 ? x / l : x; this.player.moveZ = l > 1 ? z / l : z; }
  face(heading) { if (Number.isFinite(heading)) this.player.heading = heading; }

  dodge() {
    const p = this.player;
    if (this.outcome || p.dodgeT > 0 || p.dodgeCd > 0 || p.attackT > 0) return false;
    let [dx, dz] = [p.moveX, p.moveZ];
    if (!dx && !dz) { dx = -Math.sin(p.heading); dz = -Math.cos(p.heading); } // backstep when standing still
    const l = len(dx, dz);
    p.dodgeDir = [dx / l, dz / l];
    p.dodgeT = this.P.player.dodge.time;
    p.dodgeCd = this.P.player.dodge.cooldown + p.dodgeT;
    p.blocking = false;
    this.#emit('dodge');
    return true;
  }

  setBlock(on) {
    const p = this.player, B = this.P.player.block;
    if (this.outcome) return false;
    if (on && !p.blocking) {
      p.blockPresses = p.blockPresses.filter(t => this.time - t < B.spamWindow);
      p.blockPresses.push(this.time);
      if (p.blockPresses.length > B.spamLimit) {   // mashing block breaks the stance for a moment
        p.guardBroken = B.breakTime; p.blockPresses = []; p.blocking = false;
        this.#emit('guard-broken');
        return false;
      }
      if (p.guardBroken > 0 || p.dodgeT > 0 || p.attackT > 0) return false;
      p.blocking = true; p.blockSince = this.time;
      return true;
    }
    if (!on) p.blocking = false;
    return false;
  }

  attack(kind = 'basic') {
    const p = this.player, A = this.P.player.attack;
    if (this.outcome || p.attackT > 0 || p.dodgeT > 0) return false;
    if (kind === 'technique' && this.style !== 'sword') kind = 'basic'; // body style's technique is the parry
    p.attackT = A.windup + A.recover; p.attackKind = kind; p.attackHit = false; p.blocking = false;
    this.#emit('attack', { kind });
    return true;
  }

  /** Player tab hidden / connection lost: the encounter cannot continue fairly, so the rabbit disengages. */
  disconnect() {
    if (['alert', 'windup', 'charge', 'stagger'].includes(this.rabbit.state)) this.#retreat('disconnect');
    this.player.moveX = this.player.moveZ = 0; this.player.blocking = false;
  }

  // ------------------------------------------------------------ simulation
  step(seconds) {
    const n = Math.max(0, Math.round(seconds / this.P.dt));
    for (let i = 0; i < n; i++) this.#tick(this.P.dt);
    return this.snapshot();
  }

  #tick(dt) {
    this.time += dt;
    this.#tickPlayer(dt);
    this.#tickRabbit(dt);
  }

  #tickPlayer(dt) {
    const p = this.player, P = this.P.player;
    p.dodgeCd = Math.max(0, p.dodgeCd - dt);
    p.guardBroken = Math.max(0, p.guardBroken - dt);
    if (this.outcome === 'downed') return;
    let vx = p.moveX * P.speed, vz = p.moveZ * P.speed;
    if (p.blocking || p.attackT > 0) { vx *= 0.35; vz *= 0.35; }
    if (p.dodgeT > 0) {
      p.dodgeT = Math.max(0, p.dodgeT - dt);
      const s = P.dodge.distance / P.dodge.time;
      vx = p.dodgeDir[0] * s; vz = p.dodgeDir[1] * s;
    }
    this.#walk(p, vx * dt, vz * dt, P.radius);
    if (p.attackT > 0) {
      const before = p.attackT;
      p.attackT = Math.max(0, p.attackT - dt);
      const A = P.attack;
      if (before > A.recover && p.attackT <= A.recover) this.#resolveAttack();   // the swing lands after windup
    }
  }

  #walk(o, dx, dz, r) {
    const nx = o.x + dx, nz = o.z + dz;
    const solid = this.world.walls || [];
    if (!solid.some(w => len(nx - w.x, o.z - w.z) < w.r + r)) o.x = nx;
    if (!solid.some(w => len(o.x - w.x, nz - w.z) < w.r + r)) o.z = nz;
  }

  #sees() {
    const p = this.player, r = this.rabbit;
    const d = len(p.x - r.x, p.z - r.z);
    if (d > this.P.rabbit.alertRadius) return false;
    // sight line blocked by any cover circle between rabbit and player
    for (const c of this.world.cover || []) {
      const ax = p.x - r.x, az = p.z - r.z, t = Math.max(0, Math.min(1, ((c.x - r.x) * ax + (c.z - r.z) * az) / (d * d || 1)));
      if (len(r.x + ax * t - c.x, r.z + az * t - c.z) < c.r) return false;
    }
    return true;
  }

  #tickRabbit(dt) {
    const r = this.rabbit, R = this.P.rabbit, p = this.player;
    if (this.outcome === 'won' && r.state !== 'retreat') return;
    r.t += dt;
    const dPlayer = len(p.x - r.x, p.z - r.z);
    const atSafe = this.inSafeZone();
    const leashed = len(p.x - this.world.burrow.x, p.z - this.world.burrow.z) > R.leashRadius;
    switch (r.state) {
      case 'idle': {
        r.cooldown = Math.max(0, r.cooldown - dt);
        if (!r.cooldown && !atSafe && this.#sees() && !this.outcome) this.#enter('alert');
        break;
      }
      case 'alert': {   // ears up, faces the player, thumps the ground: the first tell
        r.heading = headingTo(r.x, r.z, p.x, p.z);
        if (atSafe || leashed) { this.#retreat(atSafe ? 'safe-point' : 'left-area'); break; }
        if (!this.#sees()) { r.seen = Math.max(0, r.seen - dt * 2); if (r.t > 3 && !r.seen) this.#retreat('lost-sight'); break; }
        r.seen += dt;
        if (dPlayer < R.engageRadius && r.seen >= R.alertTime) this.#enter('windup');
        break;
      }
      case 'windup': {  // crouch + scrape: the readable warning before any hit can happen
        r.heading = headingTo(r.x, r.z, p.x, p.z);
        if (atSafe || leashed) { this.#retreat(atSafe ? 'safe-point' : 'left-area'); break; }
        if (r.t >= r.windupTime) {
          r.dir = r.heading;  // direction locks at the end of windup: side-steps after this make it miss
          r.travelled = 0; r.hitThisCharge = false;
          this.#enter('charge');
        }
        break;
      }
      case 'charge': {
        const step = R.chargeSpeed * dt;
        const nx = r.x + Math.sin(r.dir) * step, nz = r.z + Math.cos(r.dir) * step;
        const wall = (this.world.walls || []).find(w => len(nx - w.x, nz - w.z) < w.r + R.radius);
        if (wall) { this.#stagger(R.wallStagger, 'wall'); break; }
        r.x = nx; r.z = nz; r.travelled += step;
        if (!r.hitThisCharge && len(p.x - r.x, p.z - r.z) < R.radius + this.P.player.radius) this.#resolveImpact();
        if (r.state === 'charge' && r.travelled >= R.chargeMax) this.#stagger(R.staggerTime, 'overrun');
        break;
      }
      case 'stagger': { // the opening: attacks here land
        if (r.t >= r.stagger) {
          if (atSafe || leashed) this.#retreat(atSafe ? 'safe-point' : 'left-area');
          else this.#enter('alert');
        }
        break;
      }
      case 'retreat': {
        const bx = this.world.burrow.x - r.x, bz = this.world.burrow.z - r.z, d = len(bx, bz);
        if (d < 0.2) {
          r.x = this.world.burrow.x; r.z = this.world.burrow.z; r.cooldown = R.cooldownAfterRetreat;
          if (r.hp > 0) r.hp = Math.max(r.hp, 1);
          this.#enter('idle');
        } else {
          r.heading = Math.atan2(bx, bz);
          const s = Math.min(d, R.retreatSpeed * dt);
          r.x += bx / d * s; r.z += bz / d * s;
        }
        break;
      }
    }
  }

  #resolveImpact() {
    const r = this.rabbit, p = this.player, B = this.P.player.block;
    r.hitThisCharge = true;
    if (p.dodgeT > 0 && p.dodgeT > this.P.player.dodge.time - this.P.player.dodge.iframes) {
      this.stats.dodged++; this.#emit('dodged'); return;           // passes through during i-frames
    }
    const facing = Math.abs(angleDiff(p.heading, headingTo(p.x, p.z, r.x, r.z))) < B.arc / 2;
    if (p.blocking && facing) {
      const perfect = this.time - p.blockSince <= B.perfect;
      if (perfect) { this.stats.parried++; this.#emit('parry'); this.#stagger(this.style === 'body' ? this.P.rabbit.parryStagger : this.P.rabbit.blockedStagger, 'parry'); }
      else { this.stats.blocked++; this.#emit('blocked'); this.#stagger(this.P.rabbit.blockedStagger * (this.style === 'body' ? 1 : 0.75), 'blocked'); }
      return;
    }
    p.hp -= 1; this.stats.hitsTaken++;
    this.#emit('player-hit', { hp: p.hp, reason: p.blocking ? '防禦方向不對' : p.dodgeT > 0 ? '閃得太晚' : '正面被撞' });
    // knockback along the charge direction
    this.#walk(p, Math.sin(r.dir) * 0.8, Math.cos(r.dir) * 0.8, this.P.player.radius);
    if (p.hp <= 0) { p.downed = true; this.outcome = 'downed'; this.#emit('downed'); this.#retreat('player-down'); }
  }

  #resolveAttack() {
    const p = this.player, r = this.rabbit, A = this.P.player.attack;
    // practice dummies (A12) take any strike that is in range and aimed: warm-up before the real thing
    for (const [i, dm] of (this.world.dummies || []).entries()) {
      const dd = len(dm.x - p.x, dm.z - p.z);
      if (dd <= A.range + dm.r && Math.abs(angleDiff(p.heading, headingTo(p.x, p.z, dm.x, dm.z))) < A.arc / 2) {
        this.dummyHits[i] = (this.dummyHits[i] || 0) + (p.attackKind === 'technique' ? 2 : 1);
        this.#emit('dummy-hit', { index: i, total: this.dummyHits[i], worn: this.dummyHits[i] >= (dm.wearAt || 8), kind: p.attackKind });
        return;
      }
    }
    const d = len(r.x - p.x, r.z - p.z);
    const inArc = Math.abs(angleDiff(p.heading, headingTo(p.x, p.z, r.x, r.z))) < A.arc / 2;
    if (d > A.range + r.radius || !inArc || r.state === 'idle' || r.state === 'retreat') {
      this.stats.whiffs++; this.#emit('whiff', { reason: d > A.range + r.radius ? '距離太遠' : !inArc ? '沒有對準' : '目標已退' }); return;
    }
    if (r.state !== 'stagger') {   // outside the opening the rabbit sidesteps: timing matters, not animation
      this.stats.whiffs++; this.#emit('whiff', { reason: '還不是破綻，兔子躲開了' });
      if (r.state === 'alert') this.#enter('windup');
      return;
    }
    const dmg = p.attackKind === 'technique' ? 2 : 1;
    r.hp = Math.max(0, r.hp - dmg); this.stats.hitsLanded++;
    this.#emit('rabbit-hit', { dmg, hp: r.hp, kind: p.attackKind });
    if (r.hp <= 0) { this.outcome = 'won'; this.#emit('won'); this.#retreat('defeated'); }
  }

  #stagger(seconds, cause) { this.rabbit.stagger = seconds; this.#enter('stagger'); this.#emit('stagger', { cause, seconds }); }

  #retreat(reason) { this.stats.retreats++; this.#enter('retreat'); this.#emit('retreat', { reason }); }

  #enter(state) {
    const r = this.rabbit;
    r.state = state; r.t = 0;
    if (state === 'alert') r.seen = 0;
    // a hurt rabbit gets hasty: shorter windup, but never shorter than a fair reaction window
    if (state === 'windup') r.windupTime = r.hp <= 1 ? Math.max(0.6, this.P.rabbit.windup * 0.75) : this.P.rabbit.windup;
    this.#emit('state', { state, ...(state === 'windup' ? { windup: r.windupTime } : {}) });
  }

  #emit(type, data = {}) { this.events.push({ t: Math.round(this.time * 1000) / 1000, type, ...data }); }

  /** On the safe point (A09) or any extra safe zone such as the watch platform (A10). */
  inSafeZone() {
    const p = this.player;
    if (len(p.x - this.world.safe.x, p.z - this.world.safe.z) < this.P.safeRadius) return true;
    return (this.world.safeZones || []).some(z => len(p.x - z.x, p.z - z.z) < z.r);
  }

  drainEvents() { const e = this.events; this.events = []; return e; }

  /** Restart from the safe point (or world.respawn, a spot inside its radius); nothing carries over (no permanent loss in the demo). */
  resetAtSafePoint() {
    const fresh = new Encounter({ ...this.world, start: this.world.respawn || this.world.safe }, { style: this.style, params: this.P });
    Object.assign(this, fresh);
    this.#emit('reset');
  }

  snapshot() {
    const p = this.player, r = this.rabbit;
    return {
      time: this.time, style: this.style, outcome: this.outcome, notice: NOTICE,
      player: { x: p.x, z: p.z, heading: p.heading, hp: p.hp, dodging: p.dodgeT > 0, blocking: p.blocking,
        guardBroken: p.guardBroken > 0, attacking: p.attackT > 0, dodgeReady: p.dodgeCd === 0 },
      rabbit: { x: r.x, z: r.z, heading: r.heading, hp: r.hp, state: r.state, t: r.t,
        windupLeft: r.state === 'windup' ? r.windupTime - r.t : null,
        openingLeft: r.state === 'stagger' ? r.stagger - r.t : null, chargeDir: r.state === 'charge' || r.state === 'windup' ? r.dir || r.heading : null },
      stats: { ...this.stats },
    };
  }
}
