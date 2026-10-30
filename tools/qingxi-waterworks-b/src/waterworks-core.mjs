// Waterworks rules core for the old-channel repair demo: place pieces by port -> pick a direction -> complete.
//
// Pure and deterministic: no clock, no Math.random, no DOM. The same board, layout, observations and choice
// always give the same evaluation, so a broken joint is explainable and repeatable. Rendering (main.js) only
// reads evaluate(); the server is expected to run the same rules on its own ledger, see ../CONTRACT.md.
//
// Coordinates are the Blender plan of the kit (metres, x east, y north = downstream). A slot is an entry pose:
// the piece placed there has its `in` port on slot.pos, rotated so local +Y (the kit's flow axis) points along
// slot.dir. Footprint cells are the kit's 0.25 m grid cells, so overlaps are checked exactly.

export const CHOICES = Object.freeze({
  clear_silt: { label: '先清淤', short: '清淤', outcomeId: 'wwb.clear_silt.diverted' },
  restore_channel: { label: '修回舊渠', short: '修舊渠', outcomeId: 'wwb.restore_channel.direct' },
  protect_nursery: { label: '保護育幼區', short: '護育幼', outcomeId: 'wwb.protect_nursery.bypass' },
});
export const KIND_LABEL = Object.freeze({ straight: '直槽', discharge: '放流坡', bend: '彎槽', tee: '三通', gate: '閘板', patch: '補石' });
const EPS = 1e-6;
const DIR_NAME = { '0,1': '北', '0,-1': '南', '1,0': '東', '-1,0': '西' };
export const dirName = d => DIR_NAME[`${Math.round(d[0])},${Math.round(d[1])}`] ?? '?';
const fmt = v => (Math.abs(v) < EPS ? 0 : Math.round(v * 100) / 100);
export const fmtPos = p => `(${fmt(p[0])}, ${fmt(p[1])})`;
const same = (a, b) => Math.abs(a[0] - b[0]) < 0.01 && Math.abs(a[1] - b[1]) < 0.01;

// rotation that maps local +Y onto d (d is a unit axis vector)
const rot = d => ({ c: d[1], s: -d[0] });
const apply = (r, v) => [r.c * v[0] - r.s * v[1], r.s * v[0] + r.c * v[1]];
export const yawOf = d => Math.atan2(-d[0], d[1]);   // radians, counter-clockwise from +Y

// ---------------------------------------------------------------- placement geometry
export function placePiece(piece, slot) {
  const r = rot(slot.dir);
  const ports = piece.ports.map(p => {
    const w = apply(r, p.pos);
    return { ...p, pos: [slot.pos[0] + w[0], slot.pos[1] + w[1]], dir: apply(r, p.dir) };
  });
  const cells = piece.cells.map(([cx, cy]) => {
    const w = apply(r, [(cx + 0.5) * 0.25, (cy + 0.5) * 0.25]);
    return `${Math.floor((slot.pos[0] + w[0]) / 0.25 + EPS)},${Math.floor((slot.pos[1] + w[1]) / 0.25 + EPS)}`;
  });
  return { ports, cells, yaw: yawOf(slot.dir) };
}

function rectGap(cellKeys, rect) {
  let best = Infinity;
  for (const k of cellKeys) {
    const [cx, cy] = k.split(',').map(Number);
    const x0 = cx * 0.25, y0 = cy * 0.25, x1 = x0 + 0.25, y1 = y0 + 0.25;
    const dx = Math.max(rect[0] - x1, x0 - rect[2], 0), dy = Math.max(rect[1] - y1, y0 - rect[3], 0);
    best = Math.min(best, Math.hypot(dx, dy));
  }
  return best;
}
const inRect = (p, r) => p[0] >= r[0] - EPS && p[0] <= r[2] + EPS && p[1] >= r[1] - EPS && p[1] <= r[3] + EPS;

// ---------------------------------------------------------------- design (undoable) and session
export function newDesign() {
  return { placed: {}, patches: {}, gates: {}, choice: null };
}

export function newSession(board, catalog, observationIds = []) {
  return {
    design: newDesign(), past: [], future: [],
    obs: [...observationIds],
    ledger: { stock: { ...board.materialStock }, receipts: {}, completed: [], contribution: 0, siltCleared: false, seq: 0 },
  };
}

