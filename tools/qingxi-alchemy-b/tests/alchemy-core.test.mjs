// node --test tools/qingxi-alchemy-b/tests
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { MATERIALS, PR31_SOURCE, demoBag, makeBatch } from '../src/materials-adapter.mjs';
import { RECIPES, newState, identify, checkCompound, preview, brew, claimLocal } from '../src/alchemy-core.mjs';

const Q = 'pr31-qinglan_01-r1', C = 'pr31-chilu_01-r1', Y = 'pr31-yumai_01-r1';
const fresh = () => { const s = newState(demoBag()); [Q, C, Y].forEach(b => identify(s, b)); return s; };
const known = (o = {}) => ({ recipe: 'body-bath', picks: { main: Q, aux: C }, process: { main: 'slice', aux: 'soak' }, fire: 'medium', collect: 'filter', ...o });
const research = (o = {}) => ({ recipe: 'body-bath:breath', picks: { main: C, aux: Y }, process: { main: 'soak', aux: 'grind' }, fire: 'gentle', collect: 'filter', ...o });
const qty = (s, id) => s.bag.find(b => b.batchId === id).qty;

test('adapter mirrors PR #31 items without copying the package', () => {
  assert.equal(PR31_SOURCE.commit, 'e6202d7');
  assert.deepEqual(Object.values(MATERIALS).map(m => m.name), ['青溪蘭花莖', '赤露參漿果', '玉脈晶']);
  for (const m of Object.values(MATERIALS)) for (const k of ['element', 'nature', 'purity', 'stability']) assert.ok(m[k] !== undefined, `${m.id}.${k}`);
});

test('batch variation is deterministic, not random', () => {
  assert.deepEqual(makeBatch('chilu-berry', 'x-1', 3), makeBatch('chilu-berry', 'x-1', 3));
});

test('identification is required before compounding', () => {
  const s = newState(demoBag());
  const p = checkCompound(s, 'body-bath', { main: Q, aux: C });
  assert.deepEqual(p.map(x => x.code), ['UNIDENTIFIED', 'UNIDENTIFIED']);
  assert.match(identify(s, Q).text, /木屬、性溫/);
});

test('wrong material gets specific feedback naming the mismatch', () => {
  const s = fresh();
  const [p] = checkCompound(s, 'body-bath', { main: Q, aux: Y });
  assert.equal(p.code, 'WRONG_MATERIAL');
  assert.match(p.message, /玉脈晶是金屬（要火屬）、性寒（要溫性）/);
  const r = brew(s, known({ picks: { main: Q, aux: Y } }));
  assert.equal(r.ok, false); assert.equal(qty(s, Y), 2, 'nothing consumed on a refused compound');
});

test('known recipe always succeeds with correct materials, for every choice combination', () => {
  for (const main of ['slice', 'grind', 'soak']) for (const aux of ['slice', 'grind', 'soak'])
    for (const fire of ['gentle', 'medium', 'strong']) for (const collect of ['filter', 'direct']) {
      const r = brew(fresh(), known({ process: { main, aux }, fire, collect }));
      assert.equal(r.success, true, `${main}/${aux}/${fire}/${collect}`);
      assert.equal(r.product.quantity, 1);
    }
});

test('choices change potency and stability, and the preview matches the brew', () => {
  const s = fresh();
  const a = preview(s, known({ fire: 'gentle', collect: 'filter' })), b = preview(s, known({ fire: 'strong', collect: 'direct' }));
  assert.ok(b.potency > a.potency && b.stability < a.stability, JSON.stringify({ a, b }));
  const r = brew(s, known({ fire: 'strong', collect: 'direct' }));
  assert.equal(r.product.potency, b.potency); assert.equal(r.product.stability, b.stability);
});

test('same inputs give the same result (no lottery, no clock)', () => {
  assert.deepEqual(brew(fresh(), research({ fire: 'strong' })), brew(fresh(), research({ fire: 'strong' })));
  const src = readFileSync(new URL('../src/alchemy-core.mjs', import.meta.url), 'utf8').replace(/^\s*\/\/.*$/gm, '');
  assert.doesNotMatch(src, /Math\.random|Date\.now|new Date|setTimeout|performance\.now/);
});

test('research variant succeeds with gentle fire, ground crystal and filtering', () => {
  const r = brew(fresh(), research());
  assert.equal(r.success, true); assert.equal(r.product.item, 'breath-dew');
});

test('research failure explains why and returns part of the materials', () => {
  const s = fresh();
  const r = brew(s, research({ fire: 'strong' }));
  assert.equal(r.success, false); assert.equal(r.stage, 'fire'); assert.match(r.reason, /武火/);
  assert.deepEqual(r.returned.map(x => [x.material, x.qty]), [['chilu-berry', 1], ['yumai-crystal', 1]]);
  assert.equal(qty(s, C), 6 - 3 + 1); assert.equal(qty(s, Y), 2 - 1 + 1);
  assert.ok(preview(s, research({ fire: 'strong' })).warnings.some(w => /武火/.test(w)), 'research note is shown next time');
});

test('unground crystal and unstable mix fail with their own reasons', () => {
  const a = brew(fresh(), research({ process: { main: 'soak', aux: 'soak' } }));
  assert.equal(a.stage, 'process'); assert.match(a.reason, /沒研成粉/);
  const b = brew(fresh(), research({ process: { main: 'grind', aux: 'grind' }, fire: 'medium', collect: 'direct' }));
  assert.equal(b.stage, 'collect'); assert.match(b.reason, /穩定度 \d+ 低於 55/); assert.ok(b.returned.length > 0);
  const c = brew(fresh(), research({ process: { main: 'soak', aux: 'slice' } }));
  assert.equal(c.stage, 'process'); assert.match(c.reason, /刀切不動/);
});

test('repeated claim presses do not increase the local result', () => {
  const s = fresh(); const r = brew(s, known());
  const first = claimLocal(s, r, 'req-1');
  assert.equal(first.ok, true); assert.equal(first.demo, true);
  for (let i = 0; i < 5; i++) assert.equal(claimLocal(s, r, 'req-1').replayed, true);
  assert.equal(claimLocal(s, r, 'req-2').code, 'ALREADY_CLAIMED');
  assert.equal(s.products.length, 1); assert.equal(s.products[0].official, false);
  const other = brew(s, known());
  assert.equal(claimLocal(s, other, 'req-1').code, 'IDEMPOTENCY_CONFLICT');
});

test('failed brews cannot be claimed; bound materials bind the product', () => {
  const s = fresh(); const r = brew(s, research({ fire: 'strong' }));
  assert.equal(claimLocal(s, r, 'req-x').code, 'NOTHING_TO_CLAIM');
  const t = newState([{ ...makeBatch('qinglan-stem', 'b-q', 1), bound: true }, makeBatch('chilu-berry', 'b-c', 2)]);
  identify(t, 'b-q'); identify(t, 'b-c');
  assert.equal(brew(t, known({ picks: { main: 'b-q', aux: 'b-c' } })).product.bound, true);
});

test('recipes expose the server mapping the contract relies on', () => {
  assert.equal(RECIPES['body-bath'].serverRecipe, 'body-bath');
  assert.equal(RECIPES['body-bath:breath'].serverRecipe, null);
});
