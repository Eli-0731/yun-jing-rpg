// Alchemy rules core for the workshop demo: identify -> compound -> refine -> collect.
//
// Pure and deterministic: no clock, no Math.random. The same bag, recipe and choices always give the same
// result, so failures are explainable and repeatable (no lottery), and nothing depends on waiting online.
// The server is expected to run the same rules on its own inventory; see ../CONTRACT.md.

import { MATERIALS } from './materials-adapter.mjs';

export const PROCESS = Object.freeze({ slice: '切段', grind: '研碎', soak: '浸泡' });
export const FIRE = Object.freeze({ gentle: '文火', medium: '中火', strong: '武火' });
export const COLLECT = Object.freeze({ filter: '濾渣後裝瓶', direct: '直接裝瓶' });

// Per-material processing effect on { potency, stability }. `invalid` blocks the step with a reason.
const PROCESS_FX = {
  'qinglan-stem': { slice: [6, 4], grind: [2, -6], soak: [0, 8] },
  'chilu-berry': { slice: [-4, 0], grind: [6, -4], soak: [2, 6] },
  'yumai-crystal': { slice: { invalid: '玉脈晶質硬，刀切不動，只能研碎' }, grind: [4, 6], soak: [0, 0] },
};

export const RECIPES = Object.freeze({
  'body-bath': {
    id: 'body-bath', label: '淬體藥浴', kind: 'known', serverRecipe: 'body-bath', output: 'body-bath', quantity: 1,
    slots: [
      { role: 'main', label: '主藥', element: '木', nature: '溫', qty: 1, weight: 0.6 },
      { role: 'aux', label: '輔藥', element: '火', nature: '溫', qty: 2, weight: 0.4 },
    ],
    fire: { gentle: [-4, 8], medium: [4, 2], strong: [8, -10] },
    collect: { filter: [-2, 8], direct: [0, -4] },
    summary: '已知配方：木溫主藥配火溫輔藥。火候與處理只影響藥效與穩定度，材料正確必定成功。',
  },
  'body-bath:breath': {
    id: 'body-bath:breath', label: '調息清露（研究變體）', kind: 'research', serverRecipe: null, output: 'breath-dew', quantity: 1,
    slots: [
      { role: 'main', label: '主藥', element: '火', nature: '溫', qty: 3, weight: 0.65 },
      { role: 'aux', label: '佐藥', element: '金', nature: '寒', qty: 1, weight: 0.35 },
    ],
    fire: { gentle: [6, 6], medium: [0, -6], strong: { fail: 'fire', reason: '武火讓赤露參漿汁焦化，寒性的玉脈晶粉壓不住火氣，爐底結焦' } },
    collect: { filter: [-2, 8], direct: [0, -15] },
    minStability: 55,
    summary: '研究變體：以寒佐溫，求一份能平穩調息的清露。可能失敗，失敗會說明原因並退回部分材料。',
  },
});

export const GRADE = s => (s >= 75 ? '上品' : s >= 60 ? '中品' : '下品');

const clamp = v => Math.max(0, Math.min(100, Math.round(v)));
const fx = v => (Array.isArray(v) ? v : [0, 0]);

export function newState(bag) {
  return { bag: bag.map(b => ({ ...b })), identified: [], notes: [], products: [], claims: {}, claimedBrews: [], seq: 0 };
}

// Step 1 (B05 cabinet): reveal a batch's attributes. Unidentified batches cannot be compounded.
export function identify(state, batchId) {
  const b = state.bag.find(x => x.batchId === batchId);
  if (!b) return { ok: false, code: 'NO_BATCH', message: '背包裡沒有這批材料' };
  if (!state.identified.includes(batchId)) state.identified.push(batchId);
  const m = MATERIALS[b.material];
  return { ok: true, batch: b, material: m, text: `${m.name}：${m.element}屬、性${m.nature}，純度 ${b.purity}，穩定 ${b.stability}。${m.note}` };
}

