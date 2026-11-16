/** JSON for a <script> block: "<" escaped so no string can close the tag. */
export const jsonLd = (value: unknown) => JSON.stringify(value).replace(/</g, '\\u003c');

export function canonicalUrl(path: string, site: URL) {
  const url = new URL(path, site);
  url.search = '';
  url.hash = '';
  // trailingSlash: 'always'
  if (!url.pathname.endsWith('/')) url.pathname += '/';
  return url.href;
}

export const absolute = (path: string, site: URL) => new URL(path, site).href;

export const websiteId = (site: URL) => absolute('/#website', site);
export const organizationId = (site: URL) => absolute('/#organization', site);

export type GraphNode = Record<string, unknown>;
