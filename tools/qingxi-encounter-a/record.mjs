/**
 * Record one real-time playthrough of the local demo (real keys, real Chromium) as WebM, for the PR video.
 *   node record.mjs --modules <dir with playwright-core> --chrome <chrome.exe> [--url http://127.0.0.1:4181] [--out <dir>]
 * Then encode to H.264 MP4 with Blender: art/source/qingxi-encounter-a/encode_video.py.
 */
import { createRequire } from 'node:module';
import path from 'node:path';
import { mkdirSync, renameSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const arg = (k, d) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : d; };
const require = createRequire(path.join(arg('--modules', process.cwd()), 'x.js'));
const { chromium } = require('playwright-core');
const here = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.resolve(arg('--out', path.join(here, '../../art/previews/qingxi-encounter-a/demo')));
mkdirSync(OUT, { recursive: true });
const wait = ms => new Promise(r => setTimeout(r, ms));
const browser = await chromium.launch({ executablePath: arg('--chrome'), args: ['--use-angle=d3d11', '--enable-gpu', '--ignore-gpu-blocklist'] });
const ctx = await browser.newContext({ viewport: { width: 1280, height: 720 }, recordVideo: { dir: OUT, size: { width: 1280, height: 720 } } });
const p = await ctx.newPage();
await p.goto(arg('--url', 'http://127.0.0.1:4181'));
await p.waitForFunction(() => globalThis.__enc && document.getElementById('loading').hidden, null, { timeout: 120000 });
const st = () => p.evaluate(() => __enc.state());
async function until(pred, ms = 8000) { const t0 = Date.now(); while (Date.now() - t0 < ms) { const s = await st(); if (pred(s)) return s; await wait(16); } return st(); }
async function closeIn() {
  for (let i = 0; i < 40; i++) {
    const s = await st(); const dx = s.rabbit.x - s.player.x, dz = s.rabbit.z - s.player.z, d = Math.hypot(dx, dz);
    if (d < 1.3 || s.rabbit.state !== 'stagger') break;
    await p.evaluate(([x, z]) => __enc.autoMove([x, z]), [dx / d, dz / d]); await wait(30);
  }
  await p.evaluate(() => __enc.autoMove(null));
}
await wait(1500);                                                              // the shelter, looking out
await p.evaluate(() => __enc.teleport(3.4, -12.0, 0)); await wait(600);        // warm up on the vine dummy
for (let i = 0; i < 6; i++) { await p.keyboard.press(i % 2 ? 'KeyQ' : 'KeyJ'); await wait(600); }
await wait(800);
await p.evaluate(() => __enc.teleport(-4.1, -7.5, -90)); await wait(400);      // climb the watch platform and look
await p.keyboard.press('KeyE'); await wait(300);
await p.evaluate(() => __enc.look(Math.atan2(6.2, 7.5) * 180 / Math.PI, 0.55)); await wait(2500);
await p.keyboard.press('KeyE'); await wait(300);
await p.evaluate(() => { __enc.restart(true); __enc.look(0, 0.32); }); await wait(800);
await p.keyboard.down('KeyW'); await until(s => s.player.z > -2.6, 14000); await p.keyboard.up('KeyW');   // the trail, past the fence
for (let round = 0; round < 8; round++) {
  let s = await until(s => (s.rabbit.state === 'windup' && s.rabbit.windupLeft < 0.12) || s.outcome, 9000);
  if (s.outcome) break;
  const side = round % 2 ? 'KeyA' : 'KeyD';
  await p.keyboard.down(side); await wait(60); await p.keyboard.press('Space'); await wait(380); await p.keyboard.up(side);
  s = await until(s => s.rabbit.state === 'stagger' || s.outcome, 2500);
  if (s.outcome) break;
  await closeIn(); await p.keyboard.press('KeyQ'); await wait(600);
}
await wait(3500);                                                             // result card
const res = await st();
const video = p.video();
await ctx.close();
const src = await video.path();
renameSync(src, path.join(OUT, 'walkthrough.webm'));
console.log('RECORDED', JSON.stringify({ outcome: res.outcome, stats: res.stats }));
await browser.close();
