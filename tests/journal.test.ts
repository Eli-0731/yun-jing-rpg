import { before, after, test } from 'node:test';
import assert from 'node:assert/strict';
import { randomUUID } from 'node:crypto';
import { Database } from '../services/api/src/database';
import { Game, drawBirth, content } from '../services/api/src/game';
import { buildJournal, chapter } from '../services/api/src/journal';
import { Action, Snapshot, Player } from '../packages/contracts/types';
import { legacyPlayer } from './legacy-fixture';

let game: Game; let now = 1_800_000_000_000;
before(async () => { game=new Game(new Database(), { now:()=>now, birth:()=>drawBirth(now,100000), speed:60 }); await game.initialize(); });
after(async () => { await game.db.close(); });
const act=(id:string,action:Action,key=randomUUID())=>game.act(id,key,action);
const quantity=(s:Snapshot,item:string)=>s.player.inventory.filter(stack=>stack.item===item).reduce((sum,stack)=>sum+stack.quantity,0);
const reject=(promise:Promise<unknown>,code:string)=>assert.rejects(promise,(error:any)=>error.code===code);
async function player(born=true) { const id=await legacyPlayer(game,randomUUID(),'青溪來客');if(born)await act(id,{kind:'birth'});return id; }
async function meet(id:string) { for(const mentor of chapter.mentors)await act(id,{kind:'talk',mentor:mentor.id,topic:'path'}); }

test('手札內容依賴無循環、獎勵有定義、主要目標不依賴凡骨支線',()=>{
  const ids=new Set(chapter.quests.map(q=>q.id));assert.equal(ids.size,chapter.quests.length);
  function visit(id:string,path:string[]=[]){assert.ok(!path.includes(id),'Quest dependency cycle');const q=chapter.quests.find(q=>q.id===id);assert.ok(q);for(const parent of q.requires)visit(parent,[...path,id]);}
  for(const quest of chapter.quests){visit(quest.id);for(const reward of quest.rewards){assert.ok(content.items.some(item=>item.id===reward.item));assert.ok(Number.isSafeInteger(reward.quantity)&&reward.quantity>0);}if(!quest.optional)for(const parent of quest.requires)assert.equal(chapter.quests.find(q=>q.id===parent)!.optional,false);}
});

test('尚未出生可讀手札但不能取得對話與獎勵進度；未知導師及話題回滾',async()=>{
  const id=await player(false);const start=await game.snapshot(id);
  assert.equal(start.journal.quests[0].status,'locked');assert.match(start.journal.guidance,/測定/);
  await reject(act(id,{kind:'talk',mentor:'shen-yue',topic:'path'}),'BIRTH_REQUIRED');
  await act(id,{kind:'birth'});const before=await game.snapshot(id);
  await reject(act(id,{kind:'talk',mentor:'fake',topic:'path'}),'UNKNOWN_DIALOGUE');
  await reject(act(id,{kind:'talk',mentor:'shen-yue',topic:'fake'}),'UNKNOWN_DIALOGUE');
  assert.deepEqual((await game.snapshot(id)).player,before.player);
  assert.equal((await game.snapshot(id)).version,before.version);
});

test('兩位導師對話可重讀；只記一次，不會自動選宗門或改出生',async()=>{
  const id=await player(), before=await game.snapshot(id);await meet(id);await meet(id);
  const state=await game.snapshot(id);assert.equal(state.journal.quests[0].status,'ready');
  assert.equal(state.player.milestones.filter(m=>m==='talked:shen-yue').length,1);
  assert.equal(state.player.sect,'');assert.deepEqual(state.birth,before.birth);assert.deepEqual(state.player.inventory,before.player.inventory);
});

test('手札獎勵不能偽造條件或跳過前置；並行領取只發一次，原請求可重送',async()=>{
  const id=await player();
  await reject(act(id,{kind:'claim-quest',quest:'meet-mentor',completed:true,rewards:[{item:'spirit-stone',quantity:10000}]}),'QUEST_NOT_READY');
  await reject(act(id,{kind:'claim-quest',quest:'fake'}),'UNKNOWN_QUEST');
  await meet(id);const before=await game.snapshot(id);const key=randomUUID();
  const results=await Promise.allSettled([act(id,{kind:'claim-quest',quest:'meet-mentor'},key),act(id,{kind:'claim-quest',quest:'meet-mentor'})]);
  assert.equal(results.filter(r=>r.status==='fulfilled').length,1);
  const replay=await act(id,{kind:'claim-quest',quest:'meet-mentor'},key);
  assert.equal(quantity(replay,'qingling-seed'),quantity(before,'qingling-seed')+1);
  assert.ok(replay.player.inventory.some(s=>s.item==='qingling-seed'&&s.bound&&s.quantity===1));
  await reject(act(id,{kind:'claim-quest',quest:'first-trial'}),'QUEST_NOT_READY');
  const ledger=await game.db.query("SELECT * FROM ledger WHERE actor_id=$1 AND changes->>'kind'='claim-quest'",[id]);assert.equal(ledger.rows.length,1);
});

test('補給價格和數量由服務端決定，重送不重複扣款，不足完全回滾',async()=>{
  const id=await player(),key=randomUUID();const action={kind:'buy',offer:'qingling-bundle',packs:1,price:0,quantity:99999};
  const first=await act(id,action,key);assert.equal(quantity(first,'spirit-stone'),6);assert.equal(quantity(first,'qingling-herb'),3);
  assert.deepEqual(await act(id,action,key),first);
  const before=await game.snapshot(id);
  await reject(act(id,{kind:'buy',offer:'lotus-bundle',packs:2}),'MATERIALS');
  for(const packs of [0,-1,1.5,11,'1'])await reject(act(id,{kind:'buy',offer:'lotus-bundle',packs}),'INVALID_NUMBER');
  await reject(act(id,{kind:'buy',offer:'rare-root',packs:1}),'UNKNOWN_OFFER');
  assert.deepEqual((await game.snapshot(id)).player,before.player);assert.equal((await game.snapshot(id)).version,before.version);
});

