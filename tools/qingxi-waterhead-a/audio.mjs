/** Small synthesized sound set (no audio files). Starts muted until the first user gesture.
 * Pattern from tools/qingxi-encounter-a/audio.mjs (PR #39, same author): a thin stream bed, a soft tick
 * when something can be looked at, a chime when a clue is written down. */
export class Sfx {
  constructor() { this.ctx = null; this.master = null; this.stream = null; }

  unlock() {
    if (this.ctx) { this.ctx.resume?.(); return; }
    const AC = globalThis.AudioContext || globalThis.webkitAudioContext;
    if (!AC) return;
    this.ctx = new AC();
    this.master = this.ctx.createGain();
    this.master.gain.value = 0.55;
    this.master.connect(this.ctx.destination);
    this.#streamBed();
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

  /** A thin trickle: band-passed noise with a slow wobble; level follows how close the player is to the water. */
  #streamBed() {
    const n = this.#noise(3); n.loop = true;
    const bp = this.ctx.createBiquadFilter(); bp.type = 'bandpass'; bp.frequency.value = 1400; bp.Q.value = 0.6;
    const g = this.ctx.createGain(); g.gain.value = 0.0001;
    const lfo = this.ctx.createOscillator(); lfo.frequency.value = 0.7;
    const lg = this.ctx.createGain(); lg.gain.value = 500;
    lfo.connect(lg).connect(bp.frequency);
    n.connect(bp).connect(g).connect(this.master);
    n.start(); lfo.start();
    this.stream = g;
  }

  /** 0..1: how loud the stream is (distance to the water). */
  streamLevel(k) {
    if (!this.stream) return;
    this.stream.gain.setTargetAtTime(0.0001 + 0.09 * k, this.ctx.currentTime, 0.3);
  }

  tick() {
    if (!this.ctx) return;
    const t = this.ctx.currentTime;
    const o = this.ctx.createOscillator(); o.type = 'triangle'; o.frequency.value = 1180;
    this.#env(o, t, 0.003, 0.06, 0.08); o.start(t); o.stop(t + 0.12);
  }

  chime(pitch = 1) {
    if (!this.ctx) return;
    const t = this.ctx.currentTime;
    for (const [f, a] of [[660 * pitch, 0.2], [990 * pitch, 0.11], [1320 * pitch, 0.06]]) {
      const o = this.ctx.createOscillator();
      o.frequency.value = f;
      this.#env(o, t, 0.004, a, 1.2);
      o.start(t); o.stop(t + 1.3);
    }
  }

  /** Soft low knock for "nothing here" / "already noted". */
  knock() {
    if (!this.ctx) return;
    const t = this.ctx.currentTime;
    const o = this.ctx.createOscillator(); o.type = 'sine'; o.frequency.setValueAtTime(220, t); o.frequency.exponentialRampToValueAtTime(140, t + 0.12);
    this.#env(o, t, 0.004, 0.12, 0.14); o.start(t); o.stop(t + 0.2);
  }
}