const cloneDesign = d => ({ placed: { ...d.placed }, patches: { ...d.patches }, gates: { ...d.gates }, choice: d.choice });
const used = (design, id) => Object.values(design.placed).filter(p => p === id).length + Object.values(design.patches).filter(p => p === id).length;

// Validate one edit against the board and stock. Returns { ok, design } or { ok: false, code, message }.
export function edit(ctx, design, action) {
  const { board, catalog } = ctx;
  const slot = action.slot && board.slots.find(s => s.id === action.slot);
  if (action.slot && !slot) return { ok: false, code: 'NO_SLOT', message: `沒有 ${action.slot} 這個槽位` };
  const d = cloneDesign(design);
  switch (action.type) {
    case 'place': {
      const piece = catalog.pieces[action.piece];
      if (!piece || piece.kind === 'patch') return { ok: false, code: 'NOT_A_TROUGH', message: `${action.piece} 不是可放進槽位的段件` };
      if (slot.fixed) return { ok: false, code: 'FIXED_SLOT', message: `${slot.id} 是舊渠原有的石槽，不能拆換${slot.id === board.truth.crack.slot ? '；可以用補石修' : ''}` };
      const left = (board.pieceStock[piece.id] ?? 0) - used(design, piece.id) + (design.placed[slot.id] === piece.id ? 1 : 0);
      if (left <= 0) return { ok: false, code: 'NO_PIECE', message: `${piece.id} ${piece.name}已經用完（材料車上共 ${board.pieceStock[piece.id] ?? 0} 件）；先拆下別處的同款或換一款` };
      d.placed[slot.id] = piece.id;
      if (piece.kind === 'gate' && d.gates[slot.id] === undefined) d.gates[slot.id] = false;
      if (piece.kind !== 'gate') delete d.gates[slot.id];
      return { ok: true, design: d };
    }
    case 'remove': {
      if (slot.fixed) return { ok: false, code: 'FIXED_SLOT', message: `${slot.id} 是舊渠原有的石槽，不能拆` };
      if (!d.placed[slot.id]) return { ok: false, code: 'EMPTY_SLOT', message: `${slot.id} 本來就是空的` };
      delete d.placed[slot.id]; delete d.gates[slot.id];
      return { ok: true, design: d };
    }
    case 'patch': {
      const piece = catalog.pieces[action.piece];
      if (!piece || piece.kind !== 'patch') return { ok: false, code: 'NOT_A_PATCH', message: `${action.piece} 不是補石` };
      if (!slot.old) return { ok: false, code: 'NOT_OLD', message: `${slot.id} 是新放的段件，不需要補石；補石用在舊槽（${board.slots.filter(s => s.old).map(s => s.id).join('、')}）` };
      const left = (board.pieceStock[piece.id] ?? 0) - used(design, piece.id) + (design.patches[slot.id] === piece.id ? 1 : 0);
      if (left <= 0) return { ok: false, code: 'NO_PIECE', message: `${piece.id} ${piece.name}已經用完` };
      d.patches[slot.id] = piece.id;
      return { ok: true, design: d };
    }
    case 'unpatch': {
      if (!d.patches[slot.id]) return { ok: false, code: 'EMPTY_SLOT', message: `${slot.id} 沒有補石` };
      delete d.patches[slot.id];
      return { ok: true, design: d };
    }
    case 'gate': {
      const id = d.placed[slot.id];
      if (!id || catalog.pieces[id].kind !== 'gate') return { ok: false, code: 'NO_GATE', message: `${slot.id} 沒有閘板` };
      d.gates[slot.id] = action.open ?? !d.gates[slot.id];
      return { ok: true, design: d };
    }
    case 'choose': {
      if (action.choice !== null && !CHOICES[action.choice]) return { ok: false, code: 'NO_CHOICE', message: `沒有 ${action.choice} 這個處理方向` };
      d.choice = action.choice;
      return { ok: true, design: d };
    }
    case 'clear': return { ok: true, design: newDesign() };
    default: return { ok: false, code: 'NO_ACTION', message: `不認得的操作 ${action.type}` };
  }
}

