# AGENTS.md: Standup

You are working on **Standup**, a standalone Astro site. This directory is the project root.

**One sentence:** Standup reads your git commits and your agents' sessions and writes the end-of-day update you can no longer write from memory.

Read `design.md` next, then `intent.md`, then `docs/`. Do not invent features outside `intent.md`.

## The bar

Every decision leaves three people better off: the visitor (UX), the next developer (DX) and the next agent (AX). When an option helps one and costs another, find one that helps all three, or take the trade-off to the human. Keep what already works and what `docs/decisions.md` records, until the human changes it.

Every word on screen does a job. Cut taglines, helper text and secondary labels. When a screen needs them to make sense, fix the layout.

This holds wherever you design: pages in `src/`, or artboards in Paper, Figma or another canvas. Read `design.md` and the tokens in `src/styles/global.css` before the first artboard, and build with them.

## Copy

Write to the one reader `intent.md` names, in the words they use. Every line passes the swap test: put another business's name in place of **Standup** and the line stops being true. A line that still works for them is filler; replace it with the fact behind it: the number, the place, the name, the price, the date.

- Headlines make the claim. The visitor gets the point from the headline alone.
- Buttons and links say the action or the destination: "Book a table for Friday", "See the 2026 prices".
- Errors say what happened and what to do next. Empty states say what goes here and how to add it.
- One idea per sentence, verbs doing the work. Three adjectives in a row are one unproven claim; keep one and prove it.
- Read it aloud and cut every word that changes nothing.

Write and review copy with the `copywriting` skill in `.claude/skills/copywriting/` (`/copywriting` in Claude Code; any other agent reads `SKILL.md` there and follows it). A commit that changes `src/i18n/` or `src/content/` needs that review first: the pre-commit hook stops it until the skill's last step has run.

## Project structure

```
.
├── AGENTS.md · CLAUDE.md · design.md · intent.md · README.md
├── docs/                  ← specs, handoffs, formulas, sources, decisions.md (read after intent.md)
├── astro.config.mjs       ← static · trailingSlash · i18n routing · sitemap filter · 404s · Vite cacheDir split
├── site.config.mjs        ← SITE_URL, SITE_NAME, devPort, locales, Content-Signal (.env overrides URL and name)
├── wrangler.toml          ← Cloudflare Pages (name=standup-site, dist/)
├── .npmrc                 ← save-exact=true
├── public/
│   ├── _headers           ← exactly ONE /* block (deploy appends the pages.dev noindex)
│   ├── _routes.json       ← only /api/* would hit Functions; site stays static
│   ├── favicon.svg · favicon-16/32.png · favicon.ico · apple-touch-icon.png
│   ├── icon-192.png · icon-512.png
│   └── og-image.png       ← 1200×630 share card (absolute URL in layout)
├── scripts/
│   ├── markdown-pages.mjs · lint-copy.mjs · verify-build.mjs
│   ├── copy-reviewed.mjs  ← stamps a copy review; the pre-commit hook checks it
│   ├── generate-og.mjs · og-template.html · generate-icons.mjs
│   ├── local-domain.mjs   ← npm run domain (README.md → Run)
│   └── deploy.sh
├── .claude/settings.json  ← Claude Code permissions (Agent apps below)
├── .claude/skills/design-quality/  ← gate review against design.md
├── .claude/skills/copywriting/     ← writes and reviews every word against Copy below
├── .githooks/pre-commit   ← asks for a copy review when a commit changes src/i18n or src/content
├── agent-app files        ← only for the apps picked at creation (Agent apps below)
├── .github/workflows/ci.yml
├── .vscode/ · .editorconfig · .nvmrc
└── src/
    ├── i18n/              ← <code>.json strings per language · index.ts helpers
    ├── pages/[...locale]/ ← every page, built once per language
    ├── pages/404.astro    ← the default locale's 404 (renders [...locale]/404.astro)
    ├── pages/robots.txt.ts · pages/site.webmanifest.ts
    └── layouts · components · lib · data · styles
```

