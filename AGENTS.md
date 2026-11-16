# AGENTS.md: Standup

Everything about Standup lives in this one repository.

**One sentence:** Standup reads your git commits and your agents' sessions and writes the end-of-day update you can no longer write from memory.

## Where things are

| Folder | What it is | Its rules |
| --- | --- | --- |
| `plugin/` | The product: two skills (`eod-review`, `eow-review`), the Python engine behind them, the writing voices, and the manifest each agent installs from. | `plugin/README.md` |
| `site/` | The website (Astro, deployed to Cloudflare Pages). | `site/AGENTS.md`, then `site/design.md` and `site/intent.md`. Read them before any site work; they are law there. |
| `docs/` | Research and records that belong to neither: the code review, the publishing steps, the marketplace notes. | |
| `archive/` | Old copies kept for reference. Never edit them, never load skills from them. | |

The repository root holds only what must be at a root: the marketplace manifests (`.claude-plugin/`, `.cursor-plugin/`, `gemini-extension.json`), the git hook, CI, and this file.

## How to work here

- **Site commands run in `site/`:** `npm --prefix site run dev`, `npm --prefix site run build`. The site's own `AGENTS.md` lists the rest.
- **The plugin has no build.** Run it straight: `python3 plugin/skills/eod-review/eod_review.py --check`. It must keep working on Python 3.9 with no packages.
- **The site shows the plugin's real output.** When the engine's numbers or the install commands change, `site/src/data/sample-report.json` and `site/src/data/install.json` change with them, in the same piece of work.
- **Installing is by repository address**, so the manifests at the root are a public contract. After touching one, re-run every check in `docs/publishing.md`.
- Record a decision where it belongs: site decisions in `site/docs/decisions.md`, everything else in `docs/decisions.md`.