// Session wrapper with undo / redo. Completing does not touch the undo history (the ledger is never undone).
export function act(ctx, session, action) {
  const r = edit(ctx, session.design, action);
  if (!r.ok) return { ...r, session };
  return { ok: true, session: { ...session, design: r.design, past: [...session.past, session.design], future: [] } };
}
export function undo(session) {
  if (!session.past.length) return { ok: false, code: 'NOTHING_TO_UNDO', message: '沒有可以撤回的步驟', session };
  return { ok: true, session: { ...session, design: session.past.at(-1), past: session.past.slice(0, -1), future: [session.design, ...session.future] } };
}
export function redo(session) {
  if (!session.future.length) return { ok: false, code: 'NOTHING_TO_REDO', message: '沒有可以重做的步驟', session };
  return { ok: true, session: { ...session, design: session.future[0], past: [...session.past, session.design], future: session.future.slice(1) } };
}

// ---------------------------------------------------------------- evaluation
// Which pieces fit this slot so that every outlet lands on a slot entry that can continue (not a dead end),
// on a terminal, or (for a discharge ramp) in the drain? Used for "how to fix" suggestions.
function outsLand(ctx, piece, slot, deep) {
  const { board } = ctx;
  const g = placePiece(piece, slot);
  const outs = g.ports.filter(p => p.kind !== 'in');
  return outs.length > 0 && outs.every(p => {
    if (p.kind === 'discharge') return inRect(p.pos, board.zones.drain.rect);
    if (board.terminals.some(t => same(t.pos, p.pos) && same(t.dir, p.dir))) return true;
    const next = board.slots.find(x => x.id !== slot.id && same(x.pos, p.pos) && same(x.dir, p.dir));
    return !!next && (!deep || piece.kind === 'tee' || !deadEnd(ctx, next));   // a tee may hold one branch with a closed gate
  });
}
// dead end: nothing but a closed gate can sit here (water cannot continue)
export const deadEnd = (ctx, slot) => !Object.values(ctx.catalog.pieces).some(p => p.kind !== 'patch' && p.kind !== 'gate' && outsLand(ctx, p, slot, false));
export function fitsFor(ctx, slot, { kind, exclude } = {}) {
  const all = Object.values(ctx.catalog.pieces).filter(p => p.kind !== 'patch' && p.id !== exclude && (ctx.board.pieceStock[p.id] ?? 0) > 0 && outsLand(ctx, p, slot, true));
  const sameKind = all.filter(p => p.kind === kind);
  return (sameKind.length ? sameKind : all).map(p => p.id);
}

const pieceLabel = (catalog, id) => `${id} ${catalog.pieces[id].name}`;

