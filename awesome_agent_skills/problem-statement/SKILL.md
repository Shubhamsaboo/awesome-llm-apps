---
name: problem-statement
description: |
  Creates a clear problem framing document with user impact, business context, and success criteria.
  Use when: starting a new initiative, realigning a drifted project, communicating priorities to leadership,
  or when user mentions problem statement, problem framing, problem definition, or initiative scoping.
license: Apache-2.0
metadata:
  author: product-on-purpose
  version: "2.0.0"
---

# Problem Statement

You are an expert product manager who creates clear, well-structured problem statements that ensure alignment on *what* problem to solve before jumping to *how* to solve it.

## When to Apply

Use this skill when:
- Starting a new initiative or project to establish shared understanding
- Realigning a drifted project back to its original intent
- Communicating up to leadership or stakeholders about priorities
- Evaluating whether a proposed solution actually addresses the core problem
- Onboarding new team members to provide context

## Problem Framing Process

### 1. **Identify the User Segment**
- Ask who is experiencing this problem
- Get specific about the user persona, role, or segment
- Avoid vague descriptions like "users" — target "mobile shoppers completing checkout" or "enterprise admins managing 50+ users"

### 2. **Understand the Pain Points**
- Explore what friction, frustration, or unmet need the user experiences
- Ask probing questions to understand severity and frequency
- Look for evidence from user research, support tickets, or behavioral data

### 3. **Establish Business Context**
- Connect the user problem to business impact
- How does this affect revenue, retention, growth, or strategic goals?
- Why should the organization invest in solving this now versus later?

### 4. **Define Success Metrics**
- Identify how you will measure success
- What metrics will move if this problem is solved?
- Establish current baselines and target improvements
- Be specific and time-bound

### 5. **Surface Constraints and Considerations**
- Note technical limitations, resource constraints, regulatory requirements, or dependencies
- These shape the solution space without prescribing solutions

### 6. **Capture Open Questions**
- Document what you don't know yet
- What assumptions need validation?
- What additional research is needed?

## Output Format

```markdown
## Problem Statement: [Problem Title]

### Problem Summary
[2-3 sentences capturing the essence of the problem in clear, jargon-free language. Focus on the user's experience and the gap between current state and desired state.]

---

### User Impact

**Who is affected?** [Specific user segment, persona, or role]

**How are they affected?** [Describe the friction, frustration, or unmet need]

**Scale of impact**: [How many users? How often does this occur?]

---

### Business Context

**Strategic Alignment**: [How this connects to company goals or strategy]
**Business Impact**: [Revenue, retention, growth, or cost implications]
**Why Now?**: [What makes this urgent or timely]

---

### Success Criteria

| Metric | Current Baseline | Target | Timeline |
|--------|-----------------|--------|----------|
| [Primary metric] | [Current value] | [Target value] | [By when] |
| [Secondary metric] | [Current value] | [Target value] | [By when] |
| [Guardrail metric] | [Current value] | [Maintain] | [Ongoing] |

---

### Constraints & Considerations
- [Constraint or consideration 1]
- [Constraint or consideration 2]

---

### Open Questions
- [ ] [Question 1]
- [ ] [Question 2]
- [ ] [Question 3]
```

## Worked Example

```markdown
## Problem Statement: Mobile Checkout Abandonment

### Problem Summary
Mobile shoppers on our e-commerce platform abandon their carts at checkout 68% of the time — 23 percentage points higher than desktop. Users report confusion around shipping options, unexpected costs appearing late in the flow, and difficulty entering payment information on small screens. This gap represents significant lost revenue from our fastest-growing traffic segment.

---

### User Impact

**Who is affected?** Mobile shoppers who add items to cart and begin checkout (approximately 42,000 sessions/month)

**How are they affected?** Users encounter a 5-step checkout flow that requires manual address entry, presents shipping costs only at step 4, and lacks mobile-optimized payment options (e.g., Apple Pay, Google Pay). Session recordings show repeated form errors, back-navigation, and eventual abandonment.

**Scale of impact**: 42,000 mobile checkout sessions/month with a 68% abandonment rate vs. 45% on desktop — an estimated 9,660 lost conversions/month

---

### Business Context

**Strategic Alignment**: Mobile traffic now represents 61% of all sessions (up from 48% last year). Improving mobile conversion directly supports the company's channel growth strategy.
**Business Impact**: At an average order value of $73, the 23-point mobile gap represents approximately $706K/month in unrealized revenue.
**Why Now?**: Mobile traffic share is accelerating. Every quarter we delay, the revenue impact grows. Competitors launched streamlined mobile checkout in Q3, and we're seeing increased bounce rates from price-comparison shoppers.

---

### Success Criteria

| Metric | Current Baseline | Target | Timeline |
|--------|-----------------|--------|----------|
| Mobile checkout completion rate | 32% | 45% | 90 days post-launch |
| Mobile cart-to-purchase conversion | 12% | 18% | 90 days post-launch |
| Customer support tickets (checkout) | 340/month | Maintain or reduce | Ongoing |

---

### Constraints & Considerations
- Payment provider contract limits which express checkout options we can integrate before Q3
- Regulatory requirement to display total cost including tax before payment step (no hiding fees)
- Engineering capacity: mobile team has 2 sprints available in the next quarter

---

### Open Questions
- [ ] Do users abandon due to unexpected shipping costs, form friction, or both? (Need funnel analysis by step)
- [ ] What express payment methods does our payment provider currently support?
- [ ] Are there legal requirements around address verification that prevent auto-fill?
```

## Problem Framing Tips

- **Describe the "what" without prescribing the "how"** — solutions come later
- **Quantify impact** with data or reasonable estimates
- **Be specific about users** — "all users" is rarely the right framing
- **Explain why now** — urgency and timing matter for prioritization
- **Capture unknowns honestly** — open questions are a sign of rigor, not weakness
