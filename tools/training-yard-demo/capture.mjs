/**
 * Screenshot the running local demo in a real Chromium (desktop 1280x720 and phone-landscape 844x390).
 *   node capture.mjs --chrome <path-to-chrome.exe> [--url http://127.0.0.1:4178] [--out <dir>]
 * Needs playwright-core resolvable (it is not a dependency of the demo; install it outside the repo).
 * Drives the page only through the in-page `__yard` debug hook and real key/pointer input.
 */
import { createRequire } from 'node:module';
import path from 'node:path';
import { mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const arg = (k, d) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : d; };
const require = createRequire(path.join(arg('--modules', process.cwd()), 'x.js'));
const { chromium } = require('playwright-core');
const here = path.dirname(fileURLToPath(import.meta.url));
const URL_ = arg('--url', 'http://127.0.0.1:4178');
const OUT = path.resolve(arg('--out', path.join(here, '../../art/previews/qingxi-training-yard-v1/demo')));
mkdirSync(OUT, { recursive: true });
const wait = ms => new Promise(r => setTimeout(r, ms));

const browser = await chromium.launch({ executablePath: arg('--chrome'), args: ['--use-angle=d3d11', '--enable-gpu', '--ignore-gpu-blocklist', '--autoplay-policy=no-user-gesture-required'] });
async function page(viewport, mobile = false) {
  const ctx = await browser.newContext({ viewport, deviceScaleFactor: 1, hasTouch: mobile, isMobile: mobile, serviceWorkers: 'block' });
  const p = await ctx.newPage();
  const errors = [];
  p.on('pageerror', e => errors.push(String(e)));
  p.on('console', m => m.type() === 'error' && errors.push(m.text()));
  await p.goto(URL_);
  await p.waitForFunction(() => globalThis.__yard && document.getElementById('loading').hidden, null, { timeout: 120000 });
  await wait(1500);
  return { p, errors, ctx };
}
const shot = async (p, name) => { await p.screenshot({ path: path.join(OUT, name) }); console.log('SHOT', name); };

// ---------------- desktop
{
  const { p, errors, ctx } = await page({ width: 1280, height: 720 });
  await shot(p, '01-village-approach-eye-1280x720.png');
  await p.evaluate(() => __yard.teleport(0, 5.4, 0, -0.04)); await wait(900);
  await shot(p, '02-shelter-entrance-eye-1280x720.png');
  await p.evaluate(() => __yard.teleport(-0.2, 1.4, 38, -0.12)); await wait(900);
  await shot(p, '03-under-shelter-eye-1280x720.png');
  // walk with real keys from the steps to the qi post and open the chooser with E
  await p.evaluate(() => __yard.teleport(-2.0, 2.2, 0, -0.1)); await wait(300);
  await p.keyboard.down('KeyW'); await wait(500); await p.keyboard.up('KeyW'); await wait(300);
  await p.keyboard.press('KeyE'); await wait(600);
  await shot(p, '04-qi-post-chooser-1280x720.png');
  await p.click('#pick-qi');
  // follow the breath with the real Space key
  // follow the guide ring the page shows: hold through 吸/停, release for 呼/歇
  const t0 = Date.now(); let held = false;
  const breathe = async until => { while (Date.now() - t0 < until) { const s = await p.evaluate(() => __yard.state().session);
    if (!s || s.done) return; const want = s.phase === 'inhale' || s.phase === 'hold';
    if (want !== held) { held = want; await (want ? p.keyboard.down('Space') : p.keyboard.up('Space')); } await wait(15); } };
  await breathe(4300); await shot(p, '05-qi-breathing-inhale-1280x720.png');
  await breathe(7600); await shot(p, '06-qi-breathing-exhale-1280x720.png');
  await breathe(28000); if (held) await p.keyboard.up('Space'); await wait(800);
  await shot(p, '07-qi-result-1280x720.png');
  const qi = await p.evaluate(() => document.getElementById('result-grade').textContent);
  // mortal: qi locked, martial open
  await p.evaluate(() => { __yard.leave(); __yard.setRoots(false); __yard.teleport(2.0, 1.2, 0, -0.1); }); await wait(400);
  await p.keyboard.press('KeyE'); await wait(500);
  await shot(p, '08-mortal-chooser-qi-locked-1280x720.png');
  await p.click('#pick-body'); await wait(1200);
  // block with real A/S/D keys timed from the session clock
  const keyOf = { left: 'KeyA', right: 'KeyD', low: 'KeyS' };
  let done = false, n = 0, shotMid = false;
  while (!done) {
    const s = await p.evaluate(() => __yard.state().session);
    if (!s || s.done) { done = true; break; }
    if (!shotMid && s.next && s.next.eta < 0.35 && s.next.eta > 0.15 && s.judged >= 2) { await shot(p, '09-block-windup-1280x720.png'); shotMid = true; }
    if (s.next && s.next.eta < 0.04 && s.judged === n) { if (n !== 6) await p.keyboard.press(keyOf[s.next.side]); n++; }
    await wait(8);
  }
  await wait(1200);
  await shot(p, '10-block-result-1280x720.png');
  const body = await p.evaluate(() => document.getElementById('result-detail').textContent);
  console.log('RESULT qi:', qi, '| body:', body, '| errors:', JSON.stringify(errors));
  await ctx.close();
}
// ---------------- phone landscape (touch)
{
  const { p, errors, ctx } = await page({ width: 844, height: 390 }, true);
  await shot(p, '11-mobile-approach-844x390.png');
  await p.evaluate(() => { __yard.setRoots(true); __yard.teleport(2.0, 1.2, 0, -0.1); }); await wait(500);
  await p.tap('#interact'); await wait(500);
  await shot(p, '12-mobile-chooser-844x390.png');
  await p.tap('#pick-body'); await wait(3600);
  await shot(p, '13-mobile-block-844x390.png');
  await p.evaluate(() => __yard.start('qi')); await wait(1500);
  await p.dispatchEvent('#hold', 'pointerdown', { pointerId: 1, isPrimary: true }); await wait(2500);
  await shot(p, '14-mobile-qi-hold-844x390.png');
  console.log('MOBILE errors:', JSON.stringify(errors));
  await ctx.close();
}
await browser.close();
