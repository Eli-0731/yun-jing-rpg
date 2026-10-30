// Writes checks/novice-village.json (the QingxiGroundingCheck config) from novice-village.json,
// so roads and checkpoints are described once.
//   node tools/qingxi-terrain/village-checks.mjs          write
//   node tools/qingxi-terrain/village-checks.mjs --check  exit 1 if the config is stale
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const layoutFile = join(here, 'novice-village.json');
const configFile = join(here, 'checks', 'novice-village.json');

export const loadLayout = () => JSON.parse(readFileSync(layoutFile, 'utf8'));

export function buildConfig(layout) {
  const nodes = Object.fromEntries(layout.nodes.map(n => [n.id, n]));
  return {
    scene: 'Assets/YunJing/Generated/QingxiNoviceVillage.unity',
    groundTolerance: 0.05,
    buriedLimit: 0.5,
    maxWalkSlope: 35,
    comfortSlope: 20,
    stepHeight: 0.3,
    roadEdgeAllowance: 0.15,
    grassPattern: 'grass|fern|flower|reed|草',
    roadMeshPattern: 'road|path|trail|approach|路',
    ignorePattern: 'player|cultivator|camera|Body_',
    bakeNavMesh: true,
    roads: layout.edges.map(e => ({ id: e.id, width: e.width, points: [nodes[e.from].x, nodes[e.from].z, nodes[e.to].x, nodes[e.to].z] })),
    checkpoints: layout.checkpoints.map(c => ({ name: c.name, x: nodes[c.node].x, y: 0, z: nodes[c.node].z })),
    route: layout.route,
  };
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const text = JSON.stringify(buildConfig(loadLayout()), null, 1) + '\n';
  if (process.argv.includes('--check')) {
    if (!existsSync(configFile) || readFileSync(configFile, 'utf8') !== text) { console.error('checks/novice-village.json is stale'); process.exit(1); }
    console.log('village check config up to date');
  } else {
    writeFileSync(configFile, text);
    console.log('wrote', configFile);
  }
}
