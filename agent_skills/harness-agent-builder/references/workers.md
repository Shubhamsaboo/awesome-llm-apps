# Dependency workers

`iii worker add harness console` installs the full loop in one command. Each
row is a separate reusable worker on the bus; the generated agent calls them
by function id and never links against any of them.

| Worker | Installed with harness | Generated agent uses it for |
|---|---|---|
| `harness` | is the add | `harness::send`, `harness::spawn`, `harness::stop`, the `harness::turn-completed` trigger |
| `session-manager` | yes | Transcripts, multi-turn context, `session::messages`, `session::message-added/-updated` triggers |
| `context-manager` | yes | Token budgeting when transcripts grow (soft dependency) |
| `llm-router` | yes | `router::models::list`, completion routing, provider key storage |
| `provider-anthropic`, `provider-openai` | yes | Model access; more via `iii worker add provider-xai`, `provider-llamacpp` (local GGUF), and others |
| `web` | yes | `web::fetch` for the agent's allow list and for the app's own plain-code HTTP |
| `iii-state` | yes (engine built-in) | `state::set` / `state::get` / `state::list` result storage |
| `iii-cron` | yes (engine built-in) | The `cron` trigger type (6-field expressions) |
| `queue` | yes | The durable `harness-turn` queue: FIFO per session, concurrent across sessions |
| `console` | separate add | UI at http://localhost:3113: provider keys, model picker, live turn-waterfall traces |
| `http` | separate add (`iii worker add http`) | Binds functions to REST routes (`api_path`, `http_method`); functions return `{ status_code, body }` |
| `approval-gate` | separate add | Human approve/deny holds on risky function dispatches via harness pre-trigger hooks |

Credentials note: provider keys are configured once in the console's model
picker and stored in llm-router's worker config. Agent code, generated or
hand-written, should never read or hold an API key.
