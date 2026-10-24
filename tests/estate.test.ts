import { before, after, test } from 'node:test';
import assert from 'node:assert/strict';
import { randomUUID } from 'node:crypto';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { Database } from '../services/api/src/database';
import { Game, drawBirth } from '../services/api/src/game';
import { Action, Snapshot } from '../packages/contracts/types';
import { legacyPlayer } from './legacy-fixture';
let game: Game, directory: string, now=1_800_000_000_000;
before(async()=>{directory=await mkdtemp(join(tmpdir(),'yunjing-estate-'));game=new Game(new Database({directory}),{now:()=>now,birth:()=>drawBirth(now,100000),speed:60});await game.initialize();});
after(async()=>{await game.db.close();await rm(directory,{recursive:true});});
const act=(id:string,action:Action,key=randomUUID())=>game.act(id,key,action);
const reject=(promise:Promise<unknown>,code:string)=>assert.rejects(promise,(e:any)=>e.code===code);
const quantity=(s:Snapshot,item:string)=>s.player.inventory.filter(x=>x.item===item).reduce((n,x)=>n+x.quantity,0);
async function player(){const id=await legacyPlayer(game,randomUUID(),'種植者');await act(id,{kind:'birth'});return id;}
async function build(id:string){await act(id,{kind:'gather',node:'quarry'});now+=15001;await act(id,{kind:'gather',node:'quarry'});return act(id,{kind:'build-cistern'});}

