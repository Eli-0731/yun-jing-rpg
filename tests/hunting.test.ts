import { after, before, test } from 'node:test';
import assert from 'node:assert/strict';
import { randomUUID } from 'node:crypto';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { Database } from '../services/api/src/database';
import { Game, huntingContent } from '../services/api/src/game';
import { createApp } from '../services/api/src/app';
import { HuntDeath, Snapshot } from '../packages/contracts/types';

let directory: string;
let game: Game;
let now = 1_800_000_000_000;
before(async () => {
  directory = await mkdtemp(join(tmpdir(), 'yunjing-hunt-'));
  game = new Game(new Database({ directory }), { now: () => now });
  await game.initialize();
});
after(async () => { await game.db.close(); await rm(directory, { recursive: true }); });
async function player() { return game.playerFor(`hunt:${randomUUID()}`, '採獵者'); }
const quantity = (state: Snapshot, item: string) => state.player.inventory.filter(x => x.item === item).reduce((sum, x) => sum + x.quantity, 0);
const rejects = (result: Promise<unknown>, code: string) => assert.rejects(result, (error: any) => error.code === code);
const death = (participants: string[]): HuntDeath => ({ deathId: randomUUID(), roomId: 'qingxi', spawnId: randomUUID(), enemyId: 'qingxi-mountain-rabbit', occurredAt: now, participants });

test('狩獵內容使用有效物品、機率與價格', () => {
  assert.equal(huntingContent.enemies[0].drops[0].chancePerMillion, 1_000_000);
  assert.equal(huntingContent.sellPrices['rabbit-meat'], 2);
});

test('同一死亡重送與並行只發一次；換死亡識別也不能重複結算同一出生', async () => {
  const id = await player(); const event = death([id]);
  const [first, second] = await Promise.all([game.settleHuntDeath(event), game.settleHuntDeath(event)]);
  assert.deepEqual(first, second);
  assert.equal(quantity(await game.snapshot(id), 'rabbit-meat'), 1);
  await rejects(game.settleHuntDeath({ ...event, deathId: randomUUID() }), 'HUNT_ALREADY_SETTLED');
  await rejects(game.settleHuntDeath({ ...event, spawnId: randomUUID() }), 'HUNT_CONFLICT');
  const rows = await game.db.query('SELECT * FROM ledger WHERE actor_id=$1 AND request_id=$2', [id, `hunt:${event.deathId}`]);
  assert.equal(rows.rows.length, 1);
});

test('兩名參與者各領自己的材料，名單順序不影響重送收據', async () => {
  const a = await player(), b = await player(); const event = death([b, a]);
  const receipt = await game.settleHuntDeath(event);
  assert.equal(receipt.rewards.length, 2);
  assert.equal(quantity(await game.snapshot(a), 'rabbit-meat'), 1);
  assert.equal(quantity(await game.snapshot(b), 'rabbit-meat'), 1);
  assert.deepEqual(await game.settleHuntDeath({ ...event, participants: [a, b] }), receipt);
});

test('過期、未來時間、未知玩家與客戶端自訂掉落都不能發獎', async () => {
  const id = await player(); const event = death([id]);
  await rejects(game.settleHuntDeath({ ...event, occurredAt: now - 121_000 }), 'HUNT_EXPIRED');
  await rejects(game.settleHuntDeath({ ...event, occurredAt: now + 6_000 }), 'HUNT_EXPIRED');
  await rejects(game.settleHuntDeath({ ...event, participants: [randomUUID()] }), 'PLAYER_NOT_FOUND');
  await rejects(game.settleHuntDeath({ ...event, items: [{ item: 'spirit-stone', quantity: 999 }] } as HuntDeath), 'INVALID_HUNT');
  await rejects(game.settleHuntDeath({ ...event, participants: [id, id] }), 'INVALID_HUNT');
  assert.equal(quantity(await game.snapshot(id), 'rabbit-meat'), 0);
  assert.equal((await game.db.query('SELECT * FROM hunt_deaths WHERE death_id=$1', [event.deathId])).rows.length, 0);
});

