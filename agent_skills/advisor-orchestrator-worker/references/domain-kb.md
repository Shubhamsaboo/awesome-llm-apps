# Domain Knowledge Base

Papa may route here when a question has a stored answer instead of burning an
advisor consult.

## Lookup order

1. Project file `.asil/domain-answers.json` (if present) — keyed by file path
   and `DOMAIN_QUESTION` marker text
2. Skill-local `references/domain-answers.json` (if the orchestrator created
   one at the frame step from user-provided context)
3. Inline answers the user stated in the current session (quote them in the
   report; do not invent)

## When domain-kb applies

- A worker or plan touches a flagged domain zone and the answer is on file
- The user already answered a triage question this run
- Success criteria embed domain facts the orchestrator framed explicitly

## When domain-kb does NOT apply

- The question is novel this run and no answer exists on file → Papa routes
  `defer` (ask the user) or `advisor` (judgment), never `orchestrator` guessing
- Conflicting answers on file → Papa routes `advisor`

## Recording new answers

When the user answers a domain question, append to the session ledger:

```bash
# orchestrator maintains this in the final report; optional persistence:
# echo '{"path":"pkg/rates.ts","question":"grace period?","answer":"5 business days"}' \
#   >> references/domain-answers.jsonl
```

Unanswered domain questions block autonomous changes to those files until
triaged — same rule as ASIL's domain guard, adapted for orchestration runs.
