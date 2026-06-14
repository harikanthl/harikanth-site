/** Serve a standards-compliant robots.txt (overrides Cloudflare managed merge on Pages). */
export async function onRequest(): Promise<Response> {
  const body = [
    'User-agent: *',
    'Allow: /',
    '',
    'Sitemap: https://harikanth.site/sitemap-index.xml',
    '',
  ].join('\n');

  return new Response(body, {
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
      'Cache-Control': 'public, max-age=3600',
    },
  });
}
