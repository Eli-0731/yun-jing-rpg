import test from 'node:test';
import assert from 'node:assert/strict';
import {
  BreathSession, BlockSession, blockPattern, guideAt, BREATH_PHASES, WINDOW, NO_ROOT_MESSAGE, PRACTICE_NOTICE,
} from './practice.mjs';

const BREATH = BREATH_PHASES.reduce((s, p) => s + p.seconds, 0);
const LEAD = 1.5;

function playBreath(session, policy, step = 1 / 60) {
  let t = 0;
  while (!session.done && t < 60) {
    t += step;
    session.setHeld(policy(t - LEAD));
    session.update(t);
  }
  return session.snapshot();
}

test('guide ring rises on inhale, holds full, falls on exhale', () => {
  assert.equal(guideAt(-0.1).phase, 'ready');
  assert.ok(guideAt(1.6).value > 0.4 && guideAt(1.6).phase === 'inhale');
  assert.equal(guideAt(3.6).value, 1);
  assert.equal(guideAt(3.6).phase, 'hold');
  assert.ok(guideAt(5.8).value < 0.6 && guideAt(5.8).phase === 'exhale');
  assert.equal(guideAt(BREATH + 0.1).cycle, 1);
});

test('mortal (no spirit root) cannot start qi breathing and gets the server wording', () => {
  assert.throws(() => new BreathSession({ hasRoots: false }), e => e.code === 'NO_ROOT' && e.message === NO_ROOT_MESSAGE);
});

test('following the breath harmonises all three cycles', () => {
  const s = playBreath(new BreathSession(), t => {
    if (t < 0) return false;
    const u = t % BREATH;
    return u < 3.2 + 1.0; // hold through inhale and the pause, release to exhale
  });
  assert.equal(s.done, true);
  assert.equal(s.cycleGrades.length, 3);
  assert.equal(s.harmonised, 3);
  assert.ok(s.cycleGrades.every(g => g.score > 0.95 && g.label === '圓融'), JSON.stringify(s.cycleGrades));
});

test('holding the button the whole time does not pass', () => {
  const s = playBreath(new BreathSession(), () => true);
  assert.ok(s.harmonised <= 1, JSON.stringify(s.cycleGrades));
});

test('never pressing does not pass', () => {
  const s = playBreath(new BreathSession(), () => false);
  assert.equal(s.harmonised, 0);
});

test('breath score is independent of frame rate', () => {
  const policy = t => t >= 0 && (t % BREATH) < 4.0;
  const a = playBreath(new BreathSession(), policy, 1 / 30);
  const b = playBreath(new BreathSession(), policy, 1 / 144);
  a.cycleGrades.forEach((g, i) => assert.ok(Math.abs(g.score - b.cycleGrades[i].score) < 0.03));
});

test('block pattern is deterministic, three sides, speeds up', () => {
  const p = blockPattern(7);
  assert.deepEqual(p, blockPattern(7));
  assert.equal(p.length, 12);
  assert.deepEqual(new Set(p.map(s => s.side)), new Set(['left', 'right', 'low']));
  const gap = ph => p.filter(s => s.phrase === ph).map((s, i, a) => (i ? s.at - a[i - 1].at : null)).filter(Boolean)[0];
  assert.ok(gap(0) > gap(1) && gap(1) > gap(2));
});

test('blocking each strike on time in the right direction is perfect', () => {
  const s = new BlockSession();
  for (const strike of s.strikes) s.input(strike.side, strike.at + 0.02);
  const st = s.snapshot();
  assert.equal(st.done, true);
  assert.equal(st.perfect, 12);
  assert.equal(st.bestCombo, 12);
  assert.equal(st.grade, '身法如風');
  assert.equal(st.notice, PRACTICE_NOTICE);
});

test('wrong direction is a hit, late but in window is good, silence is a miss', () => {
  const s = new BlockSession();
  const [a, b] = s.strikes;
  const wrong = a.side === 'left' ? 'right' : 'left';
  assert.equal(s.input(wrong, a.at).judged.result, 'hit');
  assert.equal(s.input(b.side, b.at + WINDOW.good - 0.01).judged.result, 'good');
  const st = s.update(s.strikes[2].at + WINDOW.good + 0.05);
  assert.equal(st.last.result, 'hit');
  assert.equal(st.last.reason, '來不及格擋');
});

test('mashing between strikes flinches and resets combo; key repeat is ignored', () => {
  const s = new BlockSession();
  const [a] = s.strikes;
  s.input(a.side, a.at);
  assert.equal(s.snapshot().combo, 1);
  assert.equal(s.input('left', a.at + 0.5).judged.result, 'flinch');
  assert.equal(s.snapshot().combo, 0);
  assert.equal(s.input('left', a.at + 0.6, { repeat: true }).judged, null);
  assert.equal(s.snapshot().flinches, 1);
});

test('time must move forward', () => {
  const s = new BlockSession({ start: 5 });
  s.update(6);
  assert.throws(() => s.update(5.5));
  const b = new BreathSession({ start: 1 });
  assert.throws(() => b.update(Number.NaN));
});
