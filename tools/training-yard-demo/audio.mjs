/** Small synthesized sound set (no audio files). Starts muted until the first user gesture. */
export class Sfx {
  constructor() { this.ctx = null; this.master = null; this.drone = null; }

  unlock() {
    if (this.ctx) { this.ctx.resume?.(); return; }
    const AC = globalThis.AudioContext || globalThis.webkitAudioContext;
    if (!AC) return;
    this.ctx = new AC();
    this.master = this.ctx.createGain();
    this.master.gain.value = 0.55;
    this.master.connect(this.ctx.destination);
  }

  #noise(seconds) {
    const b = this.ctx.createBuffer(1, Math.ceil(this.ctx.sampleRate * seconds), this.ctx.sampleRate);
    const d = b.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
    const s = this.ctx.createBufferSource();
    s.buffer = b;
    return s;
  }

  #env(node, t, a, peak, r) {
    const g = this.ctx.createGain();
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(peak, t + a);
    g.gain.exponentialRampToValueAtTime(0.0001, t + a + r);
    node.connect(g).connect(this.master);
    return g;
  }

  /** Hard wood-on-wood clack for a clean block. */
  clack(strength = 1) {
    if (!this.ctx) return;
    const t = this.ctx.currentTime;
    const n = this.#noise(0.12);
    const bp = this.ctx.createBiquadFilter();
    bp.type = 'bandpass'; bp.frequency.value = 1800; bp.Q.value = 3;
    n.connect(bp);
    this.#env(bp, t, 0.002, 0.9 * strength, 0.08);
    n.start(t); n.stop(t + 0.12);
    const o = this.ctx.createOscillator();
    o.frequency.setValueAtTime(220, t); o.frequency.exponentialRampToValueAtTime(90, t + 0.1);
    this.#env(o, t, 0.002, 0.5 * strength, 0.12);
    o.start(t); o.stop(t + 0.15);
  }

  /** Dull padded thump when a strike lands on you. */
  thud() {
    if (!this.ctx) return;
    const t = this.ctx.currentTime;
    const o = this.ctx.createOscillator();
    o.type = 'sine';
    o.frequency.setValueAtTime(120, t); o.frequency.exponentialRampToValueAtTime(45, t + 0.2);
    this.#env(o, t, 0.004, 0.8, 0.22);
    o.start(t); o.stop(t + 0.3);
  }

  /** Short wooden tick before each strike (rhythm cue). */
  tick(high = false) {
    if (!this.ctx) return;
    const t = this.ctx.currentTime;
    const o = this.ctx.createOscillator();
    o.type = 'triangle';
    o.frequency.value = high ? 1320 : 990;
    this.#env(o, t, 0.002, 0.18, 0.05);
    o.start(t); o.stop(t + 0.08);
  }

  /** Clear chime: perfect block / harmonised breath. */
  chime(pitch = 1) {
    if (!this.ctx) return;
    const t = this.ctx.currentTime;
    for (const [f, a] of [[880 * pitch, 0.22], [1320 * pitch, 0.12], [1760 * pitch, 0.06]]) {
      const o = this.ctx.createOscillator();
      o.frequency.value = f;
      this.#env(o, t, 0.004, a, 1.1);
      o.start(t); o.stop(t + 1.2);
    }
  }

  /** Breath drone: filtered air whose brightness follows the player's qi ring. */
  breathStart() {
    if (!this.ctx || this.drone) return;
    const n = this.#noise(2); n.loop = true;
    const lp = this.ctx.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = 300; lp.Q.value = 0.7;
    const g = this.ctx.createGain(); g.gain.value = 0.0001;
    const o = this.ctx.createOscillator(); o.frequency.value = 110;
    const og = this.ctx.createGain(); og.gain.value = 0.0001;
    n.connect(lp).connect(g).connect(this.master);
    o.connect(og).connect(this.master);
    n.start(); o.start();
    this.drone = { n, lp, g, o, og };
  }

  breathSet(qi, sync) {
    if (!this.drone) return;
    const t = this.ctx.currentTime;
    this.drone.lp.frequency.setTargetAtTime(250 + qi * 1400, t, 0.08);
    this.drone.g.gain.setTargetAtTime(0.05 + qi * 0.16, t, 0.1);
    this.drone.o.frequency.setTargetAtTime(98 + qi * 49, t, 0.2);
    this.drone.og.gain.setTargetAtTime(0.02 + sync * 0.06, t, 0.2);
  }

  breathStop() {
    if (!this.drone) return;
    const t = this.ctx.currentTime;
    const d = this.drone;
    d.g.gain.setTargetAtTime(0.0001, t, 0.15);
    d.og.gain.setTargetAtTime(0.0001, t, 0.15);
    d.n.stop(t + 0.8); d.o.stop(t + 0.8);
    this.drone = null;
  }
}
