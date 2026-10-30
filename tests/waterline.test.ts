import { after, before, test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { randomUUID } from 'node:crypto';
import { Database } from '../services/api/src/database';
import { Game, drawBirth } from '../services/api/src/game';
import { legacyPlayer } from './legacy-fixture';
import { Action, Snapshot } from '../packages/contracts/types';
import waterline from '../packages/content/waterline.json';

// 斷流第一章: upstream clues (A), water routing (B) and the report to the village (C), settled by the server.
let directory: string; let game: Game; let now = 1_800_000_000_000;
before(async () => {
  directory = await mkdtemp(join(tmpdir(), 'yunjing-waterline-'));
  game = new Game(new Database({ directory }), { now: () => now, birth: () => drawBirth(now, 100000, 1) });
  await game.initialize();
});
after(async () => { await game.db.close(); await rm(directory, { recursive: true }); });
async function player() { const id = await legacyPlayer(game, `test:${randomUUID()}`, '巡溪人'); await game.act(id, 'birth', { kind: 'birth' }); return id; }
const act = (id: string, action: Action, key: string = randomUUID()) => game.act(id, key, action);
const stone = (state: Snapshot) => state.player.inventory.filter(x => x.item === 'stone').reduce((s, x) => s + x.quantity, 0);
const rejects = (fn: Promise<unknown>, code: string) => assert.rejects(fn, (error: any) => error.code === code);
async function quarry(id: string, times: number) { for (let i = 0; i < times; i++) { await act(id, { kind: 'gather', node: 'quarry' }); now += 15_001; } }

test('上游線索每種只記一次，未知的線索被拒絕', async () => {
  const id = await player();
  await act(id, { kind: 'observe-upstream', observation: 'silt_buildup' });
  const again = await act(id, { kind: 'observe-upstream', observation: 'silt_buildup' });
  assert.deepEqual(again.player.upstream, ['silt_buildup']);
  await rejects(act(id, { kind: 'observe-upstream', observation: 'dragon' }), 'INVALID_OBSERVATION');
});

test('線索不夠不能導水；導水扣石料、提高全村共用的水量，同一方向不重複', async () => {
  const id = await player(); await quarry(id, 4);
  await act(id, { kind: 'observe-upstream', observation: 'cracked_sluice' });
  await rejects(act(id, { kind: 'waterworks-commit', choice: 'restore_channel' }), 'CLUE_REQUIRED');
  await act(id, { kind: 'observe-upstream', observation: 'silt_buildup' });
  const before = await game.snapshot(id);
  const key = randomUUID();
  const done = await act(id, { kind: 'waterworks-commit', choice: 'restore_channel' }, key);
  const choice = waterline.choices.find(c => c.id === 'restore_channel')!;
  assert.equal(stone(done), stone(before) - choice.stone);
  assert.equal(done.world.channel, Math.min(done.world.required, before.world.channel + choice.channel));
  assert.ok(done.player.milestones.includes(`outcome:${choice.outcome}`));
  // The same request sent again is the same receipt: no second charge.
  const replay = await act(id, { kind: 'waterworks-commit', choice: 'restore_channel' }, key);
  assert.equal(stone(replay), stone(done));
  await rejects(act(id, { kind: 'waterworks-commit', choice: 'restore_channel' }), 'ALREADY_BUILT');
  await rejects(act(id, { kind: 'waterworks-commit', choice: 'build-a-dam' }), 'INVALID_CHOICE');
});

test('保護育幼區的方向讓靈獸有棲地；石料不夠時什麼都不扣', async () => {
  const id = await player();
  await act(id, { kind: 'observe-upstream', observation: 'nursery_tracks' });
  await act(id, { kind: 'observe-upstream', observation: 'silt_buildup' });
  const poor = await game.snapshot(id);
  assert.ok(stone(poor) < 12, 'a fresh character starts without 12 stone');
  await rejects(act(id, { kind: 'waterworks-commit', choice: 'protect_nursery' }), 'MATERIALS');
  assert.equal(stone(await game.snapshot(id)), stone(poor));
  await quarry(id, 4);
  const done = await act(id, { kind: 'waterworks-commit', choice: 'protect_nursery' });
  assert.equal(done.world.sanctuary, true);
});

test('回村回報可以改選，不發任何東西', async () => {
  const id = await player();
  const before = await game.snapshot(id);
  const first = await act(id, { kind: 'village-report', report: 'tell_shortage' });
  const changed = await act(id, { kind: 'village-report', report: 'inspect_crack' });
  assert.equal(changed.player.waterReport, 'inspect_crack');
  assert.deepEqual(changed.player.inventory, before.player.inventory);
  assert.equal(first.player.contribution, before.player.contribution);
  await rejects(act(id, { kind: 'village-report', report: 'shout' }), 'INVALID_REPORT');
});
