# 🚀 AI GitHub Release Monitor

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![Anthropic](https://img.shields.io/badge/Anthropic-Claude-blueviolet)](https://anthropic.com)
[![GitHub API](https://img.shields.io/badge/GitHub-REST%20API-black)](https://docs.github.com/en/rest)

An AI-powered agent that monitors GitHub repositories for new releases and provides **semantic analysis** — going beyond simple notifications to tell you *what actually changed*, whether it's breaking, how urgent it is to upgrade, and what to watch out for.

> **Why not just use RSS?** RSS tells you *something released*. This agent tells you *what it means for your project* — breaking changes, security implications, migration paths, and upgrade urgency — all analyzed by Claude.

---

## Features

- **Smart Monitoring** — Watch multiple repos, only get notified about new releases
- **Semantic Analysis** — Claude reads release notes and categorizes changes (breaking, security, deprecation, feature, fix)
- **Impact Scoring** — Each release gets a 0.0–1.0 impact score with reasoning
- **Upgrade Urgency** — Clear recommendation: immediate / soon / routine / skip
- **Breaking Change Detection** — Identifies breaking changes with migration paths
- **Security Fix Alerts** — Flags security patches with severity levels
- **Persistent History** — SQLite database tracks all analyzed releases
- **Dual Interface** — Full CLI with Rich formatting + Streamlit web UI

---

## How It Works

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐     ┌──────────────┐
│  Watchlist   │────▶│  GitHub API   │────▶│  Claude Analysis │────▶│   Display    │
│  (JSON)      │     │  (Releases)   │     │  (Structured)    │     │  (CLI / UI)  │
└─────────────┘     └──────────────┘     └─────────────────┘     └──────────────┘
                           │                       │
                           ▼                       ▼
                    ┌──────────────┐     ┌─────────────────┐
                    │  Rate Limit   │     │   SQLite DB      │
                    │  Handling     │     │   (History)      │
                    └──────────────┘     └─────────────────┘
```

1. **Fetch** — Queries GitHub REST API for latest releases from your watchlist
2. **Filter** — Skips releases you've already seen (tracked in SQLite)
3. **Enrich** — Optionally fetches commit comparison for deeper context
4. **Analyze** — Claude produces structured JSON: summary, categories, impact, urgency
5. **Store** — Results persisted for history and future reference
6. **Display** — Color-coded CLI output or interactive Streamlit dashboard

---

## Quickstart

### 1. Install dependencies

```bash
cd ai_github_release_monitor
pip install -r requirements.txt
```

### 2. Set your API key

```bash
export ANTHROPIC_API_KEY="sk-ant-..."

# Optional: GitHub token for higher rate limits (60 → 5000 requests/hour)
export GITHUB_TOKEN="ghp_..."
```

### 3. Add repos to your watchlist

```bash
python release_monitor.py --add anthropics/anthropic-sdk-python
python release_monitor.py --add pydantic/pydantic
python release_monitor.py --add astral-sh/ruff
```

### 4. Check for releases

```bash
python release_monitor.py --check
```

### 5. Or launch the web UI

```bash
streamlit run app.py
```

---

## CLI Usage

```bash
# Watchlist management
python release_monitor.py --add owner/repo       # Add a repo
python release_monitor.py --remove owner/repo    # Remove a repo
python release_monitor.py --list                 # Show watchlist

# Check releases
python release_monitor.py                        # Check all (default action)
python release_monitor.py --repo owner/repo      # Check specific repo
python release_monitor.py --model claude-opus-4-8  # Use different model

# History
python release_monitor.py --history              # Show past analyses
python release_monitor.py --show abc123          # Show specific analysis by ID
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key for Claude |
| `GITHUB_TOKEN` | No | GitHub personal access token (raises rate limit) |
| `RELEASE_MONITOR_MODEL` | No | Override default Claude model |

---

## Example Output

```
GitHub API: 58/60 requests remaining
Checking anthropics/anthropic-sdk-python...
  Analyzing anthropics/anthropic-sdk-python@v0.40.0...

╭─ anthropics/anthropic-sdk-python @ v0.40.0  ROUTINE (impact: 0.5) ─╮
│                                                                      │
│ Added streaming support for tool use and improved error messages     │
│ for common authentication issues. No breaking changes.               │
│                                                                      │
│ Categories: new_feature bug_fix                                      │
│                                                                      │
│ Highlights:                                                          │
│   - Streaming tool use support in messages API                       │
│   - Better error messages for expired/invalid API keys               │
│   - Type improvements for message batches                            │
│                                                                      │
│ Upgrade: Safe to upgrade. No breaking changes or deprecations.       │
│                                                                      │
│ ID: a1b2c3d4e5f6                                                     │
╰──────────────────────────────────────────────────────────────────────╯
```

---

## Architecture

```
release_monitor.py          Core module
├── Config & DB             ~/.release_monitor/ data directory, SQLite
├── Watchlist               JSON-based repo list management
├── GitHub API              httpx client for REST API (releases, compare)
├── Claude Analysis         Structured prompt → JSON response parsing
├── Pipeline                Orchestrates: fetch → filter → analyze → store
└── CLI                     Rich-formatted display + argparse

app.py                      Streamlit frontend
├── Sidebar                 API keys, model selector, watchlist management
├── Monitor Tab             Check button → progress → result cards
└── History Tab             Past analyses with filters
```

---

## Key Concepts

- **Structured AI Output** — Claude returns JSON matching a defined schema, enabling programmatic consumption of analysis results
- **Incremental Monitoring** — SQLite tracks seen releases so you only analyze what's new
- **Graceful Degradation** — Rich formatting is optional; app works without it. GitHub token is optional; app works at lower rate limits
- **Separation of Concerns** — Core logic (`release_monitor.py`) is fully independent of the UI (`app.py`) and can be imported as a library

---

## Extending

Ideas for enhancement:
- **Webhook mode** — Run as a service that polls on a schedule and sends notifications
- **Dependency awareness** — Parse your `requirements.txt` / `pyproject.toml` and only monitor your actual dependencies
- **Comparative analysis** — Track how a library's release velocity and breaking change frequency trends over time
- **Team dashboard** — Shared watchlist with team-specific relevance scoring
