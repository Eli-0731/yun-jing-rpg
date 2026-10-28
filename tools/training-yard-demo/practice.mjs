/**
 * Training-yard practice rules. Pure and time-driven (seconds), no DOM, no network, no storage.
 * Results are UI feedback only: the real gain is decided by the server's `practice-basic` action
 * (discipline 'qi' | 'body'); this demo never calls it and never creates cultivation.
 */
export const PRACTICE_NOTICE = '本機演示・刷新重置・不產生正式修為';
// Same wording the server returns for NO_ROOT so the demo does not invent a different rule.
export const NO_ROOT_MESSAGE = '目前未感應靈氣，可先練基礎武技、藥浴淬體或探索後天開靈';

const clamp01 = v => Math.min(1, Math.max(0, v));

/* ---------------------------------------------------------------- 引氣呼吸 (qi breathing) */
// One breath: inhale (guide ring grows), hold, exhale (shrinks), rest.
// Input: keep holding through 吸 and 停, release for 呼 and 歇.
export const BREATH_PHASES = [
  { key: 'inhale', label: '吸', seconds: 3.2 },
  { key: 'hold', label: '停', seconds: 1.0 },
  { key: 'exhale', label: '呼', seconds: 3.2 },
  { key: 'rest', label: '歇', seconds: 0.8 },
];
const BREATH_LENGTH = BREATH_PHASES.reduce((s, p) => s + p.seconds, 0);
const LEAD_IN = 1.5;

export function guideAt(t) {
  if (t < 0) return { phase: 'ready', label: '凝神', value: 0, cycle: 0, within: 0 };
  const cycle = Math.floor(t / BREATH_LENGTH);
  let u = t - cycle * BREATH_LENGTH;
  for (const p of BREATH_PHASES) {
    if (u < p.seconds) {
      const k = u / p.seconds;
      // Linear ramps: the player's ring moves at a constant rate, so a perfect follower can match exactly.
      const value = p.key === 'inhale' ? k : p.key === 'hold' ? 1 : p.key === 'exhale' ? 1 - k : 0;
      return { phase: p.key, label: p.label, value, cycle, within: k };
    }
    u -= p.seconds;
  }
  return { phase: 'rest', label: '歇', value: 0, cycle, within: 1 };
}

export function gradeBreath(score) {
  if (score >= 0.85) return { key: 'smooth', label: '圓融' };
  if (score >= 0.7) return { key: 'steady', label: '平穩' };
  return { key: 'scattered', label: '散亂' };
}

export class BreathSession {
  constructor({ hasRoots = true, cycles = 3, start = 0 } = {}) {
    if (!hasRoots) throw Object.assign(new Error(NO_ROOT_MESSAGE), { code: 'NO_ROOT' });
    this.cycles = cycles;
    this.start = start;
    this.last = start;
    this.held = false;
    this.qi = 0;          // the player's ring, 0..1
    this.acc = [];        // per cycle: [weighted match, weight]
    this.done = false;
  }

  setHeld(held) { if (!this.done) this.held = !!held; }

  /** Advance to absolute time `now` (seconds). Integrates in small steps so frame rate does not matter. */
  update(now) {
    if (!Number.isFinite(now) || now < this.last) throw new Error('time must be finite and monotonic');
    let t0 = this.last - this.start - LEAD_IN;
    const t1 = now - this.start - LEAD_IN;
    while (!this.done && t0 < t1) {
      const dt = Math.min(1 / 120, t1 - t0);
      t0 += dt;
      // Holding draws qi in, releasing lets it out: rates match the guide's inhale/exhale slope.
      const rate = (this.held ? 1 : -1) / BREATH_PHASES[0].seconds;
      this.qi = clamp01(this.qi + rate * dt);
      if (t0 >= 0) {
        const g = guideAt(t0);
        if (g.cycle >= this.cycles) { this.done = true; break; }
        const weight = g.phase === 'rest' ? 0.3 : 1;
        const match = 1 - Math.min(1, Math.abs(this.qi - g.value) / 0.45);
        const slot = this.acc[g.cycle] || (this.acc[g.cycle] = [0, 0]);
        slot[0] += match * weight * dt;
        slot[1] += weight * dt;
      }
    }
    this.last = now;
    return this.snapshot();
  }

