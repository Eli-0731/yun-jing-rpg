import { join } from 'node:path';
import content from '../../packages/content/creek-repair-v1.json';

// 修水路 (work pack B-56h, section 1): clear silt, join channel pieces, open the wheel and follow the water. Pure and
// deterministic: no clock, no random. Nothing here can fail; a wrong piece only explains itself and changes nothing.
// Joint geometry and the final layout check come from tools/qingxi-waterworks-b/src/waterworks-core.mjs, loaded, not copied.

const REPO = join(__dirname, '..', '..', '..');
export const core = require(join(REPO, 'tools', 'qingxi-waterworks-b', 'src', 'waterworks-core.mjs'));
export const board = require(join(REPO, 'tools', 'qingxi-waterworks-b', 'data', 'board.json'));
export const catalog = require(join(REPO, 'tools', 'qingxi-waterworks-b', 'data', 'catalog.json'));
export const coreCtx = { board, catalog };

export const creek = content;
export type MethodId = 'clear_silt' | 'restore_channel' | 'protect_nursery';
export const METHODS = Object.keys(content.methods) as MethodId[];
export type CreekEvent = { name: string; data: Record<string, unknown> };
export type CreekState = {
  version: string; method: MethodId; partySize: number;
  silt: Record<string, number>; slumped: string[]; placed: Record<string, string>; patches: Record<string, string>;
  aqueduct: boolean; wheelDegrees: number; flowM: number; reached: string[]; done: boolean;
  gates: Record<string, GateState>; gateLog: GateMove[]; idleSeconds: number; lastClosed: string; together: boolean;
  fired: string[]; events: CreekEvent[];
};
export type GateState = { level: number; fill: number };
/// Who moved which gate. `by` is 'villager' or a player's id, so a server can name real players later without new rules.
export type GateMove = { gate: string; level: number; by: string };
export type StepResult = { ok: boolean; code: string; message: string; gapCm?: number; moved?: number; onBeat?: boolean };
/// Where the spade went in, relative to the pile, which way it pulled, and whether it let go on the chant's beat.
export type Stroke = { at?: readonly number[]; dir?: readonly number[]; onBeat?: boolean };

const fail = (code: string, message: string, gapCm?: number): StepResult => ({ ok: false, code, message, gapCm });
const okay = (code: string, message: string, moved?: number): StepResult => ({ ok: true, code, message, moved });
const error = (code: string, message: string) => Object.assign(new Error(message), { code });
const methodOf = (s: CreekState) => content.methods[s.method];

export function checkParty(partySize: number): number {
  if (!Number.isInteger(partySize) || partySize < content.party.minSize || partySize > content.party.maxSize) throw error('PARTY_SIZE', `partySize must be 1 to 4, got ${partySize}`);
  return partySize;
}

/// Overview section 6: one carries 10 stones, three carry 30 between them, so each spends about the same time.
export const pileMass = (mass: number, partySize: number) => mass * checkParty(partySize);

export function newCreek(method: MethodId, partySize = 1): CreekState {
  const m = content.methods[method];
  if (!m) throw error('METHOD', `unknown method ${method}`);
  const silt: Record<string, number> = {};
  for (const p of m.piles) silt[p.id] = pileMass(p.mass, partySize);
  const gates: Record<string, GateState> = {};
  for (const g of content.distribution.gates) gates[g.id] = { level: 0, fill: 0 };
  return { version: content.version, method, partySize, silt, slumped: [], placed: {}, patches: {}, aqueduct: false, wheelDegrees: 0, flowM: 0, reached: [], done: false, gates, gateLog: [], idleSeconds: 0, lastClosed: '', together: false, fired: [], events: [] };
}

function fire(s: CreekState, key: string, name: string, data: Record<string, unknown>) {
  if (s.fired.includes(key)) return;
  s.fired.push(key); s.events.push({ name, data });
}

