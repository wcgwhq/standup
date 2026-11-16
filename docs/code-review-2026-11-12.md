# Code review of plugin 0.4.0

Done on 12 November 2026 by an independent Opus review, read-only, at Radu's request before publishing. This is a record of what it found and what happened to each finding. Line numbers from the review are left out: the code has moved since.

## What it confirmed works

- Commits: repos found under a folder, filtered by author and branch, kept by author date, duplicates across clones merged.
- Claude Code tokens: one reply counted once. On Radu's data 89,577 usage lines became 43,436 replies.
- Codex, Gemini CLI and opencode tokens; Cursor and Antigravity session counts; SQLite files opened read-only.
- Worktree paths from Superconductor and Conductor mapped back to their repo; personal and group splits.
- Week, month and range windows, with clear messages for bad input.
- `--check` in 0.4 seconds; identical output on Python 3.9.
- No network: only the standard library, and the only subprocess is `git` with list arguments.

## Must fix before release

| Finding | Status in 0.5.0 |
| --- | --- |
| Prices 3 to 6 times too high: every Opus model priced at $15/$75, and the skill told the model to call that list price. | Fixed. One price per model from Anthropic's table of 2026-11-03; a model with no row is unpriced and said so. |
| Cowork counted about 2.3 times (no de-duplication). | Fixed. Same rule as Claude Code. |
| Grok contributes nothing on this machine, yet `--check` and every report header said it did. | Fixed in reporting: `--check` looks for usage records, and a report names only the sources that put tokens in it. The collector itself is unchanged; where current grok-cli stores usage is still unknown. |
| Stashes reported as commits, because `--all` walks `refs/stash`. | Fixed. Local and remote branches only. |
| The no-commit list ignored personal and group settings and mislabelled nested repos. | Fixed. Rows carry `personal` and `group`, and the repo is the nearest folder with a `.git`. |
| A malformed config was silently read as empty. | Fixed. The run stops with the line number. |
| Placeholder install line and no marketplace file. | Marketplace file added and valid. The install line still has `<owner>/<repo>`: there is no repository yet. |
| `eow-review` told new users to run flags it does not have. | Fixed. It names the script that has them. |

## Should fix soon

| Finding | Status |
| --- | --- |
| Commits dated in their own timezone, tokens in local time. | Fixed (`format-local`). |
| `git status` could refresh a repo's index. | Fixed (`--no-optional-locks`). |
| A `--branch` value starting with `--` read as a git option. | Fixed (`--end-of-options`). |
| "This week" mapped two ways in the skill; uncommitted work described two ways. | Fixed. |
| Personal and group names match by substring, so `docs` captures any repo's `docs/` folder. | Open. |
| `--init` builds from default folders, not an existing config's `dev_roots`; with no code folder it loops. | Open. |
| `--check` reads only the global git email. | Open. |

## Can wait

- Speed: every run parses every transcript (about 10 GB here; 19.8 s for one day). Skip files older than the window.
- opencode's reasoning tokens are counted twice.
- Codex repeated totals: fixed in 0.5.0 in passing.
- Python 3.9 drops timestamps with unusual fraction lengths (1 of 11 Antigravity rows).
- Windows does not work: paths assume `/`.
- `CODEX_HOME` and `XDG_DATA_HOME` are ignored.
- The activity list covers Claude Code only; the README once said any agent.
- The voice examples ship real project names.

## Privacy, as the review put it

The scripts send nothing. The report they print goes into the conversation, and so to the model provider: absolute paths, commit subjects, up to 15 changed file names per repo, and the email of anyone else who committed. Transcript content is never printed. `plugin/README.md` now says this under "What leaves your machine".
