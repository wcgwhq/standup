---
name: eod-review
description: End-of-day / standup review for a work unit (a git branch, a worktree path, or a predefined named unit). Summarizes the day's commits AND the agent token usage + estimated cost attributable to that work — Claude Code, Codex, Grok, Claude Cowork, Gemini CLI and opencode (plus session counts for Cursor and Antigravity), including work run in orchestrator worktrees (Superconductor, Conductor) — then writes a succinct standup report. Personal projects you list are kept separate from the work totals. Use when the user asks for an EOD report, standup, daily summary, "what did we ship/do today", "how many tokens did we use", token/cost accounting for a branch/worktree/project, or usage across Codex / Grok / Gemini / opencode / Cursor / orchestrator worktrees. Designed to run cold in a fresh session with no prior chat context.
allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/eod_review.py *), Bash(python3 ${CLAUDE_SKILL_DIR}/eod_review.py)
---

# EOD Review

Produces a standup-style report for a **work unit** by combining two sources:

1. **Commits** — `git log`, filtered by branch + author + date window. A bare
   container path (e.g. `~/development`) fans out to **every child git repo** so
   brand-new repos are picked up automatically; duplicate SHAs from sibling
   worktrees/clones are collapsed.
2. **Token usage** — parsed from Claude Code transcripts (`~/.claude/projects/**/*.jsonl`),
   attributed by `cwd` (worktree) and `gitBranch`, bucketed by each entry's own
   local-date timestamp. Includes subagents and workflow agents. Three other
   agents are **folded in by default**, each with a `--no-*` opt-out:
   - **Codex CLI** (`--no-codex`) — `~/.codex` rollouts, shown as a `gpt` row.
   - **Grok CLI** (`--no-grok`) — per-turn usage from `~/.grok/logs/unified.jsonl`
     keyed by session id, cwd/model from each session's `summary.json`; shown as
     a `grok` row.
   - **Claude Cowork** (`--no-cowork`) — the VM's persisted transcript under
     `~/Library/Application Support/Claude/{local-agent-mode-sessions,claude-code-sessions}`,
     attributed by the session's `userSelectedFolders`; runs opus (no separate row).

   Four more agents are read by default (`--skip gemini,opencode,cursor,antigravity`
   leaves any of them out):
   - **Gemini CLI** — per-reply tokens from `~/.gemini/tmp/<project>/chats/*.json`,
     shown as a `gemini` row.
   - **opencode** — per-message tokens from its SQLite store, bucketed by the
     model it ran (`opus`, `gpt`, `gemini`, ...).
   - **Cursor** and **Antigravity** keep no token counts on disk, so the report
     lists how many sessions each had in the window (`sessions` in the JSON).

   Codex, Grok, Gemini CLI and opencode record no per-turn branch, so their slices match by worktree +
   day only. **Worktree-based orchestrators** (Superconductor, Conductor) run
   Claude, Codex, AND Grok in worktrees checked out *outside* the repo tree
   (`~/.superconductor/worktrees/<repo>/<slug>`, `~/conductor/workspaces/<repo>/<slug>`),
   so each recorded cwd is remapped to the real repo before matching — otherwise
   that work is invisible. In-repo worktrees (`<repo>/.worktrees/…`) already sit
   under the repo, so they match by prefix without remapping. Extra roots go in
   `config.json` (`worktree_roots`, `oneshot_roots`).
   **Personal projects** (none by default; list repo names in `config.json`'s
   `personal`) are pulled OUT of the work totals and reported as a separate
   "personal" line; they're still reported in full when you target them directly.

This is self-contained: it reads git + transcripts directly, so it works in a brand-new
session or a separate agent with zero prior context.

## How to run

`${CLAUDE_SKILL_DIR}` is the folder this file is in. Claude Code fills it in. In
any other agent (Codex, Cursor, Gemini CLI, opencode), replace it with that
folder's path yourself.

Run the engine, read its output, then write the report. Prefer `--json` so you can group
commits into themes yourself; use plain text for a quick look.

```bash
# Default: current worktree, current branch, today
python3 ${CLAUDE_SKILL_DIR}/eod_review.py

# A named unit (see units.json), as JSON for richer rendering
python3 ${CLAUDE_SKILL_DIR}/eod_review.py --unit my-app --json

# An explicit branch / worktree / window
python3 ${CLAUDE_SKILL_DIR}/eod_review.py --branch my-feature --json
python3 ${CLAUDE_SKILL_DIR}/eod_review.py --path /path/to/worktree --json
python3 ${CLAUDE_SKILL_DIR}/eod_review.py --days 7 --json          # last 7 days
python3 ${CLAUDE_SKILL_DIR}/eod_review.py --since 2026-06-10 --until 2026-06-16 --json
```

