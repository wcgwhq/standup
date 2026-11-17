# Standup: a week, a month or a range

The second half of the standup skill; `SKILL.md` sends you here when the request covers
more than a day or two. Produces a recap for a **work unit** over a
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
   Support/Claude`, attributed by `userSelectedFolders`). Codex and Grok
   carry no per-turn branch, so they match by worktree + day. **Worktree-based
   orchestrators** (Superconductor, Conductor) run Claude, Codex, AND Grok in
   worktrees checked out outside the repo tree (`~/.superconductor/worktrees/…`,
   `~/conductor/workspaces/…`); each cwd is remapped to the real repo so that work
   is attributed, not lost. **Personal projects** (none by default; set in
   `config.json`) are split into a separate line, unless targeted directly.

This reuses the day engine (`standup.py`, next to this file) under the hood (same
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
python3 ${CLAUDE_SKILL_DIR}/standup_week.py

# A named unit (the same units.json as the day report), as JSON for richer rendering
python3 ${CLAUDE_SKILL_DIR}/standup_week.py --unit my-app --json

# Last week
python3 ${CLAUDE_SKILL_DIR}/standup_week.py --unit my-app --week-offset -1 --json

# Explicit branch / worktree
python3 ${CLAUDE_SKILL_DIR}/standup_week.py --branch my-feature --json
python3 ${CLAUDE_SKILL_DIR}/standup_week.py --path /path/to/worktree --json
```

### Verify the window before reporting

You don't compute the window, but you DO confirm the script chose the week the
user meant. The header prints both the ISO week number and the Mon -> Sun dates
(e.g. `STANDUP (week 25, 2026)` / `window: 2026-06-15 -> 2026-06-21`):

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
  separated). This is the usual request.
- "Standup for <project> this week" → `--unit <name>` (see the predefined units).
- "This week on the <feature> branch" → `--branch <that-branch>` (or `--unit` if defined).
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

The default window is one clean Mon-Sun week, moved by `--week-offset`. Two other
windows use the same report, one at a time:

| Flag | Window |
| --- | --- |
| `--month` | The current calendar month. `--month last` is the previous one, `--month 2026-10` a named one |
| `--since YYYY-MM-DD` `--until YYYY-MM-DD` | Any range. `--until` defaults to today |

A month or a range lists only the days that have commits, under a heading per ISO
week, and the JSON `window` says `kind` (`week`, `month`, `range`), `label`
("November 2026"), `days`, and `complete` (false while the window runs past today:
say "so far" in the title). For a month, write one line per theme across the whole
month, title it `<Month Year>`, and name the weeks only where it helps. Claude Code
deletes transcripts after about 30 days, so a month older than that has commits
and few or no tokens: say so.

The JSON also carries `activity` (projects with sessions and no commits); handle
it as `SKILL.md` describes under "Work that left no commit". For
first-run setup, run `python3 ${CLAUDE_SKILL_DIR}/standup.py --check`;
this script has no `--check` of its own.

## Predefined work units

Shared with the day report: the same `~/.claude/standup/units.json` (no second
file to maintain). None exist until the user creates it from this skill's
`units.example.json`; read the file to see which are defined. Each unit may set `path` (supports `~`), `branch`, `author`,
`all_branches`, `all_authors`. Explicit flags always override the unit. New repos
under a dev root are auto-discovered by the aggregate.

## Groups (work, consulting, side projects)

Same as the day report: when `config.json` names `groups`, the report has a `by_group`
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
  **cache reads**. Quote model split only if asked. There is one row per model, named
  by its id (`opus-5-5`, `fable-5-2`, `gpt-...`). Name only the sources listed in
  `contributed`, and when `tokens.unpriced` is not empty say the estimate leaves those
  models out, as `SKILL.md` describes.
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
- The source caveats in `SKILL.md` apply (it is the same engine): non-Anthropic
  rows are unpriced until rated in `pricing.json`; orchestrator
  (Superconductor/Conductor) worktrees are remapped to their repo so Claude,
  Codex, and Grok run there are all attributed; personal projects
  are split into a separate `personal_tokens` block unless targeted directly.
- **Grok's log is not date-partitioned and starts when grok-cli logging began**,
  so a week that predates it under-reports Grok — worth a caveat for older weeks.

## Output style

If `~/.claude/standup/style.md` exists, read it before writing the report and
follow it: it overrides the generic formatting guidance above. No file means the
generic guidance applies. `style.example.md` in this skill is a ready
Slack-paste-safe style to copy.

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
