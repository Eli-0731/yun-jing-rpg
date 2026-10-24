import { after, before, test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { randomUUID, createHash } from 'node:crypto';
import { Database } from '../services/api/src/database';
import { Game, content, drawBirth } from '../services/api/src/game';
import { configuration, createApp } from '../services/api/src/app';
import { Auth } from '../services/api/src/auth';
import { legacyPlayer } from './legacy-fixture';
import { Action, Snapshot } from '../packages/contracts/types';

let directory: string; let game: Game; let now = 1_800_000_000_000;
before(async () => {
  directory = await mkdtemp(join(tmpdir(), 'yunjing-tests-'));
  game = new Game(new Database({ directory }), { now: () => now, birth: () => drawBirth(now, 100000, 1) });
  await game.initialize();
});
after(async () => { await game.db.close(); await rm(directory, { recursive: true }); });
async function player() { const id = await legacyPlayer(game,`test:${randomUUID()}`, '修行者'); await game.act(id, 'birth', { kind: 'birth' }); return id; }
const act = (id: string, action: Action, key: string = randomUUID()) => game.act(id, key, action);
const quantity = (state: Snapshot, item: string) => state.player.inventory.filter(x => x.item === item).reduce((sum, x) => sum + x.quantity, 0);
const rejects = (fn: Promise<unknown>, code: string) => assert.rejects(fn, (error: any) => error.code === code);

test('出生機率邊界精確，全部權重合計一百萬', () => {
  assert.equal(content.birthWeights.reduce((sum, x) => sum + x.weight, 0), 1_000_000);
  for (const [roll, tier] of [[0,'mortal'],[99999,'mortal'],[100000,'ordinary'],[869699,'ordinary'],[869700,'gifted'],[969700,'prodigy'],[999699,'prodigy'],[999700,'chosen'],[999999,'chosen']] as const) assert.equal(drawBirth(now, roll).tier, tier);
  assert.deepEqual(drawBirth(now, 0).roots, []);
  assert.equal(drawBirth(now, 999999).roots.length, 3);
});

test('同身分並行建立只有一位角色；並行出生與重試不重抽', async () => {
  const subject = `concurrent:${randomUUID()}`;
  const ids = await Promise.all(Array.from({ length: 12 }, () => game.playerFor(subject, '同行者')));
  assert.equal(new Set(ids).size, 1);
  const states = await Promise.all(Array.from({ length: 12 }, (_, i) => game.act(ids[0], `draw-${i}`, { kind: 'birth' })));
  for (const state of states) assert.deepEqual(state.birth, states[0].birth);
  const rows = await game.db.query('SELECT * FROM births WHERE player_id=$1', [ids[0]]);
  assert.equal(rows.rows.length, 1);
});

test('相同請求編號重送不重複採集；改變內容會拒絕', async () => {
  const id = await player(); const first = await act(id, { kind: 'gather', node: 'quarry' }, 'same');
  const replay = await act(id, { kind: 'gather', node: 'quarry' }, 'same');
  assert.deepEqual(first, replay); assert.equal(quantity(await game.snapshot(id), 'stone'), 3);
  await rejects(act(id, { kind: 'gather', node: 'seed-bank' }, 'same'), 'IDEMPOTENCY_CONFLICT');
  await rejects(act(id, { kind: 'gather', node: 'quarry' }), 'COOLDOWN');
});

test('成熟使用服務端時間，並行採收只有一次，成熟不腐爛', async () => {
  const id = await player();
  await act(id, { kind: 'plant', plot: 0, crop: 'qingling' });
  await rejects(act(id, { kind: 'harvest', plot: 0, now: now + 999999999 }), 'NOT_READY');
  now += 100 * 86400000;
  const results = await Promise.allSettled([act(id, { kind: 'harvest', plot: 0 }), act(id, { kind: 'harvest', plot: 0 })]);
  assert.equal(results.filter(x => x.status === 'fulfilled').length, 1);
  assert.equal(quantity(await game.snapshot(id), 'qingling-herb'), 3);
});

test('煉製原料扣除、離線完成、雙端領取防重複', async () => {
  const id = await player(); await act(id, { kind: 'plant', plot: 0, crop: 'qingling' }); now += 1800000;
  await act(id, { kind: 'harvest', plot: 0 });
  const state = await act(id, { kind: 'craft', recipe: 'body-bath' }); const job = state.player.jobs[0].id;
  assert.equal(quantity(state, 'qingling-herb'), 0);
  await rejects(act(id, { kind: 'claim-craft', job }), 'NOT_READY'); now += 60000;
  const results = await Promise.allSettled([act(id, { kind: 'claim-craft', job }), act(id, { kind: 'claim-craft', job })]);
  assert.equal(results.filter(x => x.status === 'fulfilled').length, 1);
  assert.equal(quantity(await game.snapshot(id), 'body-bath'), 1);
});

test('材料不足的操作完全回滾，帳本與版本不增加', async () => {
  const id = await player(); const before = await game.snapshot(id);
  await rejects(act(id, { kind: 'craft', recipe: 'body-bath' }), 'MATERIALS');
  const state = await game.snapshot(id); assert.equal(state.version, before.version); assert.deepEqual(state.player, before.player);
});

test('兩人合作保存共同成果，後來者維護後亦可領取', async () => {
  const a = await player(), b = await player();
  for (const id of [a, b]) {
    await act(id, { kind: 'investigate', clue: 'broken-array' });
    await act(id, { kind: 'gather', node: 'quarry' }); now += 16000;
    await act(id, { kind: 'gather', node: 'quarry' });
  }
  await Promise.all([act(a, { kind: 'contribute', quantity: 6 }), act(b, { kind: 'contribute', quantity: 6 })]);
  assert.equal((await game.snapshot(a)).world.channel, 12);
  for (const id of [a,b]) {
    assert.equal(quantity(await act(id, { kind: 'claim-project' }), 'spirit-stone'), 15);
    await rejects(act(id, { kind: 'claim-project' }), 'ALREADY_CLAIMED');
  }
  const later = await player(); await rejects(act(later, { kind: 'claim-project' }), 'PARTICIPATION_REQUIRED');
  await act(later, { kind: 'investigate', clue: 'broken-array' }); await act(later, { kind: 'gather', node: 'quarry' });
  await act(later, { kind: 'contribute', quantity: 1 }); await act(later, { kind: 'claim-project' });
});

test('綁定靈草接收防重複、連續28日額度、取消墓碑與成品綁定', async () => {
  const id = await player(); const link = randomUUID();
  await game.db.query('INSERT INTO companion_links(id,player_id,companion_id) VALUES($1,$2,$3)', [link, id, `companion:${id}`]);
  const transfer = { id: randomUUID(), playerId: id, linkId: link, quantity: 4 };
  await Promise.all([game.receiveTransfer(transfer), game.receiveTransfer(transfer)]);
  assert.equal(quantity(await game.snapshot(id), 'companion-herb'), 4);
  await rejects(game.receiveTransfer({ ...transfer, id: randomUUID(), quantity: 1 }), 'TRANSFER_LIMIT');
  await rejects(game.receiveTransfer({ ...transfer, cancel: true }), 'TRANSFER_RECEIVED');
  const cancelled = { ...transfer, id: randomUUID(), quantity: 1, cancel: true };
  await game.receiveTransfer(cancelled);
  assert.equal((await game.receiveTransfer({ ...cancelled, cancel: false })).status, 'cancelled');
  await act(id, { kind: 'gather', node: 'herb-bank' });
  const job = (await act(id, { kind: 'craft', recipe: 'body-bath', useCompanion: true })).player.jobs[0];
  assert.equal(quantity(await game.snapshot(id), 'qingling-herb'), 0);
  now += 60000; const state = await act(id, { kind: 'claim-craft', job: job.id });
  assert.ok(state.player.inventory.some(x => x.item === 'body-bath' && x.bound && x.potency === 110));
  now += 28 * 86400000;
  await game.receiveTransfer({ ...transfer, id: randomUUID(), quantity: 1 });
});

test('角色與天賦在資料庫關閉及重新開啟後保留', async () => {
  const id = await player(); const before = await game.snapshot(id);
  await game.db.close();
  game = new Game(new Database({ directory }), { now: () => now }); await game.initialize();
  const afterRestart = await game.snapshot(id);
  assert.deepEqual(before.player, afterRestart.player); assert.deepEqual(before.birth, afterRestart.birth);
  assert.deepEqual((await act(id, { kind: 'birth' })).birth, before.birth);
});

test('凡骨可煉體與後天開靈，保留原始無靈根紀錄', async () => {
  const mortalGame = new Game(game.db, { now: () => now, birth: () => drawBirth(now, 0) });
  const id = await legacyPlayer(mortalGame,`mortal:${randomUUID()}`, '凡骨');
  await mortalGame.act(id, 'birth', { kind: 'birth' });
  await mortalGame.act(id, 'enroll', { kind: 'enroll', sect: 'taixuan' });
  await rejects(mortalGame.act(id, 'practice-fail', { kind: 'practice' }), 'NO_ROOT');
  await mortalGame.act(id, 'enroll-body', { kind: 'enroll', sect: 'xuanyue' });
  for (let i = 0; i < 10; i++) { now += 16000; await mortalGame.act(id, `practice-${i}`, { kind: 'practice' }); }
  for (const clue of ['broken-array', 'dry-lotus', 'beast-nest']) await mortalGame.act(id, clue, { kind: 'investigate', clue });
  await mortalGame.act(id, 'plant', { kind: 'plant', plot: 0, crop: 'qingling' }); now += 1800000;
  await mortalGame.act(id, 'harvest', { kind: 'harvest', plot: 0 });
  const job = (await mortalGame.act(id, 'craft', { kind: 'craft', recipe: 'body-bath' })).player.jobs[0]; now += 60000;
  await mortalGame.act(id, 'claim', { kind: 'claim-craft', job: job.id }); await mortalGame.act(id, 'bathe', { kind: 'bathe' });
  const state = await mortalGame.act(id, 'awaken', { kind: 'awaken' });
  assert.deepEqual(state.birth!.roots, []); assert.deepEqual(state.player.roots, ['木']);
});

test('正式模式拒絕缺少憑證、加速與本機登入對外綁定', () => {
  assert.throws(() => configuration({ YUNJING_MODE: 'production' }), /正式環境/);
  assert.throws(() => configuration({ YUNJING_MODE: 'local', HOST: '0.0.0.0' }), /loopback/);
  assert.throws(() => configuration({ YUNJING_MODE: 'production', DATABASE_URL: 'x', FIREBASE_PROJECT_ID: 'x', YUNJING_INTERNAL_KEY: 'x'.repeat(32), YUNJING_SPEED: '60' }), /禁止加速/);
});

test('登入交接撤銷舊存取憑證；更新憑證單次使用', async () => {
  const auth = new Auth(game, 'local'); const alias = `user_${randomUUID().slice(0,8)}`;
  const first = await auth.local(alias); const second = await auth.local(alias);
  await rejects(auth.authenticate(`Bearer ${first.token}`), 'SESSION_EXPIRED');
  assert.equal(await auth.authenticate(`Bearer ${second.token}`), second.playerId);
  const results = await Promise.allSettled([auth.refresh(second.refreshToken), auth.refresh(second.refreshToken)]);
  assert.equal(results.filter(x => x.status === 'fulfilled').length, 1);
});

test('HTTP端到端：未登入拒絕、未知動作拒絕、內容版本與跨登入保存', async () => {
  const internalKey = 'test-only-service-key-0123456789abcdef';
  const runtime = await createApp({ mode: 'local', host: '127.0.0.1', port: 4310, speed: 60, internalKey }, new Database());
  await runtime.app.listen(0, '127.0.0.1');
  const address = runtime.app.getHttpServer().address(); assert.ok(address && typeof address !== 'string'); const base = `http://127.0.0.1:${address.port}/v1`;
  try {
    assert.equal((await fetch(`${base}/me`)).status, 401);
    const login = await (await fetch(`${base}/auth/local`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ alias: 'http-test' }) })).json() as any;
    const headers = { Authorization: `Bearer ${login.token}`, 'Content-Type': 'application/json' };
    const born = await (await fetch(`${base}/actions`, { method: 'POST', headers, body: JSON.stringify({ requestId: 'first', action: { kind: 'birth' } }) })).json() as Snapshot;
    assert.equal(born.contentVersion, content.version); assert.ok(born.birthAssigned); assert.equal(born.birth,null);
    const bad = await fetch(`${base}/actions`, { method: 'POST', headers, body: JSON.stringify({ requestId: 'bad', action: { kind: 'grant-gold', quantity: 100000 } }) });
    assert.equal(bad.status, 400);
    assert.equal((await fetch(`${base}/internal/transfers`, { method: 'POST', headers, body: '{}' })).status, 403);
    const ticket = await (await fetch(`${base}/room/ticket`, { method: 'POST', headers, body: '{}' })).json() as any;
    const redeem = () => fetch(`${base}/internal/room/redeem`, { method: 'POST', headers: { ...headers, 'X-Service-Key': internalKey }, body: JSON.stringify({ ticket: ticket.ticket, roomId: ticket.roomId }) });
    const results = await Promise.all([redeem(), redeem()]);
    assert.deepEqual(results.map(x => x.status).sort(), [201, 401]);
  } finally { await runtime.app.close(); await runtime.game.db.close(); }
});