### Resolving the date window (do this FIRST, verify before reporting)

A named weekday or relative word is NOT a date. Resolve it to an explicit `YYYY-MM-DD`
against *today's actual date*, then VERIFY before you run anything else:

- Run `date -j -f "%Y-%m-%d" "<resolved-date>" "+%A %Y-%m-%d"` (macOS; on Linux
  `date -d "<resolved-date>" "+%A %Y-%m-%d"`) and confirm the
  weekday it prints is the one the user said. "Wednesday" must map to the date `date`
  itself calls Wednesday — not to "yesterday", and not to a weekday you used earlier.
- "yesterday" = today − 1. "Monday/Tuesday/…" = the most recent date with that weekday.
- NEVER trust a weekday label from earlier in this conversation — recompute every time.
  If you mislabeled a day before, the fix is to use the correct calendar date now, not
  to repeat the wrong label.
- The report header MUST show both the weekday and the date, and they must agree
  (e.g. `EOD Wed 2026-06-17`). A header whose weekday and date disagree is a bug.

### Translating the user's request to flags

- "everything / all my repos / what did I do today" → the aggregate unit if one is
  defined (conventionally `--unit work`: a container folder, all branches, Codex +
  Grok + Cowork folded in, orchestrator worktrees remapped, personal projects
  separated). This is the usual EOD.
- "EOD for <project>" → `--unit <name>` (see the predefined units).
- "EOD for the <feature> branch" → `--branch <that-branch>` (or `--unit` if defined).
- "this week" → `--days 7`. "yesterday" → `--since`/`--until` with that date.
- "everything, all branches" → `--all-branches`. "the whole team" → `--all-authors`.
- "just my personal project" → `--unit <that-project>` (reported in full).
- No work unit mentioned → just run with defaults (current worktree + branch + today).

## Flags

| Flag | Meaning | Default |
| --- | --- | --- |
| `--unit NAME` | Load a predefined unit from `units.json` | — |
| `--path` | Worktree path (matches transcript `cwd`) | current dir |
| `--branch` | Git branch (matches commits + transcript `gitBranch`) | current branch |
| `--author` | Commit author email filter | `git config user.email` |
| `--since` / `--until` | Date window `YYYY-MM-DD` | today / today |
| `--days N` | Last N days inclusive (overrides since/until) | — |
| `--all-branches` | Don't filter by branch | off |
| `--all-authors` | Don't filter commits by author | off |
| `--no-codex` | Exclude Codex CLI usage | off (Codex folded in) |
| `--no-grok` | Exclude Grok CLI usage | off (Grok folded in) |
| `--no-cowork` | Exclude Claude Cowork (local agent mode) usage | off (Cowork folded in) |
| `--skip AGENTS` | Comma list of other agents to leave out: `gemini`, `opencode`, `cursor`, `antigravity` | none skipped |
| `--pricing FILE` | Override the cost table | built-in defaults |
| `--json` | Emit JSON instead of formatted text | off |

Repo discovery roots, personal projects, and orchestrator worktree roots are
configurable via `~/.claude/eod-review/config.json`
(`{"dev_roots": [...], "personal": [...], "groups": {...}, "worktree_roots": [...], "oneshot_roots": [...]}`);
defaults are whichever of `~/development`, `~/dev`, `~/code`, `~/projects`,
`~/src`, `~/repos`, `~/Developer`, `~/workspace` exist, no personal projects,
Superconductor + Conductor worktree dirs, and Superconductor `one-shot`.

## Predefined work units

Named units live in `~/.claude/eod-review/units.json` (shared with eow-review).
None exist until the user creates the file: copy `units.example.json` from this
skill and edit it. Read the file to see which units are defined. Each unit may set `path` (supports `~`), `branch`, `author`, `all_branches`,
`all_authors`. Explicit flags always override the unit. New repos under a dev
root are auto-discovered by the aggregate — no unit needed to be counted.

## Groups (work, consulting, side projects)

`config.json` may name groups of repos:

```json
{ "groups": { "consulting": ["acme-site", "beta-api"], "side": ["my-blog"] } }
```

Repos in no group count as `work`. When groups exist the report gains a `by_group`
block (commits, tokens and cost per group) and every commit carries its `group`.
The headline totals still cover all groups together; `personal` projects stay out
of them as before.

