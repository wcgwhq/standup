#!/usr/bin/env node
/**
 * Render public/og-image.png (1200×630) from scripts/og-template.html with this site's name,
 * default-locale description, lang/dir, and paper/ink/accent from src/styles/global.css.
 * Needs Google Chrome or Chromium (scripts/chrome.mjs).
 *
 *   npm run generate:og
 */
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { defaultLocale, siteName } from '../site.config.mjs';
import { launchChrome } from './chrome.mjs';
import { catalog, cssColor } from './shared.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = (file) => readFileSync(path.join(root, file), 'utf8');
const fail = (message) => {
  console.error(`generate-og: ${message}`);
  process.exit(1);
};

const { meta, description } = catalog(defaultLocale);
if (description.includes('fill the one-sentence intent')) {
  fail(`write the one-sentence description in src/i18n/${defaultLocale}.json first.`);
}

const color = (name) => cssColor(name) ?? fail(`--color-${name} not found in src/styles/global.css.`);

const escape = (text) =>
  String(text).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);

function fill(html, slot, text) {
  const element = new RegExp(`(<(\\w+)[^>]*data-slot="${slot}"[^>]*>)[\\s\\S]*?(</\\2>)`);
  if (!element.test(html)) fail(`data-slot="${slot}" not found in scripts/og-template.html.`);
  return html.replace(element, (_, open, _tag, close) => open + escape(text) + close);
}

let html = read('scripts/og-template.html')
  .replace(
    /<html[^>]*>/,
    () => `<html lang="${escape(meta.hreflang)}" dir="${escape(meta.dir)}" data-font="${escape(meta.font)}">`,
  )
  .replace('<head>', () => `<head>\n    <base href="${pathToFileURL(path.join(root, 'scripts'))}/" />`)
  .replace(
    '</style>',
    () =>
      `  :root { --paper: ${color('paper')}; --ink: ${color('ink')}; --accent: ${color('accent')}; }\n    </style>`,
  );
html = fill(fill(html, 'name', siteName), 'description', description);

const chrome = (await launchChrome()) ?? fail('install Google Chrome or Chromium and retry.');
const tmp = mkdtempSync(path.join(tmpdir(), 'og-'));
try {
  const page = path.join(tmp, 'og.html');
  writeFileSync(page, html);
  const tab = await chrome.tab(1200, 630);
  await tab.goto(pathToFileURL(page).href);
  await tab.evaluate('document.fonts.ready.then(() => true)');
  writeFileSync(path.join(root, 'public', 'og-image.png'), await tab.screenshot({ format: 'png' }));
} finally {
  await chrome.close();
  rmSync(tmp, { recursive: true, force: true });
}
console.log(`generate-og: public/og-image.png (${siteName}, ${defaultLocale})`);
