// Rules of the day 3 sick-boar encounter: pure logic, no Unity and no network. Numbers come from
// packages/content/zhuo-boar-encounter-v1.json. QingxiZhuoBoarRules.cs is the C# port; parity.mjs records runs that its
// smoke replays. Input per update: time, player position, obstacle list, keys. Output: state and events.
//
//   idle -> alert -> telegraph -> charge -> daze | brake -> alert -> ...
//   reposition: after every daze, after running into the bounds, or when a telegraph ends with no room to run, it trots to a spot
//   with a clear line to the player, so standing behind one tree does not work twice
//   cleanse count reached -> cleansed (stands, then runs off); hits reached -> escaped (runs off, returns to idle after the cooldown)
//
// Positions are metres on the ground plane {x, z}. Yaw is radians from +z towards +x, the same as Unity's.

export const STEP = 1 / 120;
export const CLEANSED = 'zhuoBoar.cleansed';
export const ESCAPED = 'zhuoBoar.escaped';

const dot = (a, b) => a.x * b.x + a.z * b.z;
const len = v => Math.hypot(v.x, v.z);
const sub = (a, b) => ({ x: a.x - b.x, z: a.z - b.z });
const fromYaw = yaw => ({ x: Math.sin(yaw), z: Math.cos(yaw) });
const toYaw = v => Math.atan2(v.x, v.z);
const wrap = a => { while (a > Math.PI) a -= 2 * Math.PI; while (a < -Math.PI) a += 2 * Math.PI; return a; };

export class ZhuoBoarEncounter {
  /** @param {{x:number,z:number,yaw?:number,stamina?:number,autoStart?:boolean}} home autoStart: start when the player comes close; otherwise wait for begin() */
  constructor(content, home) {
    this.c = content;
    this.t = content.tuning;
    this.home = { x: home.x, z: home.z, yaw: home.yaw ?? 0 };
    this.armed = !!home.autoStart;
    this.stamina = home.stamina ?? 100;
    this.time = 0;
    this.accumulator = 0;
    this.lastNow = null;
    this.startedAt = null;
    this.iFrameUntil = -1;
    this.dodgeReadyAt = 0;
    this.retryAt = -1;
    this.reset();
  }

  reset() {
    this.state = 'idle';
    this.x = this.home.x; this.z = this.home.z; this.yaw = this.home.yaw;
    this.stateAt = this.time;
    this.hits = 0;
    this.cleanses = 0;
    this.cleanseHeld = 0;
    this.chargeFrom = null;
    this.chargeHit = false;
    this.line = null;
    this.visible = true;
    this.fleeDir = null;
    this.wall = false;
    this.repositioned = false;
    this.moveTo = null;
  }

  get elapsed() { return this.time - this.stateAt; }
  get zhuo() { return Math.max(0, 1 - this.cleanses / this.c.cleanseNeeded); }
  get cleanseProgress() { return this.cleanseHeld / this.c.cleanseHoldSeconds; }
  get invulnerable() { return this.time < this.iFrameUntil; }
  get retryIn() { return this.state === 'escaped' ? Math.max(0, this.retryAt - this.time) : 0; }
  get finished() { return this.state === 'cleansed'; }
  get engaged() { return !['idle', 'cleansed', 'escaped'].includes(this.state); }
  canCleanse(player) { return this.state === 'daze' && len(sub(player, this)) <= this.c.cleanseRadiusM; }
  canDodge() { return this.engaged && this.time >= this.dodgeReadyAt; }

  /** The core team calls this after its scripted scene. False while it has run off or after it has been cleansed. */
  begin() {
    if (this.state !== 'idle') return false;
    this.armed = true;
    this.enter('alert');
    if (this.startedAt === null) this.startedAt = this.time;
    return true;
  }

  enter(state) { this.state = state; this.stateAt = this.time; }

  /**
   * @param {number} now seconds
   * @param {{player:{x:number,z:number}, obstacles?:{id:string,x:number,z:number,r:number}[], cleanseHeld?:boolean, dodge?:{x:number,z:number}|null, bounds?:{minX:number,maxX:number,minZ:number,maxZ:number}|null}} input
   */
  update(now, input) {
    const events = [];
    if (this.lastNow === null) this.lastNow = now;
    this.accumulator += Math.max(0, now - this.lastNow);
    this.lastNow = now;
    let dodge = input.dodge ?? null;
    if (dodge) { this.tryDodge(dodge, events); dodge = null; }
    while (this.accumulator >= STEP) {
      this.accumulator -= STEP;
      this.time += STEP;
      this.tick(input, events);
    }
    return { state: this.state, events };
  }

