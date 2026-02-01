---
name: email-drafter
description: Drafts professional emails for various situations with appropriate tone and structure.
---

# Email Drafter Skill

## When to use this skill

Use this skill when you need:
- Professional email composition
- Cold outreach emails
- Follow-up messages
- Difficult conversations via email
- Thank you and appreciation notes

## How to Use this Skill

Add this as a system prompt in your AI application:

```python
from openai import OpenAI

client = OpenAI()

system_prompt = """You are an expert email writer who crafts clear, effective professional emails.

Email Structure:
1. Subject line: Specific, actionable, under 50 characters
2. Opening: Context or purpose (1 sentence)
3. Body: Key information (2-3 short paragraphs)
4. Action: Clear next step
5. Close: Appropriate sign-off

Tone Guidelines:
- Professional: Formal, polished, respectful
- Friendly: Warm but businesslike
- Direct: Brief, action-oriented
- Diplomatic: Careful, tactful for sensitive topics

Best Practices:
- One email = one purpose
- Front-load the key message
- Use bullet points for lists
- Keep paragraphs under 3 sentences
- Always specify the ask clearly"""

response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Write a follow-up email after a job interview"}
    ]
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| situation | string | Context for the email |
| recipient | string | Who you're writing to |
| tone | string | (Optional) "professional", "friendly", "direct" |
| goal | string | (Optional) What you want to achieve |

### Returns

- Subject line options
- Complete email draft
- Tone analysis
- Alternative phrasings
- Send timing recommendation

## Example

**Input:**
```
Situation: Need to push back on an unrealistic project deadline
Recipient: My manager
Tone: Professional but assertive
```

**Output:**
```markdown
## Subject Line Options

1. "Project Timeline: Concerns and Proposed Alternatives"
2. "Re: Project X — Deadline Discussion Needed"
3. "Request: Timeline Review for Project X"

---

## Email Draft

**Subject:** Project Timeline: Concerns and Proposed Alternatives

Hi [Manager's name],

Thank you for sharing the project timeline yesterday. I've reviewed the requirements and want to flag some concerns about the March 15th deadline.

**My Assessment:**

Based on the scope, I estimate we need:
- Backend development: 4 weeks (vs. 2 planned)
- Testing & QA: 1 week (currently not allocated)
- Buffer for unknowns: 3-4 days

This puts a realistic delivery date around **April 5th**.

**The Risk:**

If we keep the March 15th deadline, we'd need to either:
1. Cut features (I can propose which)
2. Add resources (is budget available?)
3. Accept higher defect risk at launch

**Proposed Next Step:**

Could we meet for 30 minutes this week to discuss? I want to find a path that works for the business while setting the team up for success.

Let me know your availability.

Best,
[Your name]

---

## Tone Notes

- **Assertive but collaborative**: States position clearly without ultimatums
- **Solution-oriented**: Offers alternatives, not just problems
- **Data-backed**: Uses specific estimates to support concerns
- **Respectful of hierarchy**: Asks to discuss, doesn't demand

## Timing

Best sent: Tuesday-Thursday morning
Avoid: Friday afternoon, Monday morning
```
