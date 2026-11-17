// Post-build: write index.md beside every indexable index.html, then llms.txt and
// llms-full.txt from those same pages, grouped by language. llms.txt also carries what an
// agent needs to act without a second fetch: what the plugin is, and every install command.
//
// Three attributes in a page shape its markdown without changing what a visitor sees:
//   data-md="skip"        left out (the voices a picker hides)
//   data-md-label="Codex" a bold line before the element (which agent a command is for)
//   data-md-text="a: b"   the element's whole text (a row drawn as separate columns) Agents that send
// Accept: text/markdown can read the words without the markup once a Cloudflare
// Transform Rule rewrites /path/ → /path/index.md (free; paid Markdown-for-Agents not required).
import { readFileSync } from 'node:fs';
import { readFile, writeFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { join } from 'node:path';
import { NodeHtmlMarkdown } from 'node-html-markdown';
import { defaultLocale, locales, siteName, siteUrl } from '../site.config.mjs';
import { catalog, dist, distFiles, isNoindex, localeOf } from './shared.mjs';

const { parse } = createRequire(createRequire(import.meta.url).resolve('node-html-markdown'))(
  'node-html-parser',
);

const DROP =
  '[data-md="skip"], fieldset, sup, [aria-hidden="true"], [hidden], [role="img"], svg, script, style, noscript, template, dialog, img, picture, video, button, input, select, textarea';
// '<' is escaped as well, so a name like <Lab> stays text instead of becoming an HTML tag.
const markdown = new NodeHtmlMarkdown({
  bulletMarker: '-',
  maxConsecutiveNewlines: 2,
  textReplace: [[/</g, '\\<']],
});
const yaml = (value) => JSON.stringify(value);
const escapeHtml = (text) => text.replace(/[&<>"]/g, (char) => `&#${char.charCodeAt(0)};`);
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
  for (const node of root.querySelectorAll('[data-md-text]')) {
    node.textContent = node.getAttribute('data-md-text');
  }
  for (const node of root.querySelectorAll('[data-md-label]')) {
    node.insertAdjacentHTML(
      'afterbegin',
      `<p><strong>${escapeHtml(node.getAttribute('data-md-label'))}</strong></p>`,
    );
  }
  // Root-relative links become absolute: a twin is read away from the page it describes.
  for (const link of root.querySelectorAll('a[href^="/"]')) {
    link.setAttribute('href', new URL(link.getAttribute('href'), siteUrl).href);
  }
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

// The default language's strings and the install commands, the same ones the pages show.
const { ui } = JSON.parse(
  readFileSync(new URL(`../src/i18n/${defaultLocale}.json`, import.meta.url), 'utf8').replaceAll(
    '{site}',
    siteName,
  ),
);
const install = JSON.parse(readFileSync(new URL('../src/data/install.json', import.meta.url), 'utf8'));
const commands = install.agents.map((agent) => {
  const command = agent.command.replace('{repo}', install.repo);
  const note =
    agent.id === 'cursor' ? ui.installCursor : command.startsWith('git clone') ? ui.installCopy : '';
  return `- ${agent.name}: \`${command}\`${note ? `. ${note}` : ''}`;
});
const repo = `https://github.com/${install.repo}`;
const raw = `https://raw.githubusercontent.com/${install.repo}/main/plugin`;

const llms = [
  `# ${escapeMd(siteName)}`,
  '',
  `> ${escapeMd(home.description)}`,
  '',
  `${ui.llmsAbout} ${ui.requirements}`,
  '',
  ui.llmsInstall,
  '',
  ...commands,
  '',
  // Present only while the repository is private (docs/publishing.md).
  ...(ui.installNote ? [ui.installNote, ''] : []),
  ...sections.flatMap(({ name, pages }) => [
    `## ${name}`,
    '',
    ...pages.map(
      (p) => `- [${escapeMd(p.title)}](${p.canonical}): ${escapeMd(p.description)} ([markdown](${p.twin}))`,
    ),
    '',
  ]),
  `## ${ui.llmsSource}`,
  '',
  `- [${ui.llmsRepo}](${repo}): ${ui.llmsRepoNote}`,
  `- [${ui.llmsReadme}](${raw}/README.md): ${ui.llmsReadmeNote}`,
  `- [standup](${raw}/skills/standup/SKILL.md): ${ui.llmsSkillNote}`,
  '',
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
