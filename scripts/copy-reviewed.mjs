// Copy review stamp, so a commit that changes copy goes through a review first.
//   node scripts/copy-reviewed.mjs            the copywriting skill's last step: record the reviewed copy
//   node scripts/copy-reviewed.mjs --check    .githooks/pre-commit: stop when copy changed since then
//   node scripts/copy-reviewed.mjs --install  npm install (prepare): point this repo's git at .githooks
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { chmodSync, existsSync, readFileSync, realpathSync, writeFileSync } from 'node:fs';

const COPY = ['src/i18n', 'src/content'];
const HOOK = '.githooks/pre-commit';
const git = (...args) => spawnSync('git', args, { encoding: 'utf8' });
const mode = process.argv[2];

if (mode === '--install') {
  // Only when this folder is the repo root, never a repo it happens to sit in.
  const top = git('rev-parse', '--show-toplevel');
  if (top.status === 0 && realpathSync(top.stdout.trim()) === realpathSync('.') && existsSync(HOOK)) {
    git('config', 'core.hooksPath', '.githooks');
    chmodSync(HOOK, 0o755);
  }
  process.exit(0);
}

const diff = git('diff', 'HEAD', '--no-color', '--', ...COPY);
// No commit yet (or no git): nothing to compare against, and the first commit goes through.
if (diff.status !== 0) {
  if (!mode) console.log('No commit yet; the first commit needs no copy review.');
  process.exit(0);
}
const stamp = git('rev-parse', '--git-path', 'wcgw-copy-reviewed').stdout.trim();
const hash = createHash('sha256').update(diff.stdout).digest('hex');

if (mode === '--check') {
  if (!diff.stdout || (existsSync(stamp) && readFileSync(stamp, 'utf8').trim() === hash)) process.exit(0);
  const files = git('diff', 'HEAD', '--name-only', '--', ...COPY)
    .stdout.trim()
    .split('\n');
  console.error(
    `Copy changed since the last copy review: ${files.join(', ')}\n` +
      'Run the copywriting skill on it (/copywriting in Claude Code, or .claude/skills/copywriting/SKILL.md), then commit again.',
  );
  process.exit(1);
}

writeFileSync(stamp, `${hash}\n`);
console.log(
  diff.stdout
    ? 'Copy review recorded; the next commit goes through.'
    : 'No copy changes since the last commit.',
);
