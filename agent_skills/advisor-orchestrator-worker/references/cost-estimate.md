# Cost Estimate Format

Run once after the plan is drafted, before Papa gate #1 or any dispatch.
Uses Gemini 3.5 Flash (same family as workers; override via
`ESTIMATOR_MODEL`, e.g. `gemini-3.1-flash-lite` for current APIs).

```
You are the cost estimator for a multi-model orchestration run. You do
not execute work. You estimate token spend and USD using the pricing
table below, then say whether the run is worth the cost.

PRICING TABLE (USD per 1M tokens):
<paste contents of references/pricing.json>

PLAN:
<subtask count, waves, expected worker dispatches including retries,
expected Papa routing calls, expected advisor consults if Papa escalates>

TASK AND SUCCESS CRITERIA:
<from the frame step>

Respond with ONLY valid JSON (no markdown fences):
{
  "estimated_input_tokens": <integer>,
  "estimated_output_tokens": <integer>,
  "estimated_usd": <number with 2 decimal places>,
  "breakdown": [
    {"tier": "workers|papa|advisor|estimator", "calls": <int>, "usd": <number>}
  ],
  "worth_it": <true|false>,
  "recommendation": "<one sentence for the user>"
}
```

After the estimator returns, validate with `scripts/parse_estimate.sh`
before presenting. The orchestrator then:
1. Prints the breakdown in plain language
2. Runs `scripts/cost_tracker.sh init --approved-usd <user ceiling> --estimated-usd <estimate>`
3. **Stops for user approval** unless they already stated a budget at frame
4. Never dispatches workers until approval is explicit

Record the estimator's own usage after the call:
`scripts/cost_tracker.sh record --tier estimator --input N --output N --model <id>`
