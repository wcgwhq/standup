import { getRelativeLocaleUrl } from 'astro:i18n';
import { defaultLocale, locales, siteName, siteUrl } from '../../site.config.mjs';

export { defaultLocale, locales };

type Catalog = {
  meta: {
    name: string;
    english: string;
    hreflang: string;
    ogLocale: string;
    dir: 'ltr' | 'rtl';
    /** 'system' for scripts JetBrains Mono lacks (Arabic, Hebrew, Devanagari, CJK). */
    font: 'mono' | 'system';
  };
  description: string;
  ui: Record<string, string>;
};

const catalogs = new Map(
  Object.entries(import.meta.glob<Catalog>('./*.json', { eager: true, import: 'default' })).map(
    ([file, catalog]) => [file.slice('./'.length, -'.json'.length), catalog],
  ),
);

function catalog(locale: string) {
  const found = catalogs.get(locale);
  if (!found) throw new Error(`Missing src/i18n/${locale}.json for a locale in site.config.mjs.`);
  return found;
}

const uiKeys = (locale: string) => Object.keys(catalog(locale).ui).sort().join(', ');
for (const locale of locales) {
  if (uiKeys(locale) !== uiKeys(defaultLocale)) {
    throw new Error(`src/i18n/${locale}.json must have the same ui keys as ${defaultLocale}.json.`);
  }
}

/** Native name, hreflang, Open Graph locale, text direction and font. */
export const meta = (locale: string) => catalog(locale).meta;

/**
 * The site name for text in a locale. Right-to-left locales get Unicode isolates (U+2068…U+2069)
 * so a Latin name keeps its punctuation in place, including in <title> and meta where markup like
 * <bdi> cannot go.
 */
export const siteNameFor = (locale: string) =>
  meta(locale).dir === 'rtl' ? `\u2068${siteName}\u2069` : siteName;

/** The locale's description and ui strings, with {site} filled in by siteNameFor(locale). */
export function copy(locale: string): Record<string, string> {
  const { description, ui } = catalog(locale);
  const site = siteNameFor(locale);
  const strings = Object.entries(ui).map(([key, text]) => [key, text.replaceAll('{site}', () => site)]);
  return { description, ...Object.fromEntries(strings) };
}

/** A page's path in a locale: ('de', '/about/') → '/de/about/'. The default locale has no prefix. */
export const localePath = (locale: string, path = '/') =>
  getRelativeLocaleUrl(locale, path.replace(/^\//, ''));

/** A path without its locale prefix: '/de/about/' → '/about/'. */
export function pagePath(pathname: string) {
  const [, first = '', ...rest] = pathname.split('/');
  return first !== defaultLocale && locales.includes(first) ? `/${rest.join('/')}` : pathname;
}

/** The same page in every locale, default first, with its relative path and absolute URL. */
export const versions = (path: string) =>
  locales.map((locale) => {
    const localized = localePath(locale, path);
    return { locale, ...meta(locale), path: localized, url: new URL(localized, siteUrl).href };
  });

/** getStaticPaths for pages in src/pages/[...locale]/. The default locale renders at the root. */
export const localeStaticPaths = () =>
  locales.map((locale) => ({
    params: { locale: locale === defaultLocale ? undefined : locale },
    props: { locale },
  }));
