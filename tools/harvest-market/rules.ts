import content from '../../packages/content/harvest-market-v1.json';

// 第 4 天・第一次收成 (work pack 02-B): pull → sort → sell, as pure rules. No Unity, no network, no randomness.
// apps/game/Assets/YunJing/Runtime/HarvestMarket/HarvestMarketSim.cs is the C# port; tests/harvest-market.test.ts
// checks both against packages/content/harvest-market-v1.json and the replay fixture.

export type Grade = 'top' | 'mid' | 'low';
export const GRADES: readonly Grade[] = ['top', 'mid', 'low'];   // best first; index = how far down
export const harvestContent = content;

export interface HarvestInput {
  day: number;
  fieldId: string;
  /** Seconds each plant took to pull out, in field order. */
  pullSeconds: number[];
  /** Which of the three bundles (top / mid / low) the player dropped each plant on, in field order. */
  bins: Grade[];
  /** Sell (true) or keep (false) for each bundle, in the order bundleUp returns them. */
  sell: boolean[];
}
export interface Bundle { bin: Grade; plants: number[]; grades: Grade[]; quality: Grade }
export interface SettledBundle extends Bundle { sold: boolean; coins: number; line: string | null; /** every plant really is the bundle grade */ sorted: boolean }
export interface HarvestResult {
  plants: Grade[];
  bundles: SettledBundle[];
  totalCoins: number;
  kept: { item: string; quality: Grade; quantity: number }[];
  lines: string[];
  events: {
    'harvest.completed': { fieldId: string; plants: { quality: Grade }[] };
    'market.sold': { day: number; bundles: { quality: Grade; sold: boolean; coins: number }[]; totalCoins: number };
  };
}

export class HarvestRuleError extends Error { constructor(public code: string) { super(code); } }
const fail = (code: string): never => { throw new HarvestRuleError(code); };

const rank = (g: Grade) => GRADES.indexOf(g);
const grade = (id: string) => content.grades.find(g => g.id === id) ?? fail('GRADE');
export const fieldPlants = (fieldId: string): Grade[] =>
  (content.fields.find(f => f.id === fieldId) ?? fail('FIELD')).plants as Grade[];

/** Pulling faster than pullSafeSeconds snaps the root: one grade down, and the lowest grade stays where it is. */
export function pullGrade(original: Grade, seconds: number): Grade {
  if (!GRADES.includes(original)) fail('GRADE');
  if (typeof seconds !== 'number' || !Number.isFinite(seconds) || seconds < 0) fail('PULL_TIME');
  return seconds >= content.pull.pullSafeSeconds ? original : GRADES[Math.min(rank(original) + 1, GRADES.length - 1)];
}

export function harvest(fieldId: string, pullSeconds: number[]): Grade[] {
  const plants = fieldPlants(fieldId);
  if (!Array.isArray(pullSeconds) || pullSeconds.length !== plants.length) fail('PULL_COUNT');
  return plants.map((g, i) => pullGrade(g, pullSeconds[i]));
}

/** Plants dropped on the same bundle are tied in field order, bundleSize to a bundle; bundles are listed top, mid, low. */
export function bundleUp(plants: Grade[], bins: Grade[]): Bundle[] {
  if (!Array.isArray(bins) || bins.length !== plants.length) fail('SORT_COUNT');
  if (bins.some(b => !GRADES.includes(b))) fail('SORT_BIN');
  const bundles: Bundle[] = [];
  for (const bin of GRADES) {
    const mine = plants.map((_, i) => i).filter(i => bins[i] === bin);
    for (let at = 0; at < mine.length; at += content.bundleSize) {
      const idx = mine.slice(at, at + content.bundleSize), grades = idx.map(i => plants[i]);
      bundles.push({ bin, plants: idx, grades, quality: grades.reduce((w, g) => (rank(g) > rank(w) ? g : w)) });
    }
  }
  return bundles;
}

export const demandBonus = (day: number, item: string = content.item) =>
  content.dailyDemand.filter(d => d.day === day && d.item === item).reduce((sum, d) => sum + d.bonusPerBundle, 0);

/** Each plant is a third of its grade's bundle price (plus a third of today's bonus); a part bundle rounds up, so it is never 0. */
export function bundleCoins(grades: Grade[], day: number): number {
  if (grades.length === 0) return 0;
  const bonus = demandBonus(day);
  return Math.ceil(grades.reduce((sum, g) => sum + grade(g).bundlePrice + bonus, 0) / content.bundleSize);
}

export function settle(day: number, bundles: Bundle[], sell: boolean[]): Omit<HarvestResult, 'plants' | 'events'> {
  if (!Number.isInteger(day) || day < 1) fail('DAY');
  if (!Array.isArray(sell) || sell.length !== bundles.length || sell.some(s => typeof s !== 'boolean')) fail('SELL_COUNT');
  const settled: SettledBundle[] = bundles.map((b, i) => {
    const lower = b.grades.some(g => rank(g) > rank(b.bin)), higher = b.grades.some(g => rank(g) < rank(b.bin));
    // A cleanly sorted bundle earns sortBonus on top; a mixed one is simply paid by real grade (no penalty).
    const sorted = !lower && !higher, sold = sell[i], coins = sold ? bundleCoins(b.grades, day) + (sorted ? content.sortBonus.perBundle : 0) : 0;
    return { ...b, sold, coins, sorted, line: !sold ? null : lower ? 'mixed-lower' : higher ? 'mixed-higher' : null };
  });
  const keptCount = new Map<Grade, number>();
  for (const b of settled) if (!b.sold) for (const g of b.grades) keptCount.set(g, (keptCount.get(g) ?? 0) + 1);
  const sold = settled.filter(b => b.sold), lines: string[] = [];
  const say = (id: string | null) => { if (id && !lines.includes(id)) lines.push(id); };
  if (sold.length === 0) say('kept-all');
  else {
    for (const b of sold) say(b.line);
    if (sold.some(b => b.grades.length === content.bundleSize && b.grades.every(g => g === 'top'))) say('all-top');
    if (demandBonus(day) > 0) say('demand-bonus');
    say('thanks');
  }
  return {
    bundles: settled,
    totalCoins: settled.reduce((sum, b) => sum + b.coins, 0),
    kept: GRADES.filter(g => keptCount.has(g)).map(g => ({ item: content.item, quality: g, quantity: keptCount.get(g)! })),
    lines,
  };
}

/** The whole visit: field → sieve → stall. Returns what the two Unity panels emit as events. */
export function runHarvestMarket(input: HarvestInput): HarvestResult {
  const plants = harvest(input.fieldId, input.pullSeconds);
  const result = settle(input.day, bundleUp(plants, input.bins), input.sell);
  return {
    plants, ...result,
    events: {
      'harvest.completed': { fieldId: input.fieldId, plants: plants.map(quality => ({ quality })) },
      'market.sold': {
        day: input.day, totalCoins: result.totalCoins,
        bundles: result.bundles.map(b => ({ quality: b.quality, sold: b.sold, coins: b.coins })),
      },
    },
  };
}

export const lineText = (id: string) => (content.lines.find(l => l.id === id) ?? fail('LINE')).text;
