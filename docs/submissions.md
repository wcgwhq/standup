# Submission copy

Ready-to-paste text for listing Standup in each vendor's directory. Where to submit and what each vendor requires is in `marketplaces.md`; re-open the vendor's page before pasting, because forms change. Written on 18 November 2026 for plugin 0.6.1.

Every statement here is true of 0.6.1. If the engine changes what it reads or sends, change this file with it.

## The basics

| Field | Value |
| --- | --- |
| Name | `standup` |
| Display name | Standup |
| Publisher / developer | What Could Go Wrong |
| Version | 0.6.1 |
| Licence | MIT |
| Price | Free |
| Repository | https://github.com/wcgwhq/standup |
| Website | https://standup.wcgw.fun |
| Documentation | https://github.com/wcgwhq/standup/blob/main/plugin/README.md |
| Support / issues | https://github.com/wcgwhq/standup/issues |
| Privacy policy | https://standup.wcgw.fun/privacy/ |
| Publisher website | https://wcgw.fun |
| Category | Productivity (second choice: Developer tools) |
| Platforms | macOS and Linux. Needs Python 3.9 or later and git. No packages. |
| Plugin icon (PNG, 512 px) | `plugin/.claude-plugin/icon.png` |
| Plugin icon URL | https://raw.githubusercontent.com/wcgwhq/standup/main/plugin/assets/icon.png |
| Publisher logo (SVG) | https://wcgw.fun/logo.svg |
| Share image (1200×630) | https://standup.wcgw.fun/og-image.png |

Keywords: standup, daily update, end of day, weekly review, git, commits, coding agents, token usage, cost, Slack.

## Descriptions

Pick the longest one the field allows.

**Tagline (38 characters)**

> Your standup update, written from git.

**One line (96 characters)**

> Writes your standup update from your git commits and your coding agents' sessions, on your disk.

