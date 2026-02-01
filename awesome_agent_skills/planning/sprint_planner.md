---
name: sprint-planner
description: Agile sprint planning assistant for story estimation, capacity planning, and backlog prioritization.
---

# Sprint Planner Skill

## When to use this skill

Use this skill when you need:
- Sprint goal definition
- Story point estimation
- Capacity planning
- Backlog prioritization
- Sprint retrospective summaries

## How to Use this Skill

Add this as a system prompt in your AI application:

```python
from openai import OpenAI

client = OpenAI()

system_prompt = """You are an agile coach who helps teams plan effective sprints.

Sprint Planning Process:
1. Define sprint goal (one clear objective)
2. Review and refine backlog items
3. Estimate stories using points
4. Calculate team capacity
5. Commit to achievable scope

Estimation Guidelines (Fibonacci):
- 1 point: Trivial, < 2 hours
- 2 points: Small, half day
- 3 points: Medium, 1 day
- 5 points: Large, 2-3 days
- 8 points: Very large, should probably split
- 13+: Too big, must split

Capacity Calculation:
- Available hours = (Team members × Sprint days × 6 hours)
- Account for meetings, reviews, unexpected work
- Target 70-80% capacity for sustainability"""

response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Help me plan a 2-week sprint for my team"}
    ]
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| backlog | string | List of stories/tasks to consider |
| team_size | int | Number of developers |
| sprint_length | int | Sprint duration in days |
| velocity | int | (Optional) Historical velocity in points |

### Returns

- Sprint goal
- Selected stories with estimates
- Capacity analysis
- Risk flags
- Acceptance criteria suggestions

## Example

**Input:**
```
Team: 3 developers
Sprint: 2 weeks (10 days)
Previous velocity: 34 points

Backlog:
- User authentication system
- Password reset flow
- Profile page
- Admin dashboard
- Email notifications
- Search functionality
```

**Output:**
```markdown
## Sprint 12 Plan

### Sprint Goal
> Enable users to create accounts and manage their profiles

---

### Capacity

| Metric | Value |
|--------|-------|
| Team size | 3 developers |
| Sprint days | 10 |
| Gross hours | 180h (3 × 10 × 6h) |
| Meetings/overhead | -18h (10%) |
| **Net capacity** | **162h** |
| Target velocity | 34 points (historical) |

---

### Committed Stories

| Story | Points | Acceptance Criteria |
|-------|--------|---------------------|
| User authentication | 8 | Login/logout, session handling, secure tokens |
| Password reset flow | 5 | Email link, token expiry, success confirmation |
| Profile page | 5 | View/edit info, avatar upload, validation |
| Email notifications | 5 | Welcome email, password reset email, templates |

**Total committed: 23 points**

---

### Backlog (Not This Sprint)

| Story | Points | Notes |
|-------|--------|-------|
| Admin dashboard | 13 | Too large for remaining capacity, needs refinement |
| Search functionality | 8 | Deprioritized, not needed for MVP |

---

### Risks & Notes

⚠️ **Authentication (8 pts)** is the largest story. Consider splitting:
- Basic auth (5 pts)
- OAuth integration (3 pts)

⚠️ Email service integration may have external dependencies.

---

### Sprint Ceremonies

| Ceremony | When | Duration |
|----------|------|----------|
| Daily standup | Daily 9:30 AM | 15 min |
| Sprint review | Day 10, 2 PM | 1 hour |
| Retrospective | Day 10, 3 PM | 1 hour |
```
