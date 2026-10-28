// Records parity scenarios from Johnnnny0823's tools/training-yard-demo/practice.mjs for the C# port
// (QingxiTrainingPracticeRules). QingxiTrainingPracticeSmoke replays the same inputs and must match.
//   node tools/qingxi-main-scene/training-parity.mjs
import { writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { BreathSession, BlockSession, blockPattern, BREATH_PHASES } from '../training-yard-demo/practice.mjs';

const BREATH = BREATH_PHASES.reduce((s, p) => s + p.seconds, 0);
const LEAD = 1.5;
const r6 = v => Math.round(v * 1e6) / 1e6;

// Breath: frames at a fixed step; `toggles` lists the frame indices where `held` flips, so the C#
// side rebuilds the identical held/time sequence without the policy code.
function breath(name, step, policy) {
  const s = new BreathSession();
  const toggles = [];
  let t = 0, frame = 0, held = false;
  while (!s.done && t < 60) {
    t += step; frame++;
    const want = !!policy(t - LEAD);
    if (want !== held) { toggles.push(frame); held = want; }
    s.setHeld(held);
    s.update(t);
  }
  const snap = s.snapshot();
  return { name, step, frames: frame, toggles, done: snap.done, qi: r6(snap.qi), harmonised: snap.harmonised,
    scores: snap.cycleGrades.map(g => r6(g.score)), grades: snap.cycleGrades.map(g => g.label) };
}

// Block: each input is { t, side, repeat }; updates without input are { t, side: '' }.
function block(name, seed, inputs) {
  const s = new BlockSession({ seed });
  const judged = [];
  for (const i of inputs) {
    if (i.side) judged.push(s.input(i.side, i.t, { repeat: !!i.repeat }).judged?.result ?? 'ignored');
    else s.update(i.t);
  }
  const snap = s.snapshot();
  return { name, seed, inputs: inputs.map(i => ({ t: i.t, side: i.side || '', repeat: !!i.repeat })), judged,
    done: snap.done, blocked: snap.blocked, perfect: snap.perfect, bestCombo: snap.bestCombo, flinches: snap.flinches,
    grade: snap.grade ?? '' };
}

const pattern = blockPattern(7);
const pattern3 = blockPattern(3);
const sloppy = [];
pattern.forEach((st, i) => {
  if (i % 4 === 1) sloppy.push({ t: st.at + 0.12, side: st.side });                 // late but in window
  else if (i % 4 === 2) sloppy.push({ t: st.at, side: st.side === 'left' ? 'right' : 'left' }); // wrong side
  else if (i % 4 === 3) sloppy.push({ t: st.at + 0.4, side: '' });                  // silence
  else { sloppy.push({ t: st.at - 0.5, side: 'low' }); sloppy.push({ t: st.at + 0.03, side: st.side }); sloppy.push({ t: st.at + 0.04, side: st.side, repeat: true }); }
});

const data = {
  source: 'tools/training-yard-demo/practice.mjs (Johnnnny0823)',
  patterns: [
    { seed: 7, strikes: pattern.map(s => ({ at: r6(s.at), side: s.side, phrase: s.phrase })) },
    { seed: 3, strikes: pattern3.map(s => ({ at: r6(s.at), side: s.side, phrase: s.phrase })) },
  ],
  breath: [
    breath('follow', 1 / 60, t => t >= 0 && (t % BREATH) < 4.2),
    breath('always-hold', 1 / 60, () => true),
    breath('early-release-30fps', 1 / 30, t => t >= 0 && (t % BREATH) < 3.0),
  ],
  block: [
    block('perfect', 7, pattern.map(s => ({ t: s.at + 0.02, side: s.side }))),
    block('sloppy', 7, sloppy),
  ],
};
const out = resolve('apps/game/Assets/YunJing/Data/QingxiTrainingParity.json');
writeFileSync(out, JSON.stringify(data, null, 1) + '\n');
console.log('wrote', out, data.breath.map(b => `${b.name}:${b.harmonised}`).join(' '), data.block.map(b => `${b.name}:${b.blocked}/${b.perfect}/${b.flinches}`).join(' '));
