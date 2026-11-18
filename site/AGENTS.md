# AGENTS.md: Standup

You are working on the **Standup** website, an Astro site. It is the `site/` folder of the Standup repository: the plugin it describes is in `../plugin/`, and the repository's git hook (`../.githooks/`), CI (`../.github/workflows/ci.yml`) and preview config (`../.claude/launch.json`) are at the repository root. Every path below is relative to this folder, and every command runs here.

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

## How you must work

1. Treat `intent.md` as scope law. Change it with the human before adding routes or features.
2. Porting a brief from `docs/`: scope into `intent.md`; the one sentence into `description` in every `src/i18n/<code>.json` (find the old one with `grep -rlF '<old sentence>' --exclude-dir=node_modules --exclude-dir=dist .`); brand into `design.md` and `src/styles/global.css`; numbers into `src/data/`; then `npm run generate:og` and `npm run generate:icons`. Log what you decided in `docs/decisions.md`.
3. Brand token values live in `src/styles/global.css`. Gates in `design.md` are law.
4. Before claiming UI done: `/design-quality`, all gates PASS.
5. Homepage content must work with JavaScript off. Islands are optional.
6. Sourced numbers for tools/calculators live in `src/data/`, not hard-coded in JSX.
7. Preserve the day-0 SEO/AEO, language and share stubs. Extend them.
8. `npm run verify` is the gate: formatting, then the build with every check. It prints nothing when it passes. Run it before claiming done.
9. Anything that waits on the human goes in `docs/inbox.md` under "Waiting on you": the question, your recommendation, where to look. A finished deliverable gets a line under "Delivered". When they rule, log it in `docs/decisions.md` and remove the item.

## Stack locks (unless the user asks otherwise)

| Lock | Value |
|---|---|
| Framework | Astro 7 · `output: 'static'` |
| Trailing slash | `'always'` |
| CSS | Tailwind 4 via `@tailwindcss/vite` |
| React | Islands only; small typed props |
| Host | **Cloudflare Pages**, Direct Upload of `dist/` |
| Adapter | **No** `@astrojs/cloudflare` / SSR unless explicitly asked |
| Functions | One: `functions/_middleware.js` answers `Accept: text/markdown` with the page's `index.md` twin. Pages stay static files; `_routes.json` keeps assets off it. Try it with `npx wrangler pages dev dist` after a build |
| Dependencies | Exact versions, from the registry only, at least 2 days old (`.npmrc`): no `^` / `~`, no casual bumps |
| Appearance | Light, plus a dark appearance that follows the visitor's system when `darkMode` is true in `site.config.mjs`. Dark tokens sit next to the light ones in `src/styles/global.css`; `dark:` utilities follow the same switch |
| Class helpers | `clsx` + `tailwind-merge` via `src/lib/cn.ts` |
| Format | Prettier + `prettier-plugin-astro` (`format` / `format:check`) |
| Copy lint | `RULES` in `scripts/lint-copy.mjs`, run on built markdown, llms.txt and `src/i18n` |
| Analytics | Microsoft Clarity only, `clarityId` in `site.config.mjs`, behind the cookie question (`docs/kit/analytics.md`) |
| Service worker | **No** by default |

## Commands

```sh
npm install
npm run dev                # http://standup-site.localhost:4817/, and /dev/styleguide/
npm run domain             # https://standup-site.localhost/ through Caddy
npm run verify             # the gate: format:check + build, silent when it passes
npm run build              # astro check + build + markdown-pages + lint-copy + verify-build
npm run format             # prettier --write
npm run format:check
npm run lint:copy          # needs a prior build (reads dist/)
npm run generate:og        # public/og-image.png from scripts/og-template.html
npm run generate:icons     # PNG + ICO icons from public/favicon.svg
npm run deploy -- https://your-domain   # build + upload
```

## Kit reference

Read the file when its case comes up. Each is the single place for its topic.

| Read | When |
|---|---|
| `docs/kit/structure.md` | Finding where something lives, or adding a file |
| `docs/kit/languages.md` | Adding a page, a string or a language |
| `docs/kit/seo.md` | Touching `<head>`, JSON-LD, sitemap, robots, `llms.txt` or the markdown twins |
| `docs/kit/images.md` | Share card, icons, any rendered picture |
| `docs/kit/analytics.md` | Clarity, the cookie question, `/privacy/` |
| `docs/kit/deploy.md` | Deploying, or anything in `scripts/deploy.sh` and `.github/workflows/` |
| `docs/kit/local.md` | The dev server will not start, the port, `npm run domain` |
| `docs/kit/agent-apps.md` | An agent app's config file or permissions |
| `docs/kit/upgrade.md` | Taking a newer kit into this site (`wcgw upgrade`), and `src/dev/` pages |

## Do not

- Flip to SSR “just for forms”
- Add a second `/*` in `_headers`
- Ship relative `og:image` URLs
- Add a service worker unless the human asks
- Bump dependency major/minor without asking
- Push to `main` without the human's go-ahead: it deploys
- Claim green without `npm run verify`
