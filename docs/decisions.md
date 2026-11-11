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
- 2026-11-11: Copy rewritten after Radu's review ("unclear which agents, unclear the problem, unclear it covers what your agents did"). Headline now names the agents' work; two sections added: the problem, and which agents are read (with what is not read yet: Cursor, Gemini).
- 2026-11-11: Plugin 0.2.0 reads Gemini CLI and opencode tokens and counts Cursor and Antigravity sessions; the skills also run from other agents' skills folders. Site copy lists exactly that, including what has no token data.
- 2026-11-11: Headline and evening lede are Radu's own words. The lede shows the visitor's live local time and changes by part of day (morning 5-9, mid-morning 9-12, afternoon 12-17, evening 17-21, night 21-5). Strings: ui.ledeMorning … ui.ledeNight with a {time} slot. Without JavaScript the evening line shows with a fixed 6:21pm.
- 2026-11-11: Removed the starter's lint rule banning the word "client"; Radu's lede uses it.
- 2026-11-11: Headline is Radu's: "You and your agents were busy all day. Doing what?" No product name in it, on purpose (he does not want the joke explained).
- 2026-11-11: Plugin 0.3.0 adds named project groups (work / consulting / side / personal), reported separately. New homepage section says so.
- 2026-11-11: Sun dial added at Radu's request (src/components/SunDial.astro): a sun orbiting an earth, fixed top right from 768px, scrolling with the page below that. It sets the time shown in the lede, which lede shows, and the page colours (night, dawn, day, dusk; ground interpolated, ink flips by luminance). Left alone it follows the visitor's clock; pressing the earth returns to it. This overrides the starter's "dark follows the system" rule whenever JavaScript runs; without it the system setting still applies. New token --color-sun.
- 2026-11-11: Identity is direction 1 "Stand up": lowercase wordmark, "up" raised 0.54em (one x-height), Bold 700, tracking -0.04em. Small mark is an underscore and a raised u on ink (`public/favicon.svg`, drawn as paths). The share card carries the wordmark; its `name` slot moved to `<title>`. Source: Paper file "Standup identity".
