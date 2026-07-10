# Deterministic Guardrails

Papa may route here instead of an advisor consult when a rule fully decides
the case. These are checklists the orchestrator applies directly — no LLM.

## Verification guardrails

- **README grep is not verification.** If acceptance criteria require running
  a command, running tests, or reading output, grepping docs or checking file
  existence is FAIL.
- **Exit zero is not pass.** A script that prints success while doing nothing
  is FAIL.
- **Adjacent checks are FAIL.** Testing something near the target but not the
  target criterion is FAIL.

## Merge guardrails

- **No silent partial pass.** Every subtask gets PASS, FIX, or ESCALATE.
- **No hand-patching substantive failures.** FIX means redispatch with the
  failed criterion quoted.
- **No averaging contradictions.** When two workers disagree, escalate (Papa
  routes `advisor` unless domain-kb resolves it).

## Scope guardrails

- **Briefs are self-contained.** A worker brief that says "as discussed" or
  references unseen context is invalid — rewrite before dispatch.
- **Workers do not expand scope.** Output outside acceptance criteria is trimmed
  or triggers FIX.

## Budget guardrails

- **Checkpoint refused → stop the call.** Do not route around the ledger by
  inlining the work as orchestrator grunt (except the single-role degraded-mode
  exception in SKILL.md).
- **Consult budget is a hard cap** unless the user explicitly raises it mid-run.
