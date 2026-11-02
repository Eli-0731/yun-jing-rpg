import { Grade, HarvestInput, runHarvestMarket } from './rules';

// Replay cases shared by tests/harvest-market.test.ts and the Unity parity check (HarvestMarketSceneBuilder.VerifySim).
const SLOW = 1.2, FAST = 0.3;
const field = 'TY_Field01';   // original grades: mid top low mid top mid
const sorted: Grade[] = ['mid', 'top', 'low', 'mid', 'top', 'mid'];

export const harvestCases: { name: string; input: HarvestInput }[] = [
  { name: 'careful-sort-sell-all-day4', input: { day: 4, fieldId: field, pullSeconds: Array(6).fill(SLOW), bins: sorted, sell: [true, true, true] } },
  { name: 'careful-sort-sell-all-day5', input: { day: 5, fieldId: field, pullSeconds: Array(6).fill(SLOW), bins: sorted, sell: [true, true, true] } },
  // The recording's run: one top pulled too fast (now mid), one low dropped on the mid bundle; sell two, keep one.
  { name: 'recorded-run', input: { day: 4, fieldId: field, pullSeconds: [SLOW, FAST, SLOW, SLOW, SLOW, SLOW], bins: ['mid', 'mid', 'mid', 'mid', 'top', 'mid'], sell: [true, true, false] } },
  { name: 'all-rushed', input: { day: 4, fieldId: field, pullSeconds: Array(6).fill(FAST), bins: ['low', 'mid', 'low', 'low', 'mid', 'low'], sell: [true, true, true] } },
  { name: 'keep-everything', input: { day: 4, fieldId: field, pullSeconds: Array(6).fill(SLOW), bins: sorted, sell: [false, false, false] } },
  { name: 'everything-on-one-bundle', input: { day: 4, fieldId: field, pullSeconds: Array(6).fill(SLOW), bins: Array(6).fill('top'), sell: [true, true] } },
  { name: 'single-low-plant', input: { day: 4, fieldId: field, pullSeconds: Array(6).fill(SLOW), bins: ['mid', 'top', 'low', 'mid', 'top', 'mid'], sell: [false, false, true] } },
];

export const harvestTraceCases = () => harvestCases.map(c => {
  const r = runHarvestMarket(c.input);
  return {
    name: c.name, ...c.input,
    plants: r.plants,
    bundles: r.bundles.map(b => ({ bin: b.bin, grades: b.grades, quality: b.quality, sold: b.sold, coins: b.coins, line: b.line ?? '', sorted: b.sorted })),
    totalCoins: r.totalCoins, kept: r.kept, lines: r.lines,
  };
});
