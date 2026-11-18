# Share card and icons

| Asset | How |
|---|---|
| Share card 1200×630 | `ogImage` on `BaseLayout` takes a PNG or JPEG under `public/`; `verify-build` fails when a page's file is missing. `npm run generate:og` renders `scripts/og-template.html` with the site name, the default language's `description` and the paper/ink/accent tokens. Needs Chrome or Chromium. Refuses while the description is the placeholder. |
| Icons | `npm run generate:icons` renders `public/favicon.svg` on `--color-paper` at each size, and writes `favicon.ico`. Needs Chrome or Chromium. |
| More pictures | `scripts/chrome.mjs` drives one headless Chrome with no dependency: use it for a share card per page or any other rendered image |
| Layout | Absolute `og:image` / Twitter image via `Astro.site`, never relative |

The committed `og-image.png` and PNG icons are neutral ink on paper; `favicon.svg` already uses the accent. Run both generators once the brand is set.