test('最後一筆靈石的並行購買只能成功一次，混合綁定貨幣不能洗成可交易材料',async()=>{
  const id=await player();
  const playerState=(await game.snapshot(id)).player;
  playerState.inventory=[{item:'spirit-stone',quantity:2,bound:false,potency:100},{item:'spirit-stone',quantity:2,bound:true,potency:100}];
  await game.db.query('UPDATE players SET state=$2 WHERE id=$1',[id,JSON.stringify(playerState)]);
  const results=await Promise.allSettled([act(id,{kind:'buy',offer:'qingling-bundle',packs:1}),act(id,{kind:'buy',offer:'qingling-bundle',packs:1})]);
  assert.equal(results.filter(r=>r.status==='fulfilled').length,1);
  const state=await game.snapshot(id);assert.equal(quantity(state,'spirit-stone'),0);assert.equal(quantity(state,'qingling-herb'),3);
  assert.ok(state.player.inventory.find(s=>s.item==='qingling-herb')!.bound);
  const job=(await act(id,{kind:'craft',recipe:'body-bath'})).player.jobs[0];now+=1001;
  const claimed=await act(id,{kind:'claim-craft',job:job.id});assert.ok(claimed.player.inventory.find(s=>s.item==='body-bath')!.bound);
});

test('凡骨指引與可選開靈支線依出生顯示，開靈後仍保留支線，天才效率不被改動',async()=>{
  const id=await player();const state=await game.snapshot(id);
  const mortal=drawBirth(now,0), chosen=drawBirth(now,999999);
  const mortalPlayer=structuredClone(state.player) as Player;mortalPlayer.roots=[];
  const journal=buildJournal(mortalPlayer,mortal);assert.match(journal.guidance,/體修/);assert.ok(journal.quests.find(q=>q.id==='mortal-awakening')?.optional);
  mortalPlayer.roots=['木'];mortalPlayer.milestones.push('awakened');
  assert.ok(buildJournal(mortalPlayer,mortal).quests.some(q=>q.id==='mortal-awakening'));
  assert.ok(!buildJournal(state.player as Player,chosen).quests.some(q=>q.id==='mortal-awakening'));
  assert.equal(chosen.efficiency,3);assert.equal(mortal.efficiency,.65);
});

test('舊角色只讀就能得到手札，不回填／改動出生與資產，已完成目標可補領',async()=>{
  const id=await player();const old=await game.snapshot(id);old.player.milestones=['harvested'];
  await game.db.query('UPDATE players SET state=$2 WHERE id=$1',[id,JSON.stringify(old.player)]);
  const before=await game.snapshot(id);assert.equal(before.journal.quests.find(q=>q.id==='first-harvest')!.status,'locked');
  const again=await game.snapshot(id);assert.equal(before.version,again.version);assert.deepEqual(before.player,again.player);assert.deepEqual(before.birth,again.birth);
  await meet(id);await act(id,{kind:'claim-quest',quest:'meet-mentor'});
  assert.equal((await game.snapshot(id)).journal.quests.find(q=>q.id==='first-harvest')!.status,'ready');
  await act(id,{kind:'claim-quest',quest:'first-harvest'});
});

test('可走通全部主要手札，生態支線可先後完成且不封鎖，重複領取無額外收益',async()=>{
  const id=await player();await meet(id);await act(id,{kind:'claim-quest',quest:'meet-mentor'});
  await act(id,{kind:'plant',plot:0,crop:'qingling'});now+=30001;
  await act(id,{kind:'harvest',plot:0});await act(id,{kind:'claim-quest',quest:'first-harvest'});
  const job=(await act(id,{kind:'craft',recipe:'body-bath'})).player.jobs[0];now+=1001;
  await act(id,{kind:'claim-craft',job:job.id});await act(id,{kind:'claim-quest',quest:'first-formula'});
  for(const clue of chapter.clues)await act(id,{kind:'investigate',clue:clue.id});
  for(let i=0;i<4;i++){await act(id,{kind:'gather',node:'quarry'});now+=15001;await act(id,{kind:'contribute',quantity:3});}
  await act(id,{kind:'claim-project'});await act(id,{kind:'claim-quest',quest:'restore-channel'});
  await act(id,{kind:'buy',offer:'qingling-bundle',packs:1});await act(id,{kind:'resolve',route:'coexist'});
  await act(id,{kind:'claim-quest',quest:'living-stream'});
  await act(id,{kind:'buy',offer:'lotus-bundle',packs:1});
  const water=(await act(id,{kind:'craft',recipe:'water-purifier'})).player.jobs.find(j=>!j.claimed)!;now+=1001;
  await act(id,{kind:'claim-craft',job:water.id});await act(id,{kind:'resolve',route:'ecology'});
  await act(id,{kind:'enroll',sect:'xuanyue'});await act(id,{kind:'bathe'});
  for(let i=0;i<16;i++){now+=15001;await act(id,{kind:'practice'});}
  await act(id,{kind:'breakthrough'});const completed=await act(id,{kind:'claim-quest',quest:'first-trial'});
  assert.ok(completed.journal.finished);assert.equal(completed.journal.completed,5);assert.equal(completed.journal.nextQuestId,null);
  assert.ok(completed.world.sanctuary);assert.equal(completed.world.waterQuality,60);
  await reject(act(id,{kind:'claim-quest',quest:'first-trial'}),'QUEST_CLAIMED');
  assert.deepEqual((await game.snapshot(id)).player.inventory,completed.player.inventory);
});
