// Post-build: write index.md beside every indexable index.html, then llms.txt and
// llms-full.txt from those same pages, grouped by language. Agents that send
// Accept: text/markdown can read the words without the markup once a Cloudflare
// Transform Rule rewrites /path/ → /path/index.md (free; paid Markdown-for-Agents not required).
import { readFile, writeFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { join } from 'node:path';
import { NodeHtmlMarkdown } from 'node-html-markdown';
import { locales, siteName, siteUrl } from '../site.config.mjs';
import { catalog, dist, distFiles, isNoindex, localeOf } from './shared.mjs';

const { parse } = createRequire(createRequire(import.meta.url).resolve('node-html-markdown'))(
  'node-html-parser',
);

const DROP =
  '[aria-hidden="true"], [hidden], [role="img"], svg, script, style, noscript, template, dialog, img, picture, video, button, input, select, textarea';
// '<' is escaped as well, so a name like <Lab> stays text instead of becoming an HTML tag.
const markdown = new NodeHtmlMarkdown({
  bulletMarker: '-',
  maxConsecutiveNewlines: 2,
  textReplace: [[/</g, '\\<']],
});
const yaml = (value) => JSON.stringify(value);
/** Backslash-escapes markdown syntax in names and descriptions spliced into llms.txt / llms-full.txt. */
const escapeMd = (text) => text.replace(/[\\`*_[\]<>]/g, '\\$&');
/** Moves a twin's headings under its page's ### heading in llms-full.txt; code fences are left alone. */
const demote = (md) => {
  let fenced = false;
  return md
    .split('\n')
    .map((line) => {
      if (/^(```|~~~)/.test(line)) fenced = !fenced;
      return !fenced && /^#{1,6} /.test(line) ? `###${line}`.replace(/^#{7,}/, '######') : line;
    })
    .join('\n');
};

const pages = [];

for (const rel of await distFiles('index.html')) {
  const file = join(dist, rel);
  const html = await readFile(file, 'utf8');
  if (isNoindex(html)) continue;
  const headEnd = html.indexOf('</head>');
  const head = parse(html.slice(0, headEnd === -1 ? 4000 : headEnd));
  const lang = head.querySelector('html')?.getAttribute('lang');
  const title = head.querySelector('title')?.text.trim();
  const description = head.querySelector('meta[name="description"]')?.getAttribute('content')?.trim();
  const canonical = head.querySelector('link[rel="canonical"]')?.getAttribute('href');
  const main = html.match(/<main\b[^>]*>([\s\S]*)<\/main>/)?.[1];
  if (!lang || !title || !description || !canonical || !main) {
    throw new Error(`markdown-pages: ${file} lacks html lang, title, description, canonical, or <main>`);
  }
  const root = parse(main);
  for (const node of root.querySelectorAll(DROP)) node.remove();
  const body = markdown.translate(root.innerHTML).trim();
  const md = [
    '---',
    `title: ${yaml(title)}`,
    `description: ${yaml(description)}`,
    `url: ${yaml(canonical)}`,
    `lang: ${yaml(lang)}`,
    '---',
    '',
    body,
    '',
  ].join('\n');
  await writeFile(file.replace(/index\.html$/, 'index.md'), md);
  pages.push({
    locale: localeOf(rel),
    title,
    description,
    canonical,
    twin: `${canonical}index.md`,
    body,
  });
}

pages.sort((a, b) => a.canonical.localeCompare(b.canonical, 'en'));
const sections = locales.map((code) => ({
  // A one-language site lists its pages without a language heading.
  name: locales.length > 1 ? catalog(code).meta.name : 'Pages',
  pages: pages.filter((p) => p.locale === code),
}));
const home = pages.find((page) => page.canonical === siteUrl);
if (!home) throw new Error(`markdown-pages: no indexable home page at ${siteUrl}`);

const llms = [
  `# ${escapeMd(siteName)}`,
  '',
  `> ${escapeMd(home.description)}`,
  '',
  ...sections.flatMap(({ name, pages }) => [
    `## ${name}`,
    '',
    ...pages.map(
      (p) => `- [${escapeMd(p.title)}](${p.canonical}): ${escapeMd(p.description)} ([markdown](${p.twin}))`,
    ),
    '',
  ]),
  '## Optional',
  '',
  `- [llms-full.txt](${new URL('llms-full.txt', siteUrl).href}): every page above as markdown`,
  `- [Sitemap](${new URL('sitemap-index.xml', siteUrl).href})`,
  '',
];

const full = [
  `# ${escapeMd(siteName)}`,
  '',
  ...sections.flatMap(({ name, pages }) => [
    `## ${name}`,
    '',
    ...pages.flatMap((p) => [`### [${escapeMd(p.title)}](${p.canonical})`, '', demote(p.body), '']),
  ]),
];

await writeFile(join(dist, 'llms.txt'), llms.join('\n'));
await writeFile(join(dist, 'llms-full.txt'), full.join('\n'));

console.log(
  `markdown-pages: ${pages.length} page(s) in ${locales.length} language(s) + llms.txt + llms-full.txt`,
);
