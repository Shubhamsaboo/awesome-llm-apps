/**
 * Fine Gold Analyser — Cloudflare Worker API Proxy v2.3
 *
 * Routes:
 *   POST /anthropic            → https://api.anthropic.com/v1/messages
 *   POST /openai               → https://api.openai.com/v1/chat/completions
 *   POST /gemini               → https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent
 *   GET|POST|PUT /asana/*      → https://app.asana.com/api/1.0/*
 *   GET|POST /notion/*         → https://api.notion.com/v1/*
 *   POST /slack                → Slack Incoming Webhook
 *   GET|POST /clickup/*        → https://api.clickup.com/api/v2/*
 *
 * Required Worker secrets (set via `wrangler secret put` or Cloudflare dashboard):
 *   ANTHROPIC_KEY   — Anthropic API key (sk-ant-...)
 *   ASANA_TOKEN     — Asana personal access token (1/xxxxxxxx...)
 *
 * Optional Worker secrets:
 *   OPENAI_KEY      — OpenAI API key (sk-...)
 *   GEMINI_KEY      — Google Gemini API key (AIza...)
 *   NOTION_TOKEN    — Notion integration token (ntn_...)
 *   CLICKUP_TOKEN   — ClickUp API token (pk_...)
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

    // ── Origin guard ─────────────────────────────────────────────────────────
    if (!matchedOrigin) {
      return new Response(JSON.stringify({ error: 'Forbidden' }), {
        status: 403,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    const url = new URL(request.url);
    const path = url.pathname;
    const jsonHeaders = { ...corsHeaders, 'Content-Type': 'application/json' };

    // ── Anthropic proxy ───────────────────────────────────────────────────────
    if (path === '/anthropic') {
      if (request.method !== 'POST') {
        return new Response(JSON.stringify({ error: 'Method not allowed' }), { status: 405, headers: jsonHeaders });
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
      return new Response(await upstream.text(), { status: upstream.status, headers: jsonHeaders });
    }

    // ── OpenAI proxy ──────────────────────────────────────────────────────────
    if (path === '/openai') {
      if (request.method !== 'POST') {
        return new Response(JSON.stringify({ error: 'Method not allowed' }), { status: 405, headers: jsonHeaders });
      }
      const body = await request.text();
      const upstream = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${env.OPENAI_KEY}`,
        },
        body,
      });
      return new Response(await upstream.text(), { status: upstream.status, headers: jsonHeaders });
    }

    // ── Gemini proxy ──────────────────────────────────────────────────────────
    if (path === '/gemini') {
      if (request.method !== 'POST') {
        return new Response(JSON.stringify({ error: 'Method not allowed' }), { status: 405, headers: jsonHeaders });
      }
      const body = await request.text();
      const upstream = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${env.GEMINI_KEY}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body,
      });
      return new Response(await upstream.text(), { status: upstream.status, headers: jsonHeaders });
    }

    // ── Asana proxy ───────────────────────────────────────────────────────────
    if (path.startsWith('/asana/')) {
      const asanaSubPath = path.slice('/asana'.length);
      const asanaUrl = new URL('https://app.asana.com/api/1.0' + asanaSubPath);
      url.searchParams.forEach((v, k) => asanaUrl.searchParams.set(k, v));

      const reqHeaders = { 'Authorization': `Bearer ${env.ASANA_TOKEN}`, 'Accept': 'application/json' };
      const fetchOpts = { method: request.method, headers: reqHeaders };
      if (request.method !== 'GET' && request.method !== 'HEAD') {
        reqHeaders['Content-Type'] = 'application/json';
        fetchOpts.body = await request.text();
      }

      const upstream = await fetch(asanaUrl.toString(), fetchOpts);
      return new Response(await upstream.text(), { status: upstream.status, headers: jsonHeaders });
    }

    // ── Notion proxy ──────────────────────────────────────────────────────────
    if (path.startsWith('/notion/')) {
      const notionSubPath = path.slice('/notion'.length);
      const notionUrl = new URL('https://api.notion.com/v1' + notionSubPath);
      url.searchParams.forEach((v, k) => notionUrl.searchParams.set(k, v));

      const reqHeaders = {
        'Authorization': `Bearer ${env.NOTION_TOKEN}`,
        'Notion-Version': '2022-06-28',
        'Accept': 'application/json',
      };
      const fetchOpts = { method: request.method, headers: reqHeaders };
      if (request.method !== 'GET' && request.method !== 'HEAD') {
        reqHeaders['Content-Type'] = 'application/json';
        fetchOpts.body = await request.text();
      }

      const upstream = await fetch(notionUrl.toString(), fetchOpts);
      return new Response(await upstream.text(), { status: upstream.status, headers: jsonHeaders });
    }

    // ── Slack proxy ───────────────────────────────────────────────────────────
    if (path === '/slack') {
      if (request.method !== 'POST') {
        return new Response(JSON.stringify({ error: 'Method not allowed' }), { status: 405, headers: jsonHeaders });
      }
      const payload = await request.json();
      const webhookUrl = payload.webhookUrl;
      if (!webhookUrl || !webhookUrl.startsWith('https://hooks.slack.com/')) {
        return new Response(JSON.stringify({ error: 'Invalid Slack webhook URL' }), { status: 400, headers: jsonHeaders });
      }
      const { webhookUrl: _, ...slackPayload } = payload;
      const upstream = await fetch(webhookUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(slackPayload),
      });
      return new Response(await upstream.text(), { status: upstream.status, headers: jsonHeaders });
    }

    // ── ClickUp proxy ─────────────────────────────────────────────────────────
    if (path.startsWith('/clickup/')) {
      const clickupSubPath = path.slice('/clickup'.length);
      const clickupUrl = new URL('https://api.clickup.com/api/v2' + clickupSubPath);
      url.searchParams.forEach((v, k) => clickupUrl.searchParams.set(k, v));

      const reqHeaders = { 'Authorization': env.CLICKUP_TOKEN, 'Accept': 'application/json' };
      const fetchOpts = { method: request.method, headers: reqHeaders };
      if (request.method !== 'GET' && request.method !== 'HEAD') {
        reqHeaders['Content-Type'] = 'application/json';
        fetchOpts.body = await request.text();
      }

      const upstream = await fetch(clickupUrl.toString(), fetchOpts);
      return new Response(await upstream.text(), { status: upstream.status, headers: jsonHeaders });
    }

    return new Response(JSON.stringify({ error: 'Not found' }), { status: 404, headers: jsonHeaders });
  },
};
