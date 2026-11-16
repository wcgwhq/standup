# standup

Two agent skills that answer "what did my agents and I do today, and what did it cost?"

They run in Claude Code as a plugin, and in any agent that reads the open
SKILL.md format (Codex, Cursor, Gemini CLI, opencode).

- **eod-review** — a standup for one day (or any date range).
- **eow-review** — a recap for one Monday to Sunday week.

Each report combines:

1. **Commits** from `git log`, filtered by branch, author and date.
2. **Agent usage** for the same work, read from each agent's local files. Work
   run in Superconductor or Conductor worktrees is attributed to its real repo.

| Agent | What is read |
| --- | --- |
| Claude Code, Claude Cowork | Tokens and estimated cost |
| Codex CLI | Tokens and estimated cost |
| Grok CLI | Tokens and estimated cost |
| Gemini CLI | Tokens and estimated cost |
| opencode | Tokens and estimated cost |
| Cursor | Session count only. Cursor keeps no token counts on disk. |
| Antigravity | Session and step count only. Its transcripts are not readable. |
| Copilot CLI, Droid, Kiro, Windsurf, Qwen | Not read yet |

Commits come from git, so the list of what shipped covers every agent, read or not.

Everything is read from files on your machine. Nothing is sent anywhere.

## Requirements

- Python 3.9+ and git. No packages to install.
- macOS or Linux. Cowork usage is read on macOS only.

## Install

```
/plugin install standup --marketplace <owner>/<repo>
```

Needs Claude Code 2.1.275 or later.

To try it from a local checkout without installing:

```bash
claude --plugin-dir /path/to/standup
```

### Other agents

Copy `skills/eod-review` and `skills/eow-review` into the folder your agent
reads skills from, keeping the two side by side. `~/.agents/skills/` is shared
by several agents; Codex also reads `~/.codex/skills/`, Cursor `~/.cursor/skills/`,
Gemini CLI `~/.gemini/skills/` and opencode `~/.config/opencode/skills/`.

## Use

Ask in plain words ("EOD for today"), or in Claude Code call the skills directly:

```
/standup:eod-review
/standup:eow-review
```

- "EOD for today" → current folder, current branch, today.
- "What did I ship this week?" → the current week.
- "EOW for last week across all my repos" → needs a `work` unit, see below.

## Configure (optional)

All settings live in `~/.claude/eod-review/`. With none of them, the skills
report on the folder and branch you are in.

| File | What it does |
| --- | --- |
| `units.json` | Named targets for `--unit <name>`: a repo, a branch, or a folder of repos. Start from `skills/eod-review/units.example.json`. |
| `config.json` | `dev_roots` (where your repos live), `groups` (named sets of repos, each reported separately), `personal` (repo names kept out of the totals), `worktree_roots`, `oneshot_roots`. |
| `style.md` | How the written report should look. Start from `skills/eod-review/style.example.md`, which pastes cleanly into Slack. |
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
  no per-token charge. The built-in prices for Codex, Grok and Gemini are placeholders;
  set your own in `pricing.json`.
- **Codex, Grok, Gemini CLI and opencode record no branch**, so their usage
  matches by folder and day.
- **Cursor and Antigravity contribute no tokens or cost**, only session counts.
  Totals are lower than the truth on days you used them.
- **History is only as long as your transcripts.** Claude Code deletes
  transcripts after 30 days unless you raise `cleanupPeriodDays` in
  `~/.claude/settings.json`.

## License

MIT
