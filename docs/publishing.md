# Publishing the plugin

The repository is `wcgwhq/standup` on GitHub, created private on 16 November 2026 and made **public** on 17 November 2026, after the sweep recorded in `docs/decisions.md`. The steps below are the record of what came first. The site is deployed to Cloudflare Pages straight from disk.

## Before it goes public

1. ~~The email in the history.~~ Done on 16 November: every commit now carries the GitHub no-reply address, and this repository's git config uses it for new commits. The first push, which had the personal address, lives on as the private `wcgwhq/standup-old-history`; Radu asked for it to be deleted on 16 November; the `gh` login lacks the scope, so it is still there. Run `gh auth refresh -h github.com -s delete_repo`, then `gh repo delete wcgwhq/standup-old-history --yes`.
2. ~~Names in the examples.~~ Decided on 16 November: the real project names stay, with the two Romanian ones shown in English (My Pension, pension-meter).
3. ~~Owner name in the manifests.~~ Done on 16 November: What Could Go Wrong.
4. ~~Switch the repository to public~~ Done on 17 November. (Settings, or `gh repo edit wcgwhq/standup --visibility public`).
5. ~~Remove the "Not published yet" note~~ Done on 17 November: the line now states one fact about the scripts. Originally: remove `ui.installNote` from `site/src/i18n/en.json` ("Not published yet") and the two lines that print it (`index.astro`, `[agent].astro`), and redeploy the site. `llms.txt` drops the line by itself.
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
| Python 3.9 | `/usr/bin/python3 plugin/skills/standup/standup.py --check` | The engine runs on the oldest Python it claims. |

## Not yet proven

- No install from the repository has been run in any agent. The checks above use the local folder.
- Grok's `#plugin` subfolder install and Cursor's marketplace add are from their help text and docs only.
- The copied skills have not been run inside Codex, Cursor, Gemini CLI or opencode: found is not the same as working.