// Full evaluation of a design: connections, broken ports, overlaps, water flow, supply and impact.
// `known` controls what the preview may reveal; `truth: true` evaluates with the board's hidden facts.
export function evaluate(ctx, design, { obs = [], siltCleared = false, truth = false } = {}) {
  const { board, catalog } = ctx;
  const T = board.truth;
  const knows = id => truth || obs.includes(id);
  const inst = {};
  for (const slot of board.slots) {
    const id = slot.fixed ?? design.placed[slot.id];
    if (!id) continue;
    inst[slot.id] = { slot, id, piece: catalog.pieces[id], ...placePiece(catalog.pieces[id], slot), gateOpen: !!design.gates[slot.id] };
  }
  const issues = [], unknowns = [];

  // connection graph from the source
  const entryAt = (pos, dir) => board.slots.find(s => same(s.pos, pos) && same(s.dir, dir));
  const terminalAt = (pos, dir) => board.terminals.find(t => same(t.pos, pos) && same(t.dir, dir));
  const edges = {};   // slotId -> [{ port, to: slotId | terminal id | 'drain' | null }]
  const reached = new Set();
  const visit = (slotId, from) => {
    if (reached.has(slotId)) return;
    reached.add(slotId);
    const s = inst[slotId];
    edges[slotId] = [];
    for (const p of s.ports) {
      if (p.kind === 'in') continue;
      if (p.kind === 'discharge') {
        const ok = inRect(p.pos, board.zones.drain.rect);
        edges[slotId].push({ port: p, to: ok ? 'drain' : null, bad: !ok });
        continue;
      }
      const term = terminalAt(p.pos, p.dir);
      if (term) { edges[slotId].push({ port: p, to: term.id }); continue; }
      const next = entryAt(p.pos, p.dir);
      if (next && inst[next.id]) { edges[slotId].push({ port: p, to: next.id }); visit(next.id, slotId); continue; }
      edges[slotId].push({ port: p, to: null, emptySlot: next?.id });
    }
  };
  const first = entryAt(board.source.pos, board.source.dir);
  visit(first.id, 'source');

  // overlaps
  const owner = {};
  for (const s of Object.values(inst)) for (const c of s.cells) (owner[c] ??= []).push(s.slot.id);
  const pairs = new Set();
  for (const ids of Object.values(owner)) if (ids.length > 1) pairs.add([...new Set(ids)].sort().join('|'));
  for (const p of pairs) {
    const [a, b] = p.split('|');
    const movable = inst[a].slot.fixed ? b : inst[b].slot.fixed ? a : !reached.has(b) ? b : !reached.has(a) ? a : b;
    issues.push({ code: 'OVERLAP', slot: movable, blocking: true,
      message: `${a} 的 ${pieceLabel(catalog, inst[a].id)}和 ${b} 的 ${pieceLabel(catalog, inst[b].id)}疊在一起`,
      fix: `拆掉 ${movable}；${a} 和 ${b} 不能同時放（${inst[a].piece.kind === 'tee' || inst[b].piece.kind === 'tee' ? '三通的分流缽會佔到下一格' : '形體會互相穿插'}）` });
  }

  // flow: a branch carries flow if it ends in a sink (field, drain) or spills. Closed gates hold water still.
  const carries = {};
  const branch = slotId => {
    if (carries[slotId] !== undefined) return carries[slotId];
    carries[slotId] = false;   // cycle guard
    const s = inst[slotId];
    if (s.piece.kind === 'gate' && !s.gateOpen) return (carries[slotId] = false);
    let any = false;
    for (const e of edges[slotId]) any = (e.to === null || e.to === 'drain' || e.to === 'field' || branch(e.to)) || any;
    return (carries[slotId] = any);
  };
  branch(first.id);

  const flow = {}, wet = {};
  let fieldFlow = 0, drainFlow = 0, spillFlow = 0;
  const silted = slotId => slotId === T.silt.slot && !siltCleared;
  const crackLeak = slotId => slotId === T.crack.slot && catalog.pieces[design.patches[slotId]]?.crack !== T.crack.type;
  const push = (slotId, q) => {
    const s = inst[slotId];
    wet[slotId] = q > EPS ? 'flow' : 'still';
    flow[slotId] = (flow[slotId] ?? 0) + q;
    let out = q * (s.piece.eff ?? 1);
    if (silted(slotId) && knows(T.silt.observation)) out *= T.silt.factor;
    if (crackLeak(slotId) && knows(T.crack.observation)) out *= T.crack.factor;
    if (s.piece.kind === 'gate' && !s.gateOpen) { wet[slotId] = 'still'; return; }
    const live = edges[slotId].filter(e => e.to === null || e.to === 'drain' || e.to === 'field' || branch(e.to));
    for (const e of edges[slotId]) {
      const share = live.includes(e) ? out / live.length : 0;
      if (e.to === 'field') fieldFlow += share;
      else if (e.to === 'drain') drainFlow += share;
      else if (e.to === null) spillFlow += share;
      else if (share > EPS) push(e.to, share);
      else still(e.to);
    }
  };
  const still = slotId => {
    if (wet[slotId]) return;
    wet[slotId] = 'still'; flow[slotId] = 0;
    if (inst[slotId].piece.kind === 'gate' && !inst[slotId].gateOpen) return;   // water stops at a closed gate
    for (const e of edges[slotId]) if (e.to && inst[e.to]) still(e.to);
  };
  push(first.id, 1);

  // broken / open ports, named
  for (const [slotId, list] of Object.entries(edges)) {
    const s = inst[slotId];
    for (const e of list) {
      if (e.to !== null) continue;
      const where = `${slotId} 的 ${pieceLabel(catalog, s.id)}「${e.port.name}」接口`;
      const flowing = (flow[slotId] ?? 0) > EPS;
      if (e.bad) {
        issues.push({ code: 'BAD_DISCHARGE', slot: slotId, port: e.port.name, blocking: flowing,
          message: `${where}把水倒在 ${fmtPos(e.port.pos)}，那裡不是回流溝`,
          fix: `放流坡只能接在 L2，讓水倒回西邊的回流溝；這一格請改放直槽或彎槽` });
      } else if (e.emptySlot) {
        const nextSlot = board.slots.find(x => x.id === e.emptySlot);
        const dead = deadEnd(ctx, nextSlot);
        const fits = dead ? [] : fitsFor(ctx, nextSlot);
        const alt = s.slot.fixed ? [] : fitsFor(ctx, s.slot, { exclude: s.id });
        issues.push({ code: 'EMPTY_NEXT', slot: slotId, port: e.port.name, next: e.emptySlot, blocking: flowing, deadEnd: dead,
          message: `${where}朝${dirName(e.port.dir)}接到 ${e.emptySlot}，但 ${e.emptySlot} 還空著${dead ? `；${e.emptySlot} 再往前沒有槽位，只能放關著的閘板擋水` : ''}${flowing ? '，水會從這裡漫出' : ''}`,
          fix: dead && s.piece.kind === 'tee'
            ? `在 ${e.emptySlot} 放一座 B05 閘板並保持關閉，把這一側的水擋住`
            : dead
            ? `把 ${slotId} 換成不往 ${e.emptySlot} 出水的段件${alt.length ? `（例如 ${alt.slice(0, 4).join('、')}）` : ''}`
            : `在 ${e.emptySlot} 放一段能接下去的段件${fits.length ? `（例如 ${fits.slice(0, 4).join('、')}）` : ''}` });
      } else {
        const near = board.slots.filter(x => !inst[x.id] || x.id !== slotId)
          .map(x => ({ x, d: Math.hypot(x.pos[0] - e.port.pos[0], x.pos[1] - e.port.pos[1]) })).sort((a, b) => a.d - b.d)[0];
        const fits = fitsFor(ctx, s.slot, { kind: s.piece.kind, exclude: s.id });
        if (s.piece.kind === 'gate' && !s.gateOpen && !flowing) {
          issues.push({ code: 'GATE_END', slot: slotId, port: e.port.name, blocking: false,
            message: `${slotId} 閘板外側（${dirName(e.port.dir)}）還沒接槽；閘板關著，水擋在這裡不會漏`,
            fix: `要送水時先在外側接好段件再開閘；只當擋水閘用就保持關閉` });
          continue;
        }
        const hint = near && near.d < 0.6
          ? `最近的槽位 ${near.x.id} 入口在 ${fmtPos(near.x.pos)} 朝${dirName(near.x.dir)}，差 ${Math.round(near.d * 100)} cm`
          : '這個方向沒有槽位';
        issues.push({ code: 'OPEN_PORT', slot: slotId, port: e.port.name, blocking: flowing || s.piece.kind !== 'gate',
          message: `${where}落在 ${fmtPos(e.port.pos)} 朝${dirName(e.port.dir)}，沒有接上任何槽位（${hint}）${flowing ? '，水會從這裡漫出' : ''}`,
          fix: s.slot.fixed ? `${slotId} 是舊槽，請調整下游段件` : (fits.length ? `把 ${slotId} 換成 ${fits.join('、')}，接口才會對上` : `拆掉 ${slotId}，換一款出水口對得上的段件`) });
      }
    }
  }
  // placed pieces the water cannot reach
  for (const slotId of Object.keys(design.placed)) {
    if (reached.has(slotId)) continue;
    const s = inst[slotId];
    const feeders = Object.values(inst).filter(o => o.slot.id !== slotId && o.ports.some(p => p.kind === 'out' && same(p.pos, s.slot.pos) && same(p.dir, s.slot.dir)));
    const why = feeders.length ? `上游 ${feeders.map(f => f.slot.id).join('、')} 也還沒接上水路` : '上游沒有段件的出水口通到這裡';
    issues.push({ code: 'NOT_CONNECTED', slot: slotId, blocking: true,
      message: `${slotId} 的 ${pieceLabel(catalog, s.id)}沒接上水路：${why}`,
      fix: `拆掉 ${slotId}，或在上游放能通到 ${slotId} 入口 ${fmtPos(s.slot.pos)} 的段件` });
  }
  for (const [slotId, pid] of Object.entries(design.patches)) {
    if (catalog.pieces[pid].crack === T.crack.type && slotId === T.crack.slot) continue;
    if (slotId !== T.crack.slot) {
      issues.push({ code: 'PATCH_UNNEEDED', slot: slotId, blocking: false, message: `${slotId} 沒有${knows(T.crack.observation) ? '' : '已知的'}裂口，補石用不上`, fix: `撤回 ${slotId} 的補石` });
    } else if (knows(T.crack.observation)) {
      issues.push({ code: 'PATCH_WRONG', slot: slotId, blocking: false,
        message: `${pieceLabel(catalog, pid)}貼不上 ${slotId} 的裂口：這道是槽壁外側的直裂縫`, fix: '改用 B07 修補石鞍（鞍形貼牆頂）' });
    }
  }

  // supply, nursery and silt reports
  const flowing = Object.keys(flow).filter(k => flow[k] > EPS);
  const gap = flowing.length ? rectGap(flowing.flatMap(k => inst[k].cells), board.zones.nursery.rect) : Infinity;
  const nurseryLevel = !flowing.length ? 'dry' : gap < T.nursery.safeGap ? 'risk' : 'safe';
  const crackOnPath = !!inst[T.crack.slot] && (flow[T.crack.slot] ?? 0) > EPS;
  const siltOnPath = (flow[T.silt.slot] ?? 0) > EPS;
  if (!knows(T.silt.observation)) unknowns.push({ id: 'silt', text: '沒有「淤積」線索：取水口後的舊槽 P1 淤到什麼程度不知道，實際水量可能比預估少。' });
  if (!knows(T.crack.observation) && crackOnPath) unknowns.push({ id: 'crack', text: '沒有「破槽」線索：舊槽 P4 有沒有裂縫沒人查過，水走這裡可能漏掉一部分。' });
  if (!knows(T.nursery.observation)) unknowns.push({ id: 'nursery', text: '沒有「育幼區足跡」線索：不知道渠邊平常有沒有孩子走動，靠近育幼區的路線風險未知。' });

  const gates = Object.values(inst).filter(s => s.piece.kind === 'gate');
  const metrics = {
    villageSupply: Math.round(fieldFlow * 100),
    drainFlow: Math.round(drainFlow * 100),
    spill: Math.round(spillFlow * 100),
    nursery: { level: knows(T.nursery.observation) ? nurseryLevel : (nurseryLevel === 'dry' ? 'dry' : 'unknown'), gap: Number.isFinite(gap) ? Math.round(gap * 100) / 100 : null },
    silt: siltCleared ? 'cleared' : knows(T.silt.observation) ? (siltOnPath ? 'slowing' : 'remaining') : 'unknown',
    crack: !crackOnPath ? 'bypassed' : !knows(T.crack.observation) ? 'unknown' : crackLeak(T.crack.slot) ? 'leaking' : 'patched',
    pieces: Object.keys(design.placed).length,
    bends: Object.values(inst).filter(s => reached.has(s.slot.id) && s.piece.kind === 'bend').length,
    gatesOnPath: gates.filter(g => reached.has(g.slot.id)).map(g => ({ slot: g.slot.id, open: g.gateOpen })),
  };
  return { inst, edges, reached: [...reached], wet, flow, issues, unknowns, metrics, blocking: issues.filter(i => i.blocking) };
}

