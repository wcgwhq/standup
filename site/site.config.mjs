import { existsSync } from 'node:fs';
import { loadEnvFile } from 'node:process';

// Astro evaluates config before loading .env. Read the local file explicitly.
const envFile = new URL('.env', import.meta.url);
if (existsSync(envFile)) loadEnvFile(envFile);

// prettier-ignore
const url = new URL(process.env.SITE_URL || 'http://localhost:4321/');
if (
  !['http:', 'https:'].includes(url.protocol) ||
  url.pathname !== '/' ||
  url.search ||
  url.hash ||
  url.username ||
  url.password
) {
  throw new Error('SITE_URL must be a public HTTP(S) origin without a path, credentials, query or fragment.');
}

/** Canonical origin (trailing slash). Override with SITE_URL in .env. */
export const siteUrl = url.href;

/** Human-facing site name. */
// prettier-ignore
export const siteName = process.env.SITE_NAME || 'Standup';

/** Dev server port, fixed per project so the local URL never changes. PORT=<n> npm run dev overrides it. */
export const devPort = 4817;

/** Dark appearance that follows each visitor's system setting; false is light only. Colors: global.css. */
export const darkMode = true;

/**
 * Locale codes, default first. Each has src/i18n/<code>.json. The default is unprefixed (/),
 * the rest live under /<code>/, and every page exists in every locale.
 * (prettier-ignore: the scaffold writes this array on one line, however many locales.)
 */
// prettier-ignore
export const locales = ['en'];

export const defaultLocale = 'en';

/** Content Signals (contentsignals.org) for robots.txt. Flip values here, not in the host. */
export const contentSignal = 'search=yes, ai-input=yes, ai-train=yes';

/** ISO date the site first shipped. */
export const published = '2026-11-11';
