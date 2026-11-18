# Project structure

```
.
├── AGENTS.md · CLAUDE.md · design.md · intent.md · README.md
├── wcgw.json              ← the kit version and answers this site came from (`upgrade.md`)
├── docs/                  ← specs, handoffs, formulas, sources, decisions.md (read after intent.md), inbox.md (what waits on the human)
├── docs/kit/              ← how the kit's parts work (`AGENTS.md` → Kit reference)
├── astro.config.mjs       ← static · trailingSlash · i18n routing · sitemap filter · 404s · Vite cacheDir split
├── site.config.mjs        ← SITE_URL, SITE_NAME, devPort, locales, clarityId, publisher, Content-Signal (.env overrides URL and name)
├── wrangler.toml          ← Cloudflare Pages (name=standup-site, dist/)
├── functions/_middleware.js ← markdown for agents that ask for it (deployed with dist/)
├── .npmrc                 ← exact versions, registry only, nothing newer than 2 days
├── public/
│   ├── _headers           ← exactly ONE /* block (deploy appends the pages.dev noindex)
│   ├── _routes.json       ← pages run through functions/_middleware.js; assets and .md files skip it
│   ├── favicon.svg · favicon-16/32.png · favicon.ico · apple-touch-icon.png
│   ├── icon-192.png · icon-512.png
│   └── og-image.png       ← 1200×630 share card (absolute URL in layout)
├── scripts/
│   ├── verify.mjs         ← npm run verify, the gate
│   ├── markdown-pages.mjs · lint-copy.mjs · verify-build.mjs
│   ├── copy-reviewed.mjs  ← stamps a copy review; the pre-commit hook checks it
│   ├── generate-og.mjs · og-template.html · generate-icons.mjs
│   ├── chrome.mjs         ← one headless Chrome for both generators, no dependency
│   ├── local-domain.mjs   ← npm run domain (README.md → Run)
│   └── deploy.sh
├── .claude/settings.json  ← Claude Code permissions (`agent-apps.md`)
├── .claude/skills/design-quality/  ← gate review against design.md
├── .claude/skills/copywriting/     ← writes and reviews every word against `AGENTS.md` → Copy
├── ../.githooks/pre-commit ← at the repository root: asks for a copy review when a commit changes src/i18n or src/content
├── agent-app files        ← only for the apps picked at creation (`agent-apps.md`)
├── ../.github/workflows/ci.yml · deploy.yml ← at the repository root: checks, and the deploy on push to main
├── .vscode/ · .editorconfig · .nvmrc
└── src/
    ├── i18n/              ← <code>.json strings per language · index.ts helpers
    ├── pages/[...locale]/ ← every page, built once per language 
    ├── pages/404.astro    ← the default locale's 404 (renders [...locale]/404.astro)
    ├── pages/robots.txt.ts · pages/site.webmanifest.ts
    ├── dev/               ← pages served under npm run dev only (`upgrade.md` → Dev pages)
    └── layouts · components · lib · data · styles
```
