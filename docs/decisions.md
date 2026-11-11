# Decisions

- 2026-11-11: Scaffolded with wcgw. Languages: en (default en). Accent: Blue (#155dfc). Canonical URL: http://localhost:4321/.
- 2026-11-11: Audience, one job (copy the install command), framing ("the standup writes itself") and direction ("a printed receipt for your day") set with Radu. See intent.md and design.md.
- 2026-11-11: One sentence rewritten to lead with the written update, not the cost. Cost is a supporting section.
- 2026-11-11: The homepage receipt is an illustrative example (src/data/sample-report.json), captioned "Example report". Replace with a real report when one can be shown.
- 2026-11-11: Install command lives in src/data/install.json with an <owner>/<repo> placeholder and a "Not published yet" note until the plugin repo is public.
- 2026-11-11: No copy button. The command is plain selectable text so the page works with JavaScript off.
- 2026-11-11: Independent design review run. Fixed: accent bar removed (accent is for links and focus only), headline raised above section headings, 44px link targets, receipt rows now carry a cost that sums to the total, "nothing is uploaded" moved beside the install command and its own section removed.
- 2026-11-11: Accent stays the scaffold blue. Not re-picked; Radu to decide.
- 2026-11-11: Install command form `/plugin install <name> --marketplace <owner>/<repo>` taken from `claude plugin validate` output (Claude Code 2.1.275+).
- 2026-11-11: Open from review, not fixed: theme-color and favicon repeat the accent hex outside global.css (scaffold code); SITE_URL is unset, so canonical and og:image point at localhost until a domain exists.
