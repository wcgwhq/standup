#!/usr/bin/env node
// npm run verify: the gate before "done". Formatting, then the whole build with its checks.
// A pass prints nothing. A failure prints the first failing step's output, without colors.
import { spawnSync } from 'node:child_process';
import { stripVTControlCharacters } from 'node:util';

const env = { ...process.env, NO_COLOR: '1', FORCE_COLOR: '0', CI: '1' };

for (const script of ['format:check', 'build']) {
  const run = spawnSync('npm', ['run', '--silent', script], {
    env,
    encoding: 'utf8',
    maxBuffer: 1 << 28,
    shell: process.platform === 'win32',
  });
  if (run.status === 0) continue;
  process.stderr.write(stripVTControlCharacters(`npm run ${script} failed:\n${run.stdout}${run.stderr}`));
  process.exit(run.status ?? 1);
}
