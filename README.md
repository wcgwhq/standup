# Standup

Standup reads your git commits and agent sessions and writes your end-of-day update, so you stop piecing the day together from memory.

## Run

```sh
npm install
npm run dev
```

Open `http://standup-site.localhost:4817/`. The port is `devPort` in `site.config.mjs`, fixed for this site.

- **No port:** `https://standup-site.localhost/`, through the Homebrew Caddy. `npm run domain` writes the generated `$(brew --prefix)/etc/caddy.d/standup-site.caddy`, reloads Caddy and prints the URL that works. wcgw already ran it once if Caddy was running. Without a running Caddy it changes nothing and prints the setup step. It never replaces or removes a `standup-site.caddy` that wcgw did not write. Only this Mac can open the address. `npm run domain -- --remove` takes it away.
- **Certificate warning:** run `caddy trust` once.
- **Port taken:** dev stops with `Port 4817 is taken`. Stop the other server, or start this one with `PORT=<n> npm run dev`.
- **Safari on macOS 15 or older:** use `http://localhost:4817/`.

## Assets

```sh
npm run generate:og      # public/og-image.png (1200×630)
npm run generate:icons   # favicons + apple-touch + PWA icons
```

Both need Google Chrome or Chromium. `generate:og` can use puppeteer instead (`npm i -D puppeteer`); `generate:icons` also needs Python Pillow (`pip install pillow`).

## Ship (Cloudflare Pages)

```sh
npm run deploy -- https://your-domain
```

Direct Upload of `dist/`, no SSR adapter. What it checks first is at the top of `scripts/deploy.sh`.

## Agents

Read **`AGENTS.md` → `design.md` → `intent.md` → `docs/`**. `AGENTS.md` → Agent apps lists the app config files in this folder and what Claude Code may run.

A commit that changes `src/i18n/` or `src/content/` waits for a copy review: run `/copywriting` (or ask any agent to follow `.claude/skills/copywriting/SKILL.md`). `npm install` turns the hook on; `git commit --no-verify` skips it for a typo fix.