  tryDodge(dir, events) {
    const m = len(dir);
    if (m < 1e-3 || !this.canDodge()) return;
    this.iFrameUntil = this.time + this.c.dodgeIFrameSeconds;
    this.dodgeReadyAt = this.time + this.t.dodgeCooldownSeconds;
    events.push({ type: 'dodge', x: dir.x / m * this.c.dodgeDistanceM, z: dir.z / m * this.c.dodgeDistanceM });
  }

  tick(input, events) {
    const player = input.player, obstacles = input.obstacles ?? [];
    switch (this.state) {
      case 'idle':
        if (this.armed && len(sub(player, this)) < this.c.noticeRadiusM) {
          if (this.startedAt === null) this.startedAt = this.time;
          this.enter('alert');
          events.push({ type: 'alert' });
        }
        break;
      case 'alert':
        this.turnTowards(player);
        // A player who ran off holds it here instead of being charged from across the valley.
        if (this.elapsed >= this.t.alertSeconds && len(sub(player, this)) < this.c.noticeRadiusM) {
          this.enter('telegraph');
          events.push({ type: 'telegraph' });
        }
        break;
      case 'telegraph':
        this.turnTowards(player);
        this.line = this.chargeLine(obstacles, input.bounds);
        if (this.elapsed >= this.c.pawTelegraphSeconds) {
          const room = this.chargeLine(obstacles, input.bounds).length;
          if (!this.repositioned && room < this.t.minChargeRunM && this.startReposition(player, obstacles, input.bounds, events)) break;
          this.repositioned = false;
          this.line = { ...this.chargeLine(obstacles, input.bounds), fixed: true };
          this.chargeFrom = { x: this.x, z: this.z };
          this.chargeHit = false;
          this.enter('charge');
          events.push({ type: 'charge' });
        }
        break;
      case 'charge':
        this.tickCharge(player, obstacles, input.bounds, events);
        break;
      case 'brake':
        if (this.elapsed >= this.c.brakeRecoverSeconds) {
          const wall = this.wall;
          this.wall = false;
          if (wall && this.startReposition(player, obstacles, input.bounds, events)) break;
          this.enter('alert');
          events.push({ type: 'alert' });
        }
        break;
      case 'reposition':
        this.tickReposition(events);
        break;
      case 'daze':
        this.tickDaze(player, !!input.cleanseHeld, obstacles, input.bounds, events);
        break;
      case 'cleansed':
        if (this.elapsed >= this.t.cleansedStandSeconds) this.tickFlee(player, obstacles, this.elapsed - this.t.cleansedStandSeconds, events);
        break;
      case 'escaped':
        this.tickFlee(player, obstacles, this.elapsed, events);
        if (this.time >= this.retryAt) {
          this.reset();
          this.startedAt = null;
          events.push({ type: 'returned' });
        }
        break;
    }
  }

  turnTowards(target) {
    const want = toYaw(sub(target, this)), max = this.c.trackTurnDegPerSecond * Math.PI / 180 * STEP;
    const d = wrap(want - this.yaw);
    this.yaw = wrap(this.yaw + Math.max(-max, Math.min(max, d)));
  }

  /** The front sphere of the capsule. */
  head(x = this.x, z = this.z, dir = fromYaw(this.yaw)) {
    const reach = (this.t.boarLengthM - this.t.boarWidthM) / 2;
    return { x: x + dir.x * reach, z: z + dir.z * reach };
  }

  firstObstacle(obstacles) {
    const head = this.head(), dir = fromYaw(this.yaw), radius = this.t.boarWidthM / 2;
    for (const o of obstacles) {
      const to = sub(o, head);
      if (dot(to, dir) > 0 && len(to) < radius + o.r) return o;
    }
    return null;
  }

  outOfBounds(bounds) {
    if (!bounds) return false;
    const h = this.head();
    return h.x < bounds.minX || h.x > bounds.maxX || h.z < bounds.minZ || h.z > bounds.maxZ;
  }

