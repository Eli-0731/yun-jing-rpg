import { before,after,test } from 'node:test';
import assert from 'node:assert/strict';
import { randomUUID } from 'node:crypto';
import { mkdtemp,rm } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { Database } from '../services/api/src/database';
import { Game,drawBirth,SELECTION_DELAY_MS } from '../services/api/src/game';
import { Action,Birth,Player,Snapshot } from '../packages/contracts/types';
import { legacyPlayer } from './legacy-fixture';
let game:Game,directory:string,now=1_800_000_000_000,draws=0;
before(async()=>{directory=await mkdtemp(join(tmpdir(),'yunjing-onboarding-'));game=new Game(new Database({directory}),{now:()=>now,speed:3600,birth:()=>{draws++;return drawBirth(now,100000,2);}});await game.initialize();});
after(async()=>{await game.db.close();await rm(directory,{recursive:true});});
const act=(id:string,action:Action,key=randomUUID())=>game.act(id,key,action);
const reject=(p:Promise<unknown>,code:string)=>assert.rejects(p,(e:any)=>e.code===code);
const create=()=>game.playerFor(randomUUID(),'新入世者');
async function privateBirth(id:string){return (await game.db.query<{payload:Birth}>('SELECT payload FROM births WHERE player_id=$1',[id])).rows[0].payload;}
function undisclosed(state:Snapshot){assert.equal(state.birth,null);assert.equal(state.player.roots,null);assert.equal(state.player.apertures,null);assert.ok(state.birthAssigned);assert.ok(!state.journal.quests.some(q=>q.id==='mortal-awakening'));}

test('創角原子分配：並行同身分只抽一次，領訣一次，時間及初始資產不重置',async()=>{
  const subject=randomUUID(),before=draws;const ids=await Promise.all(Array.from({length:10},()=>game.playerFor(subject,'新人')));
  assert.equal(new Set(ids).size,1);assert.equal(draws-before,1);
  const id=ids[0],state=await game.snapshot(id);undisclosed(state);
  assert.equal(state.player.journey?.manual,'qi-primer');assert.equal(state.player.journey?.selectionAt,now+SELECTION_DELAY_MS);
  const birth=await privateBirth(id);now+=1000;await game.playerFor(subject,'改名不重置');
  assert.deepEqual((await game.snapshot(id)).player,state.player);assert.deepEqual(await privateBirth(id),birth);
  for(let n=0;n<3;n++)undisclosed(await act(id,{kind:'birth',roll:999999}));
  assert.deepEqual(await privateBirth(id),birth);
  assert.equal((await game.db.query('SELECT * FROM ledger WHERE actor_id=$1 AND request_id=$2',[id,'system:create'])).rows.length,1);
});

test('出生分配故障時創角全回滾，不能留下無天賦的新身分',async()=>{
  const subject=randomUUID();const failing=new Game(game.db,{now:()=>now,birth:()=>{throw new Error('injected birth failure');}});
  await assert.rejects(failing.playerFor(subject,'新人'),/injected/);
  assert.equal((await game.db.query('SELECT id FROM players WHERE subject=$1',[subject])).rows.length,0);
  await game.playerFor(subject,'新人');
});

test('十個現實日邊界：離線也計、加速與客戶端時間無效；測資不重抽',async()=>{
  const id=await create(),state=await game.snapshot(id),born=await privateBirth(id),at=state.player.journey!.selectionAt;
  await reject(act(id,{kind:'appraise',now:at+1}),'SELECTION_NOT_READY');
  await reject(act(id,{kind:'enroll',sect:'xuanyue'}),'ASSESSMENT_REQUIRED');
  now=at-1;await reject(act(id,{kind:'appraise'}),'SELECTION_NOT_READY');undisclosed(await game.snapshot(id));
  now=at;const results=await Promise.all([act(id,{kind:'appraise'}),act(id,{kind:'appraise'})]);
  for(const result of results){assert.deepEqual(result.birth,born);assert.equal(result.player.journey!.assessedAt,at);}
  now+=100000;assert.equal((await act(id,{kind:'appraise'})).player.journey!.assessedAt,at);
  assert.deepEqual(await privateBirth(id),born);
});