// ---------------------------------------------------------------- direction (choice) requirements
export function checkChoice(ctx, design, ev) {
  const { board, catalog } = ctx;
  const problems = [];
  const c = design.choice;
  if (!c) return [{ code: 'NO_CHOICE', message: '還沒選處理方向（清淤／修回舊渠／保護育幼區）' }];
  const m = ev.metrics;
  const openGate = m.gatesOnPath.some(g => g.open && (ev.flow[g.slot] ?? 0) > 0);
  if (c === 'restore_channel' || c === 'protect_nursery') {
    if (m.villageSupply <= 0) problems.push({ code: 'NO_FIELD_WATER', message: '水還沒流到村田進水口' + (m.gatesOnPath.some(g => !g.open) ? '：路上的閘板關著，按「開閘」' : '：從 B01 一路接到北邊的村田') });
    if (!m.gatesOnPath.length) problems.push({ code: 'NO_GATE', message: '水路上要有一座 B05 閘板，村裡才能控制放水；把其中一段直槽換成閘板' });
    else if (!openGate && m.villageSupply <= 0) { /* already explained above */ }
  }
  if (c === 'restore_channel' && !(ev.flow[board.truth.crack.slot] > 0))
    problems.push({ code: 'NOT_OLD_LINE', message: `「修回舊渠」要讓水走原本的舊渠（經過舊槽 ${board.truth.crack.slot}）；現在的路線繞開了它` });
  if (c === 'protect_nursery' && m.villageSupply > 0) {
    const gap = m.nursery.gap ?? Infinity;
    if (gap < board.truth.nursery.safeGap) problems.push({ code: 'TOO_CLOSE', message: `流水離育幼區只有 ${Math.round(gap * 100)} cm（至少要 ${board.truth.nursery.safeGap * 100} cm）；改走西側 L 槽位繞過去` });
  }
  if (c === 'clear_silt') {
    const tee = ev.reached.map(id => ev.inst[id]).find(s => s.piece.kind === 'tee');
    if (!tee) problems.push({ code: 'NO_TEE', message: '清淤時要先把泥水導開：在 P2 放三通，一邊接去回流溝' });
    if (m.drainFlow <= 0) problems.push({ code: 'NO_DRAIN', message: '泥水沒有導進回流溝：三通西側接 L1 直槽、L2 放流坡 B02-V05' });
    if (m.villageSupply > 0) problems.push({ code: 'MUD_TO_FIELD', message: '清淤時泥水會沖進村田：把往村田那一側的閘板關上' });
    if (tee && !ev.edges[tee.slot.id].some(e => e.to && ev.inst[e.to]?.piece.kind === 'gate'))
      problems.push({ code: 'NO_HOLD_GATE', message: '三通另一側要接一座閘板（關著），清完淤再開閘送水' });
  }
  return problems;
}