  tickCharge(player, obstacles, bounds, events) {
    const dir = fromYaw(this.yaw);
    this.x += dir.x * this.c.chargeSpeedMps * STEP;
    this.z += dir.z * this.c.chargeSpeedMps * STEP;

    if (!this.chargeHit && !this.invulnerable && this.touches(player, dir)) {
      this.chargeHit = true;
      this.hits++;
      const side = dot(sub(player, this), { x: dir.z, z: -dir.x }) >= 0 ? 1 : -1;
      const push = { x: dir.x * .6 + dir.z * side * .8, z: dir.z * .6 - dir.x * side * .8 };
      const lost = Math.min(this.c.hitStaminaLoss, Math.max(0, this.stamina - this.c.staminaFloor));
      this.stamina -= lost;
      events.push({ type: 'hit', x: push.x * this.c.hitKnockbackM, z: push.z * this.c.hitKnockbackM, staminaLost: lost, stamina: this.stamina, hits: this.hits });
      if (this.hits >= this.c.hitsBeforeEscape) { this.escape(events); return; }
    }

    const obstacle = this.firstObstacle(obstacles);
    if (obstacle) {
      this.line = null;
      this.cleanseHeld = 0;
      this.enter('daze');
      events.push({ type: 'daze', obstacle: obstacle.id });
      return;
    }
    const wall = this.outOfBounds(bounds);
    if (len(sub(this, this.chargeFrom)) >= this.c.chargeMaxDistanceM || wall) {
      this.line = null;
      this.wall = wall;
      this.enter('brake');
      events.push({ type: 'brake' });
    }
  }

  /**
   * Trots to a spot with room to charge at the player, on a path clear of obstacles and inside the bounds. False when
   * nowhere qualifies (a tight corner): it then charges from where it stands, so it can never circle for ever.
   */
  startReposition(player, obstacles, bounds, events) {
    const margin = this.t.boarLengthM, radius = this.t.boarWidthM / 2 + .2;
    let best = null, bestScore = -Infinity;
    for (const scale of [1, .6]) {
      for (let i = 0; i < 16; i++) {
        const dir = fromYaw(i / 16 * 2 * Math.PI), reach = this.t.repositionDistanceM * scale;
        const spot = { x: this.x + dir.x * reach, z: this.z + dir.z * reach };
        if (bounds && (spot.x < bounds.minX + margin || spot.x > bounds.maxX - margin || spot.z < bounds.minZ + margin || spot.z > bounds.maxZ - margin)) continue;
        if (obstacles.some(o => { const to = sub(o, this), along = Math.max(0, Math.min(reach, dot(to, dir))); return Math.hypot(to.x - dir.x * along, to.z - dir.z * along) < radius + o.r; })) continue;
        const room = this.runFrom(spot, toYaw(sub(player, spot)), obstacles, bounds);
        if (room < this.t.minChargeRunM) continue;
        // A clear line to the player beats everything: it comes round the tree they are hiding behind.
        const clear = room >= Math.min(len(sub(player, spot)) - .6, this.c.chargeMaxDistanceM - .01);
        const score = (clear ? 30 : 0) + Math.min(room, this.c.chargeMaxDistanceM) + reach * .1;
        if (score > bestScore) { bestScore = score; best = spot; }
      }
    }
    if (!best) return false;
    this.moveTo = best;
    this.line = null;
    this.repositioned = true;
    this.enter('reposition');
    events.push({ type: 'reposition' });
    return true;
  }

  tickReposition(events) {
    const to = sub(this.moveTo, this), left = len(to);
    if (left > 1e-3) {
      const max = this.t.repositionTurnDegPerSecond * Math.PI / 180 * STEP;
      const d = wrap(toYaw(to) - this.yaw);
      this.yaw = wrap(this.yaw + Math.max(-max, Math.min(max, d)));
      if (Math.abs(d) < .6) {
        const step = Math.min(left, this.t.repositionSpeedMps * STEP);
        this.x += to.x / left * step;
        this.z += to.z / left * step;
      }
    }
    if (left < .05 || this.elapsed >= this.t.repositionMaxSeconds) {
      this.moveTo = null;
      this.enter('alert');
      events.push({ type: 'alert' });
    }
  }

