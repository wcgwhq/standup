// House voice lint on what a reader or agent actually gets: per-page markdown,
// llms.txt / llms-full.txt and every string in src/i18n. Runs after markdown-pages
// on `npm run build`.
import { existsSync } from 'node:fs';
import { readFile } from 'node:fs/promises';
import { join } from 'node:path';
import { defaultLocale, locales } from '../site.config.mjs';
import { catalog, dist, distFiles } from './shared.mjs';

const RULES = [
  [
    /\b(leverag\w*|disrupt\w*|ai-powered|game-chang\w*|unlock\w*|supercharg\w*|10x|scale yourself|seamless\w*|empower\w*|cutting-edge|best-in-class|synerg\w*)\b/i,
    'SaaS speak',
  ],
  [
    /\b(passive income|while you sleep|financial freedom|side hustle|make money|easy money|get rich)\b/i,
    'hustle or passive-income tone',
  ],
  [/—/, 'an em dash (use a period, comma, colon, or parentheses)'],
  [/!(?!\[)/, 'an exclamation mark'],
  [/\b(lorem|ipsum|TODO|TBD)\b/, 'placeholder text'],
];

const problems = [];

const check = (name, text) => {
  const body = text.replace(/^---\n[\s\S]*?\n---\n/, '');
  body.split('\n').forEach((line, i) => {
    let clean = line
      .replace(/`[^`]*`/g, '')
      .replace(/\]\([^)]*\)/g, ']')
      .replace(/https?:\/\/\S+/g, '')
      .replace(/\{\{[^}]+\}\}/g, '');
    for (const [re, why] of RULES) {
      if (re.test(clean)) problems.push(`${name}:${i + 1}: ${why}: ${line.trim().slice(0, 120)}`);
    }
  });
};

for (const rel of [...(await distFiles('index.md')), 'llms.txt', 'llms-full.txt']) {
  if (existsSync(join(dist, rel))) check(rel, await readFile(join(dist, rel), 'utf8'));
}

// Catalog strings, flattened to description + ui.<key>.
const strings = (code) => {
  const { description, ui } = catalog(code);
  return { description, ...Object.fromEntries(Object.entries(ui).map(([key, text]) => [`ui.${key}`, text])) };
};
const base = strings(defaultLocale);
const untranslated = [];
for (const code of locales) {
  const own = strings(code);
  for (const [key, text] of Object.entries(own)) check(`src/i18n/${code}.json ${key}`, text);
  const same = code === defaultLocale ? [] : Object.keys(base).filter((key) => own[key] === base[key]);
  if (same.length) untranslated.push(`${code}.json: ${same.join(', ')}`);
}
if (untranslated.length) {
  console.warn(
    `lint-copy: same text as ${defaultLocale}.json (untranslated?)\n  ${untranslated.join('\n  ')}`,
  );
}

if (problems.length) {
  console.error(`lint-copy: ${problems.length} problem(s)\n${problems.join('\n')}`);
  process.exit(1);
}
console.log('lint-copy: ok');
