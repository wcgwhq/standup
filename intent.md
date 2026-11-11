# intent.md — Standup

Product scope. Update it when scope changes. Agents: do not invent product scope beyond this file.

## One sentence

> Standup reads your git commits and your agents' sessions and writes the end-of-day update you can no longer write from memory.

## Audience

- Primary: people who have to say what they worked on and find it hard to pull together, because a day of agent sessions, branches and repos is too much to hold in your head. Team members who feel they must justify their day, and the team leads who ask.
- Most of them work across several projects at once, often split into work, consulting or side gigs, and personal. The report has to keep those apart.
- Secondary: solo developers who cannot remember by evening what they did in the morning. For them it is a catch-up with yourself.

## One job

The homepage exists to make visitors do **one** thing:

- Copy the install command for the Claude Code plugin.

## Success looks like

- A visitor can say what Standup writes, and from what, after reading the first screen.
- They copy the install command.
- They know before installing that everything is read from files on their own machine.

## Out of scope

- Accounts, sign-up forms, waitlists and analytics dashboards.
- Hosted reports or anything that uploads commits or transcripts.
- Pricing. The plugin is free and MIT licensed.
- Documentation beyond the homepage. The plugin README is the reference.

## Languages

en (the first is the default, served at `/`). Source of truth: `locales` in `site.config.mjs`.

## Voice

Tone in three words:

- Plain, exact, unhurried.

Write to someone tired at the end of the day. State what the tool reads and what it writes. Numbers are estimates and the copy says so.

Words we never use: add them to `RULES` in `scripts/lint-copy.mjs` so the build enforces them.
