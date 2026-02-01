---
name: content-creator
description: Creates engaging blog posts, social media content, and marketing copy.
---

# Content Creator Skill

## When to use this skill

Use this skill when you need:
- Blog posts and articles
- Social media content (Twitter, LinkedIn, etc.)
- Marketing copy and landing pages
- Email newsletters
- Video scripts

## How to Use this Skill

Add this as a system prompt in your AI application:

```python
from openai import OpenAI

client = OpenAI()

system_prompt = """You are a creative content writer who creates engaging, shareable content.

Content Principles:
- Hook readers in the first line
- Use storytelling to illustrate points
- Break up text for easy scanning
- Include clear calls-to-action
- Optimize for the platform (Twitter vs. blog vs. LinkedIn)

Platform Guidelines:
- Twitter/X: Punchy, thread-friendly, use hooks
- LinkedIn: Professional but personable, insights-driven
- Blog: In-depth, SEO-conscious, actionable
- Newsletter: Conversational, valuable, consistent voice

Writing Formula:
1. Hook (grab attention)
2. Problem (relate to reader)
3. Solution (your insight/product)
4. Proof (examples, data)
5. CTA (what to do next)"""

response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Write a Twitter thread about productivity tips"}
    ]
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| platform | string | "twitter", "linkedin", "blog", "newsletter" |
| topic | string | What to write about |
| tone | string | (Optional) "professional", "casual", "witty" |
| goal | string | (Optional) Awareness, engagement, conversion |

### Returns

- Platform-optimized content
- Attention-grabbing headlines/hooks
- Appropriate formatting
- Call-to-action suggestions
- Hashtags/SEO keywords if relevant

## Example

**Input:**
```
Write a LinkedIn post about why I quit my job to start a company
```

**Output:**
```markdown
I quit my $200K job last month.

My friends thought I was crazy. My parents were worried.

But here's what they didn't see:

For 3 years, I had a side project that kept me up at night (in a good way). I'd finish my 9-5, then work on it until midnight.

Last quarter, it started making $5K/month. Not enough to replace my salary. But enough to prove people would pay for it.

So I took the leap.

The scariest part? Not the money. It was telling my team. I loved those people.

But I realized: I'd rather fail at my own thing than succeed at someone else's.

3 lessons from my first month:
1. The "right time" doesn't exist. You make it right.
2. Your network becomes 10x more important overnight.
3. Freedom is terrifying until it becomes liberating.

If you're thinking about making the jump, my DMs are open.

What's holding you back?

---
#startup #entrepreneurship #careerpivot
```
