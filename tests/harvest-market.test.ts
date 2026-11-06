import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { join } from 'node:path';
import {
  bundleCoins, bundleUp, demandBonus, fieldPlants, Grade, GRADES, harvest, harvestContent as c, pullGrade, runHarvestMarket, settle,
} from '../tools/harvest-market/rules';
import { harvestTraceCases } from '../tools/harvest-market/cases';

// 第 4 天・第一次收成 (work pack 02-B): pull, sort, sell — never a loss.
const SAFE = c.pull.pullSafeSeconds, SLOW = SAFE + .4, FAST = SAFE - .5;
const FIELD = 'TY_Field01';
const rejects = (fn: () => unknown, code: string) => assert.throws(fn, (e: any) => e.code === code);

test('the first harvest shows every grade: top 2, mid 3, low 1', () => {
  const plants = fieldPlants(FIELD);
  assert.equal(plants.length, 6);
  assert.deepEqual(GRADES.map(g => plants.filter(p => p === g).length), [2, 3, 1]);
  assert.deepEqual(harvest(FIELD, Array(6).fill(SLOW)), plants, 'slow pulls keep every original grade');
});

test('pulling too fast drops one grade, and the lowest grade does not drop further', () => {
  assert.equal(pullGrade('top', FAST), 'mid');
  assert.equal(pullGrade('mid', FAST), 'low');
  assert.equal(pullGrade('low', FAST), 'low');
  assert.equal(pullGrade('low', 0), 'low');
  assert.equal(pullGrade('top', SAFE), 'top', 'exactly pullSafeSeconds is safe');
  assert.equal(pullGrade('top', SAFE - 0.01), 'mid');
  assert.deepEqual(harvest(FIELD, Array(6).fill(FAST)), ['low', 'mid', 'low', 'low', 'mid', 'low']);
  rejects(() => pullGrade('top', -1), 'PULL_TIME');
  rejects(() => pullGrade('top', Number.NaN), 'PULL_TIME');
  rejects(() => harvest(FIELD, [1, 1]), 'PULL_COUNT');
  rejects(() => harvest('TY_Field99', Array(6).fill(1)), 'FIELD');
});

test('a plant on the wrong bundle is paid by its real grade, and the stall keeper says so', () => {
  // Real grades: top top top | dropped on the top bundle, but one is actually low.
  const day = 5;   // no demand bonus, so the prices are the plain table
  const mixed = settle(day, bundleUp(['top', 'top', 'low'], ['top', 'top', 'top']), [true]);
  assert.equal(mixed.bundles[0].quality, 'low', 'a mixed bundle is labelled by its worst plant');
  assert.equal(mixed.totalCoins, Math.ceil((5 + 5 + 2) / 3));
  assert.equal(mixed.bundles[0].line, 'mixed-lower');
  assert.ok(mixed.lines.includes('mixed-lower'));
  // A top plant dropped on the low bundle is not lost either.
  const hidden = settle(day, bundleUp(['top', 'low', 'low'], ['low', 'low', 'low']), [true]);
  assert.equal(hidden.totalCoins, Math.ceil((5 + 2 + 2) / 3));
  assert.equal(hidden.bundles[0].line, 'mixed-higher');
  // Correctly sorted bundles say nothing about mixing.
  const clean = settle(day, bundleUp(['mid', 'mid', 'mid'], ['mid', 'mid', 'mid']), [true]);
  assert.equal(clean.bundles[0].line, null); assert.equal(clean.totalCoins, 3 + c.sortBonus.perBundle, 'a clean bundle earns the sort bonus');
  assert.ok(clean.bundles[0].sorted && !mixed.bundles[0].sorted && !hidden.bundles[0].sorted);
});

test('a bundle short of 3 plants is paid pro rata, rounded up', () => {
  for (const g of GRADES) {
    const price = c.grades.find(x => x.id === g)!.bundlePrice;
    assert.equal(bundleCoins([g, g, g], 5), price);
    assert.equal(bundleCoins([g, g], 5), Math.ceil(price * 2 / 3));
    assert.equal(bundleCoins([g], 5), Math.ceil(price / 3));
  }
  assert.equal(bundleCoins(['top'], 5), 2);   // 5/3 → 2
  assert.equal(bundleCoins(['low'], 5), 1);   // 2/3 → 1, never 0
  assert.equal(bundleCoins(['top', 'mid'], 4), Math.ceil((5 + 1 + 3 + 1) / 3));
  // More than bundleSize on one bundle ties a second bundle.
  const b = bundleUp(['mid', 'mid', 'mid', 'mid', 'top', 'low'], Array(6).fill('mid'));
  assert.deepEqual(b.map(x => x.plants), [[0, 1, 2], [3, 4, 5]]);
  assert.ok(b.every(x => x.grades.length <= c.bundleSize));
});