// ---------------------------------------------------------------- 清淤
/// The chant keeps its own clock: true when `clockSeconds` falls near the 喲. Only ever a bonus.
export function isOnBeat(clockSeconds: number): boolean {
  const c = content.chant, phase = ((clockSeconds % c.cycleSeconds) + c.cycleSeconds) % c.cycleSeconds, d = Math.abs(phase - c.yoAtSeconds);
  return Math.min(d, c.cycleSeconds - d) <= c.windowSeconds + 1e-9;
}

/// The unspent weak spot under the spade, if there is one.
export function spotAt(s: CreekState, pileId: string, at?: readonly number[]) {
  const pile = methodOf(s).piles.find(p => p.id === pileId);
  if (!pile || !at) return undefined;
  return pile.spots.find(o => !s.slumped.includes(`${pileId}:${o.id}`) && Math.hypot(o.pos[0] - at[0], o.pos[1] - at[1]) <= content.spade.slumpRadiusM);
}

/// One drag of the spade. Mud is heavy: a short drag moves nothing, and a snatched one lets half slide back. In on a weak
/// spot, the slope above comes down with it, once. Weed comes away only when pulled out of the channel. Nothing here fails.
export function scoop(s: CreekState, pileId: string, dragM: number, seconds: number, stroke: Stroke = {}): StepResult {
  const sp = content.spade, pile = methodOf(s).piles.find(p => p.id === pileId);
  if (!pile || s.silt[pileId] === undefined) return fail('NO_PILE', `這裡沒有 ${pileId} 這堆泥`);
  if (s.silt[pileId] <= 0) return fail('PILE_CLEAR', '這堆泥已經清完了');
  const mud = content.mud[pile.kind as 'soft' | 'hard' | 'weed'];
  if (dragM < mud.minDragM) return fail('TOO_SHORT', pile.kind === 'hard' ? '這塊泥結硬了，要拖得更長更慢' : '泥很重，鏟子要拖長一點才撥得動');
  let moved = Math.min(1, dragM / mud.fullDragM) * sp.scoopMass;
  const hurried = seconds < mud.hurriedSeconds;
  if (hurried) moved *= sp.hurriedKeep;
  const spot = spotAt(s, pileId, stroke.at);
  const onBeat = !!stroke.onBeat && !hurried;
  const tangled = !spot && !!stroke.dir && pile.kind === 'weed' && stroke.dir[0] * pile.pull[0] + stroke.dir[1] * pile.pull[1] < 0;
  if (tangled) moved *= mud.wrongWayKeep;
  if (onBeat) moved *= sp.beatKeep;
  if (spot) { s.slumped.push(`${pileId}:${spot.id}`); moved += spot.slump * s.partySize; }
  moved = Math.min(moved, s.silt[pileId]);
  s.silt[pileId] = Math.max(0, +(s.silt[pileId] - moved).toFixed(3));
  checkWork(s);
  if (spot) return { ...okay('SLUMPED', '整片泥塌下來了', moved), onBeat };
  if (tangled) return { ...okay('TANGLED', '水草纏住了，要往渠外拉', moved), onBeat };
  return { ...okay(hurried ? 'HURRIED' : 'MOVED', hurried ? '撥太急，泥滑回一半' : '泥被撥開了', moved), onBeat };
}

/// Soft or hard mud is scraped, not counted in spadefuls: the game measures how much the blade really carried off and says so
/// here. Nothing can go wrong with a stroke. In on a weak spot, the slope above comes down with it, once; that needs no mud of
/// its own. The beat is only reported: a heave on the 喲 changes how it lands, not how much there is.
export function scrape(s: CreekState, pileId: string, mass: number, stroke: Stroke = {}): StepResult {
  const pile = methodOf(s).piles.find(p => p.id === pileId);
  if (!pile || s.silt[pileId] === undefined) return fail('NO_PILE', `這裡沒有 ${pileId} 這堆泥`);
  if (s.silt[pileId] <= 0) return fail('PILE_CLEAR', '這堆泥已經清完了');
  if (pile.kind === 'weed') return fail('USE_DRAG', '水草要順著拉出來');
  const spot = spotAt(s, pileId, stroke.at);
  if (mass <= 0 && !spot) return fail('NOTHING_MOVED', '');
  let moved = Math.max(0, mass);
  if (spot) { s.slumped.push(`${pileId}:${spot.id}`); moved += spot.slump * s.partySize; }
  moved = Math.min(moved, s.silt[pileId]);
  s.silt[pileId] = Math.max(0, +(s.silt[pileId] - moved).toFixed(3));
  checkWork(s);
  return { ...okay(spot ? 'SLUMPED' : 'MOVED', spot ? '整片泥塌下來了' : '泥被鏟開了', moved), onBeat: !!stroke.onBeat };
}

