# 🔔 Page Watch Agent

Page Watch is an always-on briefing agent built with Google ADK. It watches a short list of pages you depend on — a vendor pricing page, API rate-limit docs, terms of service, a status or changelog page — and tells you only when something material changed, with the old vs new text and why it matters.

The app runs interactively in ADK Web or as a scheduled FastAPI service. Sample mode is deterministic and makes no network or model calls. Scheduled delivery defaults to dry-run and remains off until Gmail or webhook settings are present.

## Features

- **Watch lists**: YAML or JSON entries with a URL, name, optional CSS selector or text anchors, and keywords that always count as material.
- **Polite fetching**: Timeout, size cap, and a dedicated User-Agent.
- **Stable snapshots**: Local files keyed by URL hash, with scripts, styles, nav, promo banners, timestamps, cache-busters, and CSRF tokens stripped before compare.
- **Paragraph diffs**: Hunk ids stay stable when unchanged paragraphs are reordered.
- **Checkable judgment**: A deterministic pre-filter (keyword hits, numeric changes such as prices or quotas) runs first; Gemini then classifies each hunk as `material` or `cosmetic`, quotes the before/after text, and tags impact.
- **Text and HTML briefs**: Grouped by page. Cosmetic-only pages are reported as no material change.
- **Google ADK agent**: Exposes `root_agent` for questions such as "what changed on the pricing page this week?"
- **Scheduler hooks**: Accepts direct HTTP and Pub/Sub triggers.
- **Opt-in delivery**: Supports Gmail and generic webhooks only when explicitly configured.

## How It Works

1. `watch.py` loads the watch list, fetches each page, normalizes readable text, stores a snapshot, and computes a paragraph-level diff.
2. Sample mode (`--sample`) loads recorded before/after pages and recorded judgments and never calls the model. Fetching a watch list uses Gemini whenever `GOOGLE_API_KEY` or `GEMINI_API_KEY` is set.
3. `judge.py` applies the deterministic pre-filter, then classifies each hunk.
4. `delivery.py` renders the selected changes as text and HTML.
5. ADK Web returns the brief interactively, while `scheduler_api.py` exposes scheduled HTTP and Pub/Sub paths.
6. The scheduler sends only when `dry_run=false` and Gmail or webhook configuration is present.

The source modules use the Python standard library for fetching, HTML normalization, diffs, snapshots, rendering, and delivery. FastAPI provides the scheduler surface, and Google ADK provides the interactive agent.

## Requirements

- Python 3.10+
- Gemini API key for ADK Web and for live hunk judgments (the default judge when a key is set)
- A YAML or JSON watch list for live fetches
- Optional Gmail OAuth credentials or a webhook URL for delivery

## Installation

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/always_on_agents/page_watch_agent
pip install -r requirements.txt
export GOOGLE_API_KEY="your_gemini_api_key"
```

## Sample-mode walkthrough

Sample mode needs no API key and opens no network connections. From this directory:

```bash
python3 watch.py --sample
```

You should see a brief that:

- Flags the Acme Cloud **pricing** page as material (`$29` → `$49`, rate limit `100` → `60`), with pre-filter verdicts next to the recorded judgments.
- Reports the Acme **API docs** page as no material change (footer timestamp and cache-buster only).
- Flags the Acme **terms** page as material because a binding arbitration clause was added.

The same payload is available as JSON:

```bash
python3 watch.py --sample --json
```

Run the unit tests from the repository root:

```bash
python3 -m pytest always_on_agents/page_watch_agent/tests/unit -q
```

## Run in ADK Web

Start with deterministic sample data:

```bash
adk web .
```

Open ADK Web, select `page_watch_agent`, and try:

```text
What changed on the pricing page this week?
```

```text
Did the API docs page change in a way that matters?
```

To fetch a real watch list before starting ADK Web:

```bash
export PAGE_WATCH_WATCHLIST="/absolute/path/to/watchlist.yaml"
export PAGE_WATCH_SNAPSHOT_DIR="/absolute/path/to/snapshots"
export PAGE_WATCH_LIVE=true
adk web .
```

Copy `watchlist.example.yaml` or `watchlist.example.json` and point each `url` at the pages you depend on. Optional `selector` (`#id`, `.class`, `tag`) and `start_anchor` / `end_anchor` fields scope the compared region.