// ---------------------------------------------------------------- outcome
const cost = (ctx, design, ev) => {
  const total = {};
  for (const id of [...Object.entries(design.placed).filter(([s]) => ev.reached.includes(s)).map(([, p]) => p), ...Object.values(design.patches)])
    for (const [k, v] of Object.entries(ctx.catalog.pieces[id].cost ?? {})) total[k] = (total[k] ?? 0) + v;
  return total;
};

export function fingerprint(design, obs) {
  const o = x => Object.keys(x).sort().map(k => `${k}=${x[k]}`).join(',');
  return `p:${o(design.placed)};x:${o(design.patches)};g:${o(design.gates)};c:${design.choice};o:${[...obs].sort().join(',')}`;
}

// Preview of what completing would do now (does not change anything).
export function preview(ctx, session) {
  const { design, obs, ledger } = session;
  const ev = evaluate(ctx, design, { obs, siltCleared: ledger.siltCleared });
  const problems = [...ev.blocking.map(i => ({ code: i.code, message: i.message, fix: i.fix })), ...checkChoice(ctx, design, ev)];
  const need = cost(ctx, design, ev);
  const short = Object.entries(need).filter(([k, v]) => (ledger.stock[k] ?? 0) < v);
  if (short.length) problems.push({ code: 'NOT_ENOUGH_MATERIAL', message: `本機展示材料不夠：${short.map(([k, v]) => `${ctx.board.materialNames[k]} 要 ${v}、剩 ${ledger.stock[k] ?? 0}`).join('；')}` });
  return { ev, problems, cost: need, ready: problems.length === 0 };
}

