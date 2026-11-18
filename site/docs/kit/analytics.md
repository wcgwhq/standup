# Analytics and the cookie question

This site has its own analytics code, older than the kit's. `wcgw upgrade` offers the kit's `Analytics.astro`, `Consent.astro` and `src/lib/consent.ts`: leave them out.

- `clarityId` in `site.config.mjs` is the Microsoft Clarity project ID; `''` turns Clarity off. There is no Google Analytics.
- `BaseLayout.astro` loads Clarity in `<head>`, on the canonical host only, with consent denied: no cookie until the visitor says yes. It reads the stored answer and sets `data-consent` on `<html>` (`ask`, `yes` or `no`).
- `src/components/ConsentNote.astro` asks once per browser and keeps the answer in `localStorage` under `standup-consent`. A `data-consent-reset` button asks again; the privacy page has one.
- `/privacy/` (`src/pages/[...locale]/privacy.astro`) is this site's own text, in `privacy*` strings in `src/i18n/en.json`. Bump its `updated` date with the text.

`verify-build` fails when a page loads Clarity without the question, loads a Google tag, or `/privacy/` is missing.
