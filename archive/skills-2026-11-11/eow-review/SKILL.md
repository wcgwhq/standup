---
name: eow-review
description: End-of-week / weekly review for a work unit (a git branch, a worktree path, or a predefined named unit). Summarizes the whole current week's commits (Mon-Sun, grouped by day) AND the agent token usage + estimated cost attributable to that work — Claude Code, Codex, Grok, Claude Cowork, Gemini CLI and opencode (plus session counts for Cursor and Antigravity), including work run in orchestrator worktrees (Superconductor, Conductor) — then writes a succinct weekly recap. Personal projects you list are kept separate from the work totals. Requires the eod-review skill installed alongside it. Use when the user asks for an EOW report, weekly standup, week-in-review, weekly summary, "what did we ship this week", "week recap", token/cost accounting for the week, or usage across Codex / Grok / Gemini / opencode / Cursor / orchestrator worktrees. Designed to run cold in a fresh session with no prior chat context.
allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/eow_review.py *), Bash(python3 ${CLAUDE_SKILL_DIR}/eow_review.py)
---

# EOW Review

The weekly companion to `eod-review`. Produces a recap for a **work unit** over a
full **Monday -> Sunday** week by combining two sources:

1. **Commits** — `git log`, filtered by branch + author, across the whole week,
   returned flat AND **grouped by day**. A bare container path (e.g.
   `~/development`) fans out to **every child git repo** so brand-new repos are
   picked up automatically; duplicate SHAs from sibling worktrees/clones collapse.
2. **Token usage** — parsed from Claude Code transcripts (`~/.claude/projects/**/*.jsonl`),
   attributed by `cwd` (worktree) and `gitBranch`, bucketed by each entry's own
   local-date timestamp, summed across the week. Includes subagents and workflow
   agents. Three other agents are **folded in by default**, each with a `--no-*`
   opt-out: **Codex CLI** (`--no-codex`, `~/.codex`, `gpt` row), **Grok CLI**
   (`--no-grok`, `~/.grok/logs/unified.jsonl` keyed by session id, `grok` row), and
   **Claude Cowork** (`--no-cowork`, the VM transcript under `~/Library/Application
   Support/Claude`, attributed by `userSelectedFolders`, opus row). Codex and Grok
   carry no per-turn branch, so they match by worktree + day. **Worktree-based
   orchestrators** (Superconductor, Conductor) run Claude, Codex, AND Grok in
   worktrees checked out outside the repo tree (`~/.superconductor/worktrees/…`,
   `~/conductor/workspaces/…`); each cwd is remapped to the real repo so that work
   is attributed, not lost. **Personal projects** (none by default; set in
   `config.json`) are split into a separate line, unless targeted directly.

This reuses the `eod-review` engine under the hood, so that skill must be
installed next to this one (same
attribution, same editable pricing, same shared `units.json`), so it works in a
brand-new session or a separate agent with zero prior context.

## How to run

`${CLAUDE_SKILL_DIR}` is the folder this file is in. Claude Code fills it in. In
any other agent (Codex, Cursor, Gemini CLI, opencode), replace it with that
folder's path yourself.

The week window is computed **deterministically by the script** from the real
system date — you do NOT do date math. Run the engine, read its output, then
write the recap. Prefer `--json` so you can group commits into themes yourself.

```bash
# Default: current worktree, current branch, THIS week (Mon-Sun)
python3 ${CLAUDE_SKILL_DIR}/eow_review.py

# A named unit (shared with eod-review's units.json), as JSON for richer rendering
python3 ${CLAUDE_SKILL_DIR}/eow_review.py --unit my-app --json

# Last week
python3 ${CLAUDE_SKILL_DIR}/eow_review.py --unit my-app --week-offset -1 --json

# Explicit branch / worktree
python3 ${CLAUDE_SKILL_DIR}/eow_review.py --branch my-feature --json
python3 ${CLAUDE_SKILL_DIR}/eow_review.py --path /path/to/worktree --json
```

### Verify the window before reporting

You don't compute the window, but you DO confirm the script chose the week the
user meant. The header prints both the ISO week number and the Mon -> Sun dates
(e.g. `EOW REVIEW (week 25, 2026)` / `window: 2026-06-15 -> 2026-06-21`):

- "this week" / "the week" / no qualifier → `--week-offset 0` (default).
- "last week" / "previous week" → `--week-offset -1`. Two weeks ago → `-2`, etc.
- A specific past week the user names by date → pick the offset whose printed
  Monday matches, OR confirm against `date -j -f "%Y-%m-%d" "<a date in it>" "+%A %Y-%m-%d"`
  (macOS; on Linux `date -d "<a date in it>" "+%A %Y-%m-%d"`).
- The report header MUST state the Mon-Sun range; the recap is about THAT range.

### Translating the user's request to flags

- "everything / all my repos / the whole week" → the aggregate unit if one is
  defined (conventionally `--unit work`: a container folder, all branches, Codex +
  Grok + Cowork folded in, orchestrator worktrees remapped, personal projects
  separated). This is the usual EOW.
