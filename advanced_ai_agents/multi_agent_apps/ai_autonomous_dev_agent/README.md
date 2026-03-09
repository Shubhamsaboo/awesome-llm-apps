# 🤖 AI Autonomous Dev Agent (Pilot)

An autonomous AI development pipeline that picks up tickets from GitHub, Linear, Jira, or Asana — plans the implementation, writes code with Claude Code, runs quality gates, and opens pull requests. No human intervention required.

## How It Works

```
GitHub Issue (labeled "pilot")
        │
        ▼
   ┌──────────┐     ┌──────────┐     ┌───────────┐
   │ Navigator │ ──► │ Executor │ ──► │Self-Review │
   │ (Planner) │     │ (Claude) │     │(Validator) │
   └──────────┘     └──────────┘     └───────────┘
        │                                  │
        └───────── Quality Gates ──────────┘
                        │
                        ▼
                   Pull Request
```

**Navigator** reads your codebase context and plans the approach. **Executor** implements using Claude Code. **Self-Reviewer** validates the changes. **Quality gates** run your tests and linter, retrying on failure.

<img width="1758" height="1124" alt="Pilot dashboard and GitHub integration" src="https://github.com/user-attachments/assets/faaff57a-a23e-4cee-a08a-b9fa08ae135d" />

## Features

- **Ticket-to-PR pipeline** — Label a GitHub issue `pilot`, get a PR back in minutes
- **Multi-agent architecture** — Navigator plans, Executor implements, Self-Reviewer validates
- **Quality gates** — Automated test, lint, build validation with retry loops
- **Autopilot modes** — dev (fast), stage (CI-gated), prod (human approval required)
- **Multi-source intake** — GitHub, Linear, Jira, Asana, GitLab, Azure DevOps, Plane, Discord
- **Epic decomposition** — Complex tasks auto-split into safe sequential subtasks
- **CI monitoring** — Watches CI, auto-fixes failures, auto-merges on green
- **Model routing** — Haiku for trivial, Sonnet for simple, Opus for complex (cost-optimized)
- **Telegram/Slack/Discord bot** — Chat-based task creation with voice support
- **TUI Dashboard** — Real-time terminal dashboard with task metrics and git graph

## Quick Start

### Option 1: Install via Homebrew (Recommended)

```bash
brew tap alekspetrov/pilot
brew install pilot
pilot init
pilot start --github --dashboard
```

Label any GitHub issue with `pilot` — Pilot picks it up within 30 seconds.

### Option 2: Docker

```bash
cd ai_autonomous_dev_agent
cp .env.example .env
# Edit .env with your GITHUB_TOKEN and ANTHROPIC_API_KEY
docker compose up -d
```

### Option 3: Demo Scripts

Use the included Python scripts to trigger Pilot programmatically:

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your tokens

# Create a GitHub issue with the pilot label
python demo_github_issue.py --repo owner/repo --title "Add health check endpoint"

# Or trigger via Pilot's webhook API (requires Pilot running with gateway)
python demo_webhook_trigger.py --url http://localhost:9090 --repo owner/repo --title "Add rate limiting"
```

## Requirements

- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) — Pilot's execution backend
- `ANTHROPIC_API_KEY` or Claude Code OAuth login
- `GITHUB_TOKEN` with repo permissions
- Go 1.24+ (only if building from source)

## Configuration

Pilot uses a YAML config file (`~/.pilot/config.yaml`). See `config.example.yaml` for a minimal GitHub-only setup.

Key settings:
- **Adapters** — Which platforms to poll (GitHub, Linear, Jira, etc.)
- **Autopilot** — CI monitoring, auto-merge, approval requirements
- **Quality gates** — Custom test/lint commands to run before PR creation
- **Model routing** — Cost optimization by task complexity

## Links

- **Repository**: [github.com/alekspetrov/pilot](https://github.com/alekspetrov/pilot)
- **Documentation**: [pilot.quantflow.studio](https://pilot.quantflow.studio)
- **License**: BSL 1.1 (converts to Apache 2.0 after 4 years)
