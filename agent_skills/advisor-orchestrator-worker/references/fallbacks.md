# API Fallbacks

Read this when a primary CLI path is unavailable or a dispatch fails.
Both fallbacks keep the primary paths' discipline: payloads built with
`jq --rawfile` from the same temp file (safe for arbitrary text),
`--fail` plus `pipefail` so an auth or quota error is a detectable
failure, and a closing jq that unwraps the response envelope so the
orchestrator reads plain text on either path.

## Workers: bare Gemini API call

No tools. Run the full wave in parallel; the 3-batch cap is an agy
quota rule and does not apply here.

```bash
api_key="${GEMINI_API_KEY:-$GOOGLE_API_KEY}"
[ -n "$api_key" ] || { echo "no Gemini key (set GEMINI_API_KEY or GOOGLE_API_KEY)" >&2; exit 1; }
( set -o pipefail
  jq -n --rawfile t "$brief" '{contents:[{parts:[{text:$t}]}]}' \
    | curl -sS --fail --max-time 300 \
      "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent" \
      -H "x-goog-api-key: $api_key" -H "Content-Type: application/json" -d @- \
    | jq -r '.candidates[0].content.parts[0].text' > "$out" ) &
pids+=($!)
```

## Advisor: bare Anthropic API call

Same model as the CLI path. The `fallbacks` parameter re-serves a
safety-classifier refusal on Opus 4.8 inside the same call, so one
declined consult cannot stall the loop.

```bash
[ -n "$ANTHROPIC_API_KEY" ] || { echo "no ANTHROPIC_API_KEY" >&2; exit 1; }
( set -o pipefail
  jq -n --rawfile c "$consult" '{model: "claude-fable-5", max_tokens: 16000,
      fallbacks: [{model: "claude-opus-4-8"}],
      messages: [{role: "user", content: $c}]}' \
    | curl -sS --fail --max-time 300 "https://api.anthropic.com/v1/messages" \
      -H "x-api-key: $ANTHROPIC_API_KEY" -H "anthropic-version: 2023-06-01" \
      -H "anthropic-beta: server-side-fallback-2026-06-01" \
      -d @- \
    | jq -r '.content[] | select(.type == "text") | .text' )
```

## Papa: bare Anthropic API call (routing only)

Short response, low token cap. Papa uses Sonnet by default — routing is
cheaper than a full advisor critique. Checkpoint `papa` on the ledger
before this call.

```bash
[ -n "$ANTHROPIC_API_KEY" ] || { echo "no ANTHROPIC_API_KEY" >&2; exit 1; }
( set -o pipefail
  jq -n --rawfile r "$routing" '{model: "claude-sonnet-4-6", max_tokens: 512,
      messages: [{role: "user", content: $r}]}' \
    | curl -sS --fail --max-time 120 "https://api.anthropic.com/v1/messages" \
      -H "x-api-key: $ANTHROPIC_API_KEY" -H "anthropic-version: 2023-06-01" \
      -d @- \
    | jq -r '.content[] | select(.type == "text") | .text' )
```

If the `claude` CLI is available, Papa may use it with a pinned Sonnet
model and the same timeout wrapper as advisor consults. Papa never uses
Fable 5 — that tier is reserved for advisor critiques.
