---
name: copywriting
description: Write and review the words on this site against AGENTS.md → Copy: headlines, body, buttons, links, form labels, errors, empty states, alt text and meta descriptions. Use when writing or changing user-facing text, when asked to review or punch up copy, and when the pre-commit hook asks for a copy review.
---

# Copywriting

`/copywriting` reviews the copy changed since the last commit. `/copywriting all` reviews every page. `/copywriting <path>` reviews that file or folder. To write new copy, draft it, then run the same steps on the draft.

## 1. Load the reader and the facts

Read `intent.md` (the reader, the one job, the voice) and what the site knows: `src/data/`, `docs/`, `docs/decisions.md`. Specific copy is built from facts. When a line needs a fact you lack (a price, the hours, a count, a name), write the most specific line the facts you hold allow and put the missing fact on the list for the human. A plain true line beats an invented number.

Done when you can name the reader in one line and list the facts you hold.

## 2. Collect every line in scope

User-facing text lives in `src/i18n/<code>.json` (`description` and `ui`) and `src/content/`. Also read the `alt`, `aria-label` and `title` attributes in `src/pages`, `src/components` and `src/layouts`. On a canvas (Paper, Figma), take the text layers of the artboards in scope.

Done when every line is listed with its key or file.

## 3. Judge each line

Read [tells.md](tells.md). Then give each line one verdict:

- **keep**: passes the swap test, makes one claim, and carries a fact or an action.
- **rewrite**: the job is right, the words are generic, buried or padded.
- **cut**: does no job (AGENTS.md → The bar). When the screen stops making sense without it, the layout needs the fix; note it for the human.

Done when every line has a verdict.

## 4. Rewrite

Start each rewrite from its fact and build the sentence around it; synonyms dropped into the old sentence keep the slop. Keep the slot's size: a button stays a few words, a hero sentence stays one sentence. Rewrite the default language first, then carry the meaning, not the word order, into every other catalog in `src/i18n/`. A new `description` is the site's one sentence: replace the old one everywhere it appears (AGENTS.md → How you must work, step 2).

Done when every rewrite passes the swap test and shows none of the tells.

## 5. Check and stamp

1. `npm run build` is green.
2. Read the rendered page top to bottom as the reader. Every line earns its place.
3. `node scripts/copy-reviewed.mjs` records that this copy was reviewed, so the pre-commit hook lets the commit through. It marks a finished review; run it last.

## Report

| Where | Before | After |
| --- | --- | --- |
| `en.json ui.about` | … | … |

Then the facts still needed from the human, one per line, and any layout fix from step 3.
