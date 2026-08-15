# 📡 Release Radar Agent

Release Radar is an always-on dependency briefing agent built with Google ADK. It reads `requirements.txt` or `package.json`, checks mapped dependencies against GitHub releases, and reports only changes that need attention: breaking changes, deprecations, security fixes, yanked releases, and major-version upgrades.

The app runs interactively in ADK Web or as a scheduled FastAPI service. Sample mode is deterministic and makes no GitHub requests. Scheduled delivery defaults to dry-run and remains off until Gmail or webhook settings are present.

## Features

- **Manifest parsing**: Reads Python requirements plus npm runtime and development dependencies.
- **GitHub release scanning**: Uses the GitHub REST API with an optional token.
- **Impact ranking**: Scores security, breaking, yanked, major-version, and deprecation signals.
- **Patch-noise filtering**: Drops routine patch and minor releases without an impact signal.
- **Text and HTML briefs**: Groups changes by dependency with version delta, reason, impact, and release link.
- **Google ADK agent**: Exposes `root_agent` for interactive dependency questions.
- **Scheduler hooks**: Accepts direct HTTP and Pub/Sub triggers.
- **Opt-in delivery**: Supports Gmail and generic webhooks only when explicitly configured.

## How It Works

1. `radar.py` parses a manifest and maps known packages or GitHub dependency URLs to repositories.
2. Sample mode loads deterministic GitHub-shaped data. Live mode fetches recent GitHub releases.
3. `ranker.py` classifies release notes and filters routine noise.
4. `delivery.py` renders the selected releases as text and HTML.
5. ADK Web returns the brief interactively, while `scheduler_api.py` exposes scheduled HTTP and Pub/Sub paths.
6. The scheduler sends only when `dry_run=false` and Gmail or webhook configuration is present.

The source modules use the Python standard library for manifest parsing, GitHub access, rendering, and delivery. FastAPI provides the scheduler surface, and Google ADK provides the interactive agent.

## Requirements

- Python 3.10+
- Gemini API key for ADK Web
- A project `requirements.txt` or `package.json` for live scans
- Optional GitHub token for higher API rate limits
- Optional Gmail OAuth credentials or a webhook URL for delivery

## Installation

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/always_on_agents/release_radar_agent
pip install -r requirements.txt
export GOOGLE_API_KEY="your_gemini_api_key"
```

## Run in ADK Web

Start with deterministic sample data:

```bash
adk web .
```

Open ADK Web, select `release_radar_agent`, and try:

```text
Give me today's dependency release brief.
```

To scan a real project, set an absolute manifest path and enable live GitHub requests before starting ADK Web:

```bash
export RELEASE_RADAR_MANIFEST="/absolute/path/to/requirements.txt"
export RELEASE_RADAR_LIVE_GITHUB=true
export RELEASE_RADAR_GITHUB_TOKEN="optional_github_token"
adk web .
```

Release Radar recognizes direct GitHub dependency URLs and common packages such as Pydantic, FastAPI, Requests, OpenAI, Anthropic, Google ADK, LangChain, React, Vite, and Zod. Unmapped dependencies appear in the scan notes instead of stopping the brief.

## Run the Scheduler API

Set the project manifest in the service environment, then start the backend from this directory:

```bash
export RELEASE_RADAR_MANIFEST="/workspace/requirements.txt"
export RELEASE_RADAR_LIVE_GITHUB=true
uvicorn scheduler_api:app --host 0.0.0.0 --port 8000
```

Preview the deterministic sample brief without delivery:

```bash
curl "http://127.0.0.1:8000/release-radar/dry-run?top_n=5&live=false"
```

Scan a manifest through the scheduler path while keeping delivery off:

```bash
curl -X POST "http://127.0.0.1:8000/release-radar/trigger" \
  -H "Content-Type: application/json" \
  -d '{"dry_run": true, "live": true, "top_n": 10}'
```

The server reads its manifest only from `RELEASE_RADAR_MANIFEST`, so request payloads cannot select arbitrary local files. The path must exist inside the scheduler service. Set `RELEASE_RADAR_GITHUB_TOKEN` in the service environment when scanning many repositories.

## Enable Delivery

Delivery has two independent guards. The request must set `"dry_run": false`, and one provider must be fully configured. Without both, the API returns a skipped status and sends nothing.

### Gmail

Create a Google OAuth client with Gmail API access and a refresh token using the `https://www.googleapis.com/auth/gmail.send` scope, then set:

```bash
export RELEASE_RADAR_DELIVERY="gmail"
export RELEASE_RADAR_EMAIL_TO="you@example.com"
export RELEASE_RADAR_EMAIL_FROM="you@example.com"
export RELEASE_RADAR_GMAIL_CLIENT_ID="your_google_oauth_client_id"
export RELEASE_RADAR_GMAIL_CLIENT_SECRET="your_google_oauth_client_secret"
export RELEASE_RADAR_GMAIL_REFRESH_TOKEN="your_gmail_refresh_token"
```

### Webhook

Use a webhook to route the brief to Slack, Linear, Jira, or an internal workflow:

```bash
export RELEASE_RADAR_DELIVERY="webhook"
export RELEASE_RADAR_WEBHOOK_URL="https://example.com/dependency-brief"
export RELEASE_RADAR_WEBHOOK_TOKEN="optional_bearer_token"
```

After configuring a provider, trigger a live delivery:

```bash
curl -X POST "http://127.0.0.1:8000/release-radar/trigger" \
  -H "Content-Type: application/json" \
  -d '{"dry_run": false, "live": true, "top_n": 10}'
```

## Cloud Scheduler

Deploy the FastAPI service behind Cloud Run or another HTTP service. Cloud Scheduler can call the direct endpoint:

```text
https://YOUR_SERVICE_URL/release-radar/trigger
```

It can also publish base64-encoded JSON to the Pub/Sub push endpoint:

```text
https://YOUR_SERVICE_URL/release-radar/pubsub
```

A weekday morning schedule is:

```text
0 9 * * 1-5
```

Keep `dry_run` set to `true` while validating the deployment.

## Test

```bash
python3 -m pytest always_on_agents/release_radar_agent/tests/unit -q
```

The tests use deterministic sample releases and patch network access when checking delivery safety.

This app is licensed under Apache-2.0 through the repository's root license.
