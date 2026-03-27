# Fine Gold Analyser

A UAE gold-trading compliance analysis tool powered by **Claude (Anthropic)**, with **Asana** project management and **Notion** documentation integration.

Covers: UAE FDL No.10/2025 · FATF · LBMA RGG v9 · UAE FIU · EOCN

## Features

- **Multi-company support** — manage compliance for FG-LLC, Madison LLC, Naples LLC, Gramaltin A.S, and ZOE FZE from a single interface
- **Claude-powered analysis** — run gap assessments, CDD/KYC/EDD reviews, LBMA compliance checks, TFS/Sanctions screening, and STR/SAR/GOAML analysis
- **Asana integration** — automatically create and route tasks into the correct project section (Workflow / Assessments / Gaps / Documents / Training)
- **Notion integration** — sync gap findings to the Gap Status Tracker, Meeting Notes Archive, and Action Items databases
- **Cloudflare Worker proxy** — keeps API keys server-side; the app never exposes credentials in the browser

## Architecture

```
Browser (index.html)
    │
    ├── Direct Notion API calls (CORS allowed)
    │
    └── Cloudflare Worker (proxy/)
            ├── POST /anthropic  →  api.anthropic.com/v1/messages
            └── *    /asana/*    →  app.asana.com/api/1.0/*
```

## Quick Start

### 1. Run the app locally

```bash
npm install
npm run dev
# Open http://localhost:8080
```

Or open `index.html` directly in a browser — all features work without a local server except the live-reload.

### 2. Deploy the Cloudflare Worker proxy

```bash
cd proxy
npm install -g wrangler
wrangler login

# Add secrets (never committed to source control)
wrangler secret put ANTHROPIC_KEY   # sk-ant-...
wrangler secret put ASANA_TOKEN     # your Asana PAT

wrangler deploy
# Note the worker URL, e.g. https://fgl-proxy.<subdomain>.workers.dev
```

### 3. Configure the app

Open the app, scroll to **API Configuration**, and enter:

| Field | Value |
|---|---|
| Anthropic API Key | `sk-ant-...` (or leave blank if using the Worker proxy) |
| Asana Personal Access Token | Your Asana PAT |
| Notion API Key | `secret_...` from notion.so/my-integrations |

Settings are saved to `localStorage` — they persist across page reloads but never leave the browser.

## Files

| File | Description |
|---|---|
| `index.html` | Main app (Fine Gold Analyser v2.1) |
| `fine_gold_analyser_v2.html` | Previous version with extended analysis features |
| `proxy/worker.js` | Cloudflare Worker — proxies Anthropic & Asana API calls |
| `proxy/wrangler.toml` | Wrangler configuration for the Worker |

## Compliance Frameworks

- **UAE FDL No.10/2025** — Federal Decree-Law on AML/CFT
- **FATF** — Financial Action Task Force recommendations
- **LBMA RGG v9** — London Bullion Market Association Responsible Gold Guidance
- **UAE FIU / GOAML** — Financial Intelligence Unit reporting
- **EOCN** — Executive Office for Control & Non-Proliferation