**Short (115 characters, fits opencode's 120-character tagline)**

> Reads your git commits and your agents' sessions and writes the standup update you can no longer write from memory.

**Medium (about 50 words)**

> Standup reads your git commits and your coding agents' sessions and writes your update for a day, a week or a month: four to six lines you can paste into Slack or say out loud. Behind them are the numbers: commits per repo, work not committed yet, tokens and an estimated cost.

**Long (about 200 words)**

> You start three things before lunch, an agent finishes two of them, and another runs in a worktree you forgot about. By the end of the day "what did you work on?" is a hard question.
>
> Standup answers it. Say "write my standup update" and it reads your git commits and the session files your coding agents keep on your disk, then writes four to six lines you can paste into Slack or say at standup. Ask for this week or this month and it covers every day in the range.
>
> Behind the update are the numbers: commits per repository, projects with work and no commit yet, tokens by type, and an estimated cost at API list prices.
>
> It reads git plus eight agents. Claude Code, Codex, Grok, Gemini CLI, opencode and Cowork give tokens and cost. Cursor and Antigravity give session counts. Work run in Superconductor or Conductor worktrees is counted under its real repository.
>
> Five voices are built in if plain is too plain: pirate, Gen Z, corporate, one-liner and observational. A Slack markup style adds bold names and inline code.
>
> Its scripts are plain Python with no packages, and they open no network connection.

## What to try

For "example prompts", "starter prompts" or "how to test".

- Write my standup update
- Write my standup update for this week
- What did we ship this month?
- Write my standup update with the numbers
- Write my standup update in pirate voice
- Write my standup update with Slack markup
- How many tokens did we use today?

## Features

For a bullet-list field.

- An update for a day, a week, a month or any date range.
- Reads git for what shipped, whoever wrote it, you or an agent.
- Token counts and an estimated cost from Claude Code, Codex, Grok, Gemini CLI, opencode and Cowork; session counts from Cursor and Antigravity.
- Marks a merge, finished work and work in progress differently, so nobody reads a merge as new work.
- Lists projects with work on disk and no commit yet.
- Keeps work, consulting and personal projects apart, each with its own totals.
- Follows orchestrator worktrees back to their real repository.
- Five built-in voices and a Slack markup style; add your own.
- Python 3.9 or later and git. No packages, no account, no network.

## Data handling

For questionnaires. Answer each question as the form asks it; these are the facts.

| Question | Answer |
| --- | --- |
| Does the plugin collect personal data? | No. It has no server and no account. |
| Does it send data to the developer? | No. Nothing is sent to What Could Go Wrong. |
| Does it make network requests? | No. Its scripts open no network connection. |
| What does it read? | Local files only: git history of the repositories you point it at, and the session files that coding agents write on your disk (Claude Code, Codex, Grok, Gemini CLI, opencode, Cowork, Cursor, Antigravity). |
| What does it write? | Nothing outside its own settings folder, `~/.claude/standup/`, which holds your groups, style and pricing. |
| What reaches the model provider? | The report the script prints becomes part of your conversation with your agent, so it reaches your model provider like anything else you say: folder paths, commit subjects, names of changed files, token counts and, when a repository has commits by someone else, their email address. No file contents and no session transcripts. |
| Does it run code? | Yes, two Python scripts in the skill's folder, run by the agent when you ask for an update. No lifecycle hooks, no background process, no MCP server. |
| Does it need credentials? | No. No API keys, tokens or logins. |
| Third-party services | None. |
| Telemetry or analytics in the plugin | None. |

**One-paragraph version**

> Standup runs on your machine and has no server, account or telemetry. Its two Python scripts read your local git history and the session files your coding agents keep on your disk, and they open no network connection. The report they print is handed to your agent, so it reaches your model provider as part of your conversation: folder paths, commit subjects, names of changed files and token counts. Nothing is sent to What Could Go Wrong.

## Privacy policy

OpenAI's catalog needs an HTTPS privacy-policy URL: **https://standup.wcgw.fun/privacy/**. The page is the full text; this is its summary, for a form that wants the policy pasted.

> **The plugin.** Standup runs on your computer. It has no server and no account, and its scripts open no network connection. It reads your local git history and the session files your coding agents keep on your disk. The report it prints is given to your agent, so it reaches your model provider as part of your conversation, under that provider's terms: folder paths, commit subjects, names of changed files and token counts. What Could Go Wrong receives none of it.
>
> **This website.** standup.wcgw.fun uses Microsoft Clarity to see how its pages are used. It sets a cookie only if you say yes to the question on your first visit, and you can change your answer on the About page. The site is served by Cloudflare, which keeps standard request logs.
>
> **Contact.** Open an issue at github.com/wcgwhq/standup.

## Notes for the reviewer

For "how can we test this" or "anything the reviewer should know".

> Install it, open any folder that holds a git repository with a commit from today, and say "write my standup update". The plugin is one skill, `standup`. Its instructions tell the agent to run `standup.py` (a day) or `standup_week.py` (a week, a month or a range) from the skill's folder and to write the update from the printed report. Both scripts are plain Python 3.9 with no imports outside the standard library and no network calls. `python3 standup.py --check` prints what it can read on this machine. With no agent session files present it still reports the git commits.

## Vendor by vendor

### Anthropic (claude.ai/directory/manage)

Not possible, as of 18 November 2026. The directory's validator accepts scripts only from Verified organisations, and the plugin's engine is two Python files. There is no application to become Verified; the public docs do not describe one. Claude Code users install from the repository instead, which needs no listing. Do not work around the rule by hiding the scripts in other file types.

If Anthropic ever verifies the organisation, three things must change before validating: remove `allowed-tools` from `SKILL.md` (anything beyond Read, Grep, Glob and LS is refused), keep every image a PNG, JPEG, GIF, WebP or ICO, and use the **Medium** description. The question to send through the portal's "Contact Anthropic" is how an organisation becomes Verified, and whether Python scripts that `SKILL.md` tells Claude to run are accepted without it, since the pre-submission checklist says they are not part of the check.

### Cursor (cursor.com/marketplace/publish)

- Repository link: https://github.com/wcgwhq/standup
- Description: **One line**. Longer field: **Medium**.
- Open source: yes, MIT.
- Before submitting, turn the plugin on in Cursor once and ask for an update. That has not been done.

### xAI Grok (pull request to xai-org/plugin-marketplace)

Checked on 18 November 2026 against their `CONTRIBUTING.md`: fork, add one entry at the end of `.grok-plugin/marketplace.json`, run `python3 scripts/generate-plugin-index.py`, then `python3 scripts/validate-catalog.py` and `python3 scripts/generate-plugin-index.py --check`. This entry passed all three in a local copy, as a 14-line addition. Scripts are allowed; their review rejects remote code, secret reading and undeclared network calls, none of which the plugin does.

Pin `sha` to the commit to list (`git ls-remote https://github.com/wcgwhq/standup.git HEAD`). Their guide asks for brand-scoped `keywords` and `domains`, not generic words, so "standup" alone is left out.

```json
{
  "name": "standup",
  "description": "Writes your standup update for a day, a week or a month from your git commits and your coding agents' sessions, with token counts and an estimated cost. Runs on your own disk and opens no network connection.",
  "category": "productivity",
  "source": {
    "source": "url",
    "url": "https://github.com/wcgwhq/standup.git",
    "sha": "<40-character commit>",
    "path": "plugin"
  },
  "homepage": "https://standup.wcgw.fun",
  "keywords": ["wcgw standup"],
  "domains": ["standup.wcgw.fun"]
}
```

Pull request title: `Add standup`. In their template: remote source, the URL and pinned SHA above, homepage https://standup.wcgw.fun, owned by What Could Go Wrong and published under its GitHub organisation `wcgwhq`, MIT. Security section: no remote code, no secrets read, no network calls; the two Python scripts read local git history and agents' session files and print a report.

### OpenAI (platform.openai.com/plugins → Upload plugin)

OpenAI takes a ZIP of the plugin folder, and reads the listing from `plugin/plugin.json` (the Agent Plugins format, with the listing under `extensions.com.openai.interface`). That file is written and within every stated limit; change the listing there, not in the dashboard.

Make the ZIP from the committed tree, so nothing stray gets in:

```sh
git archive --format=zip -o standup-0.6.1.zip HEAD:plugin
```

| Field | Value | Limit |
| --- | --- | --- |
| `displayName` | Standup | 30 characters |
| `shortDescription` | Your standup update, from git | 30 characters (it is 29) |
| `longDescription` | the **Long** text | 4000 characters |
| `developerName` | What Could Go Wrong | set from the verified developer identity |
| `category` | Productivity | a category from the dashboard |
| `capabilities` | Read local git history · Read coding agents' session files · Write a standup update | |
| `defaultPrompt` | Write my standup update · Write my standup update for this week · How many tokens did we use today? | three, 128 characters each |
| `websiteURL` | https://standup.wcgw.fun | |
| `supportURL` | https://github.com/wcgwhq/standup/issues | |
| `privacyPolicyURL` | https://standup.wcgw.fun/privacy/ | |
| `logo`, `composerIcon` | `plugin/assets/icon.png`, 512 px | square, at least 48 px |

Left out on purpose: `termsOfServiceURL` (there are no terms; OpenAI's reference says a skills-only package does not need all four URLs) and the review test cases (for plugins with an MCP server). Choose **Skills only** if the upload asks. The publisher name shown comes from the OpenAI organisation's verification, which only Radu can do.

### opencode (pull request to awesome-opencode, once the repository is 30 days old and has 25 stars)

`data/plugins/standup.yaml`:

```yaml
name: standup
repo: https://github.com/wcgwhq/standup
tagline: Reads your git commits and your agents' sessions and writes the standup update you can no longer write from memory.
description: A skill that writes your standup update for a day, a week or a month from local git commits and coding agents' session files, with token counts and an estimated cost. Plain Python, no packages, no network. Install by copying plugin/skills/standup into ~/.config/opencode/skills/.
```

### Gemini CLI and skills.sh

Nothing to write. Gemini's gallery lists the repository from the `gemini-cli-extension` topic, which is set. skills.sh lists it the first time someone runs `npx skills add wcgwhq/standup`.

## Launch post

For a release note, a README badge row or a post.

> Standup is out. It reads your git commits and your coding agents' sessions and writes the end-of-day update you can no longer write from memory. Free, MIT, runs on your own disk. https://standup.wcgw.fun