- "EOW for <project>" → `--unit <name>` (see the predefined units).
- "EOW for the <feature> branch" → `--branch <that-branch>` (or `--unit` if defined).
- "last week" → `--week-offset -1`. "two weeks ago" → `--week-offset -2`.
- "everything, all branches" → `--all-branches`. "the whole team" → `--all-authors`.
- "just my personal project" → `--unit <that-project>` (reported in full).
- No work unit mentioned → just run with defaults (current worktree + branch + this week).

## Flags

| Flag | Meaning | Default |
| --- | --- | --- |
| `--unit NAME` | Load a predefined unit from the shared `units.json` | — |
| `--path` | Worktree path (matches transcript `cwd`) | current dir |
| `--branch` | Git branch (matches commits + transcript `gitBranch`) | current branch |
| `--author` | Commit author email filter | `git config user.email` |
| `--week-offset N` | Whole-week shift: `0`=this week, `-1`=last week | `0` |
| `--all-branches` | Don't filter by branch | off |
| `--all-authors` | Don't filter commits by author | off |
| `--no-codex` | Exclude Codex CLI usage | off (Codex folded in) |
| `--no-grok` | Exclude Grok CLI usage | off (Grok folded in) |
| `--no-cowork` | Exclude Claude Cowork (local agent mode) usage | off (Cowork folded in) |
| `--skip AGENTS` | Comma list of other agents to leave out: `gemini`, `opencode`, `cursor`, `antigravity` | none skipped |
| `--pricing FILE` | Override the cost table | built-in defaults |
| `--json` | Emit JSON instead of formatted text | off |

There are intentionally NO `--since`/`--until`/`--days` flags — a week is always
a clean Mon-Sun block selected by `--week-offset`. For arbitrary ad-hoc windows,
use `eod-review` with `--since`/`--until` instead.

## Predefined work units

Shared with `eod-review` — the same `~/.claude/eod-review/units.json` (no second
file to maintain). None exist until the user creates it from eod-review's
`units.example.json`; read the file to see which are defined. Each unit may set `path` (supports `~`), `branch`, `author`,
`all_branches`, `all_authors`. Explicit flags always override the unit. New repos
under a dev root are auto-discovered by the aggregate.

## Groups (work, consulting, side projects)

Same as `eod-review`: when `config.json` names `groups`, the report has a `by_group`
block and each commit carries its `group`. Write one section per group, skip empty
ones, and never mix two groups in one update.

## Writing the report

After running the engine, produce a **succinct weekly recap** the user can paste:

- **Group the week's commits into 4-6 user-facing themes**, not one bullet per
  commit and not one bullet per day. A week has many commits — synthesize across
  days into themes (features shipped, fixes, refactors/infra). The per-day
  breakdown in the output is your evidence, not the output format.
- Lead with the headline outcomes of the week; fold refactors/docs/chores into a
  smaller trailing line.
- **Token headline:** report `output` and `fresh input` as the "real work"
  numbers, and state the grand total with the caveat that the bulk is cheap
  **cache reads (~10% rate)**. Quote model split only if asked — the rows are
  `opus`/`sonnet`/`haiku` (Claude), `gpt` (Codex), and `grok` (Grok).
- **Personal projects are a separate line.** When the report has a
  `personal_tokens` block, keep it OUT of the work headline;
  mention it separately only if the user cares. Never fold it into the work total.
- **Cost is an ESTIMATE** at API list prices from an editable table — never
  present it as billed cost (on a Max/subscription plan there's no per-token
  charge). Say "≈$X at list prices" and only include it if the user cares.
- Keep it tight: the user almost always wants "few bullet points max."

## Attribution caveats (be honest)

- Tokens are attributed by **worktree + branch + day**, summed over the week —
  not by commit — so they include exploration and dead-ends that produced no
  commit. That's the intended review semantics.
- If work spanned multiple worktrees/branches in the week, run per unit and note it.
- `synthetic` model rows are zero-cost local bookkeeping turns; ignore them in cost.
- **Gemini CLI and opencode** tokens are folded in; **Cursor and Antigravity** keep
  no token counts, so the report's `sessions` block lists their session counts
  instead. Never invent tokens or cost for them.
- Same source caveats as `eod-review` apply (it's the same engine): `gpt`/`grok`
  rows use **placeholder pricing** (edit `pricing.json`); orchestrator
  (Superconductor/Conductor) worktrees are remapped to their repo so Claude,
  Codex, and Grok run there are all attributed; personal projects
  are split into a separate `personal_tokens` block unless targeted directly.
- **Grok's log is not date-partitioned and starts when grok-cli logging began**,
  so a week that predates it under-reports Grok — worth a caveat for older weeks.

## Output style

If `~/.claude/eod-review/style.md` exists, read it before writing the report and
follow it: it overrides the generic formatting guidance above. No file means the
generic guidance applies. `style.example.md` in the eod-review skill is a ready
Slack-paste-safe style to copy.
