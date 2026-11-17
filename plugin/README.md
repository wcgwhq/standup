# standup

New here? The [repository front page](../README.md) shows what a report looks like. This page is the reference.

An agent skill that answers "what did my agents and I do today, and what did it cost?"

They run in Claude Code as a plugin, and in any agent that reads the open
SKILL.md format (Codex, Cursor, Gemini CLI, opencode).

One skill, **standup**. Ask for a day and it writes the day; ask for a week, a month or a range and it writes that, day by day.

Each report combines:

1. **Commits** from `git log`, filtered by branch, author and date.
2. **Agent usage** for the same work, read from each agent's local files. Work
   run in Superconductor or Conductor worktrees is attributed to its real repo.

| Agent | What is read |
| --- | --- |
| Claude Code, Claude Cowork | Tokens and estimated cost |
| Codex CLI | Tokens. Cost once you add its rates (see Cost) |
| Grok CLI | Tokens, when its log holds usage records. Recent versions may not write them; `--check` says. Cost once you add its rates |
| Gemini CLI | Tokens. Cost once you add its rates |
| opencode | Tokens. Cost for Claude models; others once you add their rates |
| Cursor | Session count only. Cursor keeps no token counts on disk. |
| Antigravity | Session and step count only. Its transcripts are not readable. |
| Copilot CLI, Droid, Kiro, Windsurf, Qwen | Not read yet |

Commits come from git, so the list of what shipped covers every agent, read or not.

Everything is read from files on your machine, and the scripts open no network
connection. See "What leaves your machine" for what the report itself contains.

## Requirements

- Python 3.9+ and git. No packages to install.
- macOS or Linux. Cowork usage is read on macOS only.

## Install

One repository installs everywhere: it carries the manifest each agent looks for. The plugin is the `plugin/` folder of that repository.

| Agent | Install |
| --- | --- |
| Claude Code | `/plugin install standup --marketplace wcgwhq/standup` (2.1.275 or later) |
| Codex | `codex plugin marketplace add wcgwhq/standup` then `codex plugin add standup@standup` |
| Cursor | `cursor-agent plugin marketplace add https://github.com/wcgwhq/standup`, then turn Standup on under Plugins |
| Gemini CLI | `gemini extensions install https://github.com/wcgwhq/standup` |
| Grok | `grok plugin install wcgwhq/standup#plugin` |
| opencode, and any agent that reads `SKILL.md` folders | `git clone https://github.com/wcgwhq/standup ~/standup`, then copy the `plugin/skills/standup` folder into `~/.config/opencode/skills/` (opencode) or `~/.agents/skills/` |

Then say "write my standup update".

To try it from a local checkout without installing:

```bash
claude --plugin-dir /path/to/standup/plugin
```

## Use

Ask in plain words ("write my standup update", "what have we done today?"), or in Claude Code call the skill directly:

```
/standup:standup
```

It ends each update with three things to try next.

- "Write my standup update" → current folder, current branch, today. "EOD for today" does the same.
- "What did I ship this week?" → the current week.
- "EOW for last week across all my repos" → needs a `work` unit, see below.

## Configure (optional)

All settings live in `~/.claude/standup/`. With none of them, the skill
report on the folder and branch you are in.

| File | What it does |
| --- | --- |
| `units.json` | Named targets for `--unit <name>`: a repo, a branch, or a folder of repos. Start from `skills/standup/units.example.json`. |
| `config.json` | `dev_roots` (where your repos live), `groups` (named sets of repos, each reported separately), `personal` (repo names kept out of the totals), `worktree_roots`, `oneshot_roots`. |
| (first run) | `python3 plugin/skills/standup/standup.py --check` shows your code folders, the email commits are matched on and which agents have data. `--init` writes the three files below and never overwrites one. |
| `style.md` | How the written report should look. Start from `skills/standup/style.example.md`, which pastes cleanly into Slack. |
| (Slack markup) | Say "with Slack markup" for bold names, identifiers in inline code and, when you ask for the numbers, a code block. It needs Slack's "Format messages with markup" setting. To make it your default, start `style.md` from `skills/standup/style.slack-markup.example.md`. |
| `voices/<name>.md` | Your own writing voices. Built in: `pirate`, `genz`, `corporate`, `one-liner`, `observational`. Ask for one ("eod in pirate voice") or set `"voice"` in `config.json`. Facts and numbers never change, only the wording. |
| `pricing.json` | USD per 1M tokens, per model family. Overrides the built-in table. |

Example `config.json`:

```json
{
  "dev_roots": ["~/code"],
  "groups": {
    "consulting": ["acme-site", "beta-api"],
    "side": ["my-blog"]
  },
  "personal": ["my-journal"]
}
```

### Several projects at once

Point a unit at the folder that holds all your repos and one report covers every
one of them. With `groups`, the report is split per group: repos in no group are
`work`, each named group gets its own commits, tokens and cost, and `personal`
repos stay out of the totals. An update for one group never includes another's work.

## About the numbers

- **Tokens are attributed by folder, branch and day, not by commit.** They
  include exploration that produced no commit.
- **Cost is an estimate at API list prices.** On a subscription plan there is
  no per-token charge. Only Anthropic models are priced out of the box; see Cost.
- **Codex, Grok, Gemini CLI and opencode record no branch**, so their usage
  matches by folder and day.
- **Cursor and Antigravity contribute no tokens or cost**, only session counts.
  Totals are lower than the truth on days you used them.
- **History is only as long as your transcripts.** Claude Code deletes
  transcripts after 30 days unless you raise `cleanupPeriodDays` in
  `~/.claude/settings.json`.

## Day, week, month

| Ask for | Runs |
| --- | --- |
| today, yesterday, a named day | `standup.py` (`--since` / `--until`) |
| this week, last week | `standup_week.py` (`--week-offset -1`) |
| this month, last month, October | `standup_week.py --month`, `--month last`, `--month 2026-10` |
| any range | `standup_week.py --since 2026-10-06 --until 2026-10-19` |

## What it checks

- A commit counts on the day it was written (author date), so a rebase or an amend does not move it.
- One model reply is counted once, however many transcript lines Claude Code wrote for it.
- A project with agent sessions and no commit is listed with its changed files, not dropped.
- A date that is not a date, or a range that ends before it starts, stops with a message saying what to type.
- "Every branch" means local and remote branches. Stashes and tool-private refs (agent checkpoints) are not commits and are left out.
- A typo in `config.json`, `units.json` or `pricing.json` stops the run with the line number. It is never read as an empty file.

## Cost

The estimate uses Anthropic's API list prices, one row per model, as read on the date the
report prints. On a subscription you pay none of it per token.

Models with no row are **unpriced**: their tokens are counted and their cost is left out,
and the report says which. That is every non-Anthropic model (Codex, Grok, Gemini,
opencode's providers) until you add rates to `~/.claude/standup/pricing.json`:

```json
{ "gpt": { "input": 1.25, "output": 10, "read": 0.125 } }
```

A key prices every model id that starts with it. Rates are USD per million tokens.

## What leaves your machine

The scripts open no network connection. The report they print goes to your agent, which
means it goes to your model provider like anything else in the conversation: folder
paths, commit subjects, the names of changed files and, when a repo has commits by
someone else, their email address.

## License

MIT. See [`LICENSE`](LICENSE).
