import { test } from 'node:test';
import assert from 'node:assert/strict';
import { makeRoadBlocks, makeLeftVergeBlocks, makeMeadowBlock, meadowBlocks, roadRoute } from './road-tiles.mjs';

test('short road blocks vary both edges', () => {
  const blocks = makeRoadBlocks();
  assert.equal(blocks.length, roadRoute.length - 1);
  assert.equal(new Set(blocks.map(block => block.variant)).size, 3);
  const straight = blocks[4].stations;
  assert.ok(new Set(straight.map(s => s.left[0].toFixed(3))).size > 2);
  assert.ok(new Set(straight.map(s => s.right[0].toFixed(3))).size > 2);
  for (const block of blocks) assert.ok(block.stations.flatMap(s => [...s.left, ...s.right]).every(Number.isFinite));
  for (let i = 1; i < blocks.length; i++) {
    for (const side of ['left', 'right']) for (let axis = 0; axis < 3; axis++) {
      assert.ok(Math.abs(blocks[i - 1].stations.at(-1)[side][axis] - blocks[i].stations[0][side][axis]) < 1e-9);
    }
  }
});

test('meadow patches are separate irregular pieces', () => {
  assert.equal(meadowBlocks.length, 3);
  for (const block of meadowBlocks) {
    const points = makeMeadowBlock(block);
    assert.equal(points.length, 26);
    assert.ok(points.flat().every(Number.isFinite));
  }
});

test('left verge is continuous and gently curved, without pointed circular cuts', () => {
  const pieces = makeLeftVergeBlocks();
  assert.equal(pieces.length, 6);
  for (let i = 1; i < pieces.length; i++) assert.deepEqual(pieces[i - 1].at(-1), pieces[i][0]);
  const edge = pieces.flatMap(piece => piece.slice(0, -1).map(station => station.right[0]));
  assert.ok(Math.max(...edge) - Math.min(...edge) > .3);
  for (let i = 1; i < edge.length; i++) assert.ok(Math.abs(edge[i] - edge[i - 1]) < .15);
});
