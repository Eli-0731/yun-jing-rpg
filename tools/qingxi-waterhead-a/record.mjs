/**
 * Record one real-time playthrough of the local demo (real keys, real Chromium) as WebM, for the PR video.
 *   node record.mjs --modules <dir with playwright-core> --chrome <chrome.exe> [--url http://127.0.0.1:4182] [--out <dir>]
 * Then encode to H.264 MP4 with Blender: art/source/qingxi-waterhead-a/encode_video.py.
 */
import { createRequire } from 'node:module';
import path from 'node:path';
import { mkdirSync, renameSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const arg = (k, d) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : d; };
const require = createRequire(path.join(arg('--modules', process.cwd()), 'x.js'));
const { chromium } = require('playwright-core');
const here = path.dirname(fileURLToPath(import.meta.url));
const URL_ = arg('--url', 'http://127.0.0.1:4182');
const OUT = path.resolve(arg('--out', path.join(here, '../../art/previews/qingxi-waterhead-a/demo')));
mkdirSync(OUT, { recursive: true });
const wait = ms => new Promise(r => setTimeout(r, ms));
const browser = await chromium.launch({ executablePath: arg('--chrome'), args: ['--use-angle=d3d11', '--enable-gpu', '--ignore-gpu-blocklist'] });
const ctx = await browser.newContext({ viewport: { width: 1280, height: 720 }, recordVideo: { dir: OUT, size: { width: 1280, height: 720 } } });
const p = await ctx.newPage();
await p.goto(URL_);
await p.waitForFunction(() => globalThis.__wh && document.getElementById('loading').hidden, null, { timeout: 120000 });
await wait(1500);
const st = () => p.evaluate(() => __wh.state());

/** Walk there with the W key held, turning the view smoothly (as a player would drag), then look at the target. */
async function walkTo([i, u, s], look) {
  const goal = await p.evaluate(([i, u, s]) => __wh.onRiver(i, u, s), [i, u, s]);
  await p.keyboard.down('KeyW');
  for (let k = 0; k < 600; k++) {
    const pl = (await st()).player, dx = goal.x - pl.x, dz = goal.z - pl.z;
    if (Math.hypot(dx, dz) < 0.35) break;
    await p.evaluate(([dx, dz]) => __wh.look(Math.atan2(dx, dz) * 180 / Math.PI, 0.38), [dx, dz]);
    await wait(30);
  }
  await p.keyboard.up('KeyW');
  const pl0 = (await st()).player;
  console.log('WALK', JSON.stringify([i, u, s]), 'left', Math.hypot(goal.x - pl0.x, goal.z - pl0.z).toFixed(2));
  if (look) {   // turn towards the subject over half a second
    const pl = (await st()).player, from = pl.heading, to = Math.atan2(look.x - pl.x, look.z - pl.z);
    const d = Math.atan2(Math.sin(to - from), Math.cos(to - from));
    for (let k = 1; k <= 15; k++) { await p.evaluate(([a, pi]) => __wh.look(a * 180 / Math.PI, pi), [from + d * k / 15, look.pitch ?? 0.45]); await wait(33); }
  }
  await wait(900);
}
const spots = await p.evaluate(() => __wh.spots), more = await p.evaluate(() => __wh.more);
await walkTo([0, 1.9, 1.85]);
await walkTo([0, 3.4, 1.25], { x: spots.SLUICE.x, z: spots.SLUICE.z, pitch: 0.6 });
await p.keyboard.press('KeyE'); await wait(1800);
await walkTo([1, 2.4, -2.2], { x: spots.SILT.x, z: spots.SILT.z, pitch: 0.55 });
await p.keyboard.press('KeyE'); await wait(3600);
await p.evaluate(() => document.getElementById('close').click()); await wait(400);
await walkTo([1, 3.0, -1.7], { x: spots.SILT.x, z: spots.SILT.z, pitch: 0.6 });
await p.keyboard.press('KeyE'); await wait(3200);
for (const wp of [[1, 5.6, 0.0], [2, 1.4, 0.0], [2, 3.0, 0.02], [2, 4.6, 0.0], [3, 0.6, 0.0]]) await walkTo(wp);   // up the channel, through the narrow pinch
await walkTo([3, 2.0, 0.6]);
await walkTo([3, 2.6, 0.5], { x: more.NURSERY.x, z: more.NURSERY.z, pitch: 0.8 });
await wait(800);
console.log('REACH', JSON.stringify(await p.evaluate(() => __wh.state().inReach)));
await p.keyboard.press('KeyE'); await wait(3400);
await p.evaluate(() => document.getElementById('close').click()); await wait(400);
await walkTo([3, 4.2, 3.6], { x: more.PAVILION.x, z: more.PAVILION.z, pitch: 0.4 });
const pv = more.PAVILION;
await p.keyboard.down('KeyW');
for (let k = 0; k < 300; k++) {
  const pl = (await st()).player;
  if (Math.hypot(pv.x - pl.x, pv.z - pl.z) < 1.0) break;
  await p.evaluate(([dx, dz]) => __wh.look(Math.atan2(dx, dz) * 180 / Math.PI, 0.45), [pv.x - pl.x, pv.z - pl.z]);
  await wait(30);
}
await p.keyboard.up('KeyW'); await wait(600);
await p.keyboard.press('KeyE'); await wait(3500);
const s = await st();
console.log('RECORDED', JSON.stringify({ observationIds: s.observationIds, verdict: s.verdict, siltCleared: s.siltCleared }));
const video = p.video();
await ctx.close();
renameSync(await video.path(), path.join(OUT, 'walkthrough.webm'));
await browser.close();
