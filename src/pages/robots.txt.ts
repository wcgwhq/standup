import type { APIRoute } from 'astro';
import { contentSignal } from '../../site.config.mjs';

// One * group: a crawler with its own group ignores *, so Content-Signal would not reach it.
export const GET: APIRoute = ({ site }) =>
  new Response(
    [
      'User-agent: *',
      `Content-Signal: ${contentSignal}`,
      'Allow: /',
      '',
      `Sitemap: ${new URL('/sitemap-index.xml', site).href}`,
      '',
    ].join('\n'),
    { headers: { 'Content-Type': 'text/plain; charset=utf-8' } },
  );