test('day 4 pays +1 per qingling bundle, day 5 does not', () => {
  assert.equal(demandBonus(4), 1);
  assert.equal(demandBonus(5), 0);
  assert.equal(demandBonus(4, 'lotus-herb'), 0);
  const careful = { fieldId: FIELD, pullSeconds: Array(6).fill(SLOW), bins: fieldPlants(FIELD), sell: [true, true, true] };
  const d4 = runHarvestMarket({ ...careful, day: 4 }), d5 = runHarvestMarket({ ...careful, day: 5 });
  // top 2 plants, mid 3, low 1: 5*2/3→4, 3, 2*1/3→1  (day 5) — and each plant earns a third of the +1 on day 4;
  // all three bundles are cleanly sorted, so each also earns the sort bonus.
  const sb = c.sortBonus.perBundle;
  assert.deepEqual(d5.bundles.map(b => b.coins), [4 + sb, 3 + sb, 1 + sb]);
  assert.deepEqual(d4.bundles.map(b => b.coins), [Math.ceil(12 / 3) + sb, 4 + sb, 1 + sb]);
  assert.equal(d4.totalCoins, 9 + 3 * sb); assert.equal(d5.totalCoins, 8 + 3 * sb);
  assert.ok(d4.lines.includes('demand-bonus')); assert.ok(!d5.lines.includes('demand-bonus'));
  // A full top bundle on day 4 is worth 5 + 1, better than the shop's qingling-bundle at 4.
  assert.equal(bundleCoins(['top', 'top', 'top'], 4), 6);
});

test('careful sorting pays more, careless sorting never pays less than the real grades', () => {
  const pulls = Array(6).fill(SLOW), plants = harvest(FIELD, pulls);
  const careful = settle(5, bundleUp(plants, plants), [true, true, true]);
  const dumped = settle(5, bundleUp(plants, Array(6).fill('mid')), [true, true]);
  assert.ok(careful.bundles.every(b => b.sorted));
  assert.ok(careful.totalCoins > dumped.totalCoins, `careful ${careful.totalCoins} > dumped ${dumped.totalCoins}`);
  // Dumped bundles (field order: mid top low | mid top mid) are still paid by every plant's real grade, rounded up.
  assert.deepEqual(dumped.bundles.map(b => b.coins), [Math.ceil((3 + 5 + 2) / 3), Math.ceil((3 + 5 + 3) / 3)]);
  assert.ok(c.sortBonus.perBundle > 0);
});

test('keeping everything pays 0 and every plant stays in the bag', () => {
  const r = runHarvestMarket({ day: 4, fieldId: FIELD, pullSeconds: Array(6).fill(SLOW), bins: fieldPlants(FIELD), sell: [false, false, false] });
  assert.equal(r.totalCoins, 0);
  assert.deepEqual(r.kept, [
    { item: 'qingling-herb', quality: 'top', quantity: 2 },
    { item: 'qingling-herb', quality: 'mid', quantity: 3 },
    { item: 'qingling-herb', quality: 'low', quantity: 1 },
  ]);
  assert.deepEqual(r.lines, ['kept-all']);
  assert.ok(r.events['market.sold'].bundles.every(b => !b.sold && b.coins === 0));
});

test('the lowest grade always pays more than 0, in any bundle, on any day', () => {
  assert.ok(c.grades.every(g => g.bundlePrice > 0));
  for (const day of [1, 4, 5, 10]) for (let n = 1; n <= c.bundleSize; n++)
    assert.ok(bundleCoins(Array(n).fill('low'), day) > 0, `day ${day}, ${n} low`);
  // Worst case play: every plant rushed and dumped on one bundle, everything sold.
  const r = runHarvestMarket({ day: 5, fieldId: FIELD, pullSeconds: Array(6).fill(0), bins: Array(6).fill('low'), sell: [true, true] });
  assert.ok(r.totalCoins > 0 && r.bundles.every(b => b.coins > 0));
});

