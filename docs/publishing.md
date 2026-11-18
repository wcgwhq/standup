# Publishing the plugin

The repository is `wcgwhq/standup` on GitHub, created private on 16 November 2026 and made **public** on 17 November 2026, after the sweep recorded in `docs/decisions.md`. The steps below are the record of what came first. The site is deployed to Cloudflare Pages straight from disk.

## Before it goes public

1. ~~The email in the history.~~ Done on 16 November: every commit now carries the GitHub no-reply address, and this repository's git config uses it for new commits. The first push, which had the personal address, was kept as the private `wcgwhq/standup-old-history`, which Radu deleted; on 17 November GitHub no longer resolves it.
2. ~~Names in the examples.~~ Decided on 16 November: the real project names stay, with the two Romanian ones shown in English (My Pension, pension-meter).
3. ~~Owner name in the manifests.~~ Done on 16 November: What Could Go Wrong.
4. ~~Switch the repository to public~~ Done on 17 November. (Settings, or `gh repo edit wcgwhq/standup --visibility public`).
5. ~~Remove the "Not published yet" note~~ Done on 17 November: the line now states one fact about the scripts. Originally: remove `ui.installNote` from `site/src/i18n/en.json` ("Not published yet") and the two lines that print it (`index.astro`, `[agent].astro`), and redeploy the site. `llms.txt` drops the line by itself.
6. ~~Run one real install in each agent~~ Done on 17 November from the public repository: Claude Code, Codex, Gemini CLI, Grok and opencode each installed 0.6.0 and the installed engine passed `--check`. Grok refuses without `--trust`, so the command now carries it. Cursor's `marketplace add` found the plugin; turning it on is a click in its Plugins screen and was not driven. A headless Claude Code session ("write my standup update with Slack markup") picked the skill and wrote the update.
7. ~~Old skills.~~ Done on 17 November: `~/.claude/skills/eod-review` and `eow-review` were moved to the Trash once the plugin was installed.
8. Then the listings, in the order in `marketplaces.md`. Anthropic's directory is out: it refuses scripts from an organisation that is not Verified (18 November).

## Checks to re-run after touching any manifest

Run from the repository root. Each one was green on 16 November 2026.

| Agent | Check | What it proves |
| --- | --- | --- |
| Claude Code | `claude plugin validate .` and `claude plugin validate plugin` | The marketplace file and the plugin manifest are valid. |
| Codex | `codex plugin marketplace add "$PWD"`, `codex plugin list`, then `codex plugin marketplace remove standup` | Codex finds `standup@standup` with its source at `plugin/`. |
| Gemini CLI | `gemini extensions validate .`, `gemini extensions link "$PWD"`, `gemini skills list`, then `gemini extensions uninstall standup` | The extension loads and the skill is discovered. |
| Grok | `grok plugin validate plugin` | The manifest is valid. |
| Cursor | none run | The `.cursor-plugin/` files follow Cursor's docs and have never been loaded. |
| OpenAI | `python3 -m json.tool plugin/plugin.json` and the limits in `submissions.md` | The listing manifest parses. There is no local validator for it; OpenAI checks it on upload. |
| Python 3.9 | `/usr/bin/python3 plugin/skills/standup/standup.py --check` | The engine runs on the oldest Python it claims. |

## Not yet proven

- The skill has been run by an agent only in Claude Code. In Codex, Gemini CLI, Grok and opencode it is installed and its engine runs, but no session there has been asked for an update: found is not the same as working.
- Cursor: the plugin has not been turned on or used.
- A paste into Slack with markup on has not been tried.