- Write **one section per group**, in the order `by_group` lists them, and skip a
  group with nothing in it.
- **Never mix groups in one update.** If the user asks for "the consulting update",
  give only that group. An update for one customer must not mention another's work.
- Cowork sessions are not split by group and are counted under `work`.

## Writing the report

After running the engine, produce a **succinct** standup the user can paste:

- **Group commits into 4–6 user-facing themes**, not one bullet per commit. Lead with
  features/fixes, fold refactors/docs into a smaller line.
- Mention any **uncommitted / in-progress** work only if the user asks or it's obvious
  from `git status` (the engine reports commits, not the dirty tree).
- **Token headline:** report `output` and `fresh input` as the "real work" numbers, and
  state the grand total with the caveat that the bulk is cheap **cache reads (~10% rate)**.
  Quote model split only if asked — the rows are `opus`/`sonnet`/`haiku` (Claude),
  `gpt` (Codex), `grok` (Grok) and `gemini` (Gemini).
- **Agents without token counts.** When the report has a `sessions` block (Cursor,
  Antigravity), say how many sessions each had. Never invent tokens or cost for them.
- **Personal projects are a separate line.** When the report has a `personal_tokens`
  block, keep it OUT of the work headline; mention it separately only if the user
  cares ("plus ~X on personal projects"). Never fold it into the work total.
- **Cost is an ESTIMATE** at API list prices from an editable table — never present it as
  billed cost (on a Max/subscription plan there's no per-token charge). Say "≈$X at list
  prices" and only include it if the user cares about cost.
- Keep it tight: the user almost always wants "few bullet points max."

## Attribution caveats (be honest)

- **Cursor and Antigravity have no token data.** Their work still shows up in the
  commit list, and their sessions are counted, but their tokens and cost are
  missing from the totals. Say so when either appears in `sessions`.
- **Gemini CLI** sessions in a folder that cannot be matched to a repo are skipped.
- **Not read at all:** Copilot CLI, Droid, Kiro, Windsurf, Qwen. Their commits
  still appear, because commits come from git.

- Tokens are attributed by **worktree + branch + day**, not by commit — so they include
  exploration and dead-ends that produced no commit. That's the intended EOD semantics.
- If work spanned multiple worktrees/branches in one session, run per unit and note it.
- `synthetic` model rows are zero-cost local bookkeeping turns; ignore them in cost.
- **Commits are already agent-agnostic** — `git log` doesn't know whether Claude,
  Codex, Grok, or Cowork authored a change, so their commits always appeared. Folding
  the extra sources affects only the *token/cost* half. The `gpt` (Codex) and `grok`
  (Grok) rows use **placeholder list-price estimates** (neither has a cache-write
  tier) — edit `pricing.json` to correct them.
- **Orchestrator worktrees** (Superconductor, Conductor) are remapped to their
  real repo by first path segment (`<worktree_root>/<repo>/…` → the `<repo>`
  checkout), so Claude, Codex, and Grok run in a worktree all attribute to the
  repo — not to an invisible external path. Nested repos (e.g. `clients/acme/api`)
  are resolved by a bounded search; `one-shot` runs aren't a repo, so they
  attribute to the dev root (counted in the aggregate, owned by no single repo).
  **Token attribution covers all worktrees; commit listing does not walk external
  worktree roots** — it relies on `git log --all` in the main checkout, which sees
  linked-worktree commits but would miss a separate *clone* whose commits were
  never pushed back. Tokens are unaffected.
- **Grok** usage comes from one rolling log that is NOT date-partitioned and only
  spans back to when grok-cli logging began — weeks before that under-report Grok.
  Branch isn't recorded per turn, so Grok (like Codex) matches by worktree + day.
- **Personal projects** are split out of work totals into a separate
  `personal_tokens` block, EXCEPT when you target them directly — then they report
  in full. Change the list via `config.json`'s `personal`.
- **Cowork attribution is by `userSelectedFolders`, not by the transcript** — its cwd
  is a VM path, so a Cowork session is counted in full for any unit whose path it
  touches. A session that mounted several repos **can't be split per-repo**: the
  dev-wide aggregate is exact, but separately summing narrow per-repo units can
  overlap. Cowork runs opus, so it merges into the `opus` row (no separate pricing).

## Output style

If `~/.claude/eod-review/style.md` exists, read it before writing the report and
follow it: it overrides the generic formatting guidance above. No file means the
generic guidance applies. `style.example.md` in the eod-review skill is a ready
Slack-paste-safe style to copy.
