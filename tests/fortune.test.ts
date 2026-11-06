import { after, before, test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { randomUUID } from 'node:crypto';
import { Database } from '../services/api/src/database';
import { Game, content, drawBirth } from '../services/api/src/game';
import { legacyPlayer } from './legacy-fixture';
import { Action, Snapshot } from '../packages/contracts/types';
import fortuneContent from '../packages/content/fortunes.json';

// 機緣 (K4/K7): hidden finds are settled by the server, granted once per character.
let directory: string; let game: Game; const now = 1_800_000_000_000;
before(async () => {
  directory = await mkdtemp(join(tmpdir(), 'yunjing-fortune-'));
  game = new Game(new Database({ directory }), { now: () => now, birth: () => drawBirth(now, 100000, 1) });
  await game.initialize();
});
after(async () => { await game.db.close(); await rm(directory, { recursive: true }); });
async function player() { const id = await legacyPlayer(game, `test:${randomUUID()}`, '尋緣者'); await game.act(id, 'birth', { kind: 'birth' }); return id; }
const act = (id: string, action: Action, key: string = randomUUID()) => game.act(id, key, action);
const quantity = (state: Snapshot, item: string) => state.player.inventory.filter(x => x.item === item).reduce((sum, x) => sum + x.quantity, 0);
const rejects = (fn: Promise<unknown>, code: string) => assert.rejects(fn, (error: any) => error.code === code);

test('機緣內容的獎勵物品都存在，編號不重複', () => {
  const ids = fortuneContent.fortunes.map(f => f.id);
  assert.equal(new Set(ids).size, ids.length);
  for (const f of fortuneContent.fortunes as { item?: string }[]) if (f.item) assert.ok(content.items.some(x => x.id === f.item), f.item);
});

test('發現機緣只得一次獎勵；再發現不重複給', async () => {
  const id = await player();
  const first = await act(id, { kind: 'discover-fortune', fortune: 'A1-F03' });
  assert.deepEqual(first.player.fortunes, ['A1-F03']);
  assert.equal(quantity(first, 'qing-mushroom'), 2);
  const again = await act(id, { kind: 'discover-fortune', fortune: 'A1-F03' });
  assert.equal(quantity(again, 'qing-mushroom'), 2);
  assert.deepEqual(again.player.fortunes, ['A1-F03']);
});

test('同一請求重送回同一結果；只有線索的機緣不給物品', async () => {
  const id = await player();
  const first = await act(id, { kind: 'discover-fortune', fortune: 'A1-F02' }, 'same-fortune');
  const replay = await act(id, { kind: 'discover-fortune', fortune: 'A1-F02' }, 'same-fortune');
  assert.deepEqual(first, replay);
  assert.deepEqual(first.player.fortunes, ['A1-F02']);
  await rejects(act(id, { kind: 'discover-fortune', fortune: 'A1-F04' }, 'same-fortune'), 'IDEMPOTENCY_CONFLICT');
});

test('未知的機緣編號會被拒絕', async () => {
  const id = await player();
  await rejects(act(id, { kind: 'discover-fortune', fortune: 'NOPE' }), 'INVALID_FORTUNE');
  await rejects(act(id, { kind: 'discover-fortune' }), 'INVALID_FORTUNE');
});
