// Post-build assertions for the SEO/AEO, i18n and share/unfurl contract.
import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';
import { readFile, readdir } from 'node:fs/promises';
import { join } from 'node:path';
import { darkMode, defaultLocale, locales, siteName, siteUrl } from '../site.config.mjs';
import { catalog, dist, distFiles, isNoindex, localeOf } from './shared.mjs';

const site = new URL(siteUrl);
const translated = locales.length > 1;
const meta = Object.fromEntries(locales.map((code) => [code, catalog(code).meta]));

const read = (rel) => readFile(join(dist, rel), 'utf8');
const exists = (rel) => existsSync(join(dist, rel));

/** Attributes of every <name …> tag, in any order. */
const tags = (source, name) =>
  [...source.matchAll(new RegExp(`<${name}\\b([^>]*)>`, 'g'))].map(([, attrs]) =>
    Object.fromEntries([...attrs.matchAll(/([\w:-]+)="([^"]*)"/g)].map(([, key, value]) => [key, value])),
  );

function assertLang(rel, html, code) {
  const { lang, dir } = tags(html, 'html')[0] ?? {};
  assert.equal(lang, meta[code].hreflang, `${rel}: <html lang> is ${code}'s hreflang`);
  assert.equal(dir, meta[code].dir, `${rel}: <html dir>`);
}

// _headers: exactly one /* block (a second silently wins on Cloudflare Pages)
const headers = await readFile(new URL('../public/_headers', import.meta.url), 'utf8');
const pathLines = headers
  .split(/\r?\n/)
  .map((l) => l.trim())
  .filter((l) => l.startsWith('/'));
assert.equal(pathLines.filter((l) => l === '/*').length, 1, '_headers must have exactly one /* block');

assert.ok(exists('index.html'), 'home html');
assert.ok(exists('index.md'), 'home markdown');
assert.ok(exists('llms.txt'), 'llms.txt');
assert.ok(exists('llms-full.txt'), 'llms-full.txt');
assert.ok(exists('robots.txt'), 'robots.txt');
assert.ok(exists('sitemap-index.xml'), 'sitemap-index.xml');
assert.ok(exists('_headers'), '_headers copied into dist');
assert.ok(exists('_routes.json'), '_routes.json (Pages Functions gate)');
assert.ok(exists('og-image.png'), 'og-image.png 1200×630');
assert.ok(exists('favicon.svg'), 'favicon.svg');
assert.ok(exists('apple-touch-icon.png'), 'apple-touch-icon');
assert.ok(exists('icon-192.png') && exists('icon-512.png'), 'PWA icons');

assert.ok(exists('site.webmanifest'), 'site.webmanifest');

// Appearance follows darkMode in site.config.mjs.
const homeHtml = await read('index.html');
assert.equal(
  tags(homeHtml, 'html')[0]?.['data-theme'],
  darkMode ? 'auto' : undefined,
  'html data-theme matches darkMode',
);
assert.equal(
  tags(homeHtml, 'meta').find((m) => m.name === 'color-scheme')?.content,
  darkMode ? 'light dark' : 'light',
  'color-scheme meta matches darkMode',
);

const robots = await read('robots.txt');
assert.match(robots, /Content-Signal:/);
assert.match(robots, new RegExp(`Sitemap:\\s*${site.origin.replace(/\./g, '\\.')}/sitemap`));

// Cloudflare Pages serves the nearest 404.html up the tree; without /404.html it falls back to SPA mode.
for (const code of locales) {
  const rel = code === defaultLocale ? '404.html' : `${code}/404.html`;
  assert.ok(exists(rel), `${rel} exists`);
  const html = await read(rel);
  assert.ok(isNoindex(html), `${rel}: noindex`);
  assertLang(rel, html, code);
}

/** Built pages by URL. */
const pages = new Map();
for (const rel of await distFiles('index.html')) {
  const html = await read(rel);
  pages.set(new URL(rel.replace(/index\.html$/, ''), site).href, {
    rel,
    html,
    locale: localeOf(rel),
    noindex: isNoindex(html),
    links: tags(html, 'link'),
    metas: tags(html, 'meta'),
  });
}
const indexable = [...pages].filter(([, page]) => !page.noindex);
const hreflangLinks = (page) => page.links.filter((l) => l.rel === 'alternate' && l.hreflang);

const sitemap = new Map();
for (const file of (await readdir(dist)).filter((name) => /^sitemap-\d+\.xml$/.test(name))) {
  for (const [, body] of (await read(file)).matchAll(/<url>([\s\S]*?)<\/url>/g)) {
    sitemap.set(body.match(/<loc>([^<]*)<\/loc>/)[1], tags(body, 'xhtml:link'));
  }
}
for (const url of sitemap.keys()) {
  assert.ok(
    pages.get(url) && !pages.get(url).noindex,
    `sitemap lists ${url}, which is not an indexable page`,
  );
}

const llms = await read('llms.txt');
for (const [url, page] of pages) {
  if (page.noindex) assert.ok(!llms.includes(`](${url})`), `${page.rel}: noindex, so not in llms.txt`);
}

for (const [url, page] of indexable) {
  const { rel, html, locale, links, metas } = page;
  const { hreflang, ogLocale } = meta[locale];
  assertLang(rel, html, locale);
  assert.match(html, /<main\b/, `${rel}: <main>`);
  assert.equal((html.match(/<h1\b/g) ?? []).length, 1, `${rel}: exactly one <h1>`);
  assert.deepEqual(
    links.filter((l) => l.rel === 'canonical').map((l) => l.href),
    [url],
    `${rel}: canonical is itself`,
  );
  const content = (property) => metas.filter((m) => m.property === property).map((m) => m.content);
  assert.ok(content('og:image')[0]?.startsWith(`${site.origin}/`), `${rel}: absolute og:image`);
  assert.deepEqual(content('og:locale'), [ogLocale], `${rel}: og:locale`);
  assert.ok(
    links.some((l) => l.rel === 'manifest' && l.href === '/site.webmanifest'),
    `${rel}: web manifest link`,
  );
  assert.ok(
    metas.some((m) => m.name === 'theme-color'),
    `${rel}: theme-color`,
  );
  assert.match(html, /viewport-fit=cover/, `${rel}: viewport-fit`);
  assert.ok(sitemap.has(url), `${rel}: in the sitemap`);
  assert.ok(llms.includes(`](${url})`), `${rel}: listed in llms.txt`);
  assert.ok(exists(rel.replace(/index\.html$/, 'index.md')), `${rel}: markdown twin`);

  const scripts = [...html.matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g)];
  assert.equal(scripts.length, 1, `${rel}: exactly one JSON-LD`);
  const ld = JSON.parse(scripts[0][1]);
  assert.equal(ld['@context'], 'https://schema.org');
  assert.ok(Array.isArray(ld['@graph']), `${rel}: @graph`);
  const node = (type) => ld['@graph'].find((n) => n['@type'] === type);
  const webPage = ld['@graph'].find((n) => n['@id'] === `${url}#webpage`);
  assert.ok(webPage, `${rel}: JSON-LD page node is ${url}#webpage`);
  assert.equal(node('WebSite').name, siteName, `${rel}: JSON-LD WebSite name is the site name`);
  assert.equal(webPage.inLanguage, hreflang, `${rel}: page inLanguage`);
  assert.deepEqual(
    node('WebSite').inLanguage,
    translated ? locales.map((code) => meta[code].hreflang) : hreflang,
    `${rel}: WebSite inLanguage lists every locale`,
  );

  const alternates = hreflangLinks(page);
  if (!translated) {
    assert.equal(alternates.length, 0, `${rel}: one locale, so no hreflang links`);
    continue;
  }
  assert.deepEqual(
    alternates.map((l) => l.hreflang).sort(),
    [...locales.map((code) => meta[code].hreflang), 'x-default'].sort(),
    `${rel}: hreflang for every locale plus x-default`,
  );
  const href = Object.fromEntries(alternates.map((l) => [l.hreflang, l.href]));
  const defaultUrl = href[meta[defaultLocale].hreflang];
  assert.equal(href[hreflang], url, `${rel}: hreflang references itself`);
  assert.equal(href['x-default'], defaultUrl, `${rel}: x-default is the default locale`);
  for (const [lang, target] of Object.entries(href)) {
    assert.ok(target.startsWith(`${site.origin}/`), `${rel}: hreflang ${lang} is absolute on ${site.origin}`);
    const other = pages.get(target);
    assert.ok(other && !other.noindex, `${rel}: hreflang ${lang} → ${target} is an indexable page`);
    const back = hreflangLinks(other).find((l) => l.hreflang === hreflang);
    assert.equal(back?.href, url, `${rel}: ${target} links back (reciprocal hreflang)`);
  }
  const others = locales.filter((code) => code !== locale);
  assert.deepEqual(
    content('og:locale:alternate').sort(),
    others.map((code) => meta[code].ogLocale).sort(),
    `${rel}: og:locale:alternate`,
  );
  assert.deepEqual(
    Object.fromEntries(sitemap.get(url).map((l) => [l.hreflang, l.href])),
    href,
    `${rel}: sitemap alternates match the page`,
  );
  if (locale === defaultLocale) {
    assert.deepEqual(
      webPage.workTranslation?.map((n) => n['@id']).sort(),
      others.map((code) => `${href[meta[code].hreflang]}#webpage`).sort(),
      `${rel}: JSON-LD workTranslation`,
    );
  } else {
    assert.equal(
      webPage.translationOfWork?.['@id'],
      `${defaultUrl}#webpage`,
      `${rel}: JSON-LD translationOfWork`,
    );
  }
}

assert.ok(indexable.length >= 1, 'at least one public page');

const wrangler = await readFile(new URL('../wrangler.toml', import.meta.url), 'utf8');
assert.match(wrangler, /pages_build_output_dir\s*=\s*"dist"/, 'wrangler Pages dist/');
// Ignore comments — the stub documents that we do *not* use the SSR adapter.
const wranglerCode = wrangler
  .split('\n')
  .filter((l) => !/^\s*#/.test(l))
  .join('\n');
assert.ok(!/@astrojs\/cloudflare/.test(wranglerCode), 'no SSR adapter binding in wrangler');
assert.ok(!/^\s*adapter\s*=/m.test(wranglerCode), 'no adapter key in wrangler');

console.log(
  `verify-build: ok (${indexable.length} public page(s) in ${locales.length} language(s); hreflang, sitemap, llms.txt, 404s, CF/OG/icons)`,
);
