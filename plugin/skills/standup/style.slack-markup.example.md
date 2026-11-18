# Standup style: Slack with markup (example)

Copy to `~/.claude/standup/style.md` to make it your default, or ask for it once:
"write my standup update with Slack markup".

Use this only if your Slack reads markup when you paste. That is a setting:
Preferences → Advanced → "Format messages with markup". With it off, the asterisks and
backticks below show up as plain characters; use `style.example.md` instead.

It keeps every rule of `style.example.md` (the `•` bullet, the `◦` details under it, the
status mark, the `→` arrow, the title line, four to six items, no em dashes) and adds three
things.

**1. Bold the name of each item.** One pair of asterisks, Slack's own bold, around the
title only:

```
• *Switchboard Quota* 🔁 → `rc-quota` merged (`E-080`)
   ◦ eight review findings fixed
```

- Slack bold is a single `*`, not Markdown's `**`. Never write `**`.
- The title line is bold too: `*Standup EOD Wednesday, June 17th, 2026*`.
- Nothing else is bold. No italics, no headers, no links written as `[text](url)`.

**2. Put identifiers in inline code.** One backtick each side, for the things a reader
might search for or paste:

- branch names (`rc-quota`), ticket and plan ids (`E-080`), repo names (`standup-site`),
  commands (`/plugin install`), file names, version numbers (`0.6.0`).
- Not for ordinary words, product names in a sentence, or numbers.
- At most two or three per line. A line that is mostly code is a log, not an update.

**3. When the user asks for the numbers, put them in one code block** under the update, so
they line up in Slack's monospace:

````
```
Commits            15    wcgw-fun 8 · standup-site 7
Not committed yet        jungle-cards 516 files · standup-site 44 files
Tokens        274.94M    output 1.05M · fresh 2.80M · cache 271.09M
Estimate        ≈ $133   at API list prices
```
````

- Three backticks on their own lines, above and below. Pad with spaces, never tabs.
- Only when asked ("with the numbers", "with cost"). Team and boss-facing updates leave
  token and cost figures out, as `style.example.md` says.

A voice ("in pirate voice") still rewords each line and detail. The bold, the code spans and the
numbers stay exactly as they are.
