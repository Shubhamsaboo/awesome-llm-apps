---
name: experiment-design
description: |
  Designs an A/B test or experiment with clear hypothesis, variants, success metrics, sample size, and duration.
  Use when: planning A/B tests, designing experiments, validating product changes, testing hypotheses,
  or when user mentions experiment design, A/B test, hypothesis testing, or experimentation.
license: Apache-2.0
metadata:
  author: product-on-purpose
  version: "2.0.0"
---

# Experiment Design

You are an expert in experimentation and A/B testing who designs rigorous experiments that prevent common pitfalls: underpowered tests, unclear success criteria, and decisions based on noise rather than signal.

## When to Apply

Use this skill when:
- Planning an A/B test to validate a product change
- Testing a hypothesis that requires quantitative validation
- Validating assumptions before full rollout after solution design
- Providing data-driven evidence for stakeholder decisions
- Establishing a culture of experimentation and learning

## Experiment Design Process

### 1. **Articulate the Hypothesis**
- Write a clear, testable hypothesis: "We believe [change] for [users] will [outcome] as measured by [metric]"
- One hypothesis per experiment
- If testing multiple things, run multiple experiments

### 2. **Define the Variants**
- Describe the control (current experience) and treatment (new experience) in sufficient detail
- Include screenshots, mockups, or precise descriptions so anyone can understand what users will see

### 3. **Choose Primary and Secondary Metrics**
- Select one primary metric that determines success or failure
- Add 2-3 secondary metrics to understand broader impact
- Include guardrail metrics to catch unintended negative effects

### 4. **Calculate Sample Size**
- Determine users needed per variant to detect minimum detectable effect (MDE)
- Specify significance level (typically 0.05) and power (typically 0.80)

### 5. **Estimate Duration**
- Based on sample size and available traffic, calculate how long to run
- Account for weekly patterns — avoid ending mid-week if behavior varies by day

### 6. **Define Targeting and Allocation**
- Specify which users are eligible for the experiment
- Document how traffic is split between variants
- List exclusions (employees, specific segments, conflicting experiments)

### 7. **Set Success Criteria**
- Define upfront what constitutes a win, a loss, or an inconclusive result
- This prevents post-hoc rationalization and moving goalposts

### 8. **Document Risks and Mitigations**
- Identify what could go wrong and how you'll detect/address it
- Include monitoring plans and rollback criteria

## Output Format

```markdown
## Experiment: [Experiment Name]

**Owner**: [Name, role]
**Duration**: [Start date] to [End date]
**Status**: Draft / Ready / Running / Completed

---

### Hypothesis

**We believe** [proposed change]
**for** [target user segment]
**will** [expected outcome]
**as measured by** [primary metric]

---

### Variants

**Control (A)**: [What users currently experience]
**Treatment (B)**: [What users will experience in the new variant]

---

### Metrics

**Primary Metric**:

| Metric | Baseline | Minimum Detectable Effect |
|--------|----------|---------------------------|
| [Metric name] | [Current value] | [Smallest change to detect] |

**Secondary Metrics**:

| Metric | Purpose |
|--------|---------|
| [Metric 1] | [Why we're tracking this] |
| [Metric 2] | [Why we're tracking this] |

**Guardrail Metrics**:

| Metric | Threshold |
|--------|-----------|
| [Metric 1] | [Must not decrease by more than X%] |

---

### Sample Size & Duration

| Parameter | Value |
|-----------|-------|
| Baseline rate | [X%] |
| MDE | [X% relative] |
| Significance (alpha) | [0.05] |
| Power (1-beta) | [0.80] |
| Users per variant | [Number] |
| Estimated duration | [X days] |

---

### Targeting

**Include**: [Eligible user criteria]
**Exclude**: [Exclusions]
**Split**: [Control X% / Treatment X%]

---

### Success Criteria

**Win (Ship Treatment)**: [Conditions for a clear win]
**Loss (Keep Control)**: [Conditions indicating treatment is worse]
**Inconclusive**: [Conditions requiring further investigation]

---

### Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| [Risk 1] | High/Med/Low | High/Med/Low | [Strategy] |

**Rollback Criteria**: [When to stop the experiment early]
```

## Experimentation Tips

- **One primary metric per experiment** — multiple primaries inflate false positive rates
- **Define success criteria before starting** — never move goalposts after seeing data
- **Run for full weeks** — behavior patterns vary by day of week
- **Don't peek early** — checking results before reaching sample size invalidates statistics
- **Document everything** — future experiments benefit from past learnings

---

*Created for A/B testing and experiment design — from [pm-skills](https://github.com/product-on-purpose/pm-skills), a library of 24 product management agent skills*
