#!/usr/bin/env node
/**
 * Render public/favicon.svg once at 512×512 on the site's paper color, then resize it to
 * favicon-16/32.png, apple-touch-icon.png (180), icon-192/512.png and favicon.ico (16/32/48).
 * Needs Google Chrome or Chromium, and Python 3 with Pillow (`pip install pillow`).
 *
 *   npm run generate:icons
 */
import { spawnSync } from 'node:child_process';
import { copyFileSync, existsSync, mkdtempSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { chromeScreenshot, cssColor } from './shared.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const pub = path.join(root, 'public');
const PNGS = [
  [16, 'favicon-16.png'],
  [32, 'favicon-32.png'],
  [180, 'apple-touch-icon.png'],
  [192, 'icon-192.png'],
  [512, 'icon-512.png'],
];
const outputs = [...PNGS.map(([, name]) => name), 'favicon.ico'];
const fail = (message) => {
  console.error(`generate-icons: ${message}`);
  process.exit(1);
};

const paper = cssColor('paper') ?? fail('--color-paper not found in src/styles/global.css.');

const tmp = mkdtempSync(path.join(tmpdir(), 'icons-'));
const page = path.join(tmp, 'icon.html');
const shot = path.join(tmp, 'icon.png');
writeFileSync(
  page,
  `<!doctype html><style>html,body{margin:0;width:512px;height:512px;background:${paper}}img{display:block;width:100%;height:100%}</style><img src="${pathToFileURL(path.join(pub, 'favicon.svg'))}" alt="" />`,
);
if (!chromeScreenshot(page, shot, 512, 512)) {
  rmSync(tmp, { recursive: true, force: true });
  fail('Google Chrome or Chromium not found.');
}

const resize = `
import json, sys
from PIL import Image
src, out, pngs = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])
im = Image.open(src).convert('RGB')
for size, name in pngs:
    im.resize((size, size), Image.Resampling.LANCZOS).save(f'{out}/{name}', optimize=True)
im.save(f'{out}/favicon.ico', sizes=[(16, 16), (32, 32), (48, 48)])
`;
const py = existsSync(shot)
  ? spawnSync('python3', ['-c', resize, shot, tmp, JSON.stringify(PNGS)], { encoding: 'utf8' })
  : null;
const done = outputs.every(
  (name) => existsSync(path.join(tmp, name)) && statSync(path.join(tmp, name)).size > 0,
);
if (done) for (const name of outputs) copyFileSync(path.join(tmp, name), path.join(pub, name));
rmSync(tmp, { recursive: true, force: true });

if (!py) fail('Chrome rendered nothing from public/favicon.svg.');
if (!done)
  fail(`resize failed. Needs Python 3 with Pillow (pip install pillow).\n${py.stderr || py.error || ''}`);
console.log(`generate-icons: ${outputs.join(', ')}`);
