// Serves a page's markdown twin when the request prefers text/markdown over text/html.
// Everything else passes straight through to the static files. Browsers never ask for
// markdown, so visitors always get HTML. public/_routes.json keeps assets off this function.

const quality = (accept, type) => {
  for (const part of accept.split(',')) {
    const [name, ...params] = part.trim().toLowerCase().split(';');
    if (name.trim() !== type) continue;
    const q = params.map((p) => p.trim()).find((p) => p.startsWith('q='));
    return q ? Number(q.slice(2)) || 0 : 1;
  }
  return 0;
};

export async function onRequest({ request, next, env }) {
  const url = new URL(request.url);
  if (!['GET', 'HEAD'].includes(request.method) || !url.pathname.endsWith('/')) return next();

  const accept = request.headers.get('accept') || '';
  const markdown = quality(accept, 'text/markdown');
  if (!markdown || markdown < quality(accept, 'text/html')) return next();

  const twin = await env.ASSETS.fetch(new Request(new URL(`${url.pathname}index.md`, url), request));
  return twin.ok ? twin : next();
}
