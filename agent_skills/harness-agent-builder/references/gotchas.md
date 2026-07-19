# Field-tested gotchas

Every entry below was hit while building real agents against a live engine;
none is speculative.

## Results never arrive

The consumer promise resolves from the `harness::turn-completed` binding. If
it never fires: the binding was registered against a trigger type that did
not exist yet (bind after the harness worker is up), or the handler filters
by the wrong id. Filter by `session_id` you got back from `harness::send`,
and always wrap the wait in a timeout that calls
`harness::stop { session_id }` before rejecting, so an abandoned turn does
not keep spending tokens.

## Turns fail with session::create / session::messages errors

`function_not_found: session::create` means the session-manager worker is
not registered on the bus; `invocation_stopped` mid-turn means its
connection dropped. One reproducible cause: an oversized function result.
A single unbounded `web::fetch` (the full npm registry document for a
popular package is close to a megabyte) inflates the transcript until the
`session::messages` frame kills the worker's engine connection, and the
queued frame re-poisons every reconnect until the session-manager process is
restarted. Prevent it in the prompt and the code: always pass `max_bytes`
(30000-60000) on `web::fetch`, prefer small endpoints
(`registry.npmjs.org/<pkg>/latest`, never the bare package URL), and split
big jobs into sub-agent sessions so no one transcript grows unbounded.

## The orchestrator does the work itself instead of spawning

Weaker models take the shortcut when the parent holds the same functions the
researchers need (which the subset rule forces). Prompt structurally: state
that the function is in the allow list only so it can be granted to
children, forbid direct use, and repeat per-spawn instructions inside every
task string. Then verify in the console trace that child sessions exist;
`harness::status.children` lists live children only and is empty after they
finish.

## Streaming consumers miss fast replies

Quick responses arrive as one `session::message-added`, not a stream of
`message-updated` revisions. Bind both types to the same handler. Events are
also unordered relative to `harness::turn-completed`, so print whatever tail
is missing from the completed event's `result` and filter events by
`origin.turn_id`, or a slow event from turn N bleeds into turn N+1's output.

## The chatbot narrates its function policy

With no functions allowed, the built-in identity prompt makes models open
with "function dispatch is disabled this turn". For plain chat send
`system_prompt_strategy: "override"` and `mode: "ask"`; keep `enrich` for
agents that dispatch functions, because the identity prompt is what teaches
the model the `agent_trigger` calling convention.

## Zero functions registered

`registerWorker` then `await something` then `registerFunction` registers
nothing: the registrations must be issued synchronously after
`registerWorker` so they ride the initial handshake. Do all
`registerFunction` / `registerTrigger` calls at module top level, then do
async work.

## Model picking

`harness::send` requires `model` and the harness has no default. Do not
hardcode one: any provider configured in llm-router is legal, catalogs
differ per machine, and a hardcoded id breaks everyone else. Resolve from
`router::models::list`, filter `supports_tools` when the agent dispatches
functions, auto-select only when exactly one candidate remains, and
otherwise fail with the list so the human chooses via an env var.

## Engine hygiene while iterating

Never run `iii worker add` / `remove` against a live engine you care about:
config churn re-registers providers and can desync registration tokens
until nothing spawns. Stop the stack, change the config, boot once. When a
worker process is alive but its functions are missing from
`engine::functions::list`, it is a zombie: kill the process and
`iii trigger worker::start name=<worker>`.