  /** Whether the capsule, swept this step along the charge, touches the player. */
  touches(player, dir) {
    const half = (this.t.boarLengthM - this.t.boarWidthM) / 2;
    const along = Math.max(-half, Math.min(half, dot(sub(player, this), dir)));
    const closest = { x: this.x + dir.x * along, z: this.z + dir.z * along };
    return len(sub(player, closest)) < this.t.boarWidthM / 2 + this.t.playerRadiusM;
  }

  tickDaze(player, held, obstacles, bounds, events) {
    if (held && this.canCleanse(player)) {
      this.cleanseHeld += STEP;
      if (this.cleanseHeld >= this.c.cleanseHoldSeconds - 1e-9) {
        this.cleanseHeld = 0;
        this.cleanses++;
        events.push({ type: 'cleanse', count: this.cleanses });
        if (this.cleanses >= this.c.cleanseNeeded) {
          this.pickFlee(player, obstacles);
          this.enter('cleansed');
          events.push({ type: CLEANSED, durationSeconds: this.time - this.startedAt, hitsTaken: this.hits });
          return;
        }
      }
    } else this.cleanseHeld = 0;
    if (this.elapsed >= this.c.dazeSeconds) {
      this.cleanseHeld = 0;
      if (this.startReposition(player, obstacles, bounds, events)) return;
      this.enter('alert');
      events.push({ type: 'alert' });
    }
  }

  escape(events) {
    this.line = null;
    this.retryAt = this.time + this.c.retryCooldownSeconds;
    this.enter('escaped');
    events.push({ type: ESCAPED, hitsTaken: this.hits });
  }

  /** Away from the player, through the widest gap among the obstacles. */
  pickFlee(player, obstacles) {
    let best = null, bestScore = -Infinity;
    const away = sub(this, player), awayLen = Math.max(len(away), 1e-3);
    for (let i = 0; i < 16; i++) {
      const dir = fromYaw(i / 16 * 2 * Math.PI);
      let clear = this.t.fleeSpeedMps * this.t.fleeSeconds;
      for (const o of obstacles) {
        const to = sub(o, this), along = dot(to, dir);
        if (along > 0 && Math.hypot(to.x - dir.x * along, to.z - dir.z * along) < this.t.boarWidthM / 2 + o.r + .3) clear = Math.min(clear, along);
      }
      const score = clear + dot(dir, away) / awayLen * 6;
      if (score > bestScore) { bestScore = score; best = dir; }
    }
    this.fleeDir = best;
  }

  tickFlee(player, obstacles, fleeing, events) {
    if (!this.visible) return;
    if (!this.fleeDir) this.pickFlee(player, obstacles);
    this.yaw = toYaw(this.fleeDir);
    this.x += this.fleeDir.x * this.t.fleeSpeedMps * STEP;
    this.z += this.fleeDir.z * this.t.fleeSpeedMps * STEP;
    if (fleeing >= this.t.fleeSeconds) { this.visible = false; events.push({ type: 'gone' }); }
  }

  /** Where the charge would go from here: from the boar, up to the first obstacle, the bounds or the maximum distance. */
  chargeLine(obstacles, bounds) {
    return { x: this.x, z: this.z, yaw: this.yaw, length: this.runFrom(this, this.yaw, obstacles, bounds), width: this.c.chargeLineWidthM, fixed: false };
  }

  /** How far a charge from `from` along `yaw` would run. */
  runFrom(from, yaw, obstacles, bounds) {
    const dir = fromYaw(yaw), radius = this.t.boarWidthM / 2;
    let length = this.c.chargeMaxDistanceM;
    const head = this.head(from.x, from.z, dir);
    for (const o of obstacles) {
      const to = sub(o, head), along = dot(to, dir);
      if (along <= 0) continue;
      const lateral = Math.hypot(to.x - dir.x * along, to.z - dir.z * along), reach = radius + o.r;
      if (lateral < reach) length = Math.min(length, Math.max(0, along - Math.sqrt(reach * reach - lateral * lateral)));
    }
    if (bounds) {
      const toEdge = (from, d, min, max) => d > 1e-6 ? (max - from) / d : d < -1e-6 ? (min - from) / d : Infinity;
      length = Math.min(length, Math.max(0, Math.min(toEdge(head.x, dir.x, bounds.minX, bounds.maxX), toEdge(head.z, dir.z, bounds.minZ, bounds.maxZ))));
    }
    return length;
  }
}
