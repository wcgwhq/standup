# Publishing the plugin

The repository is `wcgwhq/standup` on GitHub, created **private** on 16 November 2026. Private on purpose: see step 1. The site is deployed to Cloudflare Pages straight from disk.

## Before it goes public

1. **The email in the history.** All commits carry Radu's personal email as author and committer. A public repository publishes it for good. Either accept that, or rewrite authorship to the GitHub noreply address before the switch (a force push; easy while nobody else has cloned).
2. **Names in the examples.** `plugin/skills/eod-review/voices/*.md` and `site/src/data/sample-report.json` carry real project names (Switchboard, Cât Vine Pensia, wcgw). The sample report is already on the public site. Keep or scrub, on purpose.
3. **Owner name in the manifests.** They say "Radu Ceuca". Change to the studio name if that is the identity.
4. **Switch the repository to public** (Settings, or `gh repo edit wcgwhq/standup --visibility public`).
5. **Remove `ui.installNote`** from `site/src/i18n/en.json` ("Not published yet"), and redeploy the site.
6. **Run one real install in each agent** from the public repository. None has been run.
7. **Old skills.** Remove `~/.claude/skills/eod-review` and `eow-review` once the plugin is installed, or both sets answer.
8. Then the listings, in the order in `marketplaces.md`.

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

- No install from the repository has been run in any agent. The checks above use the local folder.
- Grok's `#plugin` subfolder install and Cursor's marketplace add are from their help text and docs only.
- The copied skills have not been run inside Codex, Cursor, Gemini CLI or opencode: found is not the same as working.
