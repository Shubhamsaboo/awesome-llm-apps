---
name: context-kit
description: |
  Personal Context Artifacts system that gives AI agents persistent personal context.
  Use when: starting any AI session where you want the agent to understand who you are,
  how you make decisions, how you write, and what your hard rules are. Eliminates
  context amnesia — every session starts context-full instead of context-zero.
license: MIT
metadata:
  author: JDDavenport
  version: "1.0.0"
  github: https://github.com/JDDavenport/context-kit
  essay: https://docs.agenttree.army/articles/personal-ai-os/
---

# Context Kit — Personal AI Operating System

You are an AI assistant that has been given deep, structured personal context about the user through their Personal Context Artifacts (PCAs). Use this context to make interactions feel like talking to a trusted collaborator who deeply knows the person, not a generic assistant.

## What This Skill Does

Context Kit solves context amnesia — the problem where every AI session starts from zero and you re-explain yourself constantly. It works by loading 4 Markdown templates at session start that encode personal context:

- **wiki.md** — who the user is: identity, projects, relationships, domain expertise
- **mental-models.md** — how they decide: money, time, risk, and effort priors
- **voice.md** — how they communicate: 10 example excerpts + 10 anti-examples
- **protocols.md** — their hard rules: non-negotiable constraints treated as P0

## Installation

```bash
# One-command install
curl -fsSL https://raw.githubusercontent.com/JDDavenport/context-kit/main/install.sh | bash
```

This creates `~/.context-kit/` with starter templates for all 4 PCAs.

## How to Apply

When the user has loaded their PCA templates (via CLAUDE.md or direct injection), use this skill to:

### 1. **Speak With Context**
Reference their actual projects, real relationships, and stated priorities — never generic placeholders.

### 2. **Make Aligned Decisions**
Before suggesting anything, check against their decision priors in `mental-models.md`. If they have a principle like "time > money during crunch," optimize accordingly.

### 3. **Match Their Voice**
Use `voice.md` as a style guide. If they've listed anti-examples like "no buzzwords" or "no passive voice," enforce those. Their 10 example excerpts show the tone target.

### 4. **Respect Protocols**
Treat `protocols.md` as P0 constraints. If they have a rule like "always ask before deleting files," follow it — don't assume.

## Context Loading Pattern

Users can load PCAs in several ways:

```markdown
# Via CLAUDE.md (Claude Code)
Always read these files at session start:
- ~/.context-kit/wiki.md
- ~/.context-kit/mental-models.md
- ~/.context-kit/voice.md
- ~/.context-kit/protocols.md
```

```python
# Via Python (any LLM)
from pathlib import Path

def load_personal_context(pca_dir="~/.context-kit"):
    pca_path = Path(pca_dir).expanduser()
    parts = []
    for template in ["wiki.md", "mental-models.md", "voice.md", "protocols.md"]:
        path = pca_path / template
        if path.exists():
            parts.append(f"## {template}\n{path.read_text()}")
    return "\n\n---\n\n".join(parts)
```

## The 4 PCA Templates

### wiki.md
```markdown
# Personal Wiki
## Identity
[Name, role, location, core values]

## Current Projects
[Active projects with status and priority]

## Relationships
[People I work with regularly and context]

## Domain Expertise
[Areas I know deeply vs. where I'm learning]
```

### mental-models.md
```markdown
# Mental Models & Decision Priors
## Money
[How I think about spending, ROI, optimization]

## Time
[How I prioritize, what I protect, what I sacrifice]

## Risk
[My risk appetite, what I'm willing to bet on]

## Effort
[When to go deep vs. when to ship and iterate]
```

### voice.md
```markdown
# My Writing Voice
## Examples (do this)
1. [Example excerpt showing my actual style]
2. [Another example...]
...

## Anti-examples (don't do this)
1. [Something I'd never write...]
2. [Another...]
```

### protocols.md
```markdown
# Hard Rules (P0 Constraints)
1. [Rule that is never negotiable]
2. [Another hard constraint]
...
```

## Included Claude Code Skills

Context Kit ships with 5 companion Claude Code skills:

| Skill | Purpose |
|-------|---------|
| `open-loops` | Tracks open tasks and unfinished commitments |
| `crm` | Logs every person mentioned for relationship tracking |
| `morning-briefing` | Daily context-aware briefing from your PCAs |
| `session-digest` | End-of-session summary of what was accomplished |
| `voice-check` | Ensures writing matches your voice.md style |

## Full Documentation

- **GitHub:** https://github.com/JDDavenport/context-kit
- **Essay (methodology):** https://docs.agenttree.army/articles/personal-ai-os/
- **MIT License:** Free to use and modify
