import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';
import { test } from 'node:test';

// The boar's rules are plain .mjs beside their tools; this runs their suite as part of npm test.
test('zhuo boar encounter rules', () => {
  execFileSync(process.execPath, ['--test', resolve(process.cwd(), 'tools/zhuo-boar/zhuo-boar-rules.test.mjs')], { stdio: 'pipe' });
});
