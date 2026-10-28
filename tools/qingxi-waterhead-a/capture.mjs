/**
 * Play the local investigation demo in a real Chromium with real key input and save screenshots.
 *   node capture.mjs --modules <dir with playwright-core> --chrome <chrome.exe> [--url http://127.0.0.1:4182] [--out <dir>]
 * playwright-core is not a dependency of the demo; install it outside the repo.
 */
import { createRequire } from 'node:module';
import path from 'node:path';
import { mkdirSync } from 'node:fs';
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

async function open(viewport, mobile = false) {
  const ctx = await browser.newContext({ viewport, deviceScaleFactor: 1, hasTouch: mobile, isMobile: mobile });
  const p = await ctx.newPage(); const errors = [];
  p.on('pageerror', e => errors.push(String(e))); p.on('console', m => m.type() === 'error' && errors.push(m.text()));
  await p.goto(URL_);
  await p.waitForFunction(() => globalThis.__wh && document.getElementById('loading').hidden, null, { timeout: 120000 });
  await wait(1200);
  return { p, ctx, errors };
}
const shot = async (p, n) => { await p.screenshot({ path: path.join(OUT, n) }); console.log('SHOT', n); };
const st = p => p.evaluate(() => __wh.state());

/** Walk with real W key presses to a module-local river spot, steering the camera toward it, then look at a target. */
async function walkTo(p, [i, u, s], look) {
  const goal = await p.evaluate(([i, u, s]) => __wh.onRiver(i, u, s), [i, u, s]);
  await p.keyboard.down('KeyW');
  let left = Infinity;
  for (let k = 0; k < 600; k++) {
    const pl = (await st(p)).player, dx = goal.x - pl.x, dz = goal.z - pl.z;
    left = Math.hypot(dx, dz);
    if (left < 0.35) break;
    await p.evaluate(([dx, dz]) => __wh.look(Math.atan2(dx, dz) * 180 / Math.PI, 0.32), [dx, dz]);
    await wait(30);
  }
  await p.keyboard.up('KeyW');
  console.log('WALK', JSON.stringify([i, u, s]), 'left', left.toFixed(2));
  if (look) await p.evaluate(([x, z, pitch]) => { const pl = __wh.state().player; __wh.look(Math.atan2(x - pl.x, z - pl.z) * 180 / Math.PI, pitch); },
    [look.x, look.z, look.pitch ?? 0.42]);
  await wait(900);   // look long enough (dwell) before pressing E
}

{
  const { p, ctx, errors } = await open({ width: 1280, height: 720 });
  const spots = await p.evaluate(() => __wh.spots);
  await shot(p, '00-entrance-1280x720.png');
  // clue 1: the cracked sluice on the right bank
  await walkTo(p, [0, 1.9, 1.85]);
  await walkTo(p, [0, 3.4, 1.25], { x: spots.SLUICE.x, z: spots.SLUICE.z, pitch: 0.75 });   // square on to the crack, on the bank slope
  await p.evaluate(() => __wh.eye(true)); await wait(400);   // eye height: the stand-in would hide the crack
  await shot(p, '01-sluice-crack-look-1280x720.png');
  await p.evaluate(() => __wh.eye(false));
  await p.keyboard.press('KeyE'); await wait(500);
  await shot(p, '02-sluice-crack-recorded-1280x720.png');
  await p.keyboard.press('KeyE'); await wait(300);   // pressing again must not record twice
  // hint: the marker stone shows two water lines
  await walkTo(p, [1, 5.9, -1.75], { x: spots.MARKER.x, z: spots.MARKER.z, pitch: 0.42 });
  await p.keyboard.press('KeyE'); await wait(500);
  await shot(p, '03-marker-stone-hint-1280x720.png');
  // clue 2: the silt bar, seen from the left bank
  await walkTo(p, [1, 2.4, -2.2], { x: spots.SILT.x, z: spots.SILT.z, pitch: 0.5 });
  await shot(p, '04-silt-look-1280x720.png');
  await p.keyboard.press('KeyE'); await wait(3600);
  await shot(p, '05-two-clues-handoff-1280x720.png');
  await p.evaluate(() => document.getElementById('close').click());
  // the rest of the run, seen from above the right bend
  await p.evaluate(() => { const q = __wh.onRiver(3, 3.2, 2.4); __wh.teleport(q.x, q.z, 160); __wh.look(150, 0.9); });
  await wait(1200);
  await shot(p, '06-upper-run-overview-1280x720.png');
  // lost? back to the entrance keeps the clue book
  await p.keyboard.press('KeyR'); await wait(800);
  await shot(p, '07-back-at-entrance-1280x720.png');
  const s = await st(p);
  const ev = await p.evaluate(() => __wh.events());
  const json = await p.evaluate(() => __wh.inv.toJSON());
  console.log('RESULT', JSON.stringify({
    observationIds: s.observationIds, verdict: s.verdict, json,
    clueEvents: ev.filter(e => e.type === 'clue').length, already: ev.filter(e => e.type === 'already').length,
    hints: ev.filter(e => e.type === 'hint').map(e => e.id), atEntrance: s.player, errors,
  }));
  await ctx.close();
}
{ // review sheets: plan views of both assemblies with module IDs, two 1.7 m eye-height views, the terminal piece
  for (const route of ['a', 'b']) {
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 1280 }, deviceScaleFactor: 1 });
    const p = await ctx.newPage();
    await p.goto(`${URL_}/?route=${route}`);
    await p.waitForFunction(() => globalThis.__wh && document.getElementById('loading').hidden, null, { timeout: 120000 });
    await wait(1000);
    console.log('ROUTE', route, JSON.stringify(await p.evaluate(() => __wh.chain)));
    await p.evaluate(() => __wh.setPlan(true)); await wait(1200);
    await shot(p, `10-plan-route-${route}-module-ids.png`);
    await ctx.close();
  }
  const { p, ctx } = await open({ width: 1280, height: 720 });
  await p.evaluate(() => { __wh.eye(true); const q = __wh.onRiver(0, 0.6, 2.4); __wh.teleport(q.x, q.z, 180); __wh.look(186, 0.32); });
  await wait(1000); await shot(p, '11-eye-1p7m-downstream-entrance.png');
  await p.evaluate(() => { const q = __wh.onRiver(2, 0.6, 2.4); __wh.teleport(q.x, q.z, 180); const c = __wh.onRiver(2, 3.0, 0);
    const pl = __wh.state().player; __wh.look(Math.atan2(c.x - pl.x, c.z - pl.z) * 180 / Math.PI, 0.55); });
  await wait(1000); await shot(p, '12-eye-1p7m-narrow-pinch.png');
  await p.evaluate(() => { const i = __wh.chain.length - 1, q = __wh.onRiver(i, 0.2, 2.2); __wh.teleport(q.x, q.z, 180); const c = __wh.onRiver(i, 3.0, 0);
    const pl = __wh.state().player; __wh.look(Math.atan2(c.x - pl.x, c.z - pl.z) * 180 / Math.PI, 0.55); });
  await wait(1000); await shot(p, '13-eye-1p7m-source-terminal.png');
  await ctx.close();
}
{
  const { p, ctx, errors } = await open({ width: 844, height: 390 }, true);
  await p.evaluate(() => { const q = __wh.onRiver(0, 2.6, 2.4); __wh.teleport(q.x, q.z, 180); __wh.look(185, 0.36); });
  await wait(1000);
  await shot(p, '08-mobile-landscape-844x390.png');
  console.log('MOBILE errors', JSON.stringify(errors));
  await ctx.close();
}
await browser.close();
