# Languages

- **URLs:** the default language is unprefixed (`/`, `/about/`); the others live under `/<code>/` (`/de/`, `/de/about/`).
- **Strings:** `src/i18n/<code>.json` holds `meta` (native name, hreflang, ogLocale, dir, font), `description` (the site's one sentence in that language) and `ui` (page strings; `{site}` becomes the site name). Every file keeps the same `ui` keys or the build fails.
- **Add a language:** copy a file in `src/i18n/` to `<code>.json`, fill its `meta` (`"font": "system"` for scripts the site's font lacks, such as Arabic, Hebrew, Devanagari or CJK), translate `description` and `ui`, then add the code to `locales` in `site.config.mjs` (default first).
- **Add a page:** put it in `src/pages/[...locale]/` with `getStaticPaths = localeStaticPaths`, pass `locale` to `BaseLayout`, add its strings to `ui` in every catalog, and link with `localePath(locale, '/path/')`. Every page exists in every language.
- **Translate:** `npm run build` warns (lint-copy) on each string still identical to the default language's.
- **Automatic, enforced by verify-build:** `<html lang dir>`, hreflang for every language plus `x-default` (reciprocal), matching sitemap alternates, `og:locale` + alternates, JSON-LD `inLanguage` and translation links, a noindex 404 per language (`/404.html`, `/<code>/404.html`), one `llms.txt` section per language, markdown twins with `lang`.