// Step 2 (B11 recipe stand): check the chosen batches against the recipe slots; specific feedback per slot.
export function checkCompound(state, recipeId, picks) {
  const r = RECIPES[recipeId];
  if (!r) return [{ slot: null, code: 'NO_RECIPE', message: '沒有這個配方' }];
  const problems = [];
  for (const slot of r.slots) {
    const b = state.bag.find(x => x.batchId === picks[slot.role]);
    if (!b) { problems.push({ slot: slot.role, code: 'EMPTY', message: `${slot.label}還沒放材料（需要${slot.element}屬、${slot.nature}性 ×${slot.qty}）` }); continue; }
    const m = MATERIALS[b.material];
    if (!state.identified.includes(b.batchId)) { problems.push({ slot: slot.role, code: 'UNIDENTIFIED', message: `${m.name}還沒辨材，先到藥櫃看清屬性` }); continue; }
    const wrong = [];
    if (m.element !== slot.element) wrong.push(`${m.element}屬（要${slot.element}屬）`);
    if (m.nature !== slot.nature) wrong.push(`性${m.nature}（要${slot.nature}性）`);
    if (wrong.length) problems.push({ slot: slot.role, code: 'WRONG_MATERIAL', message: `${slot.label}放錯：${m.name}是${wrong.join('、')}。${r.label}的${slot.label}需要${slot.element}屬、${slot.nature}性的材料` });
    else if (b.qty < slot.qty) problems.push({ slot: slot.role, code: 'NOT_ENOUGH', message: `${m.name}只剩 ${b.qty}，${slot.label}需要 ${slot.qty}` });
  }
  return problems;
}

// Live preview of potency / stability for the choices made so far (shown before committing).
// For the research variant, failure warnings appear only once a research note has recorded them.
export function preview(state, plan) {
  const r = RECIPES[plan.recipe];
  let pot = 0, stab = 0;
  const warnings = [];
  for (const slot of r.slots) {
    const b = state.bag.find(x => x.batchId === plan.picks?.[slot.role]);
    if (!b) continue;
    pot += b.purity * slot.weight; stab += b.stability * slot.weight;
    const p = plan.process?.[slot.role];
    if (p) {
      const e = PROCESS_FX[b.material][p];
      if (e && !Array.isArray(e)) warnings.push(e.invalid);
      else { pot += fx(e)[0]; stab += fx(e)[1]; }
    }
  }
  if (plan.fire) {
    const f = r.fire[plan.fire];
    if (!Array.isArray(f)) { if (state.notes.some(n => n.recipe === r.id && n.code === f.fail)) warnings.push(f.reason); }
    else { pot += f[0]; stab += f[1]; }
  }
  if (plan.collect) { const c = r.collect[plan.collect]; pot += c[0]; stab += c[1]; }
  for (const n of state.notes.filter(n => n.recipe === r.id && !warnings.includes(n.reason))) warnings.push(`研究筆記：${n.reason}`);
  return { potency: clamp(pot), stability: clamp(stab), grade: GRADE(clamp(stab)), warnings };
}

function take(state, batchId, qty) { const b = state.bag.find(x => x.batchId === batchId); b.qty -= qty; return b; }
function giveBack(state, batchId, qty) { if (qty > 0) state.bag.find(x => x.batchId === batchId).qty += qty; }

