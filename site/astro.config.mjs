// @ts-check
import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { rename, rmdir } from 'node:fs/promises';
import { join } from 'node:path';
import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import sitemap from '@astrojs/sitemap';
import tailwindcss from '@tailwindcss/vite';
import { catalog, dist, isNoindex } from './scripts/shared.mjs';
import { defaultLocale, devPort, locales, siteUrl } from './site.config.mjs';

/** The sitemap lists a page only if its built HTML is indexable. */
const indexable = (/** @type {string} */ page) => {
  const file = join(dist, decodeURI(new URL(page).pathname), 'index.html');
  return existsSync(file) && !isNoindex(readFileSync(file, 'utf8'));
};

/**
 * Cloudflare Pages serves the nearest 404.html up the tree. src/pages/404.astro already builds
 * /404.html; move each other locale's /<code>/404/index.html to /<code>/404.html.
 */
/** @type {import('astro').AstroIntegration} */
const notFoundPages = {
  name: 'not-found-pages',
  hooks: {
    'astro:build:done': async ({ dir }) => {
      for (const code of locales.filter((locale) => locale !== defaultLocale)) {
        const folder = new URL(`${code}/404/`, dir);
        await rename(new URL('index.html', folder), new URL('../404.html', folder));
        await rmdir(folder);
      }
    },
  },
};

const hreflangs = Object.fromEntries(locales.map((code) => [code, catalog(code).meta.hreflang]));

const port = Number(process.env.PORT) || devPort;

/** strictPort stops dev on a busy port. Say how to run it on another one. */
/** @type {import('astro').AstroIntegration} */
const busyPort = {
  name: 'busy-port',
  hooks: {
    'astro:server:setup': ({ server, logger }) => {
      const hint = (/** @type {NodeJS.ErrnoException} */ error) => {
        if (error.code !== 'EADDRINUSE') return;
        // The port dev tried, --port included (.claude/launch.json passes one).
        const taken = server.config.server.port;
        logger.error(`Port ${taken} is taken. Run: PORT=${taken + 1} npm run dev`);
      };
      server.httpServer?.once('error', hint).once('listening', () => server.httpServer?.off('error', hint));
    },
  },
};

/** Pages in src/dev/ exist under `npm run dev` only, at /dev/<name>/. A build never ships them. */
/** @type {import('astro').AstroIntegration} */
const devPages = {
  name: 'dev-pages',
  hooks: {
    'astro:config:setup': ({ command, injectRoute }) => {
      const folder = new URL('src/dev/', import.meta.url);
      if (command !== 'dev' || !existsSync(folder)) return;
      for (const file of readdirSync(folder).filter((name) => name.endsWith('.astro'))) {
        injectRoute({
          pattern: `/dev/${file.slice(0, -'.astro'.length)}`,
          entrypoint: new URL(file, folder),
        });
      }
    },
  },
};

export default defineConfig({
  site: siteUrl,
  output: 'static',
  trailingSlash: 'always',
  server: { port },
  i18n: { locales, defaultLocale, routing: { prefixDefaultLocale: false } },
  integrations: [
    react(),
    notFoundPages,
    busyPort,
    devPages,
    sitemap({
      filter: indexable,
      // With more than one locale, each URL lists the same alternates as its HTML head, x-default included.
      i18n: { defaultLocale, locales: hreflangs },
      serialize: (item) => {
        const fallback = item.links?.find((link) => link.lang === hreflangs[defaultLocale]);
        return fallback
          ? { ...item, links: [...(item.links ?? []), { url: fallback.url, lang: 'x-default' }] }
          : item;
      },
    }),
  ],
  vite: {
    plugins: [tailwindcss()],
    // Never inline fonts into the render-blocking CSS; unicode-range then skips unused subsets.
    build: { assetsInlineLimit: 0 },
    // A busy port is an error, never a silent move: the local URL points at this one.
    server: { strictPort: true },
    // Builds get their own dependency cache so a production build never overwrites
    // the dev server's pre-bundled React ("_jsxDEV is not a function").
    cacheDir: process.argv.includes('dev') ? 'node_modules/.vite' : 'node_modules/.vite-build',
    optimizeDeps: {
      include: ['react', 'react-dom', 'react-dom/client', 'react/jsx-runtime', 'react/jsx-dev-runtime'],
    },
  },
});
