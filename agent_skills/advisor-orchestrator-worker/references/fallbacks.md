# API Fallbacks

Read this when a primary CLI path is unavailable or a dispatch fails.
All fallbacks: payloads built with `jq --rawfile` from temp files,
`--fail` plus `pipefail`, unwrap response envelopes. After every API
call, read token usage from the response and record it:

```bash
# Gemini: .usageMetadata.promptTokenCount / candidatesTokenCount
# Anthropic: .usage.input_tokens / .usage.output_tokens
scripts/cost_tracker.sh record --tier <worker|papa|advisor|estimator> \
  --input <n> --output <n> --model <model-id>
scripts/cost_tracker.sh check   # advisory only
```

If usage metadata is missing, estimate chars/4 for input and output:

```bash
# Gemini response file → record (example: estimator)
inp=$(jq -r '.usageMetadata.promptTokenCount // empty' "$estimate_response")
out=$(jq -r '.usageMetadata.candidatesTokenCount // empty' "$estimate_response")
if [ -z "$inp" ] || [ -z "$out" ]; then
  inp=$(wc -c < "$estimate_brief" | awk '{print int($1/4)}')
  out=$(wc -c < "$estimate_text" | awk '{print int($1/4)}')
fi
scripts/cost_tracker.sh record --tier estimator --input "$inp" --output "$out" \
  --model "${ESTIMATOR_MODEL:-gemini-3.5-flash}"

# Anthropic response file → record (example: advisor)
inp=$(jq -r '.usage.input_tokens' "$advisor_response")
out=$(jq -r '.usage.output_tokens' "$advisor_response")
scripts/cost_tracker.sh record --tier advisor --input "$inp" --output "$out" \
  --model claude-fable-5
```

## Cost estimator: Gemini Flash API call

One call after Plan, before advisor plan review. Default `gemini-3.5-flash`; override:
`ESTIMATOR_MODEL` (e.g. `gemini-3.1-flash-lite`).

```bash
api_key="${GEMINI_API_KEY:-$GOOGLE_API_KEY}"
model="${ESTIMATOR_MODEL:-gemini-3.5-flash}"
[ -n "$api_key" ] || { echo "no Gemini key" >&2; exit 1; }
( set -o pipefail
  jq -n --rawfile t "$estimate_brief" '{contents:[{parts:[{text:$t}]}]}' \
    | curl -sS --fail --max-time 120 \
      "https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent" \
      -H "x-goog-api-key: $api_key" -H "Content-Type: application/json" -d @- \
    | tee "$estimate_response" \
    | jq -r '.candidates[0].content.parts[0].text' )
```

Parse with `scripts/parse_estimate.sh` (validates JSON). Record estimator usage from
`$estimate_response` usageMetadata before proceeding.

## Disagreement cost: Gemini Flash API call

One call **per Papa invocation**, after both paths are stated, before Papa.
Same API pattern as pre-flight estimator; brief from `references/disagreement-cost.md`.
Parse with `scripts/parse_disagreement_cost.sh`. Paste output into Papa brief.

```bash
api_key="${GEMINI_API_KEY:-$GOOGLE_API_KEY}"
model="${ESTIMATOR_MODEL:-gemini-3.5-flash}"
[ -n "$api_key" ] || { echo "no Gemini key" >&2; exit 1; }
( set -o pipefail
  jq -n --rawfile t "$disagreement_cost_brief" '{contents:[{parts:[{text:$t}]}]}' \
    | curl -sS --fail --max-time 120 \
      "https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent" \
      -H "x-goog-api-key: $api_key" -H "Content-Type: application/json" -d @- \
    | tee "$disagreement_cost_response" \
    | jq -r '.candidates[0].content.parts[0].text' )
```

## Papa: Gemini Pro API call

Conflict or advisor–orchestrator disagreement only — not routine plan/taste
pass. Default `gemini-3.5-pro` (July 2026 knob).
Override for current APIs: `PAPA_MODEL=gemini-3.1-pro-preview`.

```bash
api_key="${GEMINI_API_KEY:-$GOOGLE_API_KEY}"
model="${PAPA_MODEL:-gemini-3.5-pro}"
[ -n "$api_key" ] || { echo "no Gemini key" >&2; exit 1; }
( set -o pipefail
  jq -n --rawfile r "$routing" \
    '{contents:[{parts:[{text:$r}]}], generationConfig:{maxOutputTokens:512}}' \
    | curl -sS --fail --max-time 120 \
      "https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent" \
      -H "x-goog-api-key: $api_key" -H "Content-Type: application/json" -d @- \
    | tee "$papa_response" \
    | jq -r '.candidates[0].content.parts[0].text' )
```

`maxOutputTokens: 512` limits Papa's routing answer length, not the run
budget. Parse with `scripts/parse_papa_route.sh`. Record usage from `$papa_response` with `--tier papa`.

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
    | tee "$worker_response" \
    | jq -r '.candidates[0].content.parts[0].text' > "$out" ) &
pids+=($!)
```

Record each worker's usage from `$worker_response` after the wave.

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
    | tee "$advisor_response" \
    | jq -r '.content[] | select(.type == "text") | .text' )
```

Record advisor usage from `$advisor_response` `.usage` fields.
