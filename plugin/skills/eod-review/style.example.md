# Standup style (example)

Copy to `~/.claude/eod-review/style.md` and edit. This one produces updates that
paste cleanly into Slack.

Read by eod-review and eow-review before writing a report. Overrides their generic
formatting guidance.

**Per-item format** — every item is exactly:

```
[task or milestone achieved][status emoji] → [short concise description]
```

- Status emoji sits right after the title: `✅` done, `🚧` in progress, `🔁` integrated / others' work.
- Then the actual `→` glyph, then one short, concise description. Lead with the outcome.

**Arrows & dashes:**

- **Use the actual `→` glyph (U+2192), NEVER ASCII `->`** (a hyphen followed by `>`). Same
  for `↔`, not `<->`.
- **Never use em dashes (`—`) anywhere.** The separator is the `→` glyph; otherwise use
  commas, colons, or parens. Plain hyphens inside words are fine.

**Slack-paste-safe rendering** — the update MUST look like a clean bullet list when pasted into
Slack's composer, which by DEFAULT does NOT re-parse markdown on paste:

- Start each item with a literal `•` bullet character (U+2022), never a markdown `-` or `*`.
  The bullet is just a character, so it always shows — no markdown parsing required.
- Do NOT rely on markdown bold/italic. Pasted `*bold*` / `_italic_` stay LITERAL (you see the
  asterisks) unless the account has Slack Preferences → Advanced → "Format messages with markup"
  enabled. Carry emphasis with the `•` + status-emoji + `→` structure (and Title Case), never
  with `*asterisks*`.
- No markdown `#` headers (Slack shows the `#`). Use a plain title line above the bullets.
- `→`, `•`, and the status emoji always render — they are literal characters, not markup.
- Only if the user explicitly wants bold titles: tell them to enable that Advanced setting (or
  bold in-composer). Otherwise keep the output completely markup-free.

**Content:**

- Super concise, not wordy. One line per item where it fits. Cut filler, drop the play-by-play.
- **Default to the SHORTEST useful form on the FIRST pass.** Shorter is almost always what is wanted. One tight line per theme, no preamble, no per-commit detail.
  Don't post a long version and wait to be told to trim.
- **Honor a requested grouping verbatim.** If the user names buckets (e.g. "New UI" and
  "Creative Studio"), use exactly those as the section headers, in that order, and sort
  every commit into one of them — don't invent your own theme names alongside them.
- Group commits into 4-6 user-facing themes, not one bullet per commit.
- Team / boss-facing updates: no commit hashes, no token/cost numbers.
- **Don't claim others' work.** Call out merges and integrations explicitly (`🔁`), not as
  something built here, so the update reads honestly.
- **Completeness pass:** before finalizing, re-scan ALL of the day's commits so nothing real
  is missed — especially removals/extractions parked on their own branch (easy to overlook).
- Optional honest footer (no bullet): one line on where it stands (e.g. on a working branch,
  mocked backend, not yet merged) so leadership doesn't read "built" as "shipped".

**Weekly recaps (eow-review):**

- Title line: `Week of <Mon date> → <Sun date>`.
- One line per theme, synthesized across days, not one per day.
- Completeness pass covers every day of the week, including work early in the week.