function outcomeOf(ctx, design, truthEv, obs) {
  const ch = CHOICES[design.choice];
  const m = truthEv.metrics;
  const nurseryText = { risk: `流水離育幼區只有 ${Math.round((m.nursery.gap ?? 0) * 100)} cm，孩子常走的渠邊要加圍欄、派人看守`, safe: `流水離育幼區 ${Math.round((m.nursery.gap ?? 0) * 100)} cm 以上，孩子的路不受影響`, dry: '育幼區附近沒有流水' }[m.nursery.level];
  const discovered = [];
  const T = ctx.board.truth;
  if (!obs.includes(T.silt.observation) && m.silt === 'slowing') discovered.push('完工放水才發現 P1 淤了一半，水量少了四成');
  if (!obs.includes(T.crack.observation) && m.crack === 'leaking') discovered.push('放水後 P4 舊槽西牆滲水，漏掉約三成半');
  if (!obs.includes(T.nursery.observation) && m.nursery.level === 'risk') discovered.push('放水後才看到育幼區孩子的腳印橫過渠道');
  const today = design.choice === 'clear_silt' ? 0 : m.villageSupply;
  return {
    outcomeId: ch.outcomeId, choice: design.choice,
    villageSupply: today,
    villageText: design.choice === 'clear_silt' ? '今天村田沒有新水；淤泥從回流溝排走，下次開閘就是全量' : `村田進水 ${today}%`,
    nursery: m.nursery.level, nurseryText,
    silt: design.choice === 'clear_silt' ? 'cleared' : m.silt,
    crack: m.crack,
    discovered,
  };
}

