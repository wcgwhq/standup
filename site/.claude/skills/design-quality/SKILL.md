---
name: design-quality
description: Gate review of the rendered site against design.md G1–G16. Use before claiming UI done, and when reviewing layout, brand or copy changes.
---

# Design quality

`/design-quality` reviews the whole site. `/design-quality <path>` reviews that file or folder.

1. Run `npm run build` and fix it until green. The build's mechanical gates come before any visual judgement.
2. Open the rendered page or a screenshot (G15). Judge the pixels, not your memory of the code.
3. Walk every gate G1–G16 in `design.md`, and run the `copywriting` skill on the page's words; quote evidence on FAIL (the DOM, CSS or source snippet).
4. Fix the highest-impact FAIL, re-render, re-check. Stop when every gate is PASS or after 3 loops, and report what is left.

Done means a fresh pass, separate from the one that built the UI, reports every gate PASS (G16).

## Report

```
## Design quality: <site or path>

### Gates
- G1 Brand first: PASS | FAIL (evidence)
- … through G16

### Fix order
1. Highest-impact FAIL first
```

## This template

- Astro static pages, Tailwind 4 `@theme` tokens in `src/styles/global.css`, optional React islands composed with `cn` from `src/lib/cn.ts`.
- Marketing pages are HTML and CSS. Add a component library only when an interaction needs one.
- Copy rules are the `RULES` list in `scripts/lint-copy.mjs`, which `npm run build` runs.
