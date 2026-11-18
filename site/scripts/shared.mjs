// Node-side helpers for astro.config.mjs and the scripts in this folder.
// Pages and layouts read the language files through src/i18n/index.ts instead.
import { readFileSync } from 'node:fs';
import { readdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { defaultLocale, locales } from '../site.config.mjs';

export const dist = fileURLToPath(new URL('../dist/', import.meta.url));

/** src/i18n/<code>.json, parsed. */
export const catalog = (code) =>
  JSON.parse(readFileSync(new URL(`../src/i18n/${code}.json`, import.meta.url), 'utf8'));

/** The locale of a dist-relative path: its first segment, or the unprefixed default. */
export const localeOf = (rel) => {
  const first = rel.split('/')[0];
  return first !== defaultLocale && locales.includes(first) ? first : defaultLocale;
};

/** BaseLayout's noindex tag: the one switch for the sitemap, llms.txt and markdown twins. */
export const isNoindex = (html) => /<meta name="robots" content="noindex/.test(html);

/** dist-relative paths (with /) of every file called `name`, e.g. 'index.html'. */
export const distFiles = async (name) =>
  (await readdir(dist, { recursive: true }))
    .map((rel) => rel.replaceAll('\\', '/'))
    .filter((rel) => rel === name || rel.endsWith(`/${name}`));

/** A --color-<name> token value from src/styles/global.css, or undefined. */
export const cssColor = (name) =>
  readFileSync(new URL('../src/styles/global.css', import.meta.url), 'utf8')
    .match(new RegExp(`--color-${name}:\\s*([^;{}<]+);`))?.[1]
    .trim();
