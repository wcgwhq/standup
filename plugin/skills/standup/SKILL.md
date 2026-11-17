---
name: standup
description: Writes the user's standup update, what they and their coding agents did, from git commits and agent sessions, with token usage and an estimated cost, for today, a week, a month or any date range. Use when the user says "standup", "write my standup update", "what have we done today", "what have you worked on today", "what did I work on this week", "what did we ship this month", asks for an EOD, an EOW, a daily summary or a week recap, or asks "how many tokens did we use". Works on a git branch, a worktree path or a predefined named unit. Reads Claude Code, Codex, Grok, Claude Cowork, Gemini CLI and opencode (session counts for Cursor and Antigravity), including work run in orchestrator worktrees (Superconductor, Conductor). Personal projects the user lists are kept separate from the work totals. Designed to run cold in a fresh session with no prior chat context.
allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/standup.py *), Bash(python3 ${CLAUDE_SKILL_DIR}/standup.py), Bash(python3 ${CLAUDE_SKILL_DIR}/standup_week.py *), Bash(python3 ${CLAUDE_SKILL_DIR}/standup_week.py)
---

# Standup

## Which report

| The user means | Do this |
| --- | --- |
| Today, yesterday, one named day, or no period at all | Carry on in this file (`standup.py`) |
| This week, last week, a month, or a range of dates | Read `week.md`, next to this file, and follow it (`standup_week.py`) |

When the request names no period, it is today. Do not ask. Everything below is the day
report; `week.md` builds on it and says where it differs.

Produces a standup report for a **work unit** by combining two sources:

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
     attributed by the session's `userSelectedFolders`; its tokens go in the row of
     whichever model each reply used.

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
python3 ${CLAUDE_SKILL_DIR}/standup.py

# A named unit (see units.json), as JSON for richer rendering
python3 ${CLAUDE_SKILL_DIR}/standup.py --unit my-app --json

# An explicit branch / worktree / window
python3 ${CLAUDE_SKILL_DIR}/standup.py --branch my-feature --json
python3 ${CLAUDE_SKILL_DIR}/standup.py --path /path/to/worktree --json
python3 ${CLAUDE_SKILL_DIR}/standup.py --days 7 --json          # last 7 days
python3 ${CLAUDE_SKILL_DIR}/standup.py --since 2026-06-10 --until 2026-06-16 --json
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
- The update's title line is `Standup EOD <Weekday>, <Month> <day with its ordinal>, <year>`,
  for example `Standup EOD Wednesday, June 17th, 2026`. Spell the weekday and the month
  out. The weekday and the date MUST agree; a title where they disagree is a bug.

### Translating the user's request to flags

- "everything / all my repos / what did I do today" → the aggregate unit if one is
  defined (conventionally `--unit work`: a container folder, all branches, Codex +
  Grok + Cowork folded in, orchestrator worktrees remapped, personal projects
  separated). This is the usual request.
- "Standup for <project>" → `--unit <name>` (see the predefined units).
- "Standup for the <feature> branch" → `--branch <that-branch>` (or `--unit` if defined).
- "this month", "October", "last month", or any range longer than a day or two →
  read `week.md` and run `standup_week.py` (`--month`, or `--since`/`--until`): it breaks the window down by day.
- "this week" or "last week" → read `week.md` and run `standup_week.py` (a Mon-Sun week, day by day).
  "the last 7 days" → `--days 7`. "yesterday" → `--since`/`--until` with that date.
- "everything, all branches" → `--all-branches`. "the whole team" → `--all-authors`.
- "just my personal project" → `--unit <that-project>` (reported in full).
- No work unit mentioned → just run with defaults (current worktree + branch + today).

## First run

Before the first report on a machine, or when `--unit work` answers "Unknown unit",
run the setup check. It writes nothing:

```bash
python3 ${CLAUDE_SKILL_DIR}/standup.py --check
```

Show the user what it found, in a few lines: their code folders and repo count,
the email their commits are filtered by, and which agents have data (an agent with
no data, or none in 30 days, will add nothing to the report). Read any `PROBLEM:`
line out as written. If it ends "Not set up yet", ask whether to create the files,
then run `--init`: it writes `config.json`, a `work` unit covering the first code
folder, and `style.md`, and never overwrites a file that exists. Then run the report.

## Work that left no commit

The JSON has an `activity` list: every project with Claude Code sessions in the
window, with its `turns`, `commits`, `uncommitted_files` and a sample of `changed`
paths. A project with turns and no commits is real work the commit list misses.
Give it its own line in the update, marked in progress, described from its
`changed` paths, and say in the footer that it is not committed. Never present it
as shipped.

If a project has `commits_by_other_authors`, look at who they are before using
them. An agent app's own checkpoints (for example `t3 checkpoint ref=...`) are not
work to report. Commits that are the user's under another identity are: suggest
adding that name or email to `"authors"` in `config.json`.

Work in a folder that is not a git repo, or outside the code folders, is not in
the data at all. If the user says something is missing, say that is why.

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
| `--check` | First run: show config, code folders and which agents have data. Writes nothing | off |
| `--init` | First run: write the missing config files, then show `--check` | off |

Repo discovery roots, personal projects, and orchestrator worktree roots are
configurable via `~/.claude/standup/config.json`
(`{"dev_roots": [...], "authors": [...], "personal": [...], "groups": {...}, "voice": "...", "worktree_roots": [...], "oneshot_roots": [...]}`);
`authors` lists other names or emails that are also the user (commits are matched
on the git email plus these);
defaults are whichever of `~/development`, `~/dev`, `~/code`, `~/projects`,
`~/src`, `~/repos`, `~/Developer`, `~/workspace` exist, no personal projects,
Superconductor + Conductor worktree dirs, and Superconductor `one-shot`.

