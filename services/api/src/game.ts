import { createHash, randomInt, randomUUID } from 'node:crypto';
import content from '../../../packages/content/world.json';
import { Action, Birth, Player, Snapshot, Stack, Talent, World } from '../../../packages/contracts/types';
import { Database, Sql } from './database';
import { buildJournal, chapter } from './journal';
import estateContent from '../../../packages/content/estate.json';

export { content, estateContent };
export const SELECTION_DELAY_MS = 10 * 24 * 60 * 60 * 1000;
export function estateOf(player: Player) { return player.estate ?? { cistern: false, bound: false, modes: ['rain','rain','rain','rain'] }; }
export class GameError extends Error {
  constructor(public code: string, message: string, public status = 400) { super(message); }
}
export function ensure(condition: unknown, code: string, message: string, status = 400): asserts condition {
  if (!condition) throw new GameError(code, message, status);
}
export const hash = (text: string) => createHash('sha256').update(text).digest('hex');
const elements = ['金', '木', '水', '火', '土'];
export function drawBirth(now: number, roll = randomInt(1_000_000), offset = randomInt(5)): Birth {
  if (!Number.isInteger(roll) || roll < 0 || roll >= 1_000_000) throw new Error('Invalid birth roll');
  let remaining = roll;
  const tier = content.birthWeights.find(row => { remaining -= row.weight; return remaining < 0; })!;
  return {
    tier: tier.id as Talent, label: tier.label,
    roots: Array.from({ length: tier.rootCount }, (_, index) => elements[(offset + index) % 5]),
    apertures: tier.apertures, constitution: tier.id === 'chosen' ? '先天道體' : tier.id === 'prodigy' ? '清靈體' : '凡體',
    efficiency: tier.efficiency, version: content.version, createdAt: now,
  };
}
function initialPlayer(id: string, name: string): Player {
  return { id, name, realm: 0, path: 'body', sect: '', body: 0, qi: 0, roots: [], apertures: 0,
    inventory: [
      { item: 'qingling-seed', quantity: 3, bound: false, potency: 100 },
      { item: 'lotus-seed', quantity: 2, bound: false, potency: 100 },
      { item: 'spirit-stone', quantity: 10, bound: false, potency: 100 },
    ], plots: [], jobs: [], clues: [], milestones: [], cooldowns: {}, contribution: 0 };
}
export function grant(player: Player, item: string, quantity: number, bound = false, potency = 100) {
  const stack = player.inventory.find(x => x.item === item && x.bound === bound && x.potency === potency);
  if (stack) stack.quantity += quantity;
  else player.inventory.push({ item, quantity, bound, potency });
}
export function spend(player: Player, item: string, quantity: number): { bound: boolean; potency: number } {
  const stacks = player.inventory.filter(x => x.item === item).sort((a, b) => Number(a.bound) - Number(b.bound));
  ensure(stacks.reduce((sum, x) => sum + x.quantity, 0) >= quantity, 'MATERIALS', `材料不足：${content.items.find(x => x.id === item)?.label ?? item}`);
  let left = quantity, bound = false, potency = 100;
  for (const stack of stacks) {
    const used = Math.min(left, stack.quantity);
    if (used > 0) { stack.quantity -= used; left -= used; bound ||= stack.bound; potency = Math.max(potency, stack.potency); }
  }
  player.inventory = player.inventory.filter(x => x.quantity > 0);
  return { bound, potency };
}
function integer(value: unknown, min: number, max: number): number {
  ensure(typeof value === 'number' && Number.isInteger(value) && value >= min && value <= max, 'INVALID_NUMBER', '數量或位置不正確');
  return value;
}
function text(value: unknown, max = 100): string {
  ensure(typeof value === 'string' && value.length > 0 && value.length <= max, 'INVALID_TEXT', '缺少必要欄位');
  return value;
}
const mark = (player: Player, milestone: string) => { if (!player.milestones.includes(milestone)) player.milestones.push(milestone); };
const fingerprint = (action: Action) => hash(JSON.stringify(Object.fromEntries(Object.entries(action).sort(([a], [b]) => a.localeCompare(b)))));

