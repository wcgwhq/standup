<p align="center">
  <a href="https://standup.wcgw.fun">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="docs/readme/hero-dark.png">
      <img src="docs/readme/hero-light.png" width="640" alt="Standup. You and your agents were busy all day. Doing what?">
    </picture>
  </a>
</p>

<p align="center">
  Standup reads your git commits and your agents' sessions and writes the end-of-day update you can no longer write from memory.
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-1f6feb" alt="MIT licence"></a>
  <img src="https://img.shields.io/badge/python-3.9%2B-1f6feb" alt="Python 3.9 or later">
  <img src="https://img.shields.io/badge/packages-none-1f6feb" alt="No packages to install">
  <img src="https://img.shields.io/badge/network-none-1f6feb" alt="Opens no network connection">
</p>

<p align="center">
  <a href="#install">Install</a> ·
  <a href="#what-you-get">What you get</a> ·
  <a href="#what-it-reads">What it reads</a> ·
  <a href="plugin/README.md">Full reference</a> ·
  <a href="https://standup.wcgw.fun">Website</a>
</p>

## Install

Pick your agent, run one command, then say "write my standup update".

| Agent | Command |
| --- | --- |
| Claude Code | `/plugin install standup --marketplace wcgwhq/standup` |
| Codex | `codex plugin marketplace add wcgwhq/standup && codex plugin add standup@standup` |
| Cursor | `cursor-agent plugin marketplace add https://github.com/wcgwhq/standup`, then turn Standup on under Plugins |
| Gemini CLI | `gemini extensions install https://github.com/wcgwhq/standup` |
| Grok | `grok plugin install wcgwhq/standup#plugin --trust` |
| opencode | `git clone https://github.com/wcgwhq/standup ~/standup && cp -R ~/standup/plugin/skills/standup ~/.config/opencode/skills/` |

Any other agent that reads `SKILL.md` folders: same as opencode, copied into `~/.agents/skills/`.

It needs Python 3.9 or later and git, on macOS or Linux. There are no packages to install.

## What you get

Four to six lines you can say out loud. Paste them into Slack, say them at standup, or keep them as proof the day happened. This is a real one, from a day spent on this website:

> **Standup EOD Tuesday, November 17th, 2026**
>
> - **Standup Site** ✅ → went public
>   - deploys on every push
>   - the plugin is one skill, with a Slack markup style and sharper voices
>   - a sun dial, hourly stories, a page per agent
> - **Jungle Cards** 🚧 → live on its own domain, not committed
>   - cards drag on phones, one top bar, a monkey-hand cursor
>   - a looping city soundtrack with sound bites, haptics, a new share picture
>   - name kept, serparia.ro dropped
> - **Jungle Cards About Page** 🚧 → rewritten in the game’s single voice
>   - a bigger, snarkier author card
>   - picked from three painted versions
> - **WCGW Brand** ✅ → design system rebuilt on the real logo
>   - social and avatar sets
>   - 43 picked renders, profile crops, a stop-motion loop
> - **wcgw.fun** 🔁 → four pull requests from Cursor merged
>   - an Astro landing, an editorial manifesto
>   - the WCGW mark in the masthead
>
> Jungle Cards went live with no commit that day. Read the next morning, so the day is complete.

The Jungle Cards lines have no commit behind them: they come from what was asked in the agent sessions that day.

🔁 marks a merge, ✅ work finished here and 🚧 work still in progress, so nobody reads a merge as new work.

Behind the update are the numbers: commits per repo, projects with work and no commit yet, tokens, and an estimated cost at API list prices.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/readme/receipt-dark.png">
    <img src="docs/readme/receipt-light.png" width="520" alt="The numbers for 17 November 2026: 19 commits in two repos, one project with work on disk, 385.04 million tokens, about $192 at API list prices.">
  </picture>
</p>

### In another voice

Ask for "EOD in pirate voice". Facts, numbers and status marks stay as they are; only the wording changes. The first item above, three more ways:

| Voice | Line |
| --- | --- |
| `pirate` | hoisted the colours, she sails public now<br>◦ launches herself at every push<br>◦ one skill aboard, with a Slack markup style and voices sharpened on the whetstone<br>◦ a sun dial, hourly stories and a berth for every agent |
| `corporate` | pleased to report a successful public listing<br>◦ continuous deployment on every push<br>◦ portfolio consolidated into one skill, with a Slack markup style and sharper voices<br>◦ additional deliverables: a sun dial, hourly stories, a page per agent |
| `one-liner` | went public. A tool that tells you what you did, built by someone who needed it<br>◦ deploys on every push<br>◦ one skill, Slack markup, sharper voices<br>◦ a sun dial, hourly stories, a page per agent |

Also built in: `genz` and `observational`. You can add your own.

### For the week or the month

A week is covered Monday to Sunday, day by day, and a whole month the same way. Say "write my standup update for this week".

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/readme/week-dark.png">
    <img src="docs/readme/week-light.png" width="520" alt="Commits per day for the week of 9 November 2026: 104 on Monday, 22 on Tuesday, 11 on Wednesday, 9 on Thursday, none on Friday, 7 on Saturday, 1 on Sunday.">
  </picture>
</p>

## What it reads

What shipped comes from git, whoever wrote it, you or an agent. What you worked on comes from what you asked your agents and what they answered. Token counts come from the files each agent keeps on your disk.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/readme/sources-dark.png">
    <img src="docs/readme/sources-light.png" width="520" alt="git: every commit. Claude Code, Codex, Grok, Gemini CLI, opencode and Cowork: tokens and cost. Cursor and Antigravity: sessions counted.">
  </picture>
</p>

- **Work, consulting and side projects stay apart.** Point it at the folder that holds all your repos, name your groups, and each gets its own commits and its own cost.
- **Worktrees are followed home.** A session that Superconductor or Conductor ran in a separate worktree is counted under its real repo.
- **Cost is an estimate.** Anthropic models are priced out of the box at API list prices. Other models are counted and marked unpriced until you add their rates. On a subscription you pay none of it per token.

## What leaves your machine

The scripts open no network connection. The report they print goes to your agent, so it reaches your model provider like anything else in the conversation: folder paths, commit subjects, the names of changed files and short excerpts of what you asked your agents and what they answered.

## More

- [`plugin/README.md`](plugin/README.md): settings, groups, date ranges, pricing and how each number is counted.
- [Questions](https://standup.wcgw.fun/faq/) and the [changelog](https://standup.wcgw.fun/changelog/) are on the website.
- [`site/`](site/): the website. [`docs/`](docs/): the code review, the publishing steps and the marketplace notes. [`archive/`](archive/): earlier copies of the skills, kept for reference.

MIT licensed; see [`LICENSE`](LICENSE). Published by [What Could Go Wrong](https://wcgw.fun).
