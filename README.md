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

Pick your agent, run one command, then ask it for today's EOD.

| Agent | Command |
| --- | --- |
| Claude Code | `/plugin install standup --marketplace wcgwhq/standup` |
| Codex | `codex plugin marketplace add wcgwhq/standup && codex plugin add standup@standup` |
| Cursor | `cursor-agent plugin marketplace add https://github.com/wcgwhq/standup`, then turn Standup on under Plugins |
| Gemini CLI | `gemini extensions install https://github.com/wcgwhq/standup` |
| Grok | `grok plugin install wcgwhq/standup#plugin` |
| opencode | `git clone https://github.com/wcgwhq/standup ~/standup && cp -R ~/standup/plugin/skills/eod-review ~/standup/plugin/skills/eow-review ~/.config/opencode/skills/` |

Any other agent that reads `SKILL.md` folders: same as opencode, copied into `~/.agents/skills/`.

It needs Python 3.9 or later and git, on macOS or Linux. There are no packages to install.

## What you get

Four to six lines you can say out loud. Paste them into Slack, say them at standup, or keep them as proof the day happened. This is a real one, from the day the website was built:

> **EOD Wed 2026-11-11**
>
> - **Standup Site** ✅ → scaffolded, homepage written, sun dial and wordmark in, live on pages.dev
> - **Switchboard Quota (E-080)** 🔁 → rc-quota merged, eight review findings fixed
> - **Standup Plugin** ✅ → writing voices, month reports, a setup check, token counts no longer counted twice
> - **My Pension** 🚧 → site scaffolded, design prototypes and two art rounds
> - **wcgw.fun and Pipeline** 🚧 → new homepage section, pipeline plan and skills drafted
> - **wcgw Starter** ✅ → copywriting skill and a pre-commit copy review for new sites
>
> Three projects have work on disk and no commit yet. The plugin is not in git, so its line is from memory.

🔁 marks a merge, ✅ work finished here and 🚧 work still in progress, so nobody reads a merge as new work.

Behind the update are the numbers: commits per repo, projects with work and no commit yet, tokens, and an estimated cost at API list prices.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/readme/receipt-dark.png">
    <img src="docs/readme/receipt-light.png" width="520" alt="The numbers for 11 November 2026: 11 commits in three repos, three projects with no commit yet, 395.67 million tokens, about $185 at API list prices.">
  </picture>
</p>

### In another voice

Ask for "EOD in pirate voice". Facts, numbers and status marks stay as they are; only the wording changes. The first line above, three more ways:

| Voice | Line |
| --- | --- |
| `pirate` | Arr, she was bare timber at dawn and by dusk she had a homepage, a wordmark and a sun dial, for no navigator trusts a clock. She sails on pages.dev |
| `corporate` | delighted to announce that a homepage, a wordmark and a sun dial have reached general availability on pages.dev. The sun dial was not on the roadmap. It is now the roadmap |
| `one-liner` | built a sun dial for a website about saving time. It took all day |

Also built in: `genz` and `observational`. You can add your own.

### For the week or the month

`eow-review` covers Monday to Sunday day by day, and a whole month the same way. Ask "what did I ship this week?".

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/readme/week-dark.png">
    <img src="docs/readme/week-light.png" width="520" alt="Commits per day for the week of 9 November 2026: 104 on Monday, 22 on Tuesday, 11 on Wednesday.">
  </picture>
</p>

## What it reads

What shipped comes from git, whoever wrote it, you or an agent. Token counts come from the files each agent keeps on your disk.

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

The scripts open no network connection. The report they print goes to your agent, so it reaches your model provider like anything else in the conversation: folder paths, commit subjects and the names of changed files.

## More

- [`plugin/README.md`](plugin/README.md): settings, groups, date ranges, pricing and how each number is counted.
- [`site/`](site/): the website. [`docs/`](docs/): the code review, the publishing steps and the marketplace notes. [`archive/`](archive/): earlier copies of the skills, kept for reference.

MIT licensed; see [`LICENSE`](LICENSE). Published by [What Could Go Wrong](https://wcgw.fun).