## Predefined work units

Named units live in `~/.claude/standup/units.json` (shared by the day and the week reports).
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
- **Work that left no commit gets its own line**, marked in progress, as "Work that
  left no commit" above describes. A row tagged `personal` or with a `group` goes in
  that section of the update, never in the work lines.
- **Token headline:** report `output` and `fresh input` as the "real work" numbers, and
  state the grand total with the caveat that the bulk is cheap **cache reads** (billed
  at 2.5% to 10% of the input price, depending on the model).
  Quote model split only if asked. There is one row per model, named by its id:
  `opus-5-5`, `fable-5-2`, `sonnet-5-5`, `gpt-...`, and so on.
- **Name only the sources in `contributed`.** That list holds the agents that put
  tokens in this report. An agent that was read and had nothing is not in it; do not
  say its usage is included.
- **Agents without token counts.** When the report has a `sessions` block (Cursor,
  Antigravity), say how many sessions each had. Never invent tokens or cost for them.
- **Personal projects are a separate line.** When the report has a `personal_tokens`
  block, keep it OUT of the work headline; mention it separately only if the user
  cares ("plus ~X on personal projects"). Never fold it into the work total.
- **Cost is an ESTIMATE** at Anthropic's API list prices as of the `prices_as_of` date
  in the report. Never present it as billed cost (on a Max/subscription plan there's
  no per-token charge). Say "≈$X at list prices" and only include it if the user cares
  about cost.
- **Unpriced models.** `tokens.unpriced` lists models with no price row: every
  non-Anthropic model (Codex, Grok, Gemini, opencode's providers) unless the user has
  added rates to `~/.claude/standup/pricing.json`, and any Claude model newer or
  older than the built-in table. Their tokens are in the totals and their cost is NOT
  in the estimate. When that list is not empty, say so next to the figure: "≈$X at
  list prices, not counting N tokens on <models>".
- Keep it tight: the user almost always wants "few bullet points max."

## Attribution caveats (be honest)

- **Cursor and Antigravity have no token data.** Their work still shows up in the
  commit list, and their sessions are counted, but their tokens and cost are
  missing from the totals. Say so when either appears in `sessions`.
- **Gemini CLI** sessions in a folder that cannot be matched to a repo are skipped.
- **Not read at all:** Copilot CLI, Droid, Kiro, Windsurf, Qwen. Their commits
  still appear, because commits come from git.

- Tokens are attributed by **worktree + branch + day**, not by commit — so they include
  exploration and dead-ends that produced no commit. That is what a standup should count.
- If work spanned multiple worktrees/branches in one session, run per unit and note it.
- `synthetic` model rows are zero-cost local bookkeeping turns; ignore them in cost.
- **Commits are already agent-agnostic** — `git log` doesn't know whether Claude,
  Codex, Grok, or Cowork authored a change, so their commits always appeared. Folding
  the extra sources affects only the *token/cost* half. Codex and Grok rows are
  unpriced until the user adds their rates to `pricing.json`.
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
  overlap. Cowork replies are de-duplicated the same way as Claude Code's and land in
  the row of the model that wrote them.

## Output style

If `~/.claude/standup/style.md` exists, read it before writing the report and
follow it: it overrides the generic formatting guidance above. No file means the
generic guidance applies. `style.example.md` in this skill is a ready
Slack-paste-safe style to copy.

**Slack markup.** When the user asks for the update "with Slack markup", "with formatting",
"with bold" or "with code blocks", read `style.slack-markup.example.md` in this skill and
follow it for this report: bold item names, identifiers in inline code, and the numbers in
one code block when they are asked for. It needs a Slack setting, which that file names;
say so in one line after the update the first time you use it in a conversation.

## Voices

A voice changes how the report is worded. It never changes what the report says.
The built-in voices are files in this skill's `voices/` folder:
`pirate`, `genz`, `corporate`, `one-liner` and `observational`. A user's own
voices live in `~/.claude/standup/voices/<name>.md` and win on a name clash.

Use a voice only when one is chosen:

1. The user names it in the request ("eod in pirate voice", "pirate mode",
   "make it corporate"). This wins.
2. Otherwise `"voice": "<name>"` in `~/.claude/standup/config.json`.
3. Otherwise write plainly. "Plain" or "no voice" in the request turns a
   configured voice off for that report.

When a voice is chosen, read its file, then write the report under these rules:

- Every fact stays literal and unchanged: titles of work, repo and branch names,
  ticket ids, dates, counts, token and cost figures, and the status marks.
- Same lines, same order, same layout as the plain report. `style.md` still
  decides the layout; the voice only rewords the description in each line.
- The first line stays the plain title with the date, so the update can be found later.
- Jokes are about the work, the day or the writer. Never about a named person,
  a client or a group of people.
- If the user asks for a real person's voice (a named comedian, say), do not
  imitate them. Pick the nearest built-in voice, say which one you used and why.
- If a voice name matches no file, list the voices that exist and write plainly.

## After the update: say what else they can ask

After the update, leave a blank line and add one line, outside the text they will paste:

```
Try next: "for this week" · "in pirate voice" · "for last month"
```

Offer three requests that fit what they just asked: a different period, a voice
(`pirate`, `genz`, `corporate`, `one-liner`, `observational`), or one of their named
groups or units if the report showed any. Leave out anything they just used.

Skip the line when the user asked for the update only ("just the update", "nothing
else"), or when they have already seen it twice in this conversation.
