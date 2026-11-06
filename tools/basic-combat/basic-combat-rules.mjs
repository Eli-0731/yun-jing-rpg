// Novice bare-hand combat: pure logic, no Unity and no network. Numbers come from packages/content/basic-combat-v1.json;
// QingxiBasicCombatRules.cs is the C# port and parity.mjs records runs that its smoke replays.
//
//   idle -> light (windup -> active -> recovery) -> idle        press attack during recovery (from chainFrom) to chain 1 -> 2 -> 3
//   idle -> charging -> heavy (windup -> active -> recovery)     hold, release after chargeMin; cooldown starts when it fires
//   idle | recovery | charging -> dodge                          i-frames from the start of the dodge; windup and active cannot dodge
//
// Each swing hits a target at most once. On attack start the fighter turns to the nearest target within autoFaceRadius (no lock-on).
// Positions are metres on the ground plane {x, z}. Yaw is radians from +z towards +x, the same as Unity's.

export const STEP = 1 / 120;
export const HIT = 'combat.hit';

const len = v => Math.hypot(v.x, v.z);
const sub = (a, b) => ({ x: a.x - b.x, z: a.z - b.z });
const fromYaw = yaw => ({ x: Math.sin(yaw), z: Math.cos(yaw) });
const toYaw = v => Math.atan2(v.x, v.z);
const wrap = a => { while (a > Math.PI) a -= 2 * Math.PI; while (a < -Math.PI) a += 2 * Math.PI; return a; };
const deg = r => r * 180 / Math.PI;

export class BasicCombat {
  /** @param {object} content basic-combat-v1.json  @param {{x?:number,z?:number,yaw?:number}} [at] */
  constructor(content, at = {}) {
    this.c = content;
    this.x = at.x ?? 0;
    this.z = at.z ?? 0;
    this.yaw = at.yaw ?? 0;
    this.time = 0;
    this.accumulator = 0;
    this.lastNow = null;
    this.state = 'idle';
    this.stateAt = 0;
    this.combo = 0;            // index into light[] of the current or last light attack
    this.attack = null;        // the spec of the swing in progress
    this.phase = null;         // windup | active | recovery
    this.hitSet = new Set();
    this.chargeFrom = -1;
    this.heavyPower = 0;
    this.heavyReadyAt = 0;
    this.dodgeReadyAt = 0;
    this.iFrameUntil = -1;
    this.dodgeDir = { x: 0, z: 1 };
    this.events = [];
    this.swing = 0;            // increments per attack, used as attack instance id
  }

  get elapsed() { return this.time - this.stateAt; }
  get invulnerable() { return this.time < this.iFrameUntil; }
  get heavyCooldown() { return Math.max(0, this.heavyReadyAt - this.time); }
  get dodgeCooldown() { return Math.max(0, this.dodgeReadyAt - this.time); }
  get charge() { return this.state === 'charging' ? Math.min(1, (this.time - this.chargeFrom) / this.c.heavy.chargeMax) : 0; }

  enter(state) { this.state = state; this.stateAt = this.time; }

  emit(type, data = {}) { this.events.push({ type, t: +this.time.toFixed(4), ...data }); }

  /**
   * Advance to `now` in fixed steps and apply this frame's input.
   * @param {number} now seconds
   * @param {{attack?:boolean, heavyHeld?:boolean, dodge?:boolean, move?:{x:number,z:number}, x?:number, z?:number, yaw?:number}} input
   *   attack / dodge are presses this frame; heavyHeld is the button state; move is the stick in world space; x/z/yaw override the
   *   fighter's position (the engine owns walking) — combat only adds lunge and dodge displacement through velocity().
   * @param {Array<{id:string,x:number,z:number,radius?:number,alive?:boolean}>} targets
   * @returns {Array<object>} events raised during this call
   */
  update(now, input = {}, targets = []) {
    if (input.x !== undefined) { this.x = input.x; this.z = input.z; }
    if (input.yaw !== undefined && !this.busy) this.yaw = input.yaw;
    if (this.lastNow === null) this.lastNow = now;
    this.accumulator += Math.max(0, now - this.lastNow);
    this.lastNow = now;
    const start = this.events.length;
    // the held heavy button counts as held through the frame; presses land at `now`, after time has caught up
    const held = { ...input, attack: false, dodge: false };
    while (this.accumulator >= STEP - 1e-9) {
      this.accumulator -= STEP;
      this.step(STEP, held, targets);
    }
    this.applyInput(input, targets);
    return this.events.slice(start);
  }

  get busy() { return this.state === 'light' || this.state === 'heavy' || this.state === 'dodge'; }

  applyInput(input, targets) {
    if (input.dodge) this.tryDodge(input.move);
    if (input.attack) this.tryLight(targets, input.move);
    if (input.heavyHeld && this.state === 'idle') this.tryCharge();
    if (!input.heavyHeld && this.state === 'charging') this.releaseCharge(targets, input.move);
  }

  tryLight(targets, move) {
    if (this.state === 'idle') return this.startLight(0, targets, move);
    if (this.state === 'light' && this.phase === 'recovery') {
      const sinceRecovery = this.elapsed - this.attack.windup - this.attack.active;
      if (sinceRecovery >= this.attack.chainFrom && this.combo < this.c.light.length - 1) return this.startLight(this.combo + 1, targets, move);
    }
    this.emit('input.ignored', { input: 'attack', state: this.state, phase: this.phase });
    return false;
  }

  startLight(index, targets, move) {
    this.combo = index;
    this.attack = this.c.light[index];
    this.beginSwing('light', targets, move);
    return true;
  }