/// Old stones showing through this pile, out of its total: they appear slowly as the mud goes.
export function stonesShowing(s: CreekState, pileId: string): number {
  const pile = methodOf(s).piles.find(p => p.id === pileId);
  if (!pile) throw error('NO_PILE', pileId);
  const total = pileMass(pile.mass, s.partySize);
  return Math.floor(pile.stones * (1 - s.silt[pileId] / total) + 1e-6);
}

export const siltLeft = (s: CreekState) => Object.values(s.silt).reduce((a, b) => a + b, 0);

// ---------------------------------------------------------------- 接渠
/// Try a piece in a slot. A piece that does not line up says by how many centimetres and is not kept.
export function place(s: CreekState, slot: string, piece: string): StepResult {
  const w = methodOf(s).work.find(x => x.slot === slot);
  if (!w) return fail('NOT_WORK_SLOT', `${slot} 這一段不用你接`);
  if (s.placed[slot]) return fail('ALREADY_PLACED', `${slot} 已經接好了`);
  const option = w.options.find(o => o.piece === piece);
  if (!option) return fail('NOT_ON_CART', `${piece} 不在這一段的料裡`);
  if (piece !== w.piece) return fail('MISALIGNED', option.message, option.gapCm);
  s.placed[slot] = piece;
  checkWork(s);
  return okay('PLACED', `${slot} 接上了`);
}

export function patch(s: CreekState, slot: string, piece: string): StepResult {
  const w = methodOf(s).patches.find(x => x.slot === slot);
  if (!w) return fail('NOT_PATCH_SLOT', `${slot} 沒有要補的裂口`);
  if (s.patches[slot]) return fail('ALREADY_PLACED', `${slot} 已經補好了`);
  if (piece !== w.piece) return fail('WRONG_PATCH', w.wrongMessage);
  s.patches[slot] = piece;
  checkWork(s);
  return okay('PATCHED', `${slot} 的裂口補好了`);
}

export function buildAqueduct(s: CreekState): StepResult {
  if (!methodOf(s).aqueduct) return fail('NO_AQUEDUCT', '這個修法不用渡槽');
  if (s.aqueduct) return fail('ALREADY_PLACED', '渡槽已經架好了');
  s.aqueduct = true;
  checkWork(s);
  return okay('AQUEDUCT', '渡槽架好了');
}

export const workLeft = (s: CreekState) => {
  const m = methodOf(s);
  return m.work.filter(w => !s.placed[w.slot]).length + m.patches.filter(p => !s.patches[p.slot]).length + (m.aqueduct && !s.aqueduct ? 1 : 0);
};
export const workDone = (s: CreekState) => siltLeft(s) <= 0 && workLeft(s) === 0;

export function gatesOf(method: MethodId): Record<string, boolean> {
  const m = content.methods[method], out: Record<string, boolean> = {};
  for (const g of m.closedGates) out[g] = false;
  for (const g of m.openGates) out[g] = true;
  return out;
}

/// Every slot the player's layout fills, in the shape of the waterworks CONTRACT's `layout`.
export function layoutOf(s: CreekState): Record<string, string> {
  const m = methodOf(s), out: Record<string, string> = {};
  for (const g of m.given) out[g.slot] = g.piece;
  for (const [k, v] of Object.entries(s.placed)) out[k] = v;
  if (s.aqueduct && m.aqueduct) for (const g of m.aqueduct.slots) out[g.slot] = g.piece;
  return Object.fromEntries(Object.keys(out).sort().map(k => [k, out[k]]));
}

