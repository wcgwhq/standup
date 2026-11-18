# Local URL and dev server

## Local URL

`README.md` → Run covers `npm run domain`, `--remove` and what to do when the port is taken.

- Start the dev server through `npm run dev` only. The script clears `CLAUDECODE`, `AGENT` and `AI_AGENT`. Astro may still run dev in the background under Codex, Cursor or Zed.
- The port is `devPort` in `site.config.mjs`. `../.claude/launch.json`, `../t3.json` and the Caddy file repeat it. Change it only with the human: edit those two files too, then run `npm run domain` again.

## Vite cacheDir pitfall

Split `cacheDir` in `astro.config.mjs`. If islands die with `_jsxDEV is not a function`:

```sh
rm -rf node_modules/.vite node_modules/.vite-build && npm run dev
```
