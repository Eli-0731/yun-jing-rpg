/** Local-only rhythm state. No persistence, API requests, inventory or cultivation. */
export const PRACTICE_NOTICE = '本機演示・刷新重置・不產生正式修為';
export class RhythmSession {
  constructor(mode, { hasRoots = true, start = 0 } = {}) {
    if (!['qi', 'body'].includes(mode)) throw new Error('Unknown practice mode');
    if (mode === 'qi' && !hasRoots) throw new Error('凡骨可直接選擇武技格擋');
    this.mode = mode;
    this.start = start;
    this.lastTime = start;
    this.done = false;
    this.held = false;
    this.results = [];
    this.events = mode === 'qi'
      ? Array.from({ length: 3 }, (_, i) => [
          { at: 1 + i * 5.2, input: 'press', label: '吸氣：按住' },
          { at: 3.4 + i * 5.2, input: 'release', label: '吐氣：放開' },
        ]).flat()
      : Array.from({ length: 6 }, (_, i) => ({ at: 1.6 + i * 1.7, input: 'press', label: i % 2 ? '右側來勢：格擋' : '左側來勢：格擋' }));
    this.index = 0;
  }
  advance(now) {
    if (!Number.isFinite(now) || now < this.lastTime) throw new Error('Time must be finite and monotonic');
    this.lastTime = now;
    const t = now - this.start;
    const window = this.mode === 'qi' ? .38 : .24;
    while (!this.done && t > this.events[this.index].at + window) {
      this.results.push({ event: this.index++, result: 'miss', reason: '錯過節奏，可重試' });
      this.done = this.index === this.events.length;
    }
    return this.snapshot();
  }
  input(kind, now, { repeat = false } = {}) {
    this.advance(now);
    if (repeat || this.done) return this.snapshot();
    if (!['press', 'release'].includes(kind)) throw new Error('Unknown input');
    if ((kind === 'press') === this.held) return this.snapshot();
    this.held = kind === 'press';
    const event = this.events[this.index];
    const offset = now - this.start - event.at;
    const window = this.mode === 'qi' ? .38 : .24;
    if (Math.abs(offset) <= window && kind === event.input) {
      this.results.push({ event: this.index++, result: Math.abs(offset) <= .12 ? 'precise' : 'good', offset });
      this.done = this.index === this.events.length;
    } else if (kind === event.input || this.mode === 'qi') {
      this.results.push({ event: this.index++, result: 'miss', reason: '節奏不合，可重試', offset });
      this.done = this.index === this.events.length;
    }
    return this.snapshot();
  }
  snapshot() {
    return {
      mode: this.mode, done: this.done, held: this.held,
      next: this.done ? null : { ...this.events[this.index] },
      completed: this.index, total: this.events.length,
      successes: this.results.filter(x => x.result !== 'miss').length,
      notice: PRACTICE_NOTICE,
      results: this.results.map(x => ({ ...x })),
    };
  }
}
