# Decisions

Project-wide. Site decisions are in `../site/docs/decisions.md`.

- 2026-11-16: One repository for everything (Radu: "I want everything in one place"). Plain folders, not git submodules: `plugin/`, `site/`, `docs/`, `archive/`. The site repository became the parent so its history survived; the plugin, which had never been in git, moved in from `~/development/standup`.
- 2026-11-16: The marketplace manifests moved to the repository root and point at `plugin/`, because every agent installs by repository address. Gemini CLI wants its manifest and a `skills/` folder at the root, so `gemini-extension.json` is there and `skills` is a link to `plugin/skills`. Grok installs the subfolder with `#plugin`.
- 2026-11-16: The folder on disk is still called `standup-site`, because it was renamed under a live session. Rename it to `standup` when nothing has it open.
- 2026-11-16: The skills in `~/.claude/skills/` were copied to `archive/`, not moved. They are still what `/eod-review` runs until the plugin is installed and they are removed.
- 2026-11-16: The GitHub home is the organisation `wcgwhq` (Radu's pick; `wcgw`, `whatcouldgowrong` and `what-could-go-wrong` were taken), repository `wcgwhq/standup`, branch `main`. Created private first, although a public repository was approved, because the commit history carries a personal email and going public is the step that cannot be undone. See `publishing.md`.