test('蓄水池資源不足完全回滾；並行建造只扣一次，重送原收據不再收費',async()=>{
  const id=await player(),before=await game.snapshot(id);
  await reject(act(id,{kind:'build-cistern'}),'MATERIALS');assert.deepEqual((await game.snapshot(id)).player,before.player);
  await act(id,{kind:'gather',node:'quarry'});now+=15001;await act(id,{kind:'gather',node:'quarry'});
  const key=randomUUID();const results=await Promise.allSettled([act(id,{kind:'build-cistern'},key),act(id,{kind:'build-cistern'})]);
  assert.equal(results.filter(x=>x.status==='fulfilled').length,1);const state=await act(id,{kind:'build-cistern'},key);
  assert.equal(quantity(state,'stone'),0);assert.equal(quantity(state,'spirit-stone'),6);assert.ok(state.player.estate?.cistern);
});
test('共享供水額度允許兩畦催生或一畦養根，不能超額或繞過建造',async()=>{
  const id=await player();await reject(act(id,{kind:'configure-irrigation',plot:0,mode:'swift'}),'WATER_CAPACITY');await build(id);
  await act(id,{kind:'configure-irrigation',plot:0,mode:'swift'});await act(id,{kind:'configure-irrigation',plot:1,mode:'swift'});
  await reject(act(id,{kind:'configure-irrigation',plot:2,mode:'swift'}),'WATER_CAPACITY');
  await reject(act(id,{kind:'configure-irrigation',plot:0,mode:'abundant'}),'WATER_CAPACITY');
  await act(id,{kind:'configure-irrigation',plot:1,mode:'rain'});await act(id,{kind:'configure-irrigation',plot:0,mode:'abundant'});
  await reject(act(id,{kind:'configure-irrigation',plot:4,mode:'rain'}),'INVALID_NUMBER');await reject(act(id,{kind:'configure-irrigation',plot:0,mode:'free-max'}),'INVALID_IRRIGATION');
});
test('播種時鎖定生長時間及收成，生長中不能切模式，成熟不腐爛',async()=>{
  const id=await player();await build(id);await act(id,{kind:'configure-irrigation',plot:0,mode:'swift'});
  const first=await act(id,{kind:'plant',plot:0,crop:'qingling',readyAt:0,harvestYield:999});
  assert.equal(first.player.plots[0].readyAt-now,24000);assert.equal(first.player.plots[0].harvestYield,3);
  await reject(act(id,{kind:'configure-irrigation',plot:0,mode:'rain'}),'PLOT_OCCUPIED');now+=24000;
  await act(id,{kind:'harvest',plot:0});await act(id,{kind:'configure-irrigation',plot:0,mode:'abundant'});
  const second=await act(id,{kind:'plant',plot:0,crop:'qingling'});assert.equal(second.player.plots[0].readyAt-now,37500);assert.equal(second.player.plots[0].harvestYield,4);
  now+=100*86400000;const harvest=await act(id,{kind:'harvest',plot:0});assert.equal(quantity(harvest,'qingling-herb'),7);
});
test('施肥按作物識別、扣真實材料，每茬限一次，採收不重複發獎',async()=>{
  const id=await player();await act(id,{kind:'gather',node:'herb-bank'});
  const start=await act(id,{kind:'plant',plot:0,crop:'lotus'});const plantingId=start.player.plots[0].plantingId;
  await reject(act(id,{kind:'tend-plot',plot:0,plantingId:'fake'}),'PLANTING_CHANGED');
  const results=await Promise.allSettled([act(id,{kind:'tend-plot',plot:0,plantingId}),act(id,{kind:'tend-plot',plot:0,plantingId})]);
  assert.equal(results.filter(x=>x.status==='fulfilled').length,1);const cared=await game.snapshot(id);
  assert.equal(quantity(cared,'qingling-herb'),0);assert.equal(cared.player.plots[0].harvestYield,3);
  now+=240000;const harvests=await Promise.allSettled([act(id,{kind:'harvest',plot:0}),act(id,{kind:'harvest',plot:0})]);assert.equal(harvests.filter(x=>x.status==='fulfilled').length,1);
  assert.equal(quantity(await game.snapshot(id),'water-lotus'),3);
  await act(id,{kind:'plant',plot:0,crop:'lotus'});await reject(act(id,{kind:'tend-plot',plot:0,plantingId}),'PLANTING_CHANGED');
});
test('已成熟或材料不足不能施肥，失敗不扣資產、不改生長',async()=>{
  const id=await player();const state=await act(id,{kind:'plant',plot:0,crop:'qingling'});const plantingId=state.player.plots[0].plantingId;
  await reject(act(id,{kind:'tend-plot',plot:0,plantingId}),'MATERIALS');assert.deepEqual((await game.snapshot(id)).player,state.player);
  now+=30000;await act(id,{kind:'gather',node:'herb-bank'});const before=await game.snapshot(id);
  await reject(act(id,{kind:'tend-plot',plot:0,plantingId}),'CROP_MATURE');assert.deepEqual((await game.snapshot(id)).player,before.player);
});
test('使用綁定材料建池或施肥，收成及煉製成品維持綁定',async()=>{
  const id=await player();const state=await game.snapshot(id);
  state.player.inventory.push({item:'stone',quantity:6,bound:true,potency:100});
  await game.db.query('UPDATE players SET state=$2 WHERE id=$1',[id,JSON.stringify(state.player)]);
  await act(id,{kind:'build-cistern'});await act(id,{kind:'configure-irrigation',plot:0,mode:'swift'});
  const planted=await act(id,{kind:'plant',plot:0,crop:'qingling'});assert.ok(planted.player.plots[0].bound);now+=24000;
  await act(id,{kind:'harvest',plot:0});const job=(await act(id,{kind:'craft',recipe:'body-bath'})).player.jobs[0];assert.ok(job.bound);
  const natural=await act(id,{kind:'plant',plot:1,crop:'qingling'});assert.equal(natural.player.plots[0].bound,false);
  const p=natural.player;p.inventory.push({item:'qingling-herb',quantity:1,bound:true,potency:100});await game.db.query('UPDATE players SET state=$2 WHERE id=$1',[id,JSON.stringify(p)]);
  const tended=await act(id,{kind:'tend-plot',plot:1,plantingId:natural.player.plots[0].plantingId});assert.ok(tended.player.plots[0].bound);
});
test('舊存檔作物按原時間與產量採收，無新增欄位亦可讀取；不改天賦',async()=>{
  const id=await player();const old=await act(id,{kind:'plant',plot:0,crop:'qingling'});
  const plot=old.player.plots[0];delete plot.plantingId;delete plot.harvestYield;delete plot.mode;delete plot.tended;delete old.player.estate;
  await game.db.query('UPDATE players SET state=$2 WHERE id=$1',[id,JSON.stringify(old.player)]);
  const loaded=await game.snapshot(id);assert.equal(loaded.player.estate,undefined);assert.deepEqual(loaded.birth,old.birth);now+=30000;
  assert.equal(quantity(await act(id,{kind:'harvest',plot:0}),'qingling-herb'),3);
});
test('重啟後保留水路、作物識別與預定收成，不重算已種作物',async()=>{
  const id=await player();await build(id);await act(id,{kind:'configure-irrigation',plot:0,mode:'abundant'});const before=await act(id,{kind:'plant',plot:0,crop:'lotus'});
  await game.db.close();game=new Game(new Database({directory}),{now:()=>now,speed:1});await game.initialize();
  const loaded=await game.snapshot(id);assert.deepEqual(loaded.player,before.player);assert.deepEqual(loaded.birth,before.birth);
});