## Run the Scheduler API

Start the backend from this directory:

```bash
uvicorn scheduler_api:app --host 0.0.0.0 --port 8000
```

Preview the deterministic sample brief without delivery:

```bash
curl "http://127.0.0.1:8000/page-watch/dry-run"
```

Fetch the server-configured watch list through the scheduler path while keeping delivery off:

```bash
export PAGE_WATCH_WATCHLIST="/absolute/path/to/watchlist.yaml"
export PAGE_WATCH_SNAPSHOT_DIR="/absolute/path/to/snapshots"
curl -X POST "http://127.0.0.1:8000/page-watch/trigger" \
  -H "Content-Type: application/json" \
  -d '{"dry_run": true, "live": true}'
```

The server reads its watch list only from `PAGE_WATCH_WATCHLIST`, so request payloads cannot select arbitrary local files.

Fetching a watch list (`--fetch`, or `"live": true` on the scheduler) uses Gemini as the default judge whenever `GOOGLE_API_KEY` or `GEMINI_API_KEY` is set. `--sample` never calls the model. Set `PAGE_WATCH_LIVE_MODEL=false` or pass `"live_model": false` to keep recorded judgments while fetching. If Gemini fails, the brief still renders from the pre-filter and marks those hunks `source=prefilter_fallback`.

## Enable Delivery

Delivery has two independent guards. The request must set `"dry_run": false`, and one provider must be fully configured. Without both, the API returns a skipped status and sends nothing.

### Gmail

Create a Google OAuth client with Gmail API access and a refresh token using the `https://www.googleapis.com/auth/gmail.send` scope, then set:

```bash
export PAGE_WATCH_DELIVERY="gmail"
export PAGE_WATCH_EMAIL_TO="you@example.com"
export PAGE_WATCH_EMAIL_FROM="you@example.com"
export PAGE_WATCH_GMAIL_CLIENT_ID="your_google_oauth_client_id"
export PAGE_WATCH_GMAIL_CLIENT_SECRET="your_google_oauth_client_secret"
export PAGE_WATCH_GMAIL_REFRESH_TOKEN="your_gmail_refresh_token"
```

### Webhook

Use a webhook to route the brief to Slack, Linear, Jira, or an internal workflow:

```bash
export PAGE_WATCH_DELIVERY="webhook"
export PAGE_WATCH_WEBHOOK_URL="https://example.com/page-watch-brief"
export PAGE_WATCH_WEBHOOK_TOKEN="optional_bearer_token"
```

After configuring a provider, trigger a live delivery:

```bash
curl -X POST "http://127.0.0.1:8000/page-watch/trigger" \
  -H "Content-Type: application/json" \
  -d '{"dry_run": false, "live": true}'
```

## Cloud Scheduler

Deploy the FastAPI service behind Cloud Run or another HTTP service. Cloud Scheduler can call the direct endpoint:

```text
https://YOUR_SERVICE_URL/page-watch/trigger
```

It can also publish base64-encoded JSON to the Pub/Sub push endpoint:

```text
https://YOUR_SERVICE_URL/page-watch/pubsub
```

A weekday morning schedule is:

```text
0 9 * * 1-5
```

Keep `dry_run` set to `true` while validating the deployment.

## Test

```bash
python3 -m pytest always_on_agents/page_watch_agent/tests/unit -q
```

The tests use deterministic sample pages and patch network access when checking delivery safety.

This app is licensed under Apache-2.0 through the repository's root license.
