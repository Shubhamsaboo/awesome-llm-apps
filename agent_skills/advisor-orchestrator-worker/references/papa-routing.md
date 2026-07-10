# Papa Routing Format

Papa is **not** on the hot path. Mandatory advisor plan review and taste pass
stay as in v1.0. Invoke Papa only when:

1. **Conflict** — worker outputs contradict each other beyond provided context,
   or synthesis cannot merge them without guessing.
2. **Advisor–orchestrator disagreement** — after a mandatory advisor consult
   (plan review, taste pass, or mid-loop judgment call), the orchestrator
   would materially reject or diverge from the advisor's verdict/fixes.

Papa is a tie-breaker on a **different provider** than the Anthropic advisor —
that separation prevents the advisor from owning its own escalation.

Default model: `gemini-3.5-pro` (July 2026 knob). Override for current APIs:
`PAPA_MODEL=gemini-3.1-pro-preview`.

```
You are Papa, the conflict and disagreement resolver between an orchestrator
and its advisor. You never execute work and never rewrite the deliverable.
You only break ties when they cannot align.

REQUEST TYPE: <conflict | advisor-orchestrator disagreement>
TASK AND SUCCESS CRITERIA: <from the frame step>
QUESTION: <what decision is deadlocked>
MATERIAL: <conflicting worker excerpts, or advisor verdict vs orchestrator position — keep under 2k chars>
COST SNAPSHOT: <output of scripts/cost_tracker.sh status>

Respond with exactly this structure (no prose outside it):
ROUTE: <advisor | orchestrator>
REASON: one line
```

## ROUTE meaning

| ROUTE | Meaning |
|---|---|
| `advisor` | Side with the advisor — apply advisor fixes, escalate conflict to advisor judgment, or hold ship until advisor concerns are addressed |
| `orchestrator` | Side with the orchestrator — proceed with orchestrator's merge/resolution/rebuttal as stated |

Do **not** invoke Papa for straightforward plans, routine plan review, or
routine taste pass when advisor and orchestrator already align.

Record Papa usage after the call with `--tier papa --model ${PAPA_MODEL:-gemini-3.5-pro}`.

Parse with `scripts/parse_papa_route.sh`. Log every Papa ROUTE on the status
board. If the orchestrator overrides Papa's ROUTE, state why in the final
report.
