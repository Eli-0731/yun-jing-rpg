// Export reference results of the JS rules core for a fixed list of scenarios -> data/scenarios.json.
// The Unity port (unity/Assets/QingxiWaterworksB/Runtime/WaterworksRules.cs) is checked against this file.
//   node tools/qingxi-waterworks-b/scripts/export-scenarios.mjs
import { readFileSync, writeFileSync } from 'node:fs';
import * as core from '../src/waterworks-core.mjs';

const j = p => JSON.parse(readFileSync(new URL(p, import.meta.url), 'utf8'));
const board = j('../data/board.json'), catalog = j('../data/catalog.json'), fixture = j('../data/fixture-observations.json');
const ctx = { board, catalog };
const ex = c => core.exampleActions(board, c).slice(1, -1);
const P = (slot, piece) => ({ type: 'place', slot, piece });
const SCEN = [
  { name: 'direct_restore', obs: 'full', steps: [...ex('restore_channel'), { type: 'choose', choice: 'restore_channel' }], complete: 2 },
  { name: 'direct_protect_refused', obs: 'full', steps: [...ex('restore_channel'), { type: 'choose', choice: 'protect_nursery' }], complete: 1 },
  { name: 'bypass_protect', obs: 'full', steps: [...ex('protect_nursery'), { type: 'choose', choice: 'protect_nursery' }], complete: 1 },
  { name: 'bypass_restore_refused', obs: 'full', steps: [...ex('protect_nursery'), { type: 'choose', choice: 'restore_channel' }], complete: 1 },
  { name: 'desilt_then_direct', obs: 'full', steps: [...ex('clear_silt'), { type: 'choose', choice: 'clear_silt' }, { type: 'complete' }, { type: 'clear' }, ...ex('restore_channel'), { type: 'choose', choice: 'restore_channel' }], complete: 1 },
  { name: 'direct_gate_closed', obs: 'full', steps: [...ex('restore_channel'), { type: 'gate', slot: 'P2', open: false }, { type: 'choose', choice: 'restore_channel' }], complete: 1 },
  { name: 'direct_mud_refused', obs: 'full', steps: [...ex('restore_channel'), { type: 'choose', choice: 'clear_silt' }], complete: 1 },
  { name: 'wrong_tee', obs: 'full', steps: [P('P2', 'B04'), P('L1', 'B02'), P('L2', 'B02-V05'), P('R1', 'B05')], complete: 1 },
  { name: 'wrong_bend', obs: 'full', steps: [P('P2', 'B05'), { type: 'gate', slot: 'P2', open: true }, P('P3', 'B03')], complete: 0 },
  { name: 'dead_end', obs: 'full', steps: [P('P2', 'B03')], complete: 0 },
  { name: 'overlap', obs: 'full', steps: [P('P2', 'B04-V02'), P('P3', 'B02')], complete: 0 },
  { name: 'gap', obs: 'full', steps: [P('P2', 'B05'), P('P5', 'B02'), { type: 'gate', slot: 'P2', open: true }], complete: 0 },
  { name: 'gate_spill', obs: 'full', steps: [...ex('clear_silt'), { type: 'gate', slot: 'R1', open: true }], complete: 0 },
  { name: 'wrong_patch', obs: 'full', steps: [...ex('restore_channel').filter(a => a.type !== 'patch'), { type: 'patch', slot: 'P4', piece: 'B07-V03' }, { type: 'choose', choice: 'restore_channel' }], complete: 1 },
  { name: 'no_clues_direct', obs: 'none', steps: [...ex('restore_channel'), { type: 'choose', choice: 'restore_channel' }], complete: 1 },
  { name: 'partial_direct_unpatched', obs: 'partial', steps: [...ex('restore_channel').filter(a => a.type !== 'patch'), { type: 'choose', choice: 'restore_channel' }], complete: 1 },
  { name: 'undo_redo', obs: 'full', steps: [P('P2', 'B05'), P('P3', 'B02'), { type: 'undo' }, { type: 'undo' }, { type: 'redo' }, P('P3', 'B02-V04')], complete: 0 },
  { name: 'refusals', obs: 'full', steps: [{ type: 'remove', slot: 'P1' }, P('P4', 'B02'), P('P2', 'B05'), P('L4', 'B05'), P('R1', 'B05'), { type: 'patch', slot: 'P2', piece: 'B07' }], complete: 0 },
];
const round = v => Math.round(v * 1e4) / 1e4;
const out = [];
for (const sc of SCEN) {
  let s = core.newSession(board, catalog, fixture.sets[sc.obs].observationIds);
  const refusals = [];
  for (const a of sc.steps) {
    if (a.type === 'undo') { s = core.undo(s).session; continue; }
    if (a.type === 'redo') { s = core.redo(s).session; continue; }
    if (a.type === 'complete') { s = core.complete(ctx, s, core.requestIdFor(s)).session; continue; }
    const r = core.act(ctx, s, a);
    if (!r.ok) refusals.push({ code: r.code, message: r.message });
    s = r.session;
  }
  const pv = core.preview(ctx, s), ev = pv.ev;
  const res = {
    name: sc.name, obs: sc.obs, steps: sc.steps, refusals,
    design: s.design,
    wet: ev.wet, flow: Object.fromEntries(Object.entries(ev.flow).map(([k, v]) => [k, round(v)])),
    metrics: ev.metrics,
    issues: ev.issues.map(i => ({ code: i.code, slot: i.slot, port: i.port ?? null, blocking: i.blocking, message: i.message, fix: i.fix })),
    unknowns: ev.unknowns.map(u => u.id),
    problems: pv.problems.map(p => ({ code: p.code, message: p.message })),
    cost: pv.cost, ready: pv.ready, requestId: core.requestIdFor(s),
    completes: [],
  };
  for (let k = 0; k < sc.complete; k++) {
    const c = core.complete(ctx, s, core.requestIdFor(s));
    res.completes.push({ ok: c.ok, code: c.code ?? null, replayed: c.replayed ?? null, outcome: c.outcome ?? null, consumed: c.consumed ?? null, stock: c.session.ledger.stock, completed: c.session.ledger.completed.length });
    s = c.session;
  }
  out.push(res);
}
writeFileSync(new URL('../data/scenarios.json', import.meta.url), JSON.stringify({ note: 'JS 規則核心的參考結果；Unity C# 版逐案比對。由 scripts/export-scenarios.mjs 產生。', scenarios: out }, null, 1) + '\n');
console.log(`wrote ${out.length} scenarios`);
