#!/usr/bin/env node
/**
 * Render public/favicon.svg on the site's paper color at each size: favicon-16/32.png,
 * apple-touch-icon.png (180), icon-192/512.png and favicon.ico (16/32/48).
 * Needs Google Chrome or Chromium (scripts/chrome.mjs).
 *
 *   npm run generate:icons
 */
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { launchChrome } from './chrome.mjs';
import { cssColor } from './shared.mjs';

const pub = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', 'public');
const PNGS = [
  [16, 'favicon-16.png'],
  [32, 'favicon-32.png'],
  [180, 'apple-touch-icon.png'],
  [192, 'icon-192.png'],
  [512, 'icon-512.png'],
];
const ICO = [16, 32, 48];
const fail = (message) => {
  console.error(`generate-icons: ${message}`);
  process.exit(1);
};

/** An .ico file holding one PNG per size. */
function ico(images) {
  const header = Buffer.alloc(6 + 16 * images.length);
  header.writeUInt16LE(1, 2); // type: icon
  header.writeUInt16LE(images.length, 4);
  let offset = header.length;
  images.forEach(({ size, png }, i) => {
    const entry = 6 + 16 * i;
    header.writeUInt8(size, entry);
    header.writeUInt8(size, entry + 1);
    header.writeUInt16LE(1, entry + 4); // color planes
    header.writeUInt16LE(32, entry + 6); // bits per pixel
    header.writeUInt32LE(png.length, entry + 8);
    header.writeUInt32LE(offset, entry + 12);
    offset += png.length;
  });
  return Buffer.concat([header, ...images.map(({ png }) => png)]);
}

const paper = cssColor('paper') ?? fail('--color-paper not found in src/styles/global.css.');
const chrome = (await launchChrome()) ?? fail('install Google Chrome or Chromium and retry.');
const tmp = mkdtempSync(path.join(tmpdir(), 'icons-'));
try {
  const page = path.join(tmp, 'icon.html');
  writeFileSync(
    page,
    `<!doctype html><style>html,body{margin:0;width:100vw;height:100vh;overflow:hidden;background:${paper}}img{display:block;width:100%;height:100%}</style><img src="${pathToFileURL(path.join(pub, 'favicon.svg'))}" alt="" />`,
  );
  const render = async (size) => {
    const tab = await chrome.tab(size, size);
    await tab.goto(pathToFileURL(page).href);
    const png = await tab.screenshot({ format: 'png' });
    await tab.close();
    return png;
  };
  for (const [size, name] of PNGS) writeFileSync(path.join(pub, name), await render(size));
  const images = [];
  for (const size of ICO) images.push({ size, png: await render(size) });
  writeFileSync(path.join(pub, 'favicon.ico'), ico(images));
} finally {
  await chrome.close();
  rmSync(tmp, { recursive: true, force: true });
}
console.log(`generate-icons: ${[...PNGS.map(([, name]) => name), 'favicon.ico'].join(', ')}`);
