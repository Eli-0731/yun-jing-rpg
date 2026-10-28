/**
 * Play the local encounter demo in a real Chromium with real key input and save screenshots.
 *   node capture.mjs --modules <dir with playwright-core> --chrome <chrome.exe> [--url http://127.0.0.1:4181] [--out <dir>]
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
const URL_ = arg('--url', 'http://127.0.0.1:4181');
const OUT = path.resolve(arg('--out', path.join(here, '../../art/previews/qingxi-encounter-a/demo')));
mkdirSync(OUT, { recursive: true });
const wait = ms => new Promise(r => setTimeout(r, ms));
const browser = await chromium.launch({ executablePath: arg('--chrome'), args: ['--use-angle=d3d11', '--enable-gpu', '--ignore-gpu-blocklist'] });

async function open(viewport, mobile = false) {
  const ctx = await browser.newContext({ viewport, deviceScaleFactor: 1, hasTouch: mobile, isMobile: mobile });
  const p = await ctx.newPage(); const errors = [];
  p.on('pageerror', e => errors.push(String(e))); p.on('console', m => m.type() === 'error' && errors.push(m.text()));
  await p.goto(URL_);
  await p.waitForFunction(() => globalThis.__enc && document.getElementById('loading').hidden, null, { timeout: 120000 });
  await wait(1200);
  return { p, ctx, errors };
}
const shot = async (p, n) => { await p.screenshot({ path: path.join(OUT, n) }); console.log('SHOT', n); };
const st = p => p.evaluate(() => __enc.state());
async function until(p, pred, ms = 8000) { const t0 = Date.now(); while (Date.now() - t0 < ms) { const s = await st(p); if (pred(s)) return s; await wait(16); } return st(p); }

{
  const { p, ctx, errors } = await open({ width: 1280, height: 720 });
  await shot(p, '01-trail-start-1280x720.png');
  // walk up the trail with real keys until the rabbit notices
  await p.keyboard.down('KeyW'); await until(p, s => s.player.z > -2.6, 12000); await p.keyboard.up('KeyW');
  await until(p, s => s.rabbit.state === 'alert', 3000); await wait(300);
  await shot(p, '02-rabbit-alert-1280x720.png');
  await until(p, s => s.rabbit.state === 'windup', 4000); await wait(380);
  await shot(p, '03-rabbit-windup-tell-1280x720.png');
  await until(p, s => s.rabbit.state === 'windup', 2000); await until(p, s => s.rabbit.windupLeft != null && s.rabbit.windupLeft < 0.12, 2000);
  await p.keyboard.down('KeyD'); await wait(60); await p.keyboard.press('Space'); await wait(120);
  await shot(p, '04-side-dodge-1280x720.png');
  await p.keyboard.up('KeyD');
  await until(p, s => s.rabbit.state === 'stagger', 2000);
  // close in and strike inside the opening with the sword technique
  for (let i = 0; i < 40; i++) {
    const s = await st(p); const dx = s.rabbit.x - s.player.x, dz = s.rabbit.z - s.player.z, d = Math.hypot(dx, dz);
    if (d < 1.3 || s.rabbit.state !== 'stagger') break;
    await p.evaluate(([x, z]) => __enc.autoMove([x, z]), [dx / d, dz / d]); await wait(30);
  }
  await p.evaluate(() => __enc.autoMove(null));
  await p.keyboard.press('KeyQ'); await wait(200);
  await shot(p, '05-opening-strike-1280x720.png');
  // keep playing: dodge each charge, punish each opening, until the rabbit is driven off
  for (let round = 0; round < 8; round++) {
    let s = await until(p, s => (s.rabbit.state === 'windup' && s.rabbit.windupLeft < 0.12) || s.outcome, 9000);
    if (s.outcome) break;
    await p.keyboard.down('KeyA'); await wait(60); await p.keyboard.press('Space'); await wait(380); await p.keyboard.up('KeyA');
    s = await until(p, s => s.rabbit.state === 'stagger' || s.outcome, 2500);
    if (s.outcome) break;
    for (let i = 0; i < 40; i++) {
      const q = await st(p); const dx = q.rabbit.x - q.player.x, dz = q.rabbit.z - q.player.z, d = Math.hypot(dx, dz);
      if (d < 1.3 || q.rabbit.state !== 'stagger') break;
      await p.evaluate(([x, z]) => __enc.autoMove([x, z]), [dx / d, dz / d]); await wait(30);
    }
    await p.evaluate(() => __enc.autoMove(null)); await p.keyboard.press('KeyQ'); await wait(500);
  }
  await wait(1500);
  await shot(p, '06-result-1280x720.png');
  const res = await st(p);
  console.log('LOG', JSON.stringify((await p.evaluate(() => __enc.events())).filter(e => !['state'].includes(e.type) || ['windup','charge','stagger'].includes(e.state)).map(e => [e.t, e.type, e.state || e.reason || e.cause || e.kind || ''])));
  // body style: face the charge and block (parry timing)
  await p.evaluate(() => { __enc.setStyle('body'); __enc.restart(false); });
  await p.evaluate(() => __enc.teleport(0, -2.4, 0)); await until(p, s => s.rabbit.state === 'charge', 9000);
  for (;;) { const s = await st(p); const d = Math.hypot(s.rabbit.x - s.player.x, s.rabbit.z - s.player.z); if (d < 2.2 || s.rabbit.state !== 'charge') break; await wait(8); }
  await p.keyboard.down('KeyK'); await wait(260); await shot(p, '07-body-parry-1280x720.png'); await p.keyboard.up('KeyK');
  const body = await st(p);
  // spam block -> guard break
  for (let i = 0; i < 6; i++) { await p.keyboard.down('KeyK'); await wait(40); await p.keyboard.up('KeyK'); await wait(40); }
  await shot(p, '08-guard-broken-1280x720.png');
  const guard = await st(p);
  // hide the tab mid-charge: the rabbit must disengage
  await p.evaluate(() => { __enc.restart(false); __enc.teleport(0, -2.4, 0); });
  await until(p, s => s.rabbit.state === 'charge', 9000);
  const hpBefore = (await st(p)).player.hp;
  await p.evaluate(() => { Object.defineProperty(document, 'hidden', { value: true, configurable: true }); document.dispatchEvent(new Event('visibilitychange')); });
  await wait(1500);
  const after = await st(p);
  console.log('RESULT', JSON.stringify({ outcome: res.outcome, stats: res.stats, bodyStats: body.stats, guardBroken: guard.player.guardBroken,
    disconnect: { hpBefore, hpAfter: after.player.hp, rabbit: after.rabbit.state }, errors }));
  await ctx.close();
}
{
  const { p, ctx, errors } = await open({ width: 844, height: 390 }, true);
  await p.evaluate(() => __enc.teleport(0, -2.6, 0)); await until(p, s => s.rabbit.state === 'windup', 9000); await wait(300);
  await shot(p, '09-mobile-windup-844x390.png');
  console.log('MOBILE errors', JSON.stringify(errors));
  await ctx.close();
}
await browser.close();