function checkWork(s: CreekState) {
  if (workDone(s)) fire(s, 'work', 'creek.workCompleted', { method: s.method, layout: layoutOf(s), patches: { ...s.patches } });
}

// ---------------------------------------------------------------- 通水
export function turnWheel(s: CreekState, degrees: number): StepResult {
  if (!workDone(s)) return fail('WORK_PENDING', pendingText(s));
  if (degrees <= 0) return fail('WRONG_WAY', '閘輪要往開的方向轉');
  s.wheelDegrees = Math.min(content.flow.wheelDegrees, s.wheelDegrees + degrees);
  return okay('TURNED', gateOpen(s) ? '閘開了，水來了' : '閘板慢慢升起');
}

export const gateOpen = (s: CreekState) => s.wheelDegrees >= content.flow.wheelDegrees;
const pendingText = (s: CreekState) => siltLeft(s) > 0 ? '還有淤泥沒清完，水過不去' : '還有段落沒接好，現在放水會漫出來';

export const routeLength = (method: MethodId) => content.methods[method].route.reduce((a, n) => a + n.lengthM, 0);

// ---------------------------------------------------------------- 分水
const gateData = (id: string) => content.distribution.gates.find(g => g.id === id);
const moveGate = (s: CreekState, id: string, level: number, by: string) => {
  s.gates[id].level = level; s.gateLog.push({ gate: id, level, by });
  if (by === 'villager') return;
  s.idleSeconds = 0;
  s.lastClosed = level === 0 ? id : s.lastClosed === id ? '' : s.lastClosed;
};
export const fieldFull = (s: CreekState, id: string) => s.gates[id].fill >= gateData(id)!.fieldM - 1e-9;

/// Set a gate, before the water comes or while it runs. A full field needs no more, and nothing else is refused.
export function setGate(s: CreekState, id: string, level: number, by = 'player'): StepResult {
  const g = gateData(id);
  if (!g) return fail('NO_GATE', `這裡沒有 ${id} 這個閘門`);
  if (!content.distribution.levels.includes(level)) return fail('BAD_LEVEL', '閘門只有關、半開、全開');
  if (level > 0 && fieldFull(s, id)) return fail('FIELD_FULL', `${g.label}已經滿了`);
  if (s.gates[id].level === level) return okay('SAME_LEVEL', `${g.label}的閘門已經是這樣了`);
  moveGate(s, id, level, by);
  return okay('GATE_SET', `${g.label}的閘門${levelName(level)}`);
}

export const levelName = (level: number) => level === 0 ? '關上了' : level < 1 ? '半開' : '全開';

/// One press on a gate: shut, half, full, shut.
export function cycleGate(s: CreekState, id: string, by = 'player'): StepResult {
  const levels = content.distribution.levels, at = levels.indexOf((s.gates[id] ?? { level: 0 }).level);
  const next = levels[(at + 1) % levels.length];
  return setGate(s, id, next > 0 && s.gates[id] && fieldFull(s, id) ? 0 : next, by);
}

/// With the water going nowhere, another gate is lifted to what the sign shows; never the one a player just shut, unless it is the last.
function villagerOpens(s: CreekState) {
  const dry = content.distribution.gates.filter(g => !fieldFull(s, g.id)), pick = dry.find(g => g.id !== s.lastClosed) ?? dry[0];
  if (pick) moveGate(s, pick.id, pick.planLevel, 'villager');
}

