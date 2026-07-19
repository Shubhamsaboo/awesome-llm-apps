# Harness wire contracts

Verified against harness golden schemas (iii 0.21.x). The engine is the
source of truth at runtime: `iii trigger engine::functions::info
function_id=harness::send` returns the live schema; prefer it over any doc
when they disagree.

## harness::send

Request:

```json
{
  "message": "string, or a full AgentMessage object",
  "model": "REQUIRED, e.g. an id from router::models::list",
  "session_id": "omit to create a new session; reuse for multi-turn context",
  "session": { "title": "set when this send creates the session" },
  "idempotency_key": "optional webhook dedupe; repeats return the original ids",
  "options": {
    "system_prompt": "string",
    "system_prompt_strategy": "enrich (default, appends) | override (replaces)",
    "mode": "plan | ask | agent",
    "functions": { "allow": ["web::fetch"], "deny": [], "expose": "agent_trigger" },
    "output": { "type": "text" },
    "max_turns": 30,
    "thinking_level": "minimal | low | medium | high | xhigh"
  }
}
```

Response: `{ accepted, session_id, turn_id, merged?, queued?, deduplicated? }`.
A send into a session with a running turn folds into it (`merged: true`)
instead of starting a second turn.

Notes:

- `model` has no server-side default; resolve it at runtime from
  `router::models::list` (`{ models: [{ id, provider, supports_tools, ... }] }`)
  and never hardcode one.
- `options.functions` is fail-closed: absent or empty `allow` means every
  model-requested call is denied and the turn is a plain chat loop.
- `output: { type: "json", schema: {...} }` makes the turn's `result` a
  schema-validated JSON value.
- For a plain chatbot, `system_prompt_strategy: "override"` plus
  `mode: "ask"` suppresses the built-in identity prompt's function-dispatch
  narration.

## harness::turn-completed (trigger type)

Bind it; never poll for results.

```json
{
  "type": "harness::turn-completed",
  "function_id": "<yours>::on-turn-completed",
  "config": { "session_id": "optional filter", "parent_session_id": "optional" }
}
```

Payload: `{ session_id, turn_id, status, timestamp, result?, result_error?,
reason?, parent? }`. `status` is `completed | failed | cancelled`. With a
text contract `result` is the final text; with a json contract it is the
validated object.

Delivery is fire-and-forget, at-least-once, and UNORDERED: turn-completed
can arrive before the session's message events. Correlate by ids, tolerate
duplicates, and treat arrival order as meaningless.

## harness::spawn and the subset rule

`harness::spawn { task, options?, model? }` starts a child turn in a child
session and parks the calling turn until the child resolves; the model calls
it mid-turn to fan out. Response: `{ child_session_id, child_turn_id }`.

The subset rule: a child's `functions.allow` is filtered against the
parent's. A parent can only grant what it holds, so an orchestrator that
must delegate `web::fetch` needs `web::fetch` in its own allow list even if
it is told never to call it directly. Parent `deny` entries are inherited by
children. Model and provider are inherited only together.

`harness::status { session_id }` reports `children` as LIVE children only;
completed spawns disappear from it. Use the console trace, not status, to
verify fan-out happened.

## Session events (session-manager trigger types)

`session::message-added` and `session::message-updated` both carry the full
message (`{ session_id, entry_id, message, revision, origin: { turn_id } }`).
A fast reply lands as a single `message-added` with no updates, so a
streaming consumer must bind BOTH types, print by comparing lengths per
entry, filter by `origin.turn_id`, and top up any missing tail from
turn-completed's `result`.

`session::messages { session_id }` returns
`{ messages: [{ entry_id, message: { role, content, ... }, origin }] }`:
entries are envelopes, the role is nested one level down.

## Registering bus surface (Node, iii-sdk 0.21.x)

```javascript
import { registerWorker } from 'iii-sdk'
const iii = registerWorker(process.env.III_URL || 'ws://localhost:49134')

iii.registerFunction('radar::run', handler, {
  description: 'One sentence the next caller reads',
  request_format: { type: 'object', body: { task: { type: 'string' } } },
})
iii.registerTrigger({ type: 'cron', function_id: 'radar::run', config: { expression: '0 0 9 * * *' } })
const result = await iii.trigger({ function_id: 'state::get', payload: { scope: 's', key: 'k' } })
```

Register all functions synchronously after `registerWorker`; a top-level
await before registration races the handshake and registers nothing. For
optional bindings (http routes), prefer awaiting the
`engine::register_trigger` function: it errors loudly when the trigger type
is absent and its registrations are garbage-collected when the worker
disconnects.