// Local demo completion. Idempotent by requestId: the same request returns the stored receipt and changes
// nothing; the same requestId with a different design is refused. NOT an official grant; see CONTRACT.md.
export function complete(ctx, session, requestId) {
  if (typeof requestId !== 'string' || !requestId) return { ok: false, code: 'NO_REQUEST_ID', message: '缺少請求編號', session };
  const fp = fingerprint(session.design, session.obs);
  const prev = session.ledger.receipts[requestId];
  if (prev) {
    if (prev.fingerprint !== fp) return { ok: false, code: 'IDEMPOTENCY_CONFLICT', message: '相同請求編號不能用於不同方案', session };
    return { ...prev, replayed: true, session };
  }
  const pv = preview(ctx, session);
  if (!pv.ready) return { ok: false, code: 'NOT_READY', problems: pv.problems, session };
  const truthEv = evaluate(ctx, session.design, { truth: true, siltCleared: session.ledger.siltCleared });
  const outcome = outcomeOf(ctx, session.design, truthEv, session.obs);
  const L = session.ledger;
  const stock = { ...L.stock };
  for (const [k, v] of Object.entries(pv.cost)) stock[k] -= v;
  const contribution = Object.values(pv.cost).reduce((a, b) => a + b, 0);
  const seq = L.seq + 1;
  const receipt = { ok: true, demo: true, official: false, requestId, fingerprint: fp, projectId: ctx.board.id, seq,
    consumed: pv.cost, contribution, outcome, replayed: false };
  const ledger = { ...L, stock, seq, contribution: L.contribution + contribution,
    receipts: { ...L.receipts, [requestId]: receipt }, completed: [...L.completed, { seq, requestId, outcomeId: outcome.outcomeId }],
    siltCleared: L.siltCleared || session.design.choice === 'clear_silt' };
  return { ...receipt, session: { ...session, ledger } };
}

// Request id for the current design: while the design is unchanged since the last completion, pressing
// "complete" again resends that same request instead of creating a second one. Rebuilding a layout later (for
// example after desilting) is a new submission with a new id.
export function requestIdFor(session) {
  const fp = fingerprint(session.design, session.obs);
  let h = 2166136261;
  for (let i = 0; i < fp.length; i++) { h ^= fp.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; }
  const last = session.ledger.completed.at(-1);
  if (last && session.ledger.receipts[last.requestId].fingerprint === fp) return last.requestId;
  return `wwb-local-${session.ledger.seq + 1}-${h.toString(16).padStart(8, '0')}`;
}

// ---------------------------------------------------------------- reference layouts (shown after completing)
export const exampleActions = (board, choice) => [
  { type: 'clear' },
  ...board.examples[choice].steps.map(([type, slot, v]) => (type === 'gate' ? { type, slot, open: v } : { type, slot, piece: v })),
  { type: 'choose', choice },
];

// What each direction does with its reference layout on the current ledger (silt state) — the trade-off table.
export function compareDirections(ctx, session) {
  return Object.keys(CHOICES).map(choice => {
    let s = { ...session, design: newDesign(), past: [], future: [] };
    for (const a of exampleActions(ctx.board, choice)) s = act(ctx, s, a).session;
    const pv = preview(ctx, s);
    const truthEv = evaluate(ctx, s.design, { truth: true, siltCleared: session.ledger.siltCleared });
    const o = outcomeOf(ctx, s.design, truthEv, ctx.board.truth ? Object.values(ctx.board.truth).map(t => t.observation) : []);
    return { choice, title: ctx.board.examples[choice].title, outcomeId: CHOICES[choice].outcomeId, villageSupply: o.villageSupply, villageText: o.villageText,
      nursery: o.nursery, nurseryText: o.nurseryText, silt: o.silt, cost: pv.cost, pieces: Object.keys(s.design.placed).length };
  });
}
