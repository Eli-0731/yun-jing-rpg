import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile, stat } from 'node:fs/promises';
import { collaboratorModels } from './scene-content.mjs';

test('entrance route uses reviewed collaborator meshes in reachable areas', async () => {
  assert.equal(collaboratorModels.length, 12);
  assert.equal(new Set(collaboratorModels.map(model => model.id)).size, collaboratorModels.length);
  assert.deepEqual(new Set(collaboratorModels.map(model => model.owner)),
    new Set(['Eli-0731', 'Johnnnny0823', 'joshsu54']));
  for (const model of collaboratorModels) {
    assert.ok(model.x >= -7.4 && model.x <= 20, `${model.id} outside trial ground`);
    assert.ok(model.z >= -12 && model.z <= 12, `${model.id} outside trial ground`);
    assert.ok(model.size > 0 && model.size <= 5);
    const asset = new URL(model.path, import.meta.url);
    assert.ok((await stat(asset)).size > 1000, `${model.id} is still an LFS pointer`);
    assert.equal((await readFile(asset)).toString('ascii', 0, 4), 'glTF', `${model.id} is not GLB`);
  }
});
