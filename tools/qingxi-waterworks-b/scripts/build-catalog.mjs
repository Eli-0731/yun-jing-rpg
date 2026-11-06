// Build data/catalog.json from the exported model_info.json files (ports, footprint cells, author, status).
//   node tools/qingxi-waterworks-b/scripts/build-catalog.mjs
// The rules core only reads data/catalog.json, so tests and the browser never touch art/exports directly.
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const ROOT = new URL('../../../', import.meta.url);
const EXPORTS = new URL('art/exports/qingxi-waterworks-b/', ROOT);
const OUT = new URL('../data/catalog.json', import.meta.url);

// Gameplay data per piece: kind, local demo cost, water efficiency (share of flow that arrives at the out port).
const PLAY = {
  'B02': { kind: 'straight', cost: { stone: 2 }, eff: 1.0 },
  'B02-V02': { kind: 'straight', cost: { stone: 2 }, eff: 0.95, note: '牆頂略低於水面，會滲一些水' },
  'B02-V03': { kind: 'straight', cost: { stone: 3 }, eff: 1.0 },
  'B02-V04': { kind: 'straight', cost: { stone: 1 }, eff: 0.99 },
  'B02-V05': { kind: 'discharge', cost: { stone: 2 }, eff: 1.0 },
  'B03': { kind: 'bend', side: 'right', cost: { stone: 3 }, eff: 0.97 },
  'B03-V02': { kind: 'bend', side: 'right', cost: { stone: 4, timber: 1 }, eff: 0.985 },
  'B03-V03': { kind: 'bend', side: 'left', cost: { stone: 3, timber: 1 }, eff: 0.975 },
  'B03-V04': { kind: 'bend', side: 'left', cost: { stone: 3 }, eff: 0.97 },
  'B04': { kind: 'tee', cost: { stone: 3, timber: 1 }, eff: 0.97 },
  'B04-V02': { kind: 'tee', cost: { stone: 4 }, eff: 0.98 },
  'B05': { kind: 'gate', cost: { timber: 2, bronze: 1 }, eff: 0.99 },
  'B07': { kind: 'patch', crack: 'wall', cost: { mortar: 1 } },
  'B07-V02': { kind: 'patch', crack: 'corner', cost: { mortar: 1 } },
  'B07-V03': { kind: 'patch', crack: 'floor', cost: { mortar: 1 } },
};
const SCENERY = ['F01', 'B01', 'B06', 'B08', 'B09', 'B10', 'B10-V02', 'B10-V03', 'B11', 'B12'];

const pieces = {}, scenery = {};
for (const id of [...Object.keys(PLAY), ...SCENERY]) {
  const m = JSON.parse(readFileSync(new URL(`${id}/model_info.json`, EXPORTS), 'utf8'));
  const base = {
    id, name: m.name, author: m.author, status: m.status, tris: m.stats?.tris,
    glb: `art/exports/qingxi-waterworks-b/${id}/${m.exports.glb}`,
    waterGlb: m.exports.water_glb ? `art/exports/qingxi-waterworks-b/${id}/${m.exports.water_glb}` : null,
  };
  if (PLAY[id]) {
    pieces[id] = {
      ...base, ...PLAY[id],
      ports: (m.ports ?? []).map(p => ({ name: p.name, kind: p.kind, pos: [p.pos[0], p.pos[1]], dir: p.dir })),
      cells: m.footprint_cells ?? [],
    };
  } else scenery[id] = { ...base, ports: (m.ports ?? []).map(p => ({ name: p.name, kind: p.kind, pos: [p.pos[0], p.pos[1]], dir: p.dir })) };
}
writeFileSync(OUT, JSON.stringify({ source: 'art/exports/qingxi-waterworks-b/*/model_info.json', grid: 0.25, pieces, scenery }, null, 1) + '\n');
console.log(`wrote ${fileURLToPath(OUT)}: ${Object.keys(pieces).length} pieces, ${Object.keys(scenery).length} scenery`);
