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
import villageContent from '../packages/content/village.json';

// K7: gathering in the novice village is settled by the server, one herb per node per regrow.
let directory: string; let game: Game; let now = 1_800_000_000_000;
before(async () => {
  directory = await mkdtemp(join(tmpdir(), 'yunjing-village-'));
  game = new Game(new Database({ directory }), { now: () => now, birth: () => drawBirth(now, 100000, 1) });
  await game.initialize();
});
after(async () => { await game.db.close(); await rm(directory, { recursive: true }); });
async function player() { const id = await legacyPlayer(game, `test:${randomUUID()}`, '採藥人'); await game.act(id, 'birth', { kind: 'birth' }); return id; }
const act = (id: string, action: Action, key: string = randomUUID()) => game.act(id, key, action);
const quantity = (state: Snapshot, item: string) => state.player.inventory.filter(x => x.item === item).reduce((sum, x) => sum + x.quantity, 0);
const rejects = (fn: Promise<unknown>, code: string) => assert.rejects(fn, (error: any) => error.code === code);

test('村中採集點的產物都存在，編號不重複', () => {
  const ids = villageContent.nodes.map(n => n.id);
  assert.equal(new Set(ids).size, ids.length);
  for (const node of villageContent.nodes) assert.ok(content.items.some(x => x.id === node.item), node.item);
});

test('採一株得一株；再生前再採會被拒絕，再生後可以再採', async () => {
  const id = await player();
  const first = await act(id, { kind: 'village-gather', node: 'HerbNode_01' });
  assert.equal(quantity(first, 'chilu-ginseng'), 1);
  await rejects(act(id, { kind: 'village-gather', node: 'HerbNode_01' }), 'COOLDOWN');
  // Another node is independent.
  const other = await act(id, { kind: 'village-gather', node: 'HerbNode_02' });
  assert.equal(quantity(other, 'qingxi-orchid'), 1);
  now += (villageContent.regrowSeconds + 1) * 1000;
  const again = await act(id, { kind: 'village-gather', node: 'HerbNode_01' });
  assert.equal(quantity(again, 'chilu-ginseng'), 2);
});

test('同一請求重送不重複給；未知採集點被拒絕', async () => {
  const id = await player();
  const first = await act(id, { kind: 'village-gather', node: 'HerbNode_03' }, 'same-herb');
  const replay = await act(id, { kind: 'village-gather', node: 'HerbNode_03' }, 'same-herb');
  assert.deepEqual(first, replay);
  assert.equal(quantity(replay, 'qingxi-orchid'), 1);
  await rejects(act(id, { kind: 'village-gather', node: 'NOPE' }), 'INVALID_NODE');
});