export class Game {
  constructor(public db: Database, public options: { now?: () => number; birth?: () => Birth; speed?: number } = {}) {}
  now() { return this.options.now?.() ?? Date.now(); }
  get speed() { return this.options.speed ?? 1; }
  async initialize() {
    await this.db.initialize();
    const world: World = { channel: 0, required: content.project.requiredStone, waterQuality: 20, sanctuary: false, history: [] };
    await this.db.query('INSERT INTO worlds(id,state) VALUES($1,$2) ON CONFLICT DO NOTHING', ['qingxi', JSON.stringify(world)]);
  }
  async playerFor(subject: string, name: string): Promise<string> {
    text(subject, 200); text(name, 32);
    const id = randomUUID();
    return this.db.transaction(async tx => {
      const player=initialPlayer(id,name);
      const inserted=await tx.query('INSERT INTO players(id,subject,state) VALUES($1,$2,$3) ON CONFLICT(subject) DO NOTHING RETURNING id', [id, subject, JSON.stringify(player)]);
      if(inserted.rows.length) {
        const createdAt=this.now(); const birth=this.options.birth?.() ?? drawBirth(createdAt);
        player.roots=[...birth.roots];player.apertures=birth.apertures;player.path='uncommitted';
        player.journey={version:1,createdAt,selectionAt:createdAt+SELECTION_DELAY_MS,assessedAt:null,manual:'qi-primer',housing:'lodging'};
        mark(player,'received:qi-primer');
        await tx.query('UPDATE players SET state=$2 WHERE id=$1',[id,JSON.stringify(player)]);
        await tx.query('INSERT INTO births(player_id,payload) VALUES($1,$2)',[id,JSON.stringify(birth)]);
        await tx.query('INSERT INTO ledger(actor_id,request_id,changes) VALUES($1,$2,$3)',[id,'system:create',JSON.stringify({kind:'create-character',before:[],after:player.inventory})]);
      }
      return (await tx.query<{ id: string }>('SELECT id FROM players WHERE subject=$1', [subject])).rows[0].id;
    });
  }
  async snapshot(id: string): Promise<Snapshot> {
    return this.db.transaction(async tx => {
      const result = await this.lock(tx, id);
      return this.toSnapshot(result.player, result.world, result.birth, result.version);
    });
  }
  private toSnapshot(player: Player, world: World, birth: Birth | null, version: number): Snapshot {
    const hidden=!!player.journey && player.journey.assessedAt===null;
    const publicPlayer={...structuredClone(player),roots:hidden?null:[...player.roots],apertures:hidden?null:player.apertures};
    return { player:publicPlayer, world, birth:hidden?null:birth, birthAssigned:!!birth, version, serverTime: this.now(), contentVersion: content.version, speed: this.speed, journal: buildJournal(player, birth) };
  }
  private async lock(tx: Sql, id: string) {
    // All gameplay mutations use this lock order. One shared prototype world, no client authority.
    const world = (await tx.query<{ state: World }>('SELECT state FROM worlds WHERE id=$1 FOR UPDATE', ['qingxi'])).rows[0].state;
    const row = (await tx.query<{ state: Player; version: number }>('SELECT state,version FROM players WHERE id=$1 FOR UPDATE', [id])).rows[0];
    ensure(row, 'PLAYER_NOT_FOUND', '找不到修行身分', 404);
    const birth = (await tx.query<{ payload: Birth }>('SELECT payload FROM births WHERE player_id=$1', [id])).rows[0]?.payload ?? null;
    return { world, player: row.state, version: row.version, birth };
  }
  async act(id: string, requestId: string, action: Action): Promise<Snapshot> {
    text(requestId, 100); text(action.kind, 40);
    const digest = fingerprint(action);
    return this.db.transaction(async tx => {
      const state = await this.lock(tx, id);
      const previous = (await tx.query<{ fingerprint: string; result: Snapshot }>('SELECT fingerprint,result FROM receipts WHERE actor_id=$1 AND request_id=$2', [id, requestId])).rows[0];
      if (previous) {
        ensure(previous.fingerprint === digest, 'IDEMPOTENCY_CONFLICT', '相同請求編號不能用於不同操作', 409);
        // Reproject historical receipts for an unassessed character; never leak a private birth payload.
        if(state.player.journey?.assessedAt===null) {
          previous.result.birth=null;previous.result.player.roots=null;previous.result.player.apertures=null;
        }
        return previous.result;
      }
      const before = structuredClone(state.player.inventory);
      if (action.kind === 'birth') {
        if (!state.birth) {
          state.birth = this.options.birth?.() ?? drawBirth(this.now());
          state.player.roots = [...state.birth.roots]; state.player.apertures = state.birth.apertures;
          state.player.path = state.birth.tier === 'mortal' ? 'body' : 'spell';
          await tx.query('INSERT INTO births(player_id,payload) VALUES($1,$2)', [id, JSON.stringify(state.birth)]);
        }
      } else {
        ensure(state.birth, 'BIRTH_REQUIRED', '請先完成天賦分配');
        this.apply(state.player, state.world, state.birth, action);
      }
      state.version++;
      const result = this.toSnapshot(state.player, state.world, state.birth, state.version);
      await tx.query('UPDATE players SET state=$2,version=$3 WHERE id=$1', [id, JSON.stringify(state.player), state.version]);
      await tx.query('UPDATE worlds SET state=$2,version=version+1 WHERE id=$1', ['qingxi', JSON.stringify(state.world)]);
      await tx.query('INSERT INTO ledger(actor_id,request_id,changes) VALUES($1,$2,$3)', [id, requestId, JSON.stringify({ kind: action.kind, before, after: state.player.inventory })]);
      await tx.query('INSERT INTO receipts(actor_id,request_id,fingerprint,result) VALUES($1,$2,$3,$4)', [id, requestId, digest, JSON.stringify(result)]);
      return result;
    });
  }
  private apply(player: Player, world: World, birth: Birth, action: Action) {
    const now = this.now();
    const cooldown = (key: string, seconds: number) => {
      ensure((player.cooldowns[key] ?? 0) <= now, 'COOLDOWN', '尚在調息，請稍後再試', 409);
      player.cooldowns[key] = now + seconds * 1000;
    };
    const history = (label: string) => { world.history.push({ player: player.name, action: label, at: now }); world.history = world.history.slice(-30); };
    if(player.journey && ['plant','build-cistern','configure-irrigation'].includes(action.kind))
      ensure(player.journey.housing==='cave','CAVE_REQUIRED','入宗獲得洞府與靈田後才能使用；目前可採集、修煉或研究配方',409);
    switch (action.kind) {
      case 'appraise': {
        ensure(player.journey,'LEGACY_ASSESSED','既有測試角色已沿用原本資質紀錄',409);
        ensure(now>=player.journey.selectionAt,'SELECTION_NOT_READY','創角滿十個現實日後，才可前往廣場測資',409);
        if(player.journey.assessedAt===null)player.journey.assessedAt=now;
        mark(player,'assessed');break;
      }
      case 'practice-basic': {
        ensure(player.journey?.manual==='qi-primer','PRIMER_REQUIRED','此操作適用已領取煉氣訣的新入世角色',409);
        ensure(['body','qi'].includes(action.discipline as string),'INVALID_DISCIPLINE','請選擇基礎武技或煉氣訣引氣');
        if(action.discipline==='qi')ensure(player.roots.length>0,'NO_ROOT','目前未感應靈氣，可先練基礎武技、藥浴淬體或探索後天開靈');
        cooldown('practice',15);
        if(action.discipline==='body')player.body+=Math.ceil(3*birth.efficiency);
        else player.qi+=Math.ceil(3*birth.efficiency);
        mark(player,'practiced');break;
      }
      case 'build-cistern': {
        const estate = estateOf(player);
        ensure(!estate.cistern, 'ALREADY_BUILT', '蓄水池已建成', 409);
        let bound = false;
        for (const cost of estateContent.cistern.cost) { const paid = spend(player, cost.item, cost.quantity); bound ||= paid.bound; }
        player.estate = { ...estate, modes: [...estate.modes], cistern: true, bound };
        mark(player, 'built:cistern'); break;
      }
      case 'configure-irrigation': {
        const index = integer(action.plot, 0, 3);
        const mode = estateContent.modes.find(x => x.id === action.mode);
        ensure(mode, 'INVALID_IRRIGATION', '未知的灌溉方式');
        ensure(!player.plots.some(x => x.index === index), 'PLOT_OCCUPIED', '請等這一茬收成後再調整水路', 409);
        const estate = estateOf(player); const modes = [...estate.modes]; modes[index] = mode.id;
        const used = modes.reduce((sum,id) => sum + estateContent.modes.find(x => x.id === id)!.water, 0);
        ensure(used <= (estate.cistern ? estateContent.cistern.capacity : 0), 'WATER_CAPACITY', '供水不足：先建蓄水池，或釋出其他空田的水路', 409);
        player.estate = { ...estate, modes }; break;
      }
      case 'tend-plot': {
        const index = integer(action.plot, 0, 3);
        const plot = player.plots.find(x => x.index === index);
        ensure(plot && plot.plantingId && plot.plantingId === action.plantingId, 'PLANTING_CHANGED', '這一茬作物已改變，請重新確認', 409);
        ensure(!plot.tended, 'ALREADY_TENDED', '這一茬已施過草肥', 409);
        ensure(now < plot.readyAt, 'CROP_MATURE', '已成熟的作物不需再照料', 409);
        const cost = spend(player, estateContent.tending.item, estateContent.tending.quantity);
        const crop = content.crops.find(x => x.id === plot.crop)!;
        plot.harvestYield = (plot.harvestYield ?? crop.yield) + estateContent.tending.extraYield;
        plot.bound ||= cost.bound; plot.tended = true; mark(player, 'tended'); break;
      }
      case 'talk': {
        const mentor = chapter.mentors.find(x => x.id === action.mentor);
        ensure(mentor && mentor.topics.some(x => x.id === action.topic), 'UNKNOWN_DIALOGUE', '找不到這段師承對話');
        mark(player, `talked:${mentor.id}`);
        mark(player, `topic:${mentor.id}:${action.topic}`);
        break;
      }
      case 'claim-quest': {
        if(player.journey?.assessedAt===null && chapter.quests.some(q=>q.id===action.quest && q.audience))
          throw new GameError('QUEST_NOT_READY','測資後再確認個人修行支線',409);
        const quest = buildJournal(player, birth).quests.find(x => x.id === action.quest);
        ensure(quest, 'UNKNOWN_QUEST', '此修行目標不存在或不適用');
        ensure(quest.status !== 'claimed', 'QUEST_CLAIMED', '已領取此修行成果', 409);
        ensure(quest.status === 'ready', 'QUEST_NOT_READY', '請先完成目標條件與前置手札', 409);
        for (const reward of quest.rewards) grant(player, reward.item, reward.quantity, true);
        mark(player, `quest:${quest.id}`);
        break;
      }
      case 'buy': {
        const offer = chapter.merchant.offers.find(x => x.id === action.offer);
        ensure(offer, 'UNKNOWN_OFFER', '找不到這項補給');
        const packs = integer(action.packs, 1, 10);
        const payment = spend(player, 'spirit-stone', offer.price * packs);
        grant(player, offer.item, offer.quantity * packs, payment.bound);
        mark(player, 'purchased-supplies');
        break;
      }
      case 'investigate': {
        const clue = text(action.clue);
        ensure(chapter.clues.some(x => x.id === clue), 'INVALID_CLUE', '未知線索');
        if (!player.clues.includes(clue)) player.clues.push(clue);
        break;
      }
      case 'gather': {
        const node = text(action.node); ensure(['quarry', 'seed-bank', 'herb-bank'].includes(node), 'INVALID_NODE', '未知採集點');
        cooldown(`gather:${node}`, 15);
        if (node === 'quarry') grant(player, 'stone', 3);
        if (node === 'seed-bank') { grant(player, 'qingling-seed', 1); grant(player, 'lotus-seed', 1); }
        if (node === 'herb-bank') grant(player, 'qingling-herb', 1);
        mark(player, 'gathered'); break;
      }
      case 'plant': {
        const plot = integer(action.plot, 0, 3); const crop = content.crops.find(x => x.id === action.crop);
        ensure(crop, 'INVALID_CROP', '未知作物'); ensure(!player.plots.some(x => x.index === plot), 'PLOT_OCCUPIED', '這塊田已有作物', 409);
        const seed = spend(player, crop.seed, 1);
        const estate = estateOf(player);
        const mode = estateContent.modes.find(x => x.id === estate.modes[plot])!;
        player.plots.push({ index: plot, crop: crop.id, plantedAt: now, readyAt: now + Math.ceil(crop.growthSeconds * 1000 / this.speed * mode.durationPercent / 100), bound: seed.bound || (mode.water > 0 && estate.bound), plantingId: randomUUID(), mode: mode.id, harvestYield: crop.yield + mode.extraYield, tended: false });
        mark(player, 'planted'); break;
      }
      case 'harvest': {
        const index = integer(action.plot, 0, 3); const plot = player.plots.find(x => x.index === index);
        ensure(plot, 'EMPTY_PLOT', '這塊田沒有作物', 409); ensure(plot.readyAt <= now, 'NOT_READY', '作物尚未成熟', 409);
        const crop = content.crops.find(x => x.id === plot.crop)!;
        grant(player, crop.item, plot.harvestYield ?? crop.yield, plot.bound); player.plots = player.plots.filter(x => x.index !== index);
        mark(player, 'harvested'); break;
      }
      case 'craft': {
        const recipe = content.recipes.find(x => x.id === action.recipe); ensure(recipe, 'INVALID_RECIPE', '未知配方');
        ensure(player.jobs.filter(x => !x.claimed).length < 3, 'JOBS_FULL', '丹房工作位已滿', 409);
        let bound = false, potency = 100;
        if (action.useCompanion === true) {
          ensure(recipe.id === 'body-bath', 'INVALID_SUBSTITUTE', '此配方不接受替代材料');
          spend(player, 'companion-herb', 1); bound = true; potency = 110;
          spend(player, 'qingling-herb', 1);
        } else for (const ingredient of recipe.ingredients) {
          const used = spend(player, ingredient.item, ingredient.quantity); bound = used.bound || bound;
        }
        player.jobs.push({ id: randomUUID(), recipe: recipe.id, readyAt: now + recipe.seconds * 1000 / this.speed, bound, potency, claimed: false });
        break;
      }
      case 'claim-craft': {
        const job = player.jobs.find(x => x.id === action.job); ensure(job && !job.claimed, 'ALREADY_CLAIMED', '成品已領取或不存在', 409);
        ensure(job.readyAt <= now, 'NOT_READY', '尚未煉製完成', 409);
        const recipe = content.recipes.find(x => x.id === job.recipe)!;
        grant(player, recipe.output, recipe.quantity, job.bound, job.potency); job.claimed = true;
        player.jobs = player.jobs.filter(x => !x.claimed || x.id === job.id);
        mark(player, `crafted:${job.recipe}`); break;
      }
      case 'enroll': {
        const sect = content.sects.find(x => x.id === action.sect);
        ensure(sect && ['taixuan', 'xuanyue'].includes(sect.id), 'SECT_NOT_OPEN', '此階段開放太玄道院與玄岳宗');
        if(player.journey) {
          ensure(player.journey.assessedAt!==null,'ASSESSMENT_REQUIRED','滿十日後先到廣場測資，再選擇宗門',409);
          ensure(!player.sect || player.sect===sect.id,'TRANSFER_NOT_OPEN','新流程的轉宗規則尚未開放',409);
          player.journey.housing='cave';mark(player,'received:cave');
        }
        player.sect = sect.id; player.path = sect.path;
        break;
      }
      case 'practice': {
        ensure(player.sect, 'MENTOR_REQUIRED', '請先選擇師承'); cooldown('practice', 15);
        if (player.path === 'body') player.body += Math.ceil(5 * birth.efficiency);
        else { ensure(player.roots.length > 0, 'NO_ROOT', '目前無法引氣，可先向玄岳宗學習體修'); player.qi += Math.ceil(5 * birth.efficiency); }
        mark(player, 'practiced'); break;
      }
      case 'bathe': {
        const used = spend(player, 'body-bath', 1); player.body += Math.round(20 * used.potency / 100); mark(player, 'bathed'); break;
      }
      case 'awaken': {
        ensure(player.roots.length === 0, 'ALREADY_AWAKENED', '已能感應靈根', 409);
        ensure(player.body >= 40 && player.milestones.includes('bathed') && player.clues.length === 3, 'AWAKEN_REQUIREMENTS', '後天開靈需要體魄 40、完成藥浴並調查三處線索');
        player.roots.push('木'); player.apertures++; mark(player, 'awakened'); break;
      }
      case 'contribute': {
        ensure(player.clues.includes('broken-array'), 'CLUE_REQUIRED', '先調查破裂陣基');
        const requested = integer(action.quantity, 1, 12);
        const quantity = world.channel >= world.required ? 1 : Math.min(requested, world.required - world.channel);
        spend(player, 'stone', quantity); player.contribution += quantity;
        world.channel = Math.min(world.required, world.channel + quantity);
        history(world.channel >= world.required ? '維護／完成青溪水渠' : '修復青溪水渠'); break;
      }
      case 'resolve': {
        ensure(player.clues.length === 3, 'CLUE_REQUIRED', '請先完成三處調查');
        const route = text(action.route);
        ensure(['ecology', 'coexist'].includes(route), 'ROUTE_NOT_OPEN', '此路線尚未開放');
        ensure(!player.milestones.includes(`resolved:${route}`), 'ALREADY_RESOLVED', '此路線已完成', 409);
        if (route === 'ecology') { spend(player, 'water-purifier', 1); world.waterQuality = Math.min(100, world.waterQuality + 40); history('種下淨水陣，改善水質'); }
        else { spend(player, 'qingling-herb', 2); world.sanctuary = true; history('為靈獸留下棲地'); }
        player.contribution++; mark(player, `resolved:${route}`); break;
      }
      case 'claim-project': {
        ensure(world.channel >= world.required, 'PROJECT_NOT_READY', '水渠尚未修復');
        ensure(player.contribution > 0, 'PARTICIPATION_REQUIRED', '參與修復、維護或生態路線即可領取');
        ensure(!player.milestones.includes('project-reward'), 'ALREADY_CLAIMED', '已領取共同成果', 409);
        grant(player, 'spirit-stone', content.project.reward, true); mark(player, 'project-reward'); break;
      }
      case 'breakthrough': {
        ensure(player.realm === 0, 'ALREADY_ASCENDED', '已完成本階段突破', 409);
        ensure(player.sect && (player.path === 'body' ? player.body : player.qi) >= 100, 'CULTIVATION_REQUIRED', '主修進度需達 100');
        ensure(player.clues.length === 3 && player.milestones.includes('project-reward') && player.milestones.some(x => x.startsWith('crafted:')), 'TRIAL_REQUIRED', '完成調查、煉製與共同工程成果後再來試煉');
        player.realm = 1; mark(player, 'first-breakthrough'); break;
      }
      default: throw new GameError('UNKNOWN_ACTION', '未知操作');
    }
  }
  async receiveTransfer(input: { id: string; playerId: string; linkId: string; quantity: number; cancel?: boolean }) {
    text(input.id); text(input.linkId); integer(input.quantity, 1, 4);
    return this.db.transaction(async tx => {
      const state = await this.lock(tx, input.playerId);
      const previous = (await tx.query<{ player_id: string; link_id: string; quantity: number; status: string }>('SELECT * FROM transfers WHERE id=$1', [input.id])).rows[0];
      if (previous) {
        ensure(previous.player_id === input.playerId && previous.link_id === input.linkId && previous.quantity === input.quantity, 'TRANSFER_CONFLICT', '輸送識別已用於不同內容', 409);
        ensure(!(input.cancel && previous.status === 'received'), 'TRANSFER_RECEIVED', '已入帳，不能退回來源', 409);
        return { id: input.id, status: previous.status };
      }
      const link = (await tx.query('SELECT id FROM companion_links WHERE id=$1 AND player_id=$2 AND active=true', [input.linkId, input.playerId])).rows[0];
      ensure(link, 'LINK_REQUIRED', '找不到有效綁定', 409);
      ensure(state.birth, 'BIRTH_REQUIRED', '請先完成天賦分配');
      const status = input.cancel ? 'cancelled' : 'received';
      if (!input.cancel) {
        const row = (await tx.query<{ used: string }>("SELECT COALESCE(sum(quantity),0)::text AS used FROM transfers WHERE player_id=$1 AND status='received' AND at_ms > $2", [input.playerId, this.now() - content.transfer.windowDays * 86400000])).rows[0];
        ensure(Number(row.used) + input.quantity <= content.transfer.maximumHerbs, 'TRANSFER_LIMIT', '連續 28 日最多接收 4 株', 409);
        const before = structuredClone(state.player.inventory);
        grant(state.player, 'companion-herb', input.quantity, true);
        await tx.query('UPDATE players SET state=$2,version=version+1 WHERE id=$1', [input.playerId, JSON.stringify(state.player)]);
        await tx.query('INSERT INTO ledger(actor_id,request_id,changes) VALUES($1,$2,$3)', [input.playerId, `transfer:${input.id}`, JSON.stringify({ before, after: state.player.inventory })]);
      }
      await tx.query('INSERT INTO transfers(id,player_id,link_id,quantity,status,at_ms) VALUES($1,$2,$3,$4,$5,$6)', [input.id, input.playerId, input.linkId, input.quantity, status, this.now()]);
      return { id: input.id, status };
    });
  }
}
