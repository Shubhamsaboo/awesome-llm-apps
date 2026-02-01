---
name: meeting-notes
description: Creates structured meeting summaries with action items and decisions.
---

# Meeting Notes Skill

## When to use this skill

Use this skill when you need:
- Meeting summaries from transcripts
- Action item extraction
- Decision documentation
- Follow-up email drafts
- Async meeting updates

## How to Use this Skill

Add this as a system prompt in your AI application:

```python
from openai import OpenAI

client = OpenAI()

system_prompt = """You are an expert at creating clear, actionable meeting summaries.

Summary Structure:
1. Meeting metadata (date, attendees, purpose)
2. Key decisions made
3. Action items with owners and deadlines
4. Open questions / parking lot
5. Next steps

Action Item Format:
- [ ] [OWNER] Task description — Due: [DATE]

Guidelines:
- Lead with decisions, not discussion
- Every action item needs an owner
- Distinguish decisions from discussions
- Note unresolved items explicitly
- Keep summaries under 1 page

Quality Checks:
- Can someone who missed the meeting understand what happened?
- Is every action item assignable and trackable?
- Are dates specific (not "next week")?"""

response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": transcript}
    ]
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| transcript | string | Meeting recording transcript or notes |
| format | string | (Optional) "summary", "detailed", "email" |
| focus | string | (Optional) Specific topics to highlight |

### Returns

- Structured meeting summary
- Action items with owners
- Decisions made
- Follow-up email draft
- Open questions

## Example

**Input:**
```
[Raw transcript from a product planning meeting discussing Q2 roadmap, including discussion about feature priorities, timeline debates, and resource allocation]
```

**Output:**
```markdown
# Product Planning Meeting — Q2 Roadmap

**Date:** January 31, 2024
**Attendees:** Sarah (PM), Mike (Eng Lead), Lisa (Design), Tom (QA)
**Duration:** 45 minutes

---

## 📋 Decisions Made

1. **Q2 Focus**: Mobile app redesign is the top priority (unanimous)
2. **Timeline**: Launch target is May 15th (6-week development window)
3. **Resources**: Will hire 1 contractor for frontend work
4. **Scope Cut**: Analytics dashboard moved to Q3

---

## ✅ Action Items

| Owner | Task | Due |
|-------|------|-----|
| Sarah | Write PRD for mobile redesign | Feb 5 |
| Mike | Estimate engineering effort | Feb 7 |
| Lisa | Create wireframes for key flows | Feb 10 |
| Tom | Define QA test plan | Feb 12 |
| Sarah | Post contractor job listing | Feb 2 |
| Mike | Set up weekly sync for project | Feb 3 |

---

## 💬 Discussion Highlights

**Feature Prioritization:**
- Team debated between mobile app and API improvements
- Decision: Mobile wins because 60% of users are mobile-first
- API improvements still important but not blocking

**Timeline Concerns:**
- Mike raised risk about May 15th being aggressive
- Agreed: Will check in at Week 2 and adjust if needed
- Mitigation: Contractor hire will add capacity

**Design Approach:**
- Lisa proposed two options: evolution vs. revolution
- Decision: Evolution (less risk, faster delivery)
- Will revisit revolutionary redesign in Q4

---

## ❓ Open Questions (Parking Lot)

- [ ] Do we need legal review for new privacy features?
- [ ] What's the budget for the contractor?
- [ ] Should we do a beta release before full launch?

---

## 📅 Next Meeting

**Q2 Roadmap Check-in**
- When: February 14, 2024, 2:00 PM
- Purpose: Review PRD, wireframes, and estimates
- Prep: All action items above should be complete

---

## 📧 Follow-up Email (Draft)

**Subject:** Q2 Roadmap Meeting Summary — Action Items Inside

Hi team,

Thanks for the productive Q2 planning session! Here's a quick summary:

**We decided:** Mobile app redesign is our Q2 priority, targeting May 15th launch.

**Key actions:**
- Sarah: PRD by Feb 5
- Mike: Estimates by Feb 7
- Lisa: Wireframes by Feb 10
- Tom: QA plan by Feb 12

Full notes: [link to doc]

Next check-in: February 14th at 2pm.

Let me know if I missed anything!

Sarah
```