  tryCharge() {
    if (this.time < this.heavyReadyAt) { this.emit('heavy.cooldown', { remaining: +this.heavyCooldown.toFixed(3) }); return false; }
    this.chargeFrom = this.time;
    this.enter('charging');
    this.emit('heavy.charge');
    return true;
  }

  releaseCharge(targets, move) {
    const held = this.time - this.chargeFrom;
    if (held < this.c.heavy.chargeMin) {
      this.enter('idle');
      this.emit('heavy.cancelled', { held: +held.toFixed(3) });
      return false;
    }
    this.heavyPower = Math.min(1, (held - this.c.heavy.chargeMin) / (this.c.heavy.chargeMax - this.c.heavy.chargeMin));
    this.attack = this.c.heavy;
    this.heavyReadyAt = this.time + this.c.heavy.cooldown;
    this.beginSwing('heavy', targets, move);
    return true;
  }

  beginSwing(kind, targets, move) {
    this.swing++;
    this.hitSet = new Set();
    this.phase = 'windup';
    this.enter(kind);
    const target = this.nearest(targets);
    if (target) this.yaw = toYaw(sub(target, this));
    else if (move && len(move) > 0.1) this.yaw = toYaw(move);
    this.emit('attack.start', { attackId: this.attack.id, kind, swing: this.swing, facing: target ? target.id : null,
      power: kind === 'heavy' ? +this.heavyPower.toFixed(3) : undefined });
  }

  nearest(targets) {
    let best = null, bestD = this.c.facing.autoFaceRadius + 1e-9;
    for (const t of targets) {
      if (t.alive === false) continue;
      const d = len(sub(t, this));
      if (d < bestD) { best = t; bestD = d; }   // ties keep the first listed
    }
    return best;
  }

  tryDodge(move) {
    const recovering = (this.state === 'light' || this.state === 'heavy') && this.phase === 'recovery' && this.c.dodge.cancelsRecovery;
    const free = this.state === 'idle' || this.state === 'charging' || recovering;
    if (!free || this.time < this.dodgeReadyAt) { this.emit('input.ignored', { input: 'dodge', state: this.state, phase: this.phase }); return false; }
    const dir = move && len(move) > 0.1 ? move : { x: -Math.sin(this.yaw), z: -Math.cos(this.yaw) };   // standing still: step back
    const l = len(dir);
    this.dodgeDir = { x: dir.x / l, z: dir.z / l };
    if (this.state === 'charging') this.emit('heavy.cancelled', { held: +(this.time - this.chargeFrom).toFixed(3) });
    this.attack = null;
    this.phase = null;
    this.enter('dodge');
    this.iFrameUntil = this.time + this.c.dodge.iframes;
    this.dodgeReadyAt = this.time + this.c.dodge.duration + this.c.dodge.cooldown;
    this.emit('dodge.start', { cancelled: recovering });
    return true;
  }

  /** Something tries to hurt the fighter; returns 'dodged' while i-frames last. */
  receive(source = 'enemy') {
    const result = this.invulnerable ? 'dodged' : 'hit';
    this.emit('defend', { source, result });
    return result;
  }

  /** World-space velocity the engine should add this frame (lunge during windup/active, dodge displacement). */
  velocity() {
    if (this.state === 'dodge') {
      const s = this.c.dodge.distance / this.c.dodge.duration;
      return { x: this.dodgeDir.x * s, z: this.dodgeDir.z * s };
    }
    if ((this.state === 'light' || this.state === 'heavy') && this.phase !== 'recovery' && this.attack.lunge) {
      const s = this.attack.lunge / (this.attack.windup + this.attack.active);
      const f = fromYaw(this.yaw);
      return { x: f.x * s, z: f.z * s };
    }
    return { x: 0, z: 0 };
  }

  step(dt, input, targets) {
    this.time += dt;
    const v = this.velocity();
    this.x += v.x * dt; this.z += v.z * dt;
    if (this.state === 'dodge' && this.elapsed >= this.c.dodge.duration) { this.enter('idle'); this.emit('dodge.end'); }
    if (this.state === 'charging' && this.time - this.chargeFrom >= this.c.heavy.chargeMax) this.releaseCharge(targets, input.move);
    if (this.state !== 'light' && this.state !== 'heavy') return;
    const a = this.attack, e = this.elapsed;
    const phase = e < a.windup ? 'windup' : e < a.windup + a.active ? 'active' : e < a.windup + a.active + a.recovery ? 'recovery' : 'done';
    if (phase !== this.phase) {
      this.phase = phase;
      if (phase === 'done') { this.enter('idle'); this.phase = null; this.emit('attack.end', { attackId: a.id }); return; }
    }
    if (this.phase === 'active') this.resolveHits(targets);
  }

  resolveHits(targets) {
    const a = this.attack, f = fromYaw(this.yaw);
    for (const t of targets) {
      if (t.alive === false || this.hitSet.has(t.id)) continue;
      const to = sub(t, this), d = len(to);
      if (d > a.range + (t.radius ?? 0.3)) continue;
      const angle = d < 1e-6 ? 0 : Math.abs(deg(wrap(toYaw(to) - this.yaw)));
      if (angle > a.arc / 2) continue;
      this.hitSet.add(t.id);
      const heavy = this.state === 'heavy';
      const p = this.heavyPower;
      const damage = heavy ? Math.round(a.damageMin + (a.damageMax - a.damageMin) * p) : a.damage;
      const knockback = heavy ? +(a.knockbackMin + (a.knockbackMax - a.knockbackMin) * p).toFixed(3) : (a.knockback ?? 0);
      this.emit(HIT, { targetId: t.id, attackId: a.id, damage, knockback, dirX: +f.x.toFixed(4), dirZ: +f.z.toFixed(4),
        hitStop: a.hitStop, shake: a.shake, heavy, swing: this.swing });
    }
  }
}
