# Discovery Workflow

**Goal: Idea maturation, not speed.**

Proceed in phases. Even if the user provides details, complete each phase through conversation. Do not infer or assume -- discuss and validate with user. Proceed one phase at a time.

---

## Phase 1: Value Proposition

1. **Problem + User**: What problem does this solve? For whom?
2. **Pain**: How is it solved today? What's painful about that?
3. **Core actions**: 1-3 focused actions (not a full app port)

---

## Phase 2: Why LLM?

1. **Conversational win**: Where does "just say it" beat clicking through menus?
2. **LLM adds**: What does the LLM contribute? (intent parsing, generation, reasoning, summarization)
3. **What LLM lacks**: Your data? Your APIs? Ability to take real actions?

**Fail patterns** (stop if any match):

- Long-form or static content better suited for a website
- Complex multi-step workflows that exceed widget display modes
- Dashboards (use tables, lists, or short summaries instead)
- Full app ports instead of focused atomic actions
- No clear answer to "why inside an AI assistant vs standalone?"

If a fail pattern matches: explain the gap, suggest a different interface or narrower scope.

---

## Phase 3: UI Overview

Describe the user journey through core actions:

1. **First view**: What does the user see when the widget loads?
2. **Key interactions**: What happens at each core action?
3. **End state**: How does the experience conclude?

---

## Phase 4: Product Context

Gather:

- Existing products and APIs
- Authentication method (OAuth, API key, none)
- Rate limits and constraints
- Data sources

---

## Phase 5: Spec Summary

After phases 1-4 are discussed, assemble a brief spec:

```markdown
# App Name

## Value Proposition

[Problem, user, pain point, core actions]

## Why LLM?

[Conversational win, what LLM adds, what it lacks]

## UI Overview

[First view, key interactions, end state]

## Product Context

[APIs, auth, constraints]

## Tools and Widgets

[List of tools and widgets with input/output shapes]
```

After the spec is ready, proceed to [architecture.md](architecture.md) for API design, then [setup.md](setup.md) for project scaffolding.