function distribute(s: CreekState, seconds: number) {
  const d = content.distribution, gates = d.gates;
  const active = gates.filter(g => s.gates[g.id].level > 0 && !fieldFull(s, g.id));
  if (!active.length) {
    s.idleSeconds += seconds;
    if (s.idleSeconds >= d.villagerDelaySeconds - 1e-9) { s.idleSeconds = 0; villagerOpens(s); }
    return;
  }
  s.idleSeconds = 0;
  const open = active.reduce((a, g) => a + s.gates[g.id].level, 0), anyFull = gates.some(g => fieldFull(s, g.id));
  for (const g of active) {
    const st = s.gates[g.id];
    st.fill = Math.min(g.fieldM, st.fill + content.flow.speedMps * seconds * st.level / open);
    if (st.fill >= g.fieldM - 1e-9) st.fill = g.fieldM;
    if (!s.reached.includes(g.field)) { s.reached.push(g.field); fire(s, 'flow:' + g.field, 'creek.flowReached', { nodeId: g.field }); }
  }
  if (!anyFull && gates.some(g => fieldFull(s, g.id))) s.together = gates.every(g => (g.fieldM - s.gates[g.id].fill) / g.fieldM <= d.togetherWithin);
  for (const g of active) if (fieldFull(s, g.id)) moveGate(s, g.id, 0, 'villager');
  if (gates.every(g => fieldFull(s, g.id))) { s.done = true; fire(s, 'flowDone', 'creek.flowCompleted', { method: s.method }); }
}

/// The water head runs along the route to the crossing, each node reported once; from there what is open shares the water.
export function advanceFlow(s: CreekState, seconds: number): void {
  if (!gateOpen(s) || s.done || seconds <= 0) return;
  s.flowM = Math.min(routeLength(s.method), s.flowM + content.flow.speedMps * seconds);
  let at = 0;
  for (const n of methodOf(s).route) {
    if (s.flowM + 1e-6 < at) break;
    if (!s.reached.includes(n.id)) { s.reached.push(n.id); fire(s, 'flow:' + n.id, 'creek.flowReached', { nodeId: n.id }); }
    at += n.lengthM;
  }
  if (s.flowM >= routeLength(s.method) - 1e-6) distribute(s, seconds);
}

/// Fields the water has reached, in the order it got to them.
export const wetFields = (s: CreekState) => content.distribution.gates.map(g => g.field).filter(f => s.reached.includes(f)).sort((a, b) => s.reached.indexOf(a) - s.reached.indexOf(b));

// ---------------------------------------------------------------- 存檔
export const saveCreek = (s: CreekState) => JSON.stringify(s);
export function loadCreek(text: string): CreekState {
  const s = JSON.parse(text) as CreekState;
  if (s.version !== content.version) throw error('SAVE_VERSION', `save is ${s.version}, content is ${content.version}`);
  if (!content.methods[s.method]) throw error('METHOD', `unknown method ${s.method}`);
  checkParty(s.partySize);
  return s;
}

/// Party play shows the leader's world. A member whose creek is still dry takes the leader's progress, so when it is
/// repaired every unrepaired member's creek comes back; a member already repaired helped on someone else's creek and keeps their own.
export function joinLeader(member: CreekState, leader: CreekState): StepResult {
  if (member.done) return fail('ALREADY_REPAIRED', '你的溪已經修好了，這次是來幫忙');
  const events = member.events, fired = member.fired;
  const copy = JSON.parse(saveCreek(leader)) as CreekState;
  Object.assign(member, copy, { fired, events });
  if (workDone(member)) fire(member, 'work', 'creek.workCompleted', { method: member.method, layout: layoutOf(member), patches: { ...member.patches } });
  for (const id of member.reached) fire(member, 'flow:' + id, 'creek.flowReached', { nodeId: id });
  if (member.done) fire(member, 'flowDone', 'creek.flowCompleted', { method: member.method });
  return okay('JOINED', '跟著隊長的進度');
}

// ---------------------------------------------------------------- pacing
/// Expected minutes of play from the content's timing table; the pack asks for 5 to 8.
export function estimateSeconds(method: MethodId, partySize = 1): number {
  const m = content.methods[method], t = content.pacing, sp = content.spade;
  const scoops = m.piles.reduce((a, p) => a + Math.ceil(pileMass(p.mass, partySize) / partySize / sp.scoopMass), 0);
  return t.chooseAndWalkSeconds + scoops * t.scoopSeconds + m.work.length * t.pieceSeconds + m.patches.length * t.patchSeconds
    + (m.aqueduct ? t.aqueductSeconds : 0) + t.gateSeconds + t.wheelSeconds + (routeLength(method) + content.distribution.gates.reduce((a, g) => a + g.fieldM, 0)) / content.flow.speedMps + t.celebrateSeconds;
}
