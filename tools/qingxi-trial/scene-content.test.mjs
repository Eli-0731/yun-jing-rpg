import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile, stat } from 'node:fs/promises';
import { collaboratorModels } from './scene-content.mjs';

test('entrance route uses reviewed collaborator meshes in reachable areas', async () => {
  assert.equal(collaboratorModels.length, 22);
  assert.equal(new Set(collaboratorModels.map(model => model.id)).size, collaboratorModels.length);
  assert.deepEqual(new Set(collaboratorModels.map(model => model.owner)),
    new Set(['Eli-0731', 'Johnnnny0823', 'joshsu54']));
  for (const model of collaboratorModels) {
    assert.ok(model.x >= -7.4 && model.x <= 20, `${model.id} outside trial ground`);
    assert.ok(model.z >= -12 && model.z <= 12, `${model.id} outside trial ground`);
    assert.ok(model.size > 0 && model.size <= 7);
    const asset = new URL(model.path, import.meta.url);
    assert.ok((await stat(asset)).size > 1000, `${model.id} is still an LFS pointer`);
    assert.equal((await readFile(asset)).toString('ascii', 0, 4), 'glTF', `${model.id} is not GLB`);
  }
});

test('the training yard keeps its real scale and leaves the village gate walkable', async () => {
  const stone = collaboratorModels.find(model => model.id === 'training-stone');
  const shelter = collaboratorModels.find(model => model.id === 'training-shelter');
  const modelInfo = JSON.parse(await readFile(new URL('../../art/exports/qingxi-training-yard-v1/engraved-training-stone_model_info.json', import.meta.url), 'utf8'));
  const originalDiameter = Math.max(...modelInfo.dimensions_m.slice(0, 2));
  assert.equal(stone.axis, 'width');
  assert.ok(Math.abs(stone.size - originalDiameter) < .1, 'stone should be near its authored 2 m width, not enlarged by its 28 cm height');
  assert.ok(stone.x + stone.size / 2 < -1.1, 'stone must not cover the gate approach corridor');
  assert.ok(shelter.x + shelter.size / 2 < -1.1, 'shelter must not cover the gate approach corridor');
  const shelterInfo = JSON.parse(await readFile(new URL('../../art/exports/qingxi-training-yard-v1/training-shelter_model_info.json', import.meta.url), 'utf8'));
  const shelterDepth = shelter.size * shelterInfo.dimensions_m[1] / Math.max(...shelterInfo.dimensions_m.slice(0, 2));
  const stoneDepth = stone.size * modelInfo.dimensions_m[1] / originalDiameter;
  assert.ok(shelter.z + shelterDepth / 2 + .4 < stone.z - stoneDepth / 2,
    'the separate training stone must not intersect the shelter');
});
