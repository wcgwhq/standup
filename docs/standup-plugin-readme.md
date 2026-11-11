# standup

Two Claude Code skills that answer "what did I do, and what did it cost?"

- **eod-review** — a standup for one day (or any date range).
- **eow-review** — a recap for one Monday to Sunday week.

Each report combines:

1. **Commits** from `git log`, filtered by branch, author and date.
2. **Agent token usage** for the same work, read from local transcripts:
   Claude Code, Codex CLI, Grok CLI and Claude Cowork. Work run in
   Superconductor or Conductor worktrees is attributed to its real repo.

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

## Use

Ask in plain words, or call the skills directly:

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
| `config.json` | `dev_roots` (where your repos live), `personal` (repo names kept out of work totals), `worktree_roots`, `oneshot_roots`. |
| `style.md` | How the written report should look. Start from `skills/eod-review/style.example.md`, which pastes cleanly into Slack. |
| `pricing.json` | USD per 1M tokens, per model family. Overrides the built-in table. |

Example `config.json`:

```json
{
  "dev_roots": ["~/code"],
  "personal": ["my-side-project"]
}
```

## About the numbers

- **Tokens are attributed by folder, branch and day, not by commit.** They
  include exploration that produced no commit.
- **Cost is an estimate at API list prices.** On a subscription plan there is
  no per-token charge. The built-in prices for Codex and Grok are placeholders;
  set your own in `pricing.json`.
- **Codex and Grok record no branch**, so their usage matches by folder and day.
- **History is only as long as your transcripts.** Claude Code deletes
  transcripts after 30 days unless you raise `cleanupPeriodDays` in
  `~/.claude/settings.json`.

## License

MIT
