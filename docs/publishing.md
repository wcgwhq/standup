# Publishing the plugin

Nothing here is public yet. As of 16 November 2026 the repository has no remote and no `main` branch, and the site is deployed to Cloudflare Pages straight from disk.

## Before the first push

1. **Owner.** Pick the GitHub owner. `wcgw` is taken by someone else's organisation; `wcgwfun` and `wcgw-fun` were free on 12 November. Only Radu can create the organisation.
2. **Names in the examples.** `plugin/skills/eod-review/voices/*.md` and `site/src/data/sample-report.json` carry real project names (Switchboard, Cât Vine Pensia, wcgw). Keep or scrub, on purpose.
3. **`main`.** The only branch is `content/homepage`. Rename it or merge it.
4. **Owner name in the manifests.** They say "Radu Ceuca". Change to the studio name if that is the identity.
5. **Replace `<owner>/<repo>`** in `plugin/README.md` and in `repo` and `command` in `site/src/data/install.json`, and remove `ui.installNote` from `site/src/i18n/en.json`.
6. **Old skills.** Remove `~/.claude/skills/eod-review` and `eow-review` once the plugin is installed, or both sets answer.

## Checks to re-run after touching any manifest

Run from the repository root. Each one was green on 16 November 2026.

| Agent | Check | What it proves |
| --- | --- | --- |
| Claude Code | `claude plugin validate .` and `claude plugin validate plugin` | The marketplace file and the plugin manifest are valid. |
| Codex | `codex plugin marketplace add "$PWD"`, `codex plugin list`, then `codex plugin marketplace remove standup` | Codex finds `standup@standup` with its source at `plugin/`. |
| Gemini CLI | `gemini extensions validate .`, `gemini extensions link "$PWD"`, `gemini skills list`, then `gemini extensions uninstall standup` | The extension loads and both skills are discovered. |
| Grok | `grok plugin validate plugin` | The manifest is valid. |
| Cursor | none run | The `.cursor-plugin/` files follow Cursor's docs and have never been loaded. |
| Python 3.9 | `/usr/bin/python3 plugin/skills/eod-review/eod_review.py --check` | The engine runs on the oldest Python it claims. |

## Not yet proven

- No install from a public repository has been run in any agent. The checks above use the local folder.
- Grok's `#plugin` subfolder install and Cursor's marketplace add are from their help text and docs only.
- The copied skills have not been run inside Codex, Cursor, Gemini CLI or opencode: found is not the same as working.
