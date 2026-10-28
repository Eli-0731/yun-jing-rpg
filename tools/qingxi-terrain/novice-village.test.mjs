import test from 'node:test';
import assert from 'node:assert/strict';
import { loadLayout, buildConfig } from './village-checks.mjs';

const layout = loadLayout();
const nodes = Object.fromEntries(layout.nodes.map(n => [n.id, n]));
const padEdge = (p, x, z) => Math.max(Math.abs(x - p.x) - p.halfX, Math.abs(z - p.z) - p.halfZ);

test('roads connect known nodes and have a width', () => {
  for (const e of layout.edges) {
    assert.ok(nodes[e.from] && nodes[e.to], e.id);
    assert.ok(e.width > 0, e.id);
  }
});

test('every checkpoint and route stop exists', () => {
  const names = new Set(layout.checkpoints.map(c => c.name));
  for (const c of layout.checkpoints) assert.ok(nodes[c.node], c.name);
  for (const r of layout.route) assert.ok(names.has(r), r);
});

test('pads do not overlap, so each zone keeps one flat height', () => {
  for (let i = 0; i < layout.pads.length; i++)
    for (let j = i + 1; j < layout.pads.length; j++) {
      const a = layout.pads[i], b = layout.pads[j];
      const gapX = Math.abs(a.x - b.x) - a.halfX - b.halfX, gapZ = Math.abs(a.z - b.z) - a.halfZ - b.halfZ;
      assert.ok(gapX > 0 || gapZ > 0, `${a.id} overlaps ${b.id}`);
    }
});

// Walking a road from one pad to the next must stay well under the 35° controller limit.
test('the climb between neighbouring pads along each road is gentle', () => {
  for (const e of layout.edges) {
    const a = nodes[e.from], b = nodes[e.to];
    const padA = layout.pads.find(p => padEdge(p, a.x, a.z) <= 0);
    const padB = layout.pads.find(p => padEdge(p, b.x, b.z) <= 0);
    if (!padA || !padB || padA === padB) continue;
    const len = Math.hypot(b.x - a.x, b.z - a.z);
    let outside = 0;   // road length that lies between the two pads
    for (let i = 0; i <= 200; i++) {
      const t = i / 200, x = a.x + (b.x - a.x) * t, z = a.z + (b.z - a.z) * t;
      if (padEdge(padA, x, z) > 0 && padEdge(padB, x, z) > 0) outside += len / 200;
    }
    const grade = Math.atan2(Math.abs(padA.height - padB.height), Math.max(outside, 0.5)) * 180 / Math.PI;
    assert.ok(grade < 20, `${e.id}: ${grade.toFixed(1)}° between ${padA.id} and ${padB.id}`);
  }
});

test('the check config mirrors the layout', () => {
  const config = buildConfig(layout);
  assert.equal(config.roads.length, layout.edges.length);
  assert.deepEqual(config.route, layout.route);
  assert.ok(config.checkpoints.every(c => Number.isFinite(c.x) && Number.isFinite(c.z)));
});
