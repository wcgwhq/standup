# design.md: Standup

Craft over chrome. Design contract for **this site**. Rewrite tokens for the real brand; keep the gates.

**Truth order:** token values live in `src/styles/global.css`; gates win over any code. If code breaks a gate, fix the code.

After scaffold: fill brand here, then run `/design-quality` before claiming a UI pass. Product scope lives in `intent.md`.

---

## Gates (must pass)

Fail any gate → not done.

### G1 · Brand first
The first viewport is one composition. **Standup** is a hero-level signal. No headline, eyebrow cluster, or chrome outranks the brand. If you strip the nav and the page could belong to another product, branding failed.

### G2 · Hero budget
First viewport only: brand, one headline (or the brand *is* the headline), one short supporting sentence, one CTA group, one dominant visual. No stats strips, schedules, address blocks, promo chips, or secondary marketing in that frame. When imagery leads: full-bleed edge-to-edge plane (no inset hero cards). No floating badges, stickers, or info chips on hero media.

### G3 · One job per section
Each section: one purpose, one headline, usually one short supporting sentence. Cards are not the default container. Cards only when they wrap a real interaction.

### G4 · Tokens, not literals
Color, type, and radius come from CSS variables / `@theme` in `src/styles/global.css`. Components do not invent one-off hex or px radii. Change the tokens and the whole site reprints.

### G5 · Color harmony
The palette holds together: neutrals + accents share a clear relationship (temperature, chroma, contrast roles). Accents may be more than one when they harmonize and each has a job (e.g. brand + data verdict). Random rainbow chrome, clashing hues, or decorative color noise fails. Accents are still signals for meaning, not wallpaper (no wash / heading fill / side-stripe decoration).

### G6 · Anti-slop (reject on sight)
No purple→indigo AI defaults, lazy cream+terracotta+serif kits, glow stacks, glassmorphism, gradient text / split-color headings, colored card side-stripes, identical card grids, hero-metric templates, eyebrow kickers on every section, emoji clutter, or rounded-full pill clusters as chrome.

### G7 · Type with purpose
Never ship Inter / Roboto / Arial / system-ui as the brand voice. One family (or one deliberate pairing) with a real scale. Hierarchy from size, weight, space, and italic, not from a third novelty face. Body measure ~60–70ch when reading. `text-balance` on headings, `text-pretty` on body where it helps. `tabular-nums` for data.

### G8 · Motion budget
At most 2–3 intentional motions on a marketing surface. Compositor props only (`transform`, `opacity`). Interaction feedback ≤ ~200ms, ease-out. No bounce/elastic, no scroll-jacking, no layout-property animation. Honor `prefers-reduced-motion` (hard stop).

### G9 · A11y floor
Visible `:focus-visible` rings (never `outline: none` without a replacement). Skip link to `#main`. Real `<button>` / `<a>` / labeled inputs. Meaningful `alt` on images; decorative images `alt=""`. Body text ≥ 4.5:1. Touch targets ≥ 44px where tapped. `h-dvh` not `h-screen`. Icon-only controls need `aria-label`.

### G10 · Honesty
HTML-first marketing works with JS off. Islands only when interaction needs JS. No fake data, placeholder brands, or generated screenshots as "product". Sourced numbers live in `src/data/`. Copy: AGENTS.md → Copy and the `copywriting` skill; `scripts/lint-copy.mjs` runs on build. `/tools/*` stays noindex if heavy.

### G11 · Propose before implementing (agent)
For layout or visual-hierarchy work: describe the approach in 2–3 sentences, wait for human confirmation, then implement.

### G12 · Share surface
Absolute `og:image` 1200×630, favicon + PWA set, one `_headers` `/*` block. Unfurl shows the brand card, not a broken relative image.

### G13 · Whisper elevation
Depth from tone + hairlines first. Resting shadows stay near-invisible (≲0.05 alpha) or absent. Clear, heavy drop shadows at rest fail. Lift belongs on hover/focus/floating layers.

### G14 · North star named
`design.md` states one creative north-star sentence for this site. Agents may not invent a second aesthetic mid-build without rewriting that sentence with the human.

### G15 · Visual grounding
Do not claim UI done from source alone. Open the rendered page (or a screenshot) and check hierarchy, spacing, and contrast against what you think you shipped. Text-only self-review fails this gate.

### G16 · Separate critique pass
The agent that implemented the UI does not rubber-stamp PASS. Run `/design-quality` as its own pass (fresh checklist). Prefer a second agent or a clean turn when available. Cap fix loops at **3** unless the human raises the budget (builder ≠ reviewer).

---

## Guidance (how to design)

### Creative north star
**North star:** _A printed receipt for your day._

One narrow column on paper, set in one monospace face. Hairline and dashed rules do the structure. Numbers are tabular and right-aligned, like line items and a total. The accent marks links and focus only.

Pick one sentence for this site's atmosphere (examples: "founder's field guide", "one price on newsprint", "red pen on a manifesto"). Everything serves that sentence. Quiet surface, loud content. (Gate G14.)

### Color
- Structure in neutrals (warm or cool on purpose, not "cream by reflex").
- Harmonized accents (G5): one or several, each purposeful. Verdict / data colors when the product needs them, never as default body text.
- Light and dark (if both exist) are real appearances sharing one ramp, not an afterthought invert.

### Elevation
Prefer tone + hairlines over drop shadows. If a shadow exists at rest and you can clearly see it, it is too heavy. Lift on state, not by default.

### Imagery
Full-bleed when imagery leads the hero. No inset media cards or floating badges on hero media. Real product, place, or atmosphere; decorative gradients do not count as the visual idea.

### Interaction (islands)
Eight states when something is interactive: default, hover, focus, active, disabled, loading, error, success. Prefer native `<dialog>`, popover, and `inert` over hand-rolled traps when the stack allows. Use `cn` for class composition. Destructive actions confirm.

### Copy × design
AGENTS.md → Copy is the copy contract. Numbers do the joke when the product is satirical; copy deadpans. Languages are `locales` in `site.config.mjs`, strings live in `src/i18n/<code>.json`, and every language follows the rules in `scripts/lint-copy.mjs`.

### Orchestration loop (agents)
```
propose (G11) → implement → npm run build
  → /design-quality (G1–G16) → look at render (G15)
  → fix ≤3 rounds → human OK → ship
```
Mechanical gates (`astro check`, lint-copy, verify-build) run before any screenshot critique.

---

## Seed tokens (rewrite)

| Token | Role |
|---|---|
| `--color-paper` | Page ground |
| `--color-ink` | Body / structure |
| `--color-muted` | Secondary text |
| `--color-rule` | Hairlines |
| `--color-accent` (+ optional siblings) | Dominant accent from the CLI picker; add harmonious siblings later |
| `--font-sans` / `--font-mono` | Brand faces (JetBrains Mono is a seed, not destiny) |

## Interaction split

| Surface | Rendering |
|---|---|
| Marketing / content | Astro SSG HTML first |
| Forms / widgets | React islands (`client:idle` / `client:load`) |
| `/tools/*` | Heavy client OK; **noindex**; out of sitemap |

## Acceptance

A stranger on `/` understands **Standup** and the one job in under five seconds. `/design-quality` reports all gates green. Social unfurl shows the brand card.
