/**
 * TeamGenie AI — Cloudflare Worker (Edge Compute)
 * Handles: API routing, caching, geo-blocking, DDoS detection
 * Deploy: wrangler deploy
 */

export interface Env {
  API_ORIGIN: string;
  KV_CACHE: KVNamespace;
}

// Banned states in India (fantasy sports restricted)
const BANNED_STATES = ['AS', 'OR', 'TG', 'SK', 'NL'];

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // Health check
    if (url.pathname === '/health') {
      return new Response(JSON.stringify({ status: 'healthy', edge: true }), {
        headers: { 'Content-Type': 'application/json' },
      });
    }

    // Geo-blocking check
    const country = request.headers.get('CF-IPCountry') || '';
    const region = request.headers.get('CF-Region') || '';

    if (country === 'IN' && BANNED_STATES.includes(region)) {
      return new Response(
        JSON.stringify({
          error: { code: 'geo_restricted', message: `Service not available in ${region}` },
        }),
        { status: 451, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Cache GET requests
    if (request.method === 'GET' && url.pathname.startsWith('/api/')) {
      const cacheKey = `edge:${url.pathname}${url.search}`;
      const cached = await env.KV_CACHE.get(cacheKey);
      if (cached) {
        return new Response(cached, {
          headers: {
            'Content-Type': 'application/json',
            'X-Cache': 'HIT',
            'X-Edge': 'cloudflare',
          },
        });
      }
    }

    // Proxy to origin (Render/FastAPI)
    const originUrl = `${env.API_ORIGIN}${url.pathname}${url.search}`;
    const response = await fetch(originUrl, {
      method: request.method,
      headers: request.headers,
      body: request.method !== 'GET' ? request.body : undefined,
    });

    // Cache successful GET responses for 5 minutes
    if (request.method === 'GET' && response.ok) {
      const body = await response.text();
      await env.KV_CACHE.put(`edge:${url.pathname}${url.search}`, body, { expirationTtl: 300 });
      return new Response(body, {
        status: response.status,
        headers: { ...Object.fromEntries(response.headers), 'X-Cache': 'MISS', 'X-Edge': 'cloudflare' },
      });
    }

    return response;
  },
};
