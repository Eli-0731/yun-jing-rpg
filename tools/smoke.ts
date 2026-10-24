import assert from 'node:assert/strict';
import { randomUUID } from 'node:crypto';
async function main() {
  const base = 'http://127.0.0.1:4310/v1';
  const health = await (await fetch(`${base}/health`)).json() as any;
  assert.equal(health.mode, 'local', 'Smoke writes test data only in local mode');
  const alias = `smoke-${randomUUID().slice(0,8)}`;
  const login = await (await fetch(`${base}/auth/local`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ alias }) })).json() as any;
  const headers = { 'Content-Type': 'application/json', Authorization: `Bearer ${login.token}` };
  const body = JSON.stringify({ requestId: randomUUID(), action: { kind: 'birth' } });
  const request = () => fetch(`${base}/actions`, { method: 'POST', headers, body }).then(async r => { assert.equal(r.status,201); return r.json() as any; });
  const first = await request(); assert.ok(first.birthAssigned); assert.equal(first.birth,null); assert.equal(first.player.roots,null); assert.deepEqual(await request(), first);
  console.log(`PASS: ${alias}, one birth, durable receipt replay, content ${health.contentVersion}`);
}
main().catch(error => { console.error(error.message); process.exitCode=1; });
