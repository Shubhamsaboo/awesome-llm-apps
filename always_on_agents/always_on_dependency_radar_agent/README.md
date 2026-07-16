# 📡 Always-on Dependency Radar Agent

An always-on dependency watchdog built on the [iii engine](https://iii.dev). On a cron schedule it diffs your `package.json` against the npm registry, hands the outdated packages to a harness agent that actually reads the changelogs and release notes between your version and the latest, and stores a digest that grades every upgrade as `safe`, `review`, or `breaking` with maintainer-actionable notes.

Everything infrastructural comes from reusable iii workers; this app is one file of business logic on the bus. The engine routes all communication as functions and triggers, so the app never talks to a model provider, a scheduler, a store, or an HTTP server directly.

| Capability | Who provides it |
|---|---|
| Agent loop (context, streaming, function dispatch) | `harness` worker |
| Model access, any provider | `llm-router` + `provider-*` workers |
| npm registry and changelog fetching | `web` worker (`web::fetch`) |
| Scheduling | engine `cron` trigger |
| Digest storage and history | `iii-state` worker (`state::set` / `state::get`) |
| REST endpoints (optional) | `http` worker |

## How It Works

1. A `cron` trigger fires `radar::scan` every morning (expression configurable).
2. The scan reads the target `package.json` and resolves each dependency's latest version through `web::fetch` against `https://registry.npmjs.org/<name>/latest`. Version comparison is plain code; no tokens are spent on arithmetic.
3. The outdated list, sorted by how far behind each package is, goes to `harness::send` with a JSON output contract and a function policy allowing only `web::fetch`.
4. The agent reads the release notes between your version and the latest for each package, classifies the upgrade risk, and writes notes grounded in what the changelog actually says.
5. The app hears `harness::turn-completed`, stores the digest in state under the date and `latest` keys, and optionally posts a summary to a webhook (Slack-compatible payload).

Example digest entry, produced from a real run against `express@4.17.0`:

```json
{
  "name": "express",
  "current": "4.17.0",
  "latest": "5.2.1",
  "risk": "breaking",
  "notes": "Major version bump. Express v5 drops Node.js <18 support, updates routing to path-to-regexp@8.x (removes sub-expression regex for ReDoS mitigation), enables promise rejection handling in middleware... Check the migration guide at expressjs.com/en/guide/migrating-5.html.",
  "changelog_url": "https://github.com/expressjs/express/releases"
}
```

## Requirements

- Node.js 20+
- The iii engine with the `harness` worker
- At least one model provider configured in `llm-router`

The app holds no API keys. Credentials live in the `llm-router` worker; whatever provider you configure there is what the analyst agent runs on.

## Installation

**Step 1: Install the iii engine**

```bash
curl -fsSL https://install.iii.dev/iii/main/install.sh | sh
```

**Step 2: Start the engine**

```bash
mkdir iii-app && cd iii-app
touch config.yaml
iii -c config.yaml
```

**Step 3: Add the workers this app depends on**

From a second terminal in the same folder (`iii worker add` writes to the `config.yaml` of the directory it runs in):

```bash
cd iii-app
iii worker add harness console
```

`harness` is the only required add: it installs the whole dependency set of the loop in one command, and each piece is a reusable worker this app calls over the bus:

| Worker (installed with harness) | Used here for |
|---|---|
| `harness` | The analyst agent turn, `harness::send`, the `harness::turn-completed` trigger |
| `session-manager` | The analyst's transcript |
| `context-manager` | Token budgeting per turn |
| `llm-router` + `provider-anthropic` / `provider-openai` | Model catalog and completion routing |
| `web` | `web::fetch` for the npm registry, changelogs, and the delivery webhook |
| `iii-state` | `state::set` / `state::get` for digest storage and history |
| `iii-cron` | The `cron` trigger type behind the schedule |
| `queue` | The durable `harness-turn` queue |

`console` adds the UI at `http://localhost:3113`: provider key configuration and the live trace of every scan.

**Step 4: Configure a model provider**

Open `http://localhost:3113`, click the model picker, and paste an Anthropic or OpenAI key (stored in the `llm-router` worker config). Other providers are one add away (`iii worker add provider-xai`, `provider-llamacpp` for local models, ...).

**Step 5 (optional): REST endpoints**

```bash
iii worker add http
```

**Step 6: Install and run the app**

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/always_on_agents/always_on_dependency_radar_agent
npm install
```

## Usage

One-shot scan of any project (prints the digest and exits):

```bash
RADAR_PACKAGE_JSON=~/my-app/package.json node radar.js
```

Always-on mode (cron schedule plus callable functions):

```bash
RADAR_PACKAGE_JSON=~/my-app/package.json node radar.js --serve
```

In serve mode the app registers `radar::scan` (run now) and `radar::digest` (fetch a stored digest by date key or `latest`) on the bus, so any other worker, agent, or the console can call them. With the `http` worker installed (`iii worker add http`) the same surface is exposed over REST:

```bash
curl -X POST http://localhost:3111/radar/scan
curl http://localhost:3111/radar/digest
```

## Configuration

| Env var | Default | Meaning |
|---|---|---|
| `III_URL` | `ws://localhost:49134` | Engine WebSocket address |
| `RADAR_PACKAGE_JSON` | `./package.json` | The manifest to watch |
| `RADAR_CRON` | `0 0 9 * * *` | 6-field cron expression (sec min hour day month weekday) |
| `RADAR_MODEL` | none | Model id; required only when several models are available |
| `RADAR_MAX_RESEARCH` | `6` | Changelog-research cap per run; packages beyond it are listed unresearched |
| `RADAR_WEBHOOK_URL` | none | POST a summary here after each digest (Slack-compatible `{text}`) |
| `RADAR_TIMEOUT_MS` | `300000` | Abort the analysis turn after this long |