## How you must work

1. Treat `intent.md` as scope law. Change it with the human before adding routes or features.
2. Porting a brief from `docs/`: scope into `intent.md`; the one sentence into `description` in every `src/i18n/<code>.json` (find the old one with `grep -rlF '<old sentence>' --exclude-dir=node_modules --exclude-dir=dist .`); brand into `design.md` and `src/styles/global.css`; numbers into `src/data/`; then `npm run generate:og` and `npm run generate:icons`. Log what you decided in `docs/decisions.md`.
3. Brand token values live in `src/styles/global.css`. Gates in `design.md` are law.
4. Before claiming UI done: `/design-quality`, all gates PASS.
5. Homepage content must work with JavaScript off. Islands are optional.
6. Sourced numbers for tools/calculators live in `src/data/`, not hard-coded in JSX.
7. Preserve the day-0 SEO/AEO, language and share stubs. Extend them.
8. Run `npm run build` before claiming done.

## Stack locks (unless the user asks otherwise)

| Lock | Value |
|---|---|
| Framework | Astro 7 · `output: 'static'` |
| Trailing slash | `'always'` |
| CSS | Tailwind 4 via `@tailwindcss/vite` |
| React | Islands only; small typed props |
| Host | **Cloudflare Pages**, Direct Upload of `dist/` |
| Adapter | **No** `@astrojs/cloudflare` / SSR unless explicitly asked |
| Functions | Optional later; `_routes.json` keeps only `/api/*` on Workers |
| Dependencies | Exact versions (`.npmrc` save-exact): no `^` / `~`, no casual bumps |
| Appearance | Light, plus a dark appearance that follows the visitor's system when `darkMode` is true in `site.config.mjs`. Dark tokens sit next to the light ones in `src/styles/global.css`; `dark:` utilities follow the same switch |
| Class helpers | `clsx` + `tailwind-merge` via `src/lib/cn.ts` |
| Format | Prettier + `prettier-plugin-astro` (`format` / `format:check`) |
| Copy lint | `RULES` in `scripts/lint-copy.mjs`, run on built markdown, llms.txt and `src/i18n` |
| Service worker | **No** by default |

## Commands

```sh
npm install
npm run dev                # http://standup-site.localhost:4817/ (Local URL below)
npm run domain             # https://standup-site.localhost/ through Caddy
npm run build              # astro check + build + markdown-pages + lint-copy + verify-build
npm run format             # prettier --write
npm run format:check
npm run lint:copy          # needs a prior build (reads dist/)
npm run generate:og        # public/og-image.png from scripts/og-template.html
npm run generate:icons     # PNG + ICO icons from public/favicon.svg
npm run deploy -- https://your-domain   # build + upload (see below)
```

## Local URL

`README.md` → Run covers `npm run domain`, `--remove` and what to do when the port is taken.

- Start the dev server through `npm run dev` only. The script clears `CLAUDECODE`, `AGENT` and `AI_AGENT`. Astro may still run dev in the background under Codex, Cursor or Zed.
- The port is `devPort` in `site.config.mjs`. `.claude/launch.json`, `t3.json` and the Caddy file repeat it. Change it only with the human: edit those two files too, then run `npm run domain` again.

## Agent apps

`.claude/settings.json` is in every site. Claude Code runs `npm run *` without asking, asks before `npm run deploy` and `npx wrangler *`, and is blocked from reading `.env` and `.dev.vars`. It applies once the folder is trusted in Claude Code.

The scaffold wrote these only for the apps picked at creation:

| File | App | For |
|---|---|---|
| `.claude/launch.json` | Claude desktop | Starts `npm run dev` for its preview pane |
| `.codex/environments/environment.toml` | Codex app | Setup (`npm install`) and Dev, Build, Preview actions |
| `.super.engineering/config.json` | super.engineering | Setup and the dev, build, preview run scripts |
| `t3.json` | T3 Code | Install, Dev (opens the preview), Build, Preview actions; import them once in the app |
| `.zed/tasks.json` | Zed | dev, build, preview tasks |

