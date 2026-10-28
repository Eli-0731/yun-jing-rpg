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

const roadDistance = (x, z) => Math.min(...layout.edges.map(e => {
  const a = nodes[e.from], b = nodes[e.to];
  const abx = b.x - a.x, abz = b.z - a.z, len2 = abx * abx + abz * abz;
  const t = len2 ? Math.max(0, Math.min(1, ((x - a.x) * abx + (z - a.z) * abz) / len2)) : 0;
  return Math.hypot(x - a.x - abx * t, z - a.z - abz * t) - e.width / 2;
}));

test('every building and prop stands on a flat pad', () => {
  for (const p of layout.placements)
    assert.ok(layout.pads.some(pad => padEdge(pad, p.x, p.z) <= -0.5), `${p.id} is not inside a pad`);
});

test('herbs grow in open ground, off roads and pads', () => {
  for (const h of layout.herbs) {
    assert.ok(roadDistance(h.x, h.z) > 2, `${h.id} is on or next to a road`);
    assert.ok(layout.pads.every(pad => padEdge(pad, h.x, h.z) > 2), `${h.id} is on a pad`);
    assert.ok(Math.abs(h.x) < 44 && Math.abs(h.z) < 44, `${h.id} is outside the village boundary`);
  }
});

const creekDistance = (x, z) => {
  const p = layout.creek.points;
  let best = Infinity;
  for (let i = 0; i + 3 < p.length; i += 2) {
    const ax = p[i], az = p[i + 1], bx = p[i + 2], bz = p[i + 3];
    const abx = bx - ax, abz = bz - az, len2 = abx * abx + abz * abz;
    const t = len2 ? Math.max(0, Math.min(1, ((x - ax) * abx + (z - az) * abz) / len2)) : 0;
    best = Math.min(best, Math.hypot(x - ax - abx * t, z - az - abz * t));
  }
  return best;
};

test('the creek keeps clear of pads, roads, herbs and buildings', () => {
  const c = layout.creek;
  assert.ok(c && c.points.length >= 4 && c.points.length % 2 === 0, 'creek needs x,z pairs');
  const clear = c.width / 2 + c.bank;
  // Sample the creek every half metre against every pad and road.
  const p = c.points;
  for (let i = 0; i + 3 < p.length; i += 2)
    for (let t = 0; t <= 1; t += 0.05) {
      const x = p[i] + (p[i + 2] - p[i]) * t, z = p[i + 1] + (p[i + 3] - p[i + 1]) * t;
      for (const pad of layout.pads) assert.ok(padEdge(pad, x, z) > clear - 1, `creek at ${x.toFixed(1)},${z.toFixed(1)} cuts into ${pad.id}`);
      assert.ok(roadDistance(x, z) > c.width / 2, `creek at ${x.toFixed(1)},${z.toFixed(1)} crosses a road`);
    }
  for (const h of layout.herbs) assert.ok(creekDistance(h.x, h.z) > clear, `${h.id} is on the creek bank`);
  for (const pl of layout.placements) assert.ok(creekDistance(pl.x, pl.z) > clear, `${pl.id} is in the creek`);
  assert.ok(creekDistance(c.crossing.x, c.crossing.z) < 0.5, 'the crossing must sit on the creek');
});

test('the check config mirrors the layout', () => {
  const config = buildConfig(layout);
  assert.equal(config.roads.length, layout.edges.length);
  assert.deepEqual(config.route, layout.route);
  assert.ok(config.checkpoints.every(c => Number.isFinite(c.x) && Number.isFinite(c.z)));
});
