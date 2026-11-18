# SEO and AEO

| Piece | Where |
|---|---|
| Head + one JSON-LD `@graph` | `BaseLayout.astro`, `lib/seo.ts` |
| Publisher | `publisher` in `site.config.mjs`: the JSON-LD Organization. Empty means the site itself; set a name, URL and `sameAs` profiles when a studio or company runs it |
| Per-page extras | `BaseLayout` props: `graph` (extra JSON-LD nodes, same `@graph`), `noindex`, `ogImage`, `pageType`, `locale` |
| `llms.txt` · `llms-full.txt` · `index.md` twins | `scripts/markdown-pages.mjs`, generated after the build from the pages actually built. `llms.txt` also carries every install command. `data-md`, `data-md-label` and `data-md-text` on an element shape its markdown (the script's header) |
| One page per agent | `src/pages/[...locale]/[agent].astro`, one per `slug` in `src/data/install.json`; strings are `<id>Title`, `<id>Description`, `<id>Body` |
| Sitemap (indexable pages only) · robots (one `*` group) | `astro.config.mjs`, `pages/robots.txt.ts` |
| Headers (one `/*`) | `public/_headers` |
| Manifest · theme-color · viewport-fit | `BaseLayout` + `pages/site.webmanifest.ts`; both read their colors from `src/styles/global.css` (`src/lib/theme.ts`) |
| `dateModified` | The last commit's date (`modified` in `site.config.mjs`); a page passes its own to `BaseLayout` |
| Contract | `scripts/verify-build.mjs`: also one title and description per page in a language, and every internal link lands on a built page |

`noindex` is the one switch: a noindex page drops out of the sitemap, `llms.txt` and the markdown twins. If you add `/tools/*`: pass `noindex` (noindex + out of sitemap).