Cursor needs no file. Every app reads this file (`CLAUDE.md` imports it), so all agent instructions live here.

## Cloudflare Pages

```sh
npm run deploy -- https://your-domain           # production branch main
npm run deploy -- https://your-domain preview   # any other branch is a preview
```

The header of `scripts/deploy.sh` lists what it refuses, how to log in, and how pages.dev hosts are noindexed.

## OG + icons

| Asset | How |
|---|---|
| Share card 1200×630 | `npm run generate:og` renders `scripts/og-template.html` with the site name, the default language's `description` and the paper/ink/accent tokens. Needs Chrome or Chromium (or `npm i -D puppeteer`). Refuses while the description is the placeholder. |
| Icons | `npm run generate:icons` renders `public/favicon.svg` on `--color-paper`, then resizes it. Needs Chrome or Chromium and Python Pillow (`pip install pillow`). |
| Layout | Absolute `og:image` / Twitter image via `Astro.site`, never relative |

The committed `og-image.png` and PNG icons are neutral ink on paper; `favicon.svg` already uses the accent. Run both generators once the brand is set.

## Vite cacheDir pitfall

Split `cacheDir` in `astro.config.mjs`. If islands die with `_jsxDEV is not a function`:

```sh
rm -rf node_modules/.vite node_modules/.vite-build && npm run dev
```

## SEO / AEO (preserve)

| Piece | Where |
|---|---|
| Head + one JSON-LD `@graph` | `BaseLayout.astro`, `lib/seo.ts` |
| Per-page extras | `BaseLayout` props: `graph` (extra JSON-LD nodes, same `@graph`), `noindex`, `ogImage`, `pageType`, `locale` |
| `llms.txt` · `llms-full.txt` · `index.md` twins | `scripts/markdown-pages.mjs`, generated after the build from the pages actually built |
| Sitemap (indexable pages only) · robots (one `*` group) | `astro.config.mjs`, `pages/robots.txt.ts` |
| Headers (one `/*`) | `public/_headers` |
| Manifest · theme-color · viewport-fit | `BaseLayout` + `pages/site.webmanifest.ts` |
| Contract | `scripts/verify-build.mjs` |

`noindex` is the one switch: a noindex page drops out of the sitemap, `llms.txt` and the markdown twins. If you add `/tools/*`: pass `noindex` (noindex + out of sitemap).

## Languages

- **URLs:** the default language is unprefixed (`/`, `/about/`); the others live under `/<code>/` (`/de/`, `/de/about/`).
- **Strings:** `src/i18n/<code>.json` holds `meta` (native name, hreflang, ogLocale, dir, font), `description` (the site's one sentence in that language) and `ui` (page strings; `{site}` becomes the site name). Every file keeps the same `ui` keys or the build fails.
- **Add a language:** copy a file in `src/i18n/` to `<code>.json`, fill its `meta` (`"font": "system"` for scripts JetBrains Mono lacks, such as Arabic, Hebrew, Devanagari or CJK), translate `description` and `ui`, then add the code to `locales` in `site.config.mjs` (default first).
- **Add a page:** put it in `src/pages/[...locale]/` with `getStaticPaths = localeStaticPaths`, pass `locale` to `BaseLayout`, add its strings to `ui` in every catalog, and link with `localePath(locale, '/path/')`. Every page exists in every language.
- **Translate:** `npm run build` warns (lint-copy) on each string still identical to the default language's.
- **Automatic, enforced by verify-build:** `<html lang dir>`, hreflang for every language plus `x-default` (reciprocal), matching sitemap alternates, `og:locale` + alternates, JSON-LD `inLanguage` and translation links, a noindex 404 per language (`/404.html`, `/<code>/404.html`), one `llms.txt` section per language, markdown twins with `lang`.

## Do not

- Flip to SSR “just for forms”
- Add a second `/*` in `_headers`
- Ship relative `og:image` URLs
- Add a service worker unless the human asks
- Bump dependency major/minor without asking
- Claim green without `npm run build`
