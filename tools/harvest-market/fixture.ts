import { writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { harvestTraceCases } from './cases';

// npm run build && node dist/tools/harvest-market/fixture.js — rewrites the replay fixture Unity checks HarvestMarketSim.cs against.
const file = join(__dirname, '..', '..', '..', 'tests', 'fixtures', 'harvest-market-trace.json');
writeFileSync(file, JSON.stringify({ cases: harvestTraceCases() }, null, 1) + '\n');
console.log('wrote', file);