// Steps 3-5 (B03 mortar / B01 furnace / B09 filter): run the whole brew. Consumes materials, returns a result.
// Known recipe: always succeeds when the compound check passes. Research variant: may fail with a reason and
// a partial return decided by the stage that failed.
export function brew(state, plan) {
  const r = RECIPES[plan.recipe];
  const problems = checkCompound(state, plan.recipe, plan.picks);
  if (problems.length) return { ok: false, code: 'COMPOUND', problems };
  for (const k of ['fire', 'collect']) if (!plan[k]) return { ok: false, code: 'INCOMPLETE', problems: [{ code: 'INCOMPLETE', message: `還沒選${k === 'fire' ? '火候' : '收取方式'}` }] };
  for (const slot of r.slots) if (!plan.process?.[slot.role]) return { ok: false, code: 'INCOMPLETE', problems: [{ code: 'INCOMPLETE', message: `${slot.label}還沒處理（切段／研碎／浸泡）` }] };
  const pv = preview({ ...state, notes: [] }, plan);
  const used = r.slots.map(s => ({ slot: s.role, batch: take(state, plan.picks[s.role], s.qty), qty: s.qty }));
  const bound = used.some(u => u.batch.bound);
  state.seq += 1;
  const brewId = `brew-${state.seq}-${r.id}`;
  const base = { brewId, recipe: r.id, label: r.label, consumed: used.map(u => ({ batchId: u.batch.batchId, material: u.batch.material, qty: u.qty })), choices: { process: plan.process, fire: plan.fire, collect: plan.collect } };
  const fail = (stage, reason, back) => {
    for (const [role, qty] of Object.entries(back)) giveBack(state, plan.picks[role], qty);
    const returned = Object.entries(back).filter(([, q]) => q > 0).map(([role, qty]) => ({ batchId: plan.picks[role], material: state.bag.find(x => x.batchId === plan.picks[role]).material, qty }));
    const note = { recipe: r.id, code: stage, reason };
    if (!state.notes.some(n => n.recipe === r.id && n.reason === reason)) state.notes.push(note);
    return { ok: true, success: false, ...base, stage, reason, returned, potency: pv.potency, stability: pv.stability };
  };
  // processing that cannot work stops at the mortar: nothing has been cooked yet, only one portion is spoiled
  for (const slot of r.slots) {
    const e = PROCESS_FX[used.find(u => u.slot === slot.role).batch.material][plan.process[slot.role]];
    if (e && !Array.isArray(e)) {
      const back = Object.fromEntries(r.slots.map(s => [s.role, s.role === slot.role ? s.qty : Math.max(0, s.qty - 1)]));
      return fail('process', `${e.invalid}；${slot.label}沒處理好就停手，損耗一份${slot.role === 'main' ? '主藥' : '材料'}`, back);
    }
  }
  if (r.kind === 'research') {
    if (plan.process.aux !== 'grind') return fail('process', '玉脈晶沒研成粉就下爐，溶不進藥液，沉在爐底', { main: 1, aux: 1 });
    const f = r.fire[plan.fire];
    if (!Array.isArray(f)) return fail('fire', f.reason, { main: 1, aux: 1 });   // crystal recovered from the residue in the filter
    if (pv.stability < r.minStability) return fail('collect', `穩定度 ${pv.stability} 低於 ${r.minStability}，藥液分層，只能從濾布上刮回少許赤露參`, { main: 1, aux: 0 });
  }
  const product = { item: r.output, label: r.label, quantity: r.quantity, potency: pv.potency, stability: pv.stability, grade: GRADE(pv.stability), bound };
  return { ok: true, success: true, ...base, product, returned: [] };
}

// Local demo claim. Idempotent by requestId: repeating a request returns the stored receipt and adds nothing;
// a second request id for an already-claimed brew is refused. This is NOT an official grant; see CONTRACT.md.
export function claimLocal(state, result, requestId) {
  if (typeof requestId !== 'string' || !requestId) return { ok: false, code: 'NO_REQUEST_ID', message: '缺少請求編號' };
  const prev = state.claims[requestId];
  if (prev) {
    if (prev.brewId !== result?.brewId) return { ok: false, code: 'IDEMPOTENCY_CONFLICT', message: '相同請求編號不能用於不同成品' };
    return { ...prev, replayed: true };
  }
  if (!result?.success) return { ok: false, code: 'NOTHING_TO_CLAIM', message: '這爐沒有成品可領' };
  if (state.claimedBrews.includes(result.brewId)) return { ok: false, code: 'ALREADY_CLAIMED', message: '這爐成品已領過' };
  const receipt = { ok: true, demo: true, requestId, brewId: result.brewId, granted: { ...result.product }, replayed: false };
  state.claims[requestId] = receipt; state.claimedBrews.push(result.brewId); state.products.push({ ...result.product, brewId: result.brewId, official: false });
  return receipt;
}