test('未測資時所有快照與收據不揭露確切資質，專屬支線亦不充當探測入口',async()=>{
  const hiddenGame=new Game(game.db,{now:()=>now,birth:()=>drawBirth(now,0)});
  const id=await hiddenGame.playerFor(randomUUID(),'未測資凡骨');
  const key=randomUUID();undisclosed(await hiddenGame.act(id,key,{kind:'gather',node:'quarry'}));
  undisclosed(await hiddenGame.act(id,key,{kind:'gather',node:'quarry'}));
  const receipts=await game.db.query<{result:Snapshot}>('SELECT result FROM receipts WHERE actor_id=$1',[id]);
  for(const receipt of receipts.rows)undisclosed(receipt.result);
  await reject(hiddenGame.act(id,randomUUID(),{kind:'claim-quest',quest:'mortal-awakening'}),'QUEST_NOT_READY');
  const ordinary=await create();await reject(act(ordinary,{kind:'claim-quest',quest:'mortal-awakening'}),'QUEST_NOT_READY');
});

test('人人領煉氣訣：凡骨第一天可練武，無根仍不能引氣；天才效率仍更高',async()=>{
  const gains:number[]=[];
  for(const roll of [0,100000,999999]) {
    const runner=new Game(game.db,{now:()=>now,birth:()=>drawBirth(now,roll)});
    const id=await runner.playerFor(randomUUID(),'修行者');const body=await runner.act(id,randomUUID(),{kind:'practice-basic',discipline:'body'});
    gains.push(body.player.body);undisclosed(body);now+=15001;
    if(roll===0)await reject(runner.act(id,randomUUID(),{kind:'practice-basic',discipline:'qi'}),'NO_ROOT');
    else assert.ok((await runner.act(id,randomUUID(),{kind:'practice-basic',discipline:'qi'})).player.qi>0);
  }
  assert.ok(gains[0]<gains[1]&&gains[1]<gains[2]);
});

test('新手領地第一天就能種兩塊田；蓄水池與另外兩塊田等入宗後的住處，重入不重置水池與物資',async()=>{
  const id=await create();await reject(act(id,{kind:'plant',plot:2,crop:'qingling'}),'PLOT_LOCKED');
  const planted=await act(id,{kind:'plant',plot:1,crop:'qingling'});assert.equal(planted.player.plots[0].index,1);
  await reject(act(id,{kind:'build-cistern'}),'CAVE_REQUIRED');
  now=(await game.snapshot(id)).player.journey!.selectionAt;await act(id,{kind:'appraise'});
  const harvested=await act(id,{kind:'harvest',plot:1});assert.equal(harvested.player.vein,1);
  await reject(act(id,{kind:'plant',plot:3,crop:'qingling'}),'PLOT_LOCKED');
  const enrolled=await act(id,{kind:'enroll',sect:'xuanyue'});assert.equal(enrolled.player.journey!.housing,'cave');
  await act(id,{kind:'gather',node:'quarry'});now+=15001;await act(id,{kind:'gather',node:'quarry'});await act(id,{kind:'build-cistern'});
  const before=await game.snapshot(id),again=await act(id,{kind:'enroll',sect:'xuanyue'});
  assert.deepEqual(again.player.inventory,before.player.inventory);assert.deepEqual(again.player.estate,before.player.estate);
  assert.equal(again.player.milestones.filter(x=>x==='received:cave').length,1);
  await reject(act(id,{kind:'enroll',sect:'taixuan'}),'TRANSFER_NOT_OPEN');
  await act(id,{kind:'plant',plot:0,crop:'qingling'});
});

test('舊測試存檔登入不加新門檻、不倒扣財產或重抽；舊出生收據保留',async()=>{
  const subject=randomUUID(),id=await legacyPlayer(game,subject,'舊角色');const birth=await act(id,{kind:'birth'});
  await act(id,{kind:'plant',plot:0,crop:'qingling'});const before=await game.snapshot(id);
  assert.equal(await game.playerFor(subject,'再登入'),id);const loaded=await game.snapshot(id);
  assert.deepEqual(loaded.player,before.player);assert.deepEqual(loaded.birth,birth.birth);assert.equal(loaded.player.journey,undefined);
});

test('重啟保留創角時計、先天及隱藏狀態，十日後仍可正常揭露',async()=>{
  const id=await create(),before=await game.snapshot(id),born=await privateBirth(id);
  await game.db.close();game=new Game(new Database({directory}),{now:()=>now});await game.initialize();
  assert.deepEqual((await game.snapshot(id)).player,before.player);undisclosed(await game.snapshot(id));
  now=before.player.journey!.selectionAt+500;assert.deepEqual((await act(id,{kind:'appraise'})).birth,born);
});
