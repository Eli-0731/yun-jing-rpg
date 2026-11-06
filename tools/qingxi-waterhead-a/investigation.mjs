/**
 * Upstream investigation rules (pure, no rendering). The player walks the low stream from the downstream
 * entrance, looks at evidence up close and records it in a local clue book. Any order, any two clues are
 * enough to go back and discuss a diversion plan, all three give a fuller judgement. Nothing here grants
 * resources; the only output is the observationIds list (see observations.example.json) for parts B and C.
 */
export const OBSERVATION_IDS = ['cracked_sluice', 'silt_buildup', 'nursery_tracks'];

export const CLUE_TEXT = {
  cracked_sluice: { title: '裂開的古導水石槽', note: '石槽側面裂開，水從破口漏到岸上，下游分到的水變少。' },
  silt_buildup: { title: '泥沙堵住河道', note: '泥沙和斷枝堆成一道矮壩，水在後面積成一灘，只剩一側細流通過。' },
  nursery_tracks: { title: '妖獸育幼足跡', note: '濕泥上有大小三種足跡，有東西在這附近育幼，還踩塌了岸。' },
};

/** Environment hints: they react when looked at, but are never recorded as an answer. */
export const HINT_TEXT = {
  water_gauge: '木樁水位尺：舊刻痕在膝蓋高，現在的水只到腳踝。',
  marker_stone: '示跡石：上方一圈乾掉的苔痕是以前的水位，下方濕線才是現在。',
  resonance_stone: '水脈共鳴石：靠近時微微發亮、嗡鳴，越往上游越清楚。',
};

export const PARAMS = {
  walkSpeed: 3.2,          // m/s
  playerRadius: 0.35,
  observeRange: 2.2,       // must be this close to the evidence
  observeCone: 0.35,       // dot(facing, toClue) must exceed this: you have to look at it
  dwell: 0.6,              // s of looking before a clue can be recorded (no drive-by pickups)
};

const len = (x, z) => Math.hypot(x, z);

/** Distance from (x, z) to a convex polygon [[x, z], ...] (either winding); 0 inside. Used for walls taken from the
 *  models' collision hulls, so the player stops at the real outline of a trough or stone, not at a guessed circle. */
export function polyDistance(poly, x, z) {
  let inside = true, sign = 0, best = Infinity;
  for (let i = 0; i < poly.length; i++) {
    const [ax, az] = poly[i], [bx, bz] = poly[(i + 1) % poly.length];
    const ex = bx - ax, ez = bz - az, cross = ex * (z - az) - ez * (x - ax);
    if (cross !== 0) { if (sign && Math.sign(cross) !== sign) inside = false; sign ||= Math.sign(cross); }
    const t = Math.max(0, Math.min(1, ((x - ax) * ex + (z - az) * ez) / (ex * ex + ez * ez || 1)));
    best = Math.min(best, len(x - ax - ex * t, z - az - ez * t));
  }
  return inside ? 0 : best;
}

export class Investigation {
  constructor(world, opts = {}) {
    this.world = world;
    this.P = { ...PARAMS, ...(opts.params || {}) };
    this.player = { x: world.start.x, z: world.start.z, heading: world.start.heading || 0 };
    this.book = [];                    // [{ id, t }] in the order found
    this.t = 0;
    this.events = [];
    this.focus = null;                 // { kind: 'clue'|'hint', id, held }
    this.zones = new Set();            // named zones the player is standing in
    this.siltCleared = false;          // scene state: the player raked the silt bar open (shows what clearing would do)
  }

  #emit(type, data = {}) { this.events.push({ t: Math.round(this.t * 1000) / 1000, type, ...data }); }
  drainEvents() { const e = this.events; this.events = []; return e; }

  get observationIds() { return OBSERVATION_IDS.filter(id => this.book.some(b => b.id === id)); }

  /** null until two clues, 'discuss' with two, 'full' with all three. */
  get verdict() {
    const n = this.book.length;
    return n >= OBSERVATION_IDS.length ? 'full' : n >= 2 ? 'discuss' : null;
  }

  /** What the player is close to and looking at most directly right now (clues or hints). */
  inReach() {
    const p = this.player, fx = Math.sin(p.heading), fz = Math.cos(p.heading);
    let best = null;
    for (const [kind, list] of [['clue', this.world.clues || []], ['hint', this.world.hints || []]]) {
      for (const c of list) {
        const dx = c.x - p.x, dz = c.z - p.z, d = len(dx, dz);
        const range = c.range ?? this.P.observeRange;
        if (d > range) continue;
        const facing = d < 0.3 ? 1 : (dx * fx + dz * fz) / d;
        if (facing < this.P.observeCone) continue;
        // whatever the player is looking at most directly wins; a clue only gets a slight edge over a hint
        const score = d * 0.5 + (1 - facing) * 3 - (kind === 'clue' ? 0.15 : 0);
        if (!best || score < best.score) best = { kind, id: c.id, score };
      }
    }
    return best && { kind: best.kind, id: best.id };
  }