test('the recorded run: one rushed pull, one misplaced plant, sell two bundles and keep one', () => {
  const r = runHarvestMarket({
    day: 4, fieldId: FIELD, pullSeconds: [SLOW, FAST, SLOW, SLOW, SLOW, SLOW],
    bins: ['mid', 'mid', 'mid', 'mid', 'top', 'mid'], sell: [true, true, false],
  });
  assert.deepEqual(r.plants, ['mid', 'mid', 'low', 'mid', 'top', 'mid']);
  assert.deepEqual(r.bundles.map(b => [b.bin, b.grades.join('+'), b.sold, b.coins]), [
    ['top', 'top', true, 3], ['mid', 'mid+mid+low', true, 4], ['mid', 'mid+mid', false, 0],
  ]);   // the lone top is cleanly sorted (2 + 1); the mixed mid bundle gets no bonus but loses nothing
  assert.equal(r.totalCoins, 7);
  assert.deepEqual(r.kept, [{ item: 'qingling-herb', quality: 'mid', quantity: 2 }]);
  assert.deepEqual(r.lines, ['mixed-lower', 'demand-bonus', 'thanks']);
  assert.deepEqual(r.events['harvest.completed'], { fieldId: FIELD, plants: r.plants.map(quality => ({ quality })) });
  assert.deepEqual(r.events['market.sold'], {
    day: 4, totalCoins: 7,
    bundles: [{ quality: 'top', sold: true, coins: 3 }, { quality: 'low', sold: true, coins: 4 }, { quality: 'mid', sold: false, coins: 0 }],
  });
});

test('malformed input is rejected, and the stall keeper never says more than six lines', () => {
  rejects(() => bundleUp(['top'], ['top', 'mid']), 'SORT_COUNT');
  rejects(() => bundleUp(['top'], ['best' as Grade]), 'SORT_BIN');
  rejects(() => settle(4, bundleUp(['top'], ['top']), []), 'SELL_COUNT');
  rejects(() => settle(0, [], []), 'DAY');
  assert.ok(c.lines.length <= 6);
  for (const tc of harvestTraceCases()) for (const id of tc.lines) assert.ok(c.lines.some(l => l.id === id), `${tc.name}: line ${id} exists`);
});

test('the replay fixture Unity checks HarvestMarketSim.cs against is current', async () => {
  const fixture = JSON.parse(await readFile(join(__dirname, '..', '..', 'tests', 'fixtures', 'harvest-market-trace.json'), 'utf8'));
  assert.deepEqual(fixture.cases, harvestTraceCases(), 'run: npm run build && node dist/tools/harvest-market/fixture.js');
});

test('the C# port carries the same content', async () => {
  const cs = await readFile(join(__dirname, '..', '..', 'apps', 'game', 'Assets', 'YunJing', 'Runtime', 'HarvestMarket', 'HarvestMarketSim.cs'), 'utf8');
  assert.equal(Number(cs.match(/pullSafeSeconds = ([\d.]+)/)?.[1]), c.pull.pullSafeSeconds);
  assert.equal(Number(cs.match(/bundleSize = (\d+)/)?.[1]), c.bundleSize);
  assert.ok(cs.includes(`item = "${c.item}"`));
  for (const g of c.grades) assert.ok(cs.includes(`("${g.id}", "${g.label}", ${g.bundlePrice}, "${c.looks[g.look as keyof typeof c.looks]}")`), `grade ${g.id}`);
  for (const f of c.fields) assert.ok(cs.includes(`("${f.id}", new[] { ${f.plants.map(p => `"${p}"`).join(', ')} })`), `field ${f.id}`);
  assert.ok(cs.includes(`sortBonus = ${c.sortBonus.perBundle};`), 'sort bonus');
  for (const d of c.dailyDemand) assert.ok(cs.includes(`(${d.day}, "${d.item}", ${d.bonusPerBundle})`), `demand day ${d.day}`);
  for (const l of c.lines) assert.ok(cs.includes(`("${l.id}", "${l.text}")`), `line ${l.id}`);
});
