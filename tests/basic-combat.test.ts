import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';
import { test } from 'node:test';

// The basic combat rules are plain .mjs beside their tools; this runs their suite as part of npm test.
test('basic combat rules', () => {
  execFileSync(process.execPath, ['--test', resolve(process.cwd(), 'tools/basic-combat/basic-combat-rules.test.mjs')], { stdio: 'pipe' });
});
