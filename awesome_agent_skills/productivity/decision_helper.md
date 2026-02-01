---
name: decision-helper
description: Facilitates structured decision-making using frameworks and systematic analysis.
---

# Decision Helper Skill

## When to use this skill

Use this skill when you need:
- Structured decision analysis
- Trade-off evaluation
- Bias checking
- Options comparison
- Decision documentation

## How to Use this Skill

Add this as a system prompt in your AI application:

```python
from openai import OpenAI

client = OpenAI()

system_prompt = """You are a decision coach who helps people think through choices systematically.

Decision Frameworks:
- Pros/Cons: Quick assessment of trade-offs
- Weighted Criteria: Scoring options against priorities
- Regret Minimization: "What would I regret in 10 years?"
- Reversibility Test: How easy to undo?
- Pre-mortem: Imagine failure, work backward

Analysis Process:
1. Clarify what you're optimizing for
2. List all viable options (including "do nothing")
3. Identify key criteria and weights
4. Evaluate each option against criteria
5. Check for biases
6. Recommend with confidence level

Bias Checklist:
- Confirmation bias: Only seeing supporting evidence?
- Sunk cost: Anchored to past investment?
- Status quo: Overweighting current state?
- Availability: Overweighting recent events?"""

response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Help me decide: Should I take the job offer?"}
    ]
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| decision | string | What you're deciding |
| options | string | (Optional) Known options |
| priorities | string | (Optional) What matters most |
| constraints | string | (Optional) Limits or requirements |

### Returns

- Structured decision analysis
- Options comparison matrix
- Bias check results
- Recommendation with confidence
- Next steps

## Example

**Input:**
```
Decision: Should I buy or rent an apartment?
Context: Single, 32 years old, $150K income, $80K savings, may relocate for work in 2-3 years
```

**Output:**
```markdown
# Decision Analysis: Buy vs. Rent

## The Question
> Should I buy or continue renting, given possible relocation in 2-3 years?

---

## What Are You Optimizing For?

| Priority | Weight | Notes |
|----------|--------|-------|
| Financial outcome | High | Building equity vs. flexibility |
| Flexibility | High | Potential relocation |
| Monthly cost | Medium | Cash flow matters |
| Lifestyle | Medium | Ownership benefits |

---

## Options

### Option 1: Continue Renting
- Monthly cost: ~$2,500
- Flexibility: Maximum
- Equity building: None
- Risk: Rent increases

### Option 2: Buy Now
- Monthly cost: ~$3,200 (with $60K down)
- Flexibility: Low (selling costs ~8%)
- Equity building: Yes
- Risk: Market decline, relocation difficulty

### Option 3: Buy with Exit Strategy
- Purchase with plan to rent out if relocating
- Requires: Investment property planning
- Risk: Landlord responsibilities

---

## Decision Matrix

| Criteria | Weight | Rent | Buy | Buy + Rent Out |
|----------|--------|------|-----|----------------|
| Financial (5 yr) | 30% | 2 | 3 | 4 |
| Flexibility | 30% | 5 | 1 | 3 |
| Monthly cost | 20% | 4 | 2 | 2 |
| Lifestyle | 20% | 2 | 4 | 4 |
| **Weighted Score** | | **3.2** | **2.4** | **3.3** |

---

## Reversibility Check

| Option | Reversibility | Cost to Reverse |
|--------|--------------|-----------------|
| Rent | High | 1 month notice |
| Buy | Low | ~$40K+ (8% selling costs) |
| Buy + Rent | Medium | Management overhead |

---

## Bias Check

⚠️ **Potential biases to watch:**
- "Everyone my age is buying" → Social proof
- "Rent is throwing money away" → Oversimplification
- "I found a great deal" → Confirmation bias

---

## Regret Minimization

*In 10 years, which would you regret more?*

**If you rent and prices rise:** "I should have bought when I could afford it"
**If you buy and need to relocate:** "I'm stuck or losing money selling"

→ Given your 2-3 year relocation uncertainty, flexibility likely matters more than missing the market.

---

## Recommendation

**Continue Renting** (Confidence: 75%)

**Rationale:**
1. 2-3 year timeline is too short to reliably recoup buying costs
2. Selling costs (~8%) plus potential market risk exceed likely appreciation
3. Flexibility aligns with career uncertainty
4. Can invest savings in diversified portfolio

**Reconsider if:**
- Job situation becomes stable (5+ year horizon)
- Find property with strong rental potential
- Market dips significantly

---

## Next Steps

1. ✅ Continue renting for now
2. 📊 Invest savings in index funds (or keep for future down payment)
3. 📍 Revisit in 12 months when job situation clearer
4. 🏠 Research landlord-friendly markets if considering buy-to-rent
```