  snapshot() {
    const t = this.last - this.start - LEAD_IN;
    const g = guideAt(Math.min(t, this.cycles * BREATH_LENGTH - 1e-6));
    const scores = this.acc.map(([m, w]) => (w ? m / w : 0));
    const finished = scores.slice(0, this.done ? this.cycles : g.cycle);
    return {
      mode: 'qi', done: this.done, held: this.held, qi: this.qi,
      guide: t < 0 ? 0 : g.value, phase: t < 0 ? 'ready' : g.phase, label: t < 0 ? '凝神' : g.label,
      cycle: Math.min(g.cycle, this.cycles - 1), cycles: this.cycles,
      sync: 1 - Math.min(1, Math.abs(this.qi - (t < 0 ? 0 : g.value)) / 0.45),
      cycleGrades: finished.map(s => ({ score: s, ...gradeBreath(s) })),
      harmonised: finished.filter(s => s >= 0.7).length,
      notice: PRACTICE_NOTICE,
    };
  }
}

/* ---------------------------------------------------------------- 武技格擋 (block rhythm) */
export const SIDES = ['left', 'right', 'low'];
export const SIDE_LABEL = { left: '左臂', right: '右臂', low: '下樁' };
export const WINDOW = { perfect: 0.09, good: 0.18 };

/** Three phrases that speed up; fixed per seed so a retry can be the same drill. */
export function blockPattern(seed = 7) {
  let s = seed >>> 0;
  const rnd = () => ((s = (1664525 * s + 1013904223) >>> 0) / 2 ** 32);
  const phrases = [{ n: 4, gap: 1.25 }, { n: 4, gap: 1.0 }, { n: 4, gap: 0.8 }];
  const strikes = [];
  let at = 2.0;
  let prev = null;
  for (const [pi, ph] of phrases.entries()) {
    for (let i = 0; i < ph.n; i++) {
      let side = SIDES[Math.floor(rnd() * 3)];
      if (side === prev && rnd() < 0.6) side = SIDES[(SIDES.indexOf(side) + 1) % 3];
      strikes.push({ at, side, phrase: pi });
      prev = side;
      at += ph.gap;
    }
    at += 0.9; // breath between phrases
  }
  return strikes;
}

export class BlockSession {
  constructor({ seed = 7, start = 0 } = {}) {
    this.strikes = blockPattern(seed);
    this.start = start;
    this.last = start;
    this.index = 0;
    this.results = [];
    this.combo = 0;
    this.bestCombo = 0;
    this.flinches = 0;
    this.done = false;
  }

  update(now) {
    if (!Number.isFinite(now) || now < this.last) throw new Error('time must be finite and monotonic');
    this.last = now;
    const t = now - this.start;
    while (!this.done && t > this.strikes[this.index].at + WINDOW.good) {
      this.#record({ result: 'hit', reason: '來不及格擋' });
    }
    return this.snapshot();
  }

  /** side: 'left' | 'right' | 'low'. Key-repeat events must be filtered by the caller (repeat=true). */
  input(side, now, { repeat = false } = {}) {
    this.update(now);
    if (repeat || this.done || !SIDES.includes(side)) return { judged: null, state: this.snapshot() };
    const strike = this.strikes[this.index];
    const offset = now - this.start - strike.at;
    if (Math.abs(offset) > WINDOW.good) {
      // Pressing with nothing arriving breaks the stance: mashing cannot farm combos.
      this.flinches += 1;
      this.combo = 0;
      return { judged: { result: 'flinch', reason: '架勢鬆了' }, state: this.snapshot() };
    }
    const judged = side !== strike.side
      ? { result: 'hit', reason: `擋錯方向，${SIDE_LABEL[strike.side]}打到` }
      : { result: Math.abs(offset) <= WINDOW.perfect ? 'perfect' : 'good', offset };
    this.#record(judged);
    return { judged, state: this.snapshot() };
  }

  #record(r) {
    const strike = this.strikes[this.index];
    this.results.push({ ...r, side: strike.side, index: this.index });
    this.combo = r.result === 'perfect' || r.result === 'good' ? this.combo + 1 : 0;
    this.bestCombo = Math.max(this.bestCombo, this.combo);
    this.index += 1;
    this.done = this.index >= this.strikes.length;
  }

  snapshot() {
    const blocked = this.results.filter(r => r.result === 'perfect' || r.result === 'good').length;
    const perfect = this.results.filter(r => r.result === 'perfect').length;
    const t = this.last - this.start;
    return {
      mode: 'body', done: this.done, total: this.strikes.length, judged: this.results.length,
      blocked, perfect, combo: this.combo, bestCombo: this.bestCombo, flinches: this.flinches,
      next: this.done ? null : { ...this.strikes[this.index], eta: this.strikes[this.index].at - t },
      upcoming: this.strikes.slice(this.index, this.index + 3).map(s => ({ ...s, eta: s.at - t })),
      last: this.results.at(-1) || null,
      grade: !this.done ? null : blocked >= 11 ? '身法如風' : blocked >= 8 ? '架勢已成' : '再練一輪',
      notice: PRACTICE_NOTICE,
    };
  }
}
