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
/** Evidence shot at 1.7 m eye height (the stand-in would cover the subject), then back to the play camera. */
async function eyeShot(p, n) { await p.evaluate(() => __wh.eye(true)); await wait(500); await shot(p, n); await p.evaluate(() => __wh.eye(false)); }

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
  // scene change 1: rake the silt open (only after it was looked at) -> the water below it rises
  await walkTo(p, [1, 3.0, -1.7], { x: spots.SILT.x, z: spots.SILT.z, pitch: 0.95 });
  await eyeShot(p, '06-silt-before-raking-1280x720.png');
  await p.keyboard.press('KeyE'); await wait(3600);
  await eyeShot(p, '07-silt-raked-water-up-1280x720.png');
  const more = await p.evaluate(() => __wh.more);
  // hint: the water gauge (zero at the tile base: today 0.30 m, old high water 0.86 m)
  await p.evaluate(() => { const g = __wh.more.GAUGE, q = __wh.onRiver(0, 2.2, 0.3); __wh.teleport(q.x, q.z, 0); __wh.face(g.x, g.z); });
  await walkTo(p, [0, 2.1, 0.5], { x: more.GAUGE.x, z: more.GAUGE.z, pitch: 0.55 });
  await p.keyboard.press('KeyE'); await wait(600);
  await eyeShot(p, '08-water-gauge-hint-1280x720.png');
  // clue 3 + scene change 2: cross over to the nursery side; a non-combat warning, then the tracks
  await p.evaluate(() => { const q = __wh.onRiver(3, 0.6, 0.0); __wh.teleport(q.x, q.z, 180); });
  await walkTo(p, [3, 2.0, 0.6]);
  await walkTo(p, [3, 2.6, 0.5], { x: more.NURSERY.x, z: more.NURSERY.z, pitch: 0.8 });   // from the channel, looking up onto the mud
  await eyeShot(p, '09-nursery-warning-1280x720.png');
  await p.keyboard.press('KeyE'); await wait(3400);
  await shot(p, '10-three-clues-notes-1280x720.png');
  await p.evaluate(() => document.getElementById('close').click());
  // the observation pavilion: stand on it and open the notes to compare
  await p.evaluate(() => { const v = __wh.more.PAVILION; __wh.teleport(v.x, v.z, 0); __wh.look(260, 0.45); });
  await wait(900);
  await shot(p, '11-pavilion-1280x720.png');
  await p.keyboard.press('KeyE'); await wait(800);
  await shot(p, '12-pavilion-notes-1280x720.png');
  await p.evaluate(() => document.getElementById('close').click());
  // hint: the resonance stone glows and hums as you come close
  await p.evaluate(() => { const q = __wh.onRiver(4, 0.4, -1.6); __wh.teleport(q.x, q.z, 180); });
  await walkTo(p, [4, 1.0, -1.8], { x: more.RESONANCE.x, z: more.RESONANCE.z, pitch: 0.6 });
  await p.keyboard.press('KeyE'); await wait(700);
  // step back along the same bank (2.2 m downstream, still inside the hint range so it keeps glowing), level with it
  await p.evaluate(() => {
    const r = __wh.more.RESONANCE, q = __wh.onRiver(4, -0.6, -2.75);
    __wh.teleport(q.x, q.z, 0); __wh.face(r.x, r.z);
    __wh.look(__wh.state().player.heading * 180 / Math.PI, 0.82);
  });
  await wait(600);
  await eyeShot(p, '13-resonance-stone-hint-1280x720.png');
  // the bamboo screen: walk through its gap on the right bank
  const __bamboo = more.BAMBOO;
  await p.evaluate(() => { const q = __wh.onRiver(1, 1.6, 3.2); __wh.teleport(q.x, q.z, 180); });
  await walkTo(p, [1, 2.7, 3.2], { ...__bamboo, pitch: 0.4 });
  await shot(p, '14-bamboo-gap-1280x720.png');
  await walkTo(p, [1, 4.2, 3.2]);   // through the gap under the arch, along the bank-top path
  await walkTo(p, [1, 6.0, 3.2]);
  const through = await st(p);
  console.log('BAMBOO', JSON.stringify(through.player));
  // lost? back to the entrance keeps the clue book
  await p.keyboard.press('KeyR'); await wait(800);
  await shot(p, '15-back-at-entrance-1280x720.png');
  const s = await st(p);
  const ev = await p.evaluate(() => __wh.events());
  const json = await p.evaluate(() => __wh.inv.toJSON());
  console.log('RESULT', JSON.stringify({
    observationIds: s.observationIds, verdict: s.verdict, json,
    clueEvents: ev.filter(e => e.type === 'clue').length, already: ev.filter(e => e.type === 'already').length,
    hints: ev.filter(e => e.type === 'hint').map(e => e.id), zones: ev.filter(e => e.type.endsWith('-zone')).map(e => e.type + ':' + e.id),
    siltCleared: s.siltCleared, atEntrance: s.player, errors,
  }));
  await ctx.close();
}
{ // review sheets: plan views of both assemblies with module IDs, two 1.7 m eye-height views, the terminal piece
  for (const route of ['a', 'b']) {
    const ctx = await browser.newContext({ viewport: { width: 1600, height: 1600 }, deviceScaleFactor: 1 });
    const p = await ctx.newPage();
    await p.goto(`${URL_}/?route=${route}`);
    await p.waitForFunction(() => globalThis.__wh && document.getElementById('loading').hidden, null, { timeout: 120000 });
    await wait(1000);
    console.log('ROUTE', route, JSON.stringify(await p.evaluate(() => __wh.chain)));
    await p.evaluate(() => __wh.setPlan(true)); await wait(1200);
    await shot(p, `20-plan-route-${route}-variant-ids.png`);
    if (route === 'a') {
      await p.evaluate(() => { __wh.colliders(true); __wh.setPlan(true); }); await wait(1200);
      await shot(p, '21-seams-colliders-route-a.png');
    }
    await ctx.close();
  }
  const { p, ctx } = await open({ width: 1280, height: 720 });
  await p.evaluate(() => { __wh.eye(true); const q = __wh.onRiver(0, 0.6, 2.4); __wh.teleport(q.x, q.z, 180); __wh.look(186, 0.32); });
  await wait(1000); await shot(p, '22-eye-1p7m-downstream-entrance.png');
  await p.evaluate(() => { const q = __wh.onRiver(2, 0.6, 2.4); __wh.teleport(q.x, q.z, 180); const c = __wh.onRiver(2, 3.0, 0);
    const pl = __wh.state().player; __wh.look(Math.atan2(c.x - pl.x, c.z - pl.z) * 180 / Math.PI, 0.55); });
  await wait(1000); await shot(p, '23-eye-1p7m-narrow-pinch.png');
  await p.evaluate(() => { const i = __wh.chain.length - 1, q = __wh.onRiver(i, 0.2, 2.2); __wh.teleport(q.x, q.z, 180); const c = __wh.onRiver(i, 3.0, 0);
    const pl = __wh.state().player; __wh.look(Math.atan2(c.x - pl.x, c.z - pl.z) * 180 / Math.PI, 0.55); });
  await wait(1000); await shot(p, '24-eye-1p7m-source-terminal.png');
  // A08 states: today the stones stand out of the water; at the old high water (0.86 m) the ford is under water
  await p.evaluate(() => { const f = __wh.more.FORDS[0], q = __wh.onRiver(0, 3.4, 2.3); __wh.teleport(q.x, q.z, 0);
    const pl = __wh.state().player; __wh.look(Math.atan2(f.x - pl.x, f.z - pl.z) * 180 / Math.PI, 0.6); });
  await wait(900); await shot(p, '25-ford-low-water-exposed.png');
  await p.evaluate(() => __wh.highWater(true)); await wait(600); await shot(p, '26-ford-old-high-water-submerged.png');
  await p.evaluate(() => __wh.highWater(false));
  await ctx.close();
}
{
  const { p, ctx, errors } = await open({ width: 844, height: 390 }, true);
  await p.evaluate(() => { const q = __wh.onRiver(0, 2.6, 2.4); __wh.teleport(q.x, q.z, 180); __wh.look(185, 0.36); });
  await wait(1000);
  await shot(p, '30-mobile-landscape-844x390.png');
  console.log('MOBILE errors', JSON.stringify(errors));
  await ctx.close();
}
await browser.close();
