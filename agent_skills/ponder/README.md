# ⚖️ Ponder

A coverage-gated, multi-pass deliberation loop for coding agents. Instead of
letting a single pass skip the last files in a directory or letting an
unstructured multi-pass prompt invent nitpicks on pass 4, Ponder tracks unit
coverage and finding revisions in a local append-only JSONL ledger.

- **Coverage gate**: `scripts/ponder decide stop` exits `2` (`blocked`) while any
  enumerated file, module, or screen in `units.json` is ungraded.
- **Four perspectives to four ledger operations**: `dreamer` (`add`), `builder`
  (`edit`), `empath` (`change`), and `skeptic` (`delete`) revise prior findings
  with required `why` rationales rather than rewriting from scratch.
- **Epistemic silence**: When all four perspectives re-check the evidence and
  produce zero deltas across consecutive passes, the session converges and
  stops cleanly.

Upstream repository and full benchmark study:
[github.com/Quinnod345/ponder](https://github.com/Quinnod345/ponder)

## Install

```bash
npx skills add https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/agent_skills/ponder
```

## Run

Ask the agent:

> Ponder the architecture of `src/auth` until it converges, then show me the
> must-fix plan.

Or drive the deterministic CLI directly:

```bash
scripts/ponder start "auth module" --lens architecture --min-passes 2 --max-passes 4
scripts/ponder status
scripts/ponder verify
```

Requires Node.js `>= 18` with zero npm dependencies. Operates locally and
offline (`PONDER_OCA=off` by default) and never modifies source files.