  /** Record what the player is looking at. Repeats never add a second entry. */
  observe() {
    const r = this.inReach();
    if (!r) { this.#emit('nothing'); return null; }
    if (r.kind === 'hint') { this.#emit('hint', { id: r.id }); return r; }
    if (!this.focus || this.focus.id !== r.id || this.focus.held < this.P.dwell) { this.#emit('look-closer', { id: r.id }); return null; }
    if (this.book.some(b => b.id === r.id)) { this.#emit('already', { id: r.id }); return r; }
    this.book.push({ id: r.id, t: Math.round(this.t * 1000) / 1000 });
    this.#emit('clue', { id: r.id, count: this.book.length });
    if (this.book.length === 2) this.#emit('verdict', { verdict: 'discuss' });
    if (this.book.length === OBSERVATION_IDS.length) this.#emit('verdict', { verdict: 'full' });
    return r;
  }

  /** Lost or stuck: back to the downstream entrance. The clue book is kept. */
  returnToEntrance() {
    const s = this.world.start;
    Object.assign(this.player, { x: s.x, z: s.z, heading: s.heading || 0 });
    this.focus = null;
    this.#emit('returned');
  }

  /** After the silt bar has been looked at, the player may rake part of it open beside it: the bar is replaced by its
   * cleared state and the water downstream rises. Only a scene change; it grants nothing and is not a handoff outcome. */
  clearSilt() {
    const silt = (this.world.clues || []).find(c => c.id === 'silt_buildup');
    if (this.siltCleared) { this.#emit('already-cleared'); return false; }
    if (!silt || !this.book.some(b => b.id === 'silt_buildup')) { this.#emit('look-first'); return false; }
    const p = this.player;
    if (len(silt.x - p.x, silt.z - p.z) > (silt.clearRange ?? 3.0)) { this.#emit('too-far'); return false; }
    this.siltCleared = true;
    this.#emit('silt-cleared');
    return true;
  }

  /** Start over: empty clue book, silt back in place, back at the entrance. */
  reset() {
    this.book = []; this.siltCleared = false; this.returnToEntrance(); this.#emit('reset');
  }

  #blocked(x, z) {
    const r = this.P.playerRadius, w = this.world;
    for (const c of w.walls || []) if (c.poly ? polyDistance(c.poly, x, z) < r : len(x - c.x, z - c.z) < c.r + r) return true;
    if (w.walkable && !w.walkable(x, z)) return true;
    return false;
  }

  /** Fixed-step update. input: { moveX, moveZ } in world axes (length <= 1), optional heading override. */
  step(dt, input = {}) {
    this.t += dt;
    const p = this.player;
    let mx = input.moveX || 0, mz = input.moveZ || 0;
    const m = len(mx, mz);
    if (m > 1) { mx /= m; mz /= m; }
    if (m > 0.05) {
      p.heading = Math.atan2(mx, mz);
      const sp = this.P.walkSpeed * dt;
      const nx = p.x + mx * sp, nz = p.z + mz * sp;
      if (!this.#blocked(nx, nz)) { p.x = nx; p.z = nz; }
      else if (!this.#blocked(nx, p.z)) p.x = nx;       // slide along walls
      else if (!this.#blocked(p.x, nz)) p.z = nz;
    }
    if (input.heading !== undefined) p.heading = input.heading;
    // dwell: how long the same thing has been in reach
    const r = this.inReach();
    if (r && this.focus && this.focus.id === r.id) this.focus.held += dt;
    else this.focus = r ? { ...r, held: 0 } : null;
    // zones (e.g. the nursery side): enter / leave events, never damage
    for (const z of this.world.zones || []) {
      const inside = len(p.x - z.x, p.z - z.z) < z.r;
      if (inside && !this.zones.has(z.id)) { this.zones.add(z.id); this.#emit('enter-zone', { id: z.id }); }
      if (!inside && this.zones.has(z.id)) { this.zones.delete(z.id); this.#emit('leave-zone', { id: z.id }); }
    }
  }

  snapshot() {
    return {
      t: this.t, player: { ...this.player }, observationIds: this.observationIds, verdict: this.verdict,
      inReach: this.inReach(), zones: [...this.zones], siltCleared: this.siltCleared,
    };
  }

  /** The handoff record for B / C. Local fixture only; it grants nothing. */
  toJSON() {
    return {
      schema: 'qingxi-waterhead-a/observations@1',
      observationIds: this.observationIds,
      order: this.book.map(b => b.id),
      verdict: this.verdict,
    };
  }
}
