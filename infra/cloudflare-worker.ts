/**
 * TeamGenie AI — Cloudflare Worker (Edge Compute)
 * Handles: API routing, caching, geo-blocking, rate-limit headers, security headers
 * Deploy: wrangler deploy
 */

export interface Env {
  API_ORIGIN: string;
  KV_CACHE: KVNamespace;
}

// Banned states in India (fantasy sports restricted under state law)
const BANNED_STATES = new Set(['AS', 'OR', 'TG', 'SK', 'NL', 'AP', 'AR']);

// Standard security headers applied to every response
const SECURITY_HEADERS: Record<string, string> = {
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
  'X-Edge': 'cloudflare',
};

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // Health check — fast path
    if (url.pathname === '/health') {
      return Response.json(
        { status: 'healthy', edge: true },
        { headers: SECURITY_HEADERS }
      );
    }

    // Geo-blocking check (451 = Unavailable for Legal Reasons)
    const country = request.headers.get('CF-IPCountry') || '';
    const region = request.headers.get('CF-Region') || '';

    if (country === 'IN' && BANNED_STATES.has(region)) {
      return Response.json(
        {
          error: {
            code: 'geo_restricted',
            message: `Fantasy sports service is not available in ${region} due to state regulations.`,
          },
        },
        { status: 451, headers: { ...SECURITY_HEADERS, 'Content-Type': 'application/json' } }
      );
    }

    // Edge cache for GET /api/* requests
    if (request.method === 'GET' && url.pathname.startsWith('/api/')) {
      const cacheKey = `edge:${url.pathname}${url.search}`;
      const cached = await env.KV_CACHE.get(cacheKey);
      if (cached) {
        return new Response(cached, {
          headers: {
            'Content-Type': 'application/json',
            'X-Cache': 'HIT',
            ...SECURITY_HEADERS,
          },
        });
      }
    }

    // Proxy to origin (Render / FastAPI)
    const originUrl = `${env.API_ORIGIN}${url.pathname}${url.search}`;
    const originRequest = new Request(originUrl, {
      method: request.method,
      headers: request.headers,
      body: request.method !== 'GET' && request.method !== 'HEAD' ? request.body : undefined,
    });

    const response = await fetch(originRequest);

    // Cache successful GET responses for 5 minutes
    if (request.method === 'GET' && response.ok) {
      const body = await response.text();
      // Don't await KV put — fire and forget for latency
      env.KV_CACHE.put(cacheKey, body, { expirationTtl: 300 }).catch(() => {});

      const responseHeaders = new Headers(response.headers);
      responseHeaders.set('X-Cache', 'MISS');
      Object.entries(SECURITY_HEADERS).forEach(([k, v]) => responseHeaders.set(k, v));

      return new Response(body, {
        status: response.status,
        headers: responseHeaders,
      });
    }

    // Non-cacheable responses — still add security headers
    const finalHeaders = new Headers(response.headers);
    Object.entries(SECURITY_HEADERS).forEach(([k, v]) => finalHeaders.set(k, v));

    return new Response(response.body, {
      status: response.status,
      headers: finalHeaders,
    });
  },
};