test('重啟後死亡收據保留，不會再發一份', async () => {
  const id = await player(); const event = death([id]); const first = await game.settleHuntDeath(event);
  await game.db.close(); game = new Game(new Database({ directory }), { now: () => now }); await game.initialize();
  assert.deepEqual(await game.settleHuntDeath(event), first);
  assert.equal(quantity(await game.snapshot(id), 'rabbit-meat'), 1);
});

test('只有在商販附近可出售；重送、並行與缺貨都不複製靈石', async () => {
  const id = await player(); await game.settleHuntDeath(death([id]));
  const action = { kind: 'sell-hunt', item: 'rabbit-meat', quantity: 1 };
  await rejects(game.act(id, randomUUID(), action), 'MERCHANT_DISTANCE');
  await game.markMerchantProximity(id, 'qingxi', 'material-merchant');
  const before = await game.snapshot(id); const key = randomUUID();
  const [a,b] = await Promise.all([game.act(id, key, action), game.act(id, key, action)]);
  assert.deepEqual(a,b);
  assert.equal(quantity(await game.snapshot(id), 'rabbit-meat'), 0);
  assert.equal(quantity(await game.snapshot(id), 'spirit-stone'), quantity(before, 'spirit-stone') + 2);
  await rejects(game.act(id, key, { ...action, quantity: 2 }), 'IDEMPOTENCY_CONFLICT');
  await rejects(game.act(id, randomUUID(), action), 'MATERIALS');
  now += 30_001;
  await rejects(game.act(id, randomUUID(), action), 'MERCHANT_DISTANCE');
});

test('綁定的山兔材料不能出售，失敗保持帳本不變', async () => {
  const id = await player(); await game.settleHuntDeath(death([id]));
  const state = await game.snapshot(id); const meat = state.player.inventory.find(x => x.item === 'rabbit-meat')!;
  meat.bound = true;
  await game.db.query('UPDATE players SET state=$2 WHERE id=$1', [id, JSON.stringify(state.player)]);
  await game.markMerchantProximity(id, 'qingxi', 'material-merchant');
  const before = await game.snapshot(id);
  await rejects(game.act(id, randomUUID(), { kind: 'sell-hunt', item: 'rabbit-meat', quantity: 1 }), 'MATERIALS');
  assert.deepEqual((await game.snapshot(id)).player.inventory, before.player.inventory);
});

test('HTTP 端點只接受內部憑證結算死亡與標記商販距離', async () => {
  const key = 'local-hunt-test-internal-key-0123456789';
  const runtime = await createApp({ mode: 'local', host: '127.0.0.1', port: 4310, speed: 1, internalKey: key }, new Database());
  await runtime.app.listen(0, '127.0.0.1');
  const address = runtime.app.getHttpServer().address(); assert.ok(address && typeof address !== 'string');
  const base = `http://127.0.0.1:${address.port}/v1`;
  try {
    const id = await runtime.game.playerFor(`http-hunt:${randomUUID()}`, '測試獵人');
    const event = { ...death([id]), occurredAt: runtime.game.now() };
    const body = JSON.stringify(event);
    const denied = await fetch(`${base}/internal/hunt/death`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body });
    assert.equal(denied.status, 403);
    const accepted = await fetch(`${base}/internal/hunt/death`, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Service-Key': key }, body });
    assert.equal(accepted.status, 201);
    const visitDenied = await fetch(`${base}/internal/merchant/proximity`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ playerId: id, roomId: 'qingxi', merchantId: 'material-merchant' }) });
    assert.equal(visitDenied.status, 403);
    const visitAccepted = await fetch(`${base}/internal/merchant/proximity`, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Service-Key': key }, body: JSON.stringify({ playerId: id, roomId: 'qingxi', merchantId: 'material-merchant' }) });
    assert.equal(visitAccepted.status, 201);
  } finally { await runtime.app.close(); await runtime.game.db.close(); }
});
