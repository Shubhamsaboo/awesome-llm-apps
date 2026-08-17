# 🛡️ Anti-UI-Slop Gate

A small, local-first Agent Skill for catching concrete UI quality risks before
they ship. It is a runnable example from [UIZZE](https://uizze.com)'s broader
anti-UI-slop workflow, packaged for the [Awesome LLM Apps](https://github.com/Shubhamsaboo/awesome-llm-apps)
collection.

## Install

```bash
npx skills add https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/agent_skills/anti-ui-slop
```

Then ask an agent to audit a frontend project for UI slop, or run the core
checker directly:

```bash
python3 scripts/check_ui_slop.py --path /path/to/project
```

## What it checks

- generic placeholder copy;
- buttons that have no visible source-level action hook;
- images without an `alt` attribute;
- forms with no visible state vocabulary;
- repeated raw color values in CSS.

The checker is deterministic, uses only the Python standard library, and never
edits the project or accesses the network. Source heuristics are triage, not a
design verdict: delegated event handlers, generated markup, and intentional
one-off values need human review.

## Example output

```text
WARN generic-copy src/Checkout.tsx:18 — placeholder copy: "Click here"
WARN inert-control src/Checkout.tsx:32 — button has no visible action hook
ERROR image-alt src/Checkout.tsx:41 — image is missing alt text

3 finding(s): 1 error, 2 warning(s)
```

For live UI evidence, the full [UIZZE MCP](https://uizze.com) can search
800,000+ real web and iOS screens. The free local Skill and no-account preview
remain available from the [canonical UIZZE repository](https://github.com/uizze/uizze).
