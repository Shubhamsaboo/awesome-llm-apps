---
name: project-planner
description: Breaks down projects into actionable tasks with timelines and dependencies.
---

# Project Planner Skill

## When to use this skill

Use this skill when you need:
- Project scope definition
- Work breakdown structure (WBS)
- Task dependencies and sequencing
- Timeline and milestone planning
- Resource allocation

## How to Use this Skill

Add this as a system prompt in your AI application:

```python
from openai import OpenAI

client = OpenAI()

system_prompt = """You are an expert project planner who breaks complex projects into achievable tasks.

Planning Process:
1. Define the end goal and success criteria
2. Identify major deliverables (milestones)
3. Break deliverables into tasks (2-8 hours each)
4. Map dependencies between tasks
5. Estimate effort and assign owners
6. Build timeline with buffer for risks

Task Guidelines:
- Each task should have a clear "done" criteria
- No task longer than 2 days
- Identify blockers and dependencies upfront
- Include testing/review time in estimates
- Add 20-30% buffer for unknowns

Output Format:
- Project overview
- Milestones with dates
- Task breakdown by phase
- Dependency diagram
- Risk factors"""

response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Plan a mobile app launch"}
    ]
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| project | string | What you're planning |
| deadline | string | (Optional) Target completion date |
| team_size | int | (Optional) Number of people |
| constraints | string | (Optional) Budget, tech, or other limits |

### Returns

- Project overview and goals
- Milestone breakdown
- Detailed task list with estimates
- Dependency map
- Risk assessment and mitigation

## Example

**Input:**
```
Plan a company website redesign. Team: 1 designer, 2 developers. Deadline: 6 weeks.
```

**Output:**
```markdown
## Project: Website Redesign

**Goal**: Launch redesigned company website
**Timeline**: 6 weeks
**Team**: 1 designer, 2 developers

---

## Milestones

| # | Milestone | Target Date | Owner |
|---|-----------|-------------|-------|
| 1 | Design approved | Week 2 | Designer |
| 2 | Development complete | Week 5 | Dev team |
| 3 | QA & Launch | Week 6 | All |

---

## Phase 1: Discovery & Design (Weeks 1-2)

| Task | Effort | Owner | Depends On |
|------|--------|-------|------------|
| Audit current site | 4h | Designer | - |
| Gather stakeholder requirements | 4h | Designer | - |
| Create wireframes | 8h | Designer | Requirements |
| Design homepage mockup | 8h | Designer | Wireframes |
| Design inner page templates | 8h | Designer | Homepage |
| Stakeholder review & revisions | 8h | Designer | Mockups |

## Phase 2: Development (Weeks 3-5)

| Task | Effort | Owner | Depends On |
|------|--------|-------|------------|
| Set up dev environment | 4h | Dev 1 | - |
| Build component library | 16h | Dev 1 | Design approved |
| Develop homepage | 16h | Dev 2 | Components |
| Develop inner pages | 24h | Dev 1+2 | Homepage |
| CMS integration | 12h | Dev 1 | Pages |
| Responsive testing | 8h | Dev 2 | All pages |

## Phase 3: Launch (Week 6)

| Task | Effort | Owner | Depends On |
|------|--------|-------|------------|
| Content migration | 8h | Dev 2 | CMS ready |
| QA testing | 8h | All | Migration |
| Bug fixes | 8h | Devs | QA |
| DNS/hosting setup | 2h | Dev 1 | Bug fixes |
| Launch & monitoring | 4h | All | Everything |

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Design feedback delays | High | Schedule reviews in advance |
| Scope creep | Medium | Lock requirements after Week 1 |
| Content not ready | Medium | Start content early, use placeholders |
```
