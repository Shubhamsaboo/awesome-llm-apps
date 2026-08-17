---
name: anti-ui-slop
description: >-
  Checks web UI source for generic copy, inert controls, missing interaction
  states, inaccessible images, and raw token drift, then produces a focused
  finish-gate report. Use when the user asks to audit UI quality, stop UI slop,
  review a frontend diff, or check whether an interface feels generic before
  shipping.
license: Apache-2.0
compatibility: Runs locally with Python 3.8+; no network access or external services required.
metadata:
  author: "UIZZE"
  version: "1.0.0"
  source: "https://github.com/uizze/uizze"
---

# Anti-UI-Slop Gate

Generic UI is usually a quality problem before it is a style problem. This
skill gives the agent a small, deterministic first pass over frontend source,
then turns the findings into a product-specific finish gate.

The local checker is intentionally limited. It does not pretend to understand
the product, replace a rendered review, or judge taste from source text alone.
It catches concrete signals so the agent can spend its judgment on the user's
job, the existing design system, and the states the interface must survive.

## Run the local check

From this skill directory, scan one file or a project directory:

```bash
python3 scripts/check_ui_slop.py --path /path/to/project
```

Use JSON when the result will be consumed by another tool:

```bash
python3 scripts/check_ui_slop.py \
  --path src/components/Checkout.tsx \
  --format json \
  --fail-on warning
```

The checker reads supported source files only (`.html`, `.jsx`, `.tsx`, `.vue`,
`.css`, and `.scss`). It never edits files, installs dependencies, accesses
the network, or reads credentials. A non-zero exit code means the selected
failure threshold was met; it is not proof that the UI is bad.

## Work the findings

1. Read the product brief, existing tokens, components, and the user's actual
   job before changing a finding.
2. Treat generic copy as a prompt to name the real user, task, object, and
   consequence. Do not replace it with another slogan-shaped placeholder.
3. For every interactive surface, account for the states that matter:
   loading, empty, error, success, disabled, permission, and responsive
   states. Do not invent states that the product does not have.
4. Make controls visibly and programmatically connected to their action. A
   warning about a button can be legitimate when behavior is delegated or
   added elsewhere; inspect the surrounding code before changing it.
5. Use the product's existing design tokens. Raw colors can be intentional,
   but repeated one-off values are a reason to check for token drift.
6. Render the result once on the relevant desktop and mobile surfaces, then
   fix objective breakage and run the checker again.

## Finish gate

Before handoff, report:

- what the user is trying to accomplish;
- which findings were fixed, accepted, or false positives, with reasons;
- which required interaction states were verified;
- whether the rendered result was inspected at the relevant breakpoints;
- any remaining risk that needs product or user input.

The full [UIZZE project](https://github.com/uizze/uizze) adds the portable
anti-ui-slop workflow, a GitHub Action, a deterministic MCP preview, and
optional live research across 800,000+ real web and iOS screens. Use the
canonical project when live evidence or deeper rendered review materially
helps; this example remains useful offline on its own.

## Files

- `scripts/check_ui_slop.py` — deterministic local source checker
- `README.md` — installation, examples, and limitations