test('PKCE交換需正確驗證碼，未授權不放行，授權後並行交換只能成功一次', async () => {
  const auth = new Auth(game, 'local'); const verifier = 'x'.repeat(64);
  const challenge = await auth.challenge(createHash('sha256').update(verifier).digest('base64url'));
  assert.deepEqual(await auth.exchange(challenge.id, verifier), { pending: true });
  await rejects(auth.exchange(challenge.id, 'y'.repeat(64)), 'INVALID_PKCE');
  const id = await player();
  // Emulate a verified provider callback at the DB boundary; this is NOT a Firebase integration test.
  await game.db.query('UPDATE challenges SET player_id=$2 WHERE id=$1', [challenge.id, id]);
  const results = await Promise.allSettled([auth.exchange(challenge.id, verifier), auth.exchange(challenge.id, verifier)]);
  assert.equal(results.filter(x => x.status === 'fulfilled').length, 1);
  const expired = await auth.challenge(createHash('sha256').update(verifier).digest('base64url')); now += 300001;
  await rejects(auth.exchange(expired.id, verifier), 'INVALID_CHALLENGE');
});

test('普通角色從調查、種植、煉製、共同工程到啟蒙試煉走通', async () => {
  const id = await player();
  await rejects(act(id, { kind: 'breakthrough' }), 'CULTIVATION_REQUIRED');
  await act(id, { kind: 'enroll', sect: 'xuanyue' });
  for (const clue of ['broken-array', 'dry-lotus', 'beast-nest']) await act(id, { kind: 'investigate', clue });
  await act(id, { kind: 'plant', plot: 0, crop: 'qingling' }); now += 1800000;
  await act(id, { kind: 'harvest', plot: 0 });
  const job = (await act(id, { kind: 'craft', recipe: 'body-bath' })).player.jobs[0]; now += 60000;
  await act(id, { kind: 'claim-craft', job: job.id }); await act(id, { kind: 'bathe' });
  for (let i=0; i<30 && (await game.snapshot(id)).player.body<100; i++) { now += 16000; await act(id, { kind: 'practice' }); }
  await act(id, { kind: 'gather', node: 'quarry' }); await act(id, { kind: 'contribute', quantity: 1 });
  await act(id, { kind: 'claim-project' });
  const state = await act(id, { kind: 'breakthrough' });
  assert.equal(state.player.realm, 1); assert.ok(state.player.milestones.includes('first-breakthrough'));
  await rejects(act(id, { kind: 'breakthrough' }), 'ALREADY_ASCENDED');
});
