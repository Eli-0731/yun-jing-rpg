import { after, before, test } from 'node:test';
import assert from 'node:assert/strict';
import { randomUUID } from 'node:crypto';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { Database } from '../services/api/src/database';
import { Game, drawBirth, SELECTION_DELAY_MS } from '../services/api/src/game';

const day = 86_400_000;
let directory: string, game: Game, now = 1_800_000_000_000;
before(async () => {
  directory = await mkdtemp(join(tmpdir(), 'yunjing-study-'));
  game = new Game(new Database({ directory }), { now: () => now, speed: 3600, birth: () => drawBirth(now, 900000, 1) });
  await game.initialize();
});
after(async () => { await game.db.close(); await rm(directory, { recursive: true }); });
const act = (id: string, kind: string, extras: Record<string, unknown> = {}, requestId = randomUUID()) => game.act(id, requestId, { kind, ...extras });

test('專注研習離線累積、轉修保留進度；測資前不揭露效率', async () => {
  const id = await game.playerFor(randomUUID(), '採藥者');
  const born = now;
  await act(id, 'focus-technique', { technique: 'herb-lore' });
  now += 10 * day;
  const hidden = await game.snapshot(id);
  assert.equal(hidden.birth, null);
  assert.deepEqual(hidden.player.study?.progressMs, {});
  await assert.rejects(act(id, 'claim-technique', { technique: 'herb-lore' }), (error: any) => error.code === 'ASSESSMENT_REQUIRED');
  await act(id, 'focus-technique', { technique: 'stone-sense' });
  await act(id, 'appraise');
  const revealed = await game.snapshot(id);
  assert.equal(revealed.player.study?.progressMs['herb-lore'], 13 * day);
  assert.equal(revealed.player.journey?.selectionAt, born + SELECTION_DELAY_MS);
  now += 5 * day;
  await act(id, 'focus-technique', { technique: 'herb-lore' });
  assert.equal((await game.snapshot(id)).player.study?.progressMs['stone-sense'], 4 * day);
  now += 6 * day;
  const ready = await game.snapshot(id);
  assert.ok((ready.player.study?.progressMs['herb-lore'] ?? 0) >= 20 * day);
  const key = randomUUID();
  const mastered = await act(id, 'claim-technique', { technique: 'herb-lore' }, key);
  assert.ok(mastered.player.study?.mastered.includes('herb-lore'));
  assert.deepEqual(await act(id, 'claim-technique', { technique: 'herb-lore' }, key), mastered);
  await assert.rejects(act(id, 'claim-technique', { technique: 'herb-lore' }), (error: any) => error.code === 'ALREADY_MASTERED');
  const before = mastered.player.inventory.filter(x => x.item === 'qingling-herb').reduce((sum, x) => sum + x.quantity, 0);
  const gathered = await act(id, 'gather', { node: 'herb-bank' });
  const after = gathered.player.inventory.filter(x => x.item === 'qingling-herb').reduce((sum, x) => sum + x.quantity, 0);
  assert.equal(after - before, 2);
});

test('本機種植加速不縮短技藝的現實日門檻', async () => {
  const id = await game.playerFor(randomUUID(), '研習者');
  await act(id, 'focus-technique', { technique: 'body-footwork' });
  now += 60_000;
  const hidden = await game.snapshot(id);
  assert.deepEqual(hidden.player.study?.progressMs, {});
  const stored = (await game.db.query<{ state: { study: { since: number } } }>('SELECT state FROM players WHERE id=$1', [id])).rows[0].state;
  assert.equal(stored.study.since, now - 60_000);
  now += 10 * day;
  await act(id, 'appraise');
  const progress = (await game.snapshot(id)).player.study?.progressMs['body-footwork'] ?? 0;
  assert.ok(progress >= 8 * day && progress < 8.1 * day);
});
