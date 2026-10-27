import test from 'node:test';
import assert from 'node:assert/strict';
import { RhythmSession } from './rhythm.mjs';
test('qi alternates held inhale and released exhale across three cycles', () => {
  const s = new RhythmSession('qi');
  for (const e of s.events) s.input(e.input, e.at);
  assert.equal(s.snapshot().successes, 6);
  assert.equal(s.done, true);
  assert.equal(s.held, false);
});
test('rootless player can finish martial practice and cannot start qi', () => {
  assert.throws(() => new RhythmSession('qi', { hasRoots: false }), /凡骨/);
  const s = new RhythmSession('body', { hasRoots: false });
  for (const e of s.events) { s.input('press', e.at); s.input('release', e.at + .05); }
  assert.equal(s.snapshot().successes, 6);
});
test('holding or keyboard auto-repeat cannot farm successive blocks', () => {
  const s = new RhythmSession('body');
  s.input('press', 1.6);
  s.input('press', 3.3, { repeat: true });
  s.input('press', 5);
  s.advance(20);
  assert.equal(s.snapshot().successes, 1);
  assert.equal(s.results.length, 6);
});
test('misses finish cleanly and retry creates a fresh session', () => {
  const s = new RhythmSession('qi');s.advance(40);
  assert.equal(s.done, true);assert.equal(s.snapshot().successes, 0);
  assert.equal(new RhythmSession('qi', { start: 40 }).snapshot().completed, 0);
});
test('premature release fails inhale rather than silently counting a hold', () => {
  const s = new RhythmSession('qi');s.input('press',1);s.input('release',1.2);
  assert.equal(s.results[1].result,'miss');
});
test('timing uses session origin and rejects stale input', () => {
  const s = new RhythmSession('body',{ start: 100 });
  s.input('press',101.6);assert.equal(s.snapshot().successes,1);
  assert.throws(()=>s.advance(100),/monotonic/);
});
test('returned state cannot mutate scoring and no formal rewards exist', () => {
  const s = new RhythmSession('body');const state=s.input('press',1.6);
  state.results[0].result='miss';assert.equal(s.snapshot().successes,1);
  assert.equal('qi' in state,false);assert.equal('inventory' in state,false);
});
