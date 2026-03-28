/**
 * Fine Gold Analyser — Cloudflare Worker API Proxy
 *
 * Routes:
 *   POST /anthropic            → https://api.anthropic.com/v1/messages
 *   GET|POST|PUT /asana/*      → https://app.asana.com/api/1.0/*
 *
 * Required Worker secrets (set via `wrangler secret put`):
 *   ANTHROPIC_KEY   — your Anthropic API key (sk-ant-...)
 *   ASANA_TOKEN     — your Asana personal access token (1/xxxxxxxx...)
 *
 * The Worker validates the Origin header so only requests from the
 * configured GitHub Pages URL are accepted.
 */

const ALLOWED_ORIGINS = [
  'https://trex051192.github.io',
  'https://compliancetool.com',
  'https://www.compliancetool.com',
];

export default {
  async fetch(request, env) {
    const origin = request.headers.get('Origin') || '';
    const matchedOrigin = ALLOWED_ORIGINS.includes(origin) ? origin : '';

    const corsHeaders = {
      'Access-Control-Allow-Origin': matchedOrigin || ALLOWED_ORIGINS[0],
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
      'Access-Control-Max-Age': '86400',
    };

    // ── CORS preflight ────────────────────────────────────────────────────────
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: corsHeaders });
    }

    // ── Origin guard — reject everything except the allowed sites ─────────────
    if (!matchedOrigin) {
      return new Response(JSON.stringify({ error: 'Forbidden' }), {
        status: 403,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    const url = new URL(request.url);
    const path = url.pathname;

    // ── Anthropic proxy ───────────────────────────────────────────────────────
    if (path === '/anthropic') {
      if (request.method !== 'POST') {
        return new Response(JSON.stringify({ error: 'Method not allowed' }), {
          status: 405,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      }

      const body = await request.text();
      const upstream = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': env.ANTHROPIC_KEY,
          'anthropic-version': '2023-06-01',
        },
        body,
      });

      const upstreamBody = await upstream.text();
      return new Response(upstreamBody, {
        status: upstream.status,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // ── Asana proxy ───────────────────────────────────────────────────────────
    // HTML calls /asana/<apiPath>  →  https://app.asana.com/api/1.0/<apiPath>
    if (path.startsWith('/asana/')) {
      const asanaSubPath = path.slice('/asana'.length); // e.g. /tasks, /projects/123/tasks
      const asanaUrl = new URL('https://app.asana.com/api/1.0' + asanaSubPath);

      // Forward query-string parameters (e.g. opt_fields, limit)
      url.searchParams.forEach((v, k) => asanaUrl.searchParams.set(k, v));

      const reqHeaders = {
        'Authorization': `Bearer ${env.ASANA_TOKEN}`,
        'Accept': 'application/json',
      };

      const fetchOpts = { method: request.method, headers: reqHeaders };
      if (request.method !== 'GET' && request.method !== 'HEAD') {
        reqHeaders['Content-Type'] = 'application/json';
        fetchOpts.body = await request.text();
      }

      const upstream = await fetch(asanaUrl.toString(), fetchOpts);
      const upstreamBody = await upstream.text();
      return new Response(upstreamBody, {
        status: upstream.status,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    return new Response(JSON.stringify({ error: 'Not found' }), {
      status: 404,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  },
};
