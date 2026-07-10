# Disagreement Cost Format

Run **only when invoking Papa** — after a conflict or advisor–orchestrator
deadlock is identified, **before** the Papa call. Same Flash estimator
family as pre-flight (`ESTIMATOR_MODEL`); one extra call per Papa invocation.

Cost advisory prices **both sides** of the tie-break so Papa can weigh
substance **and** spend.

```
You are the cost estimator for a deadlocked decision in a multi-model run.
You do not execute work and you do not pick a winner. Price what each
resolution path would cost in tokens and USD from this point forward.

PRICING TABLE (USD per 1M tokens):
<paste contents of references/pricing.json>

REQUEST TYPE: <conflict | advisor-orchestrator disagreement>
TASK AND SUCCESS CRITERIA: <from frame>

ORCHESTRATOR PATH (what happens if orchestrator wins the tie-break):
<concrete actions: e.g. merge rule, rebuttal accepted, redispatch plan, ship as-is>

ADVISOR PATH (what happens if advisor wins the tie-break):
<concrete actions: e.g. apply advisor fixes, extra consult, expand scope, hold ship>

RUN SO FAR:
<output of scripts/cost_tracker.sh status>

Respond with ONLY valid JSON (no markdown fences):
{
  "orchestrator_path": {
    "estimated_input_tokens": <integer>,
    "estimated_output_tokens": <integer>,
    "estimated_usd": <number with 2 decimal places>,
    "summary": "<one line: what this path does>"
  },
  "advisor_path": {
    "estimated_input_tokens": <integer>,
    "estimated_output_tokens": <integer>,
    "estimated_usd": <number with 2 decimal places>,
    "summary": "<one line: what this path does>"
  },
  "delta_usd": <advisor_path.estimated_usd minus orchestrator_path.estimated_usd>,
  "cost_note": "<one sentence for Papa: who is cheaper and by how much>"
}
```

After the call:
1. `scripts/parse_disagreement_cost.sh` on the response text
2. Paste the validated JSON (or `cost_note` + both USD lines) into the Papa
   brief under `DISAGREEMENT COST:` — see `references/papa-routing.md`
3. Record estimator usage: `--tier estimator`

Papa **must** receive this block. Do not call Papa without pricing both paths.
