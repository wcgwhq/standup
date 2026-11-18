import type { APIRoute } from 'astro';
import { copy, defaultLocale, meta } from '@/i18n';
import { colors } from '@/lib/theme';
import { siteName } from '../../site.config.mjs';

export const GET: APIRoute = () => {
  const { hreflang, dir } = meta(defaultLocale);
  const manifest = {
    name: siteName,
    short_name: siteName,
    description: copy(defaultLocale).description,
    lang: hreflang,
    dir,
    start_url: '/',
    display: 'standalone',
    background_color: colors('paper')[0],
    theme_color: colors('accent')[0],
    icons: [
      { src: '/icon-192.png', sizes: '192x192', type: 'image/png', purpose: 'any' },
      { src: '/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any maskable' },
    ],
  };
  return new Response(JSON.stringify(manifest, null, 2), {
    headers: { 'Content-Type': 'application/manifest+json' },
  });
};
