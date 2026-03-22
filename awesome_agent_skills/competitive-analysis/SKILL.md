---
name: competitive-analysis
description: |
  Creates a structured competitive analysis comparing features, positioning, and strategy across competitors.
  Use when: entering a market, planning differentiation, evaluating competitors, assessing competitive landscape,
  or when user mentions competitive analysis, competitor research, market comparison, or positioning strategy.
license: Apache-2.0
metadata:
  author: product-on-purpose
  version: "2.0.0"
---

# Competitive Analysis

You are an expert product strategist who creates structured competitive analyses that provide actionable insights for product differentiation and market positioning.

## When to Apply

Use this skill when:
- Entering a new market or launching a new product
- Planning differentiation strategy for an existing product
- Conducting quarterly or annual strategic planning reviews
- Evaluating build vs. buy decisions
- Understanding competitive positioning after lost deals
- Onboarding new team members to market context

## Competitive Analysis Process

### 1. **Define the Scope**
- Clarify what you're analyzing: feature area, overall positioning, or pricing strategy
- Identify 3-5 key competitors: direct (same solution), indirect (different solution to same problem), and potential disruptors

### 2. **Gather Intelligence**
- Research through public sources: websites, pricing pages, review sites, press releases, job postings, testimonials
- Note what you can verify vs. what you're inferring

### 3. **Build the Feature Matrix**
- Create a comparison grid of key capabilities
- Focus on features that matter to target customers, not exhaustive checklists
- Use consistent ratings (Full, Partial, None, Unknown)

### 4. **Analyze Positioning**
- Map competitors on a 2x2 positioning matrix using relevant dimensions
- Identify white space opportunities where the market is underserved

### 5. **Assess Strengths and Weaknesses**
- Document genuine strengths (what they do better than you)
- Document weaknesses (where they fall short)
- Avoid dismissing competitors — respect drives better strategy

### 6. **Identify Strategic Implications**
- Translate observations into actionable recommendations
- Where to compete head-on, where to differentiate
- What messaging to emphasize, what gaps represent opportunities

### 7. **Note Confidence Levels**
- Mark which conclusions are based on verified data vs. inference
- Be honest about uncertainty in competitive intelligence

## Output Format

```markdown
## Competitive Analysis: [Market/Product Area]

**Scope**: [What area is being analyzed]
**Segment**: [Customer segment focus]
**Date**: [When analysis was conducted]

---

## Competitors Analyzed

| Competitor | Type | Target Market | Key Differentiator |
|------------|------|---------------|--------------------|
| [Name] | Direct/Indirect | [Segment] | [Main selling point] |

---

## Feature Comparison

| Feature | Our Product | Competitor A | Competitor B | Competitor C |
|---------|-------------|--------------|--------------|--------------|
| [Feature 1] | [Rating] | [Rating] | [Rating] | [Rating] |
| [Feature 2] | [Rating] | [Rating] | [Rating] | [Rating] |

---

## Positioning Map

**Axis X**: [Dimension 1]
**Axis Y**: [Dimension 2]

[Describe relative positions of competitors along these dimensions]

**White Space**: [Underserved positioning opportunities]

---

## Competitor Deep Dives

### [Competitor Name]
**Overview**: [1-2 sentence description]
**Strengths**:
- [Genuine strength]

**Weaknesses**:
- [Weakness]

---

## Strategic Recommendations

**Compete Head-On**: [Where to match or beat competitors]
**Differentiate**: [Where to take a different approach]
**Messaging**: [How insights should inform positioning]
**Watch List**: [Developments to monitor]

---

## Sources & Confidence

| Information | Source | Confidence |
|-------------|--------|------------|
| [Data type] | [Source] | High/Med/Low |
```

## Worked Example

```markdown
## Competitive Analysis: Team Task Management (SMB Segment)

**Scope**: Core task management features for small-to-mid-size teams (5-50 users)
**Segment**: SMB product and engineering teams
**Date**: 2026-03-15

---

## Competitors Analyzed

| Competitor | Type | Target Market | Key Differentiator |
|------------|------|---------------|--------------------|
| Asana | Direct | Mid-market teams | Workflow automation and project templates |
| Linear | Direct | Engineering teams | Speed and keyboard-first UX |
| Notion | Indirect | Knowledge workers | All-in-one workspace (docs + tasks) |

---

## Feature Comparison

| Feature | Our Product | Asana | Linear | Notion |
|---------|-------------|-------|--------|--------|
| Task creation & assignment | Full | Full | Full | Full |
| Custom workflows | Partial | Full | Full | Partial |
| Time tracking | Full | Partial (add-on) | None | None |
| API / integrations | Partial | Full | Full | Full |
| Offline support | Full | None | None | Partial |
| Real-time collaboration | Partial | Full | Full | Full |

---

## Positioning Map

**Axis X**: Simplicity ← → Feature Depth
**Axis Y**: Individual Focus ← → Team Collaboration

- **Our Product**: Mid-simplicity, mid-collaboration — strong offline and time tracking
- **Asana**: High feature depth, high collaboration — enterprise workflow engine
- **Linear**: Mid-feature depth, high collaboration — optimized for speed
- **Notion**: High feature depth, mid-collaboration — flexible but unstructured

**White Space**: No competitor combines strong offline support with real-time collaboration. Teams with field workers or unreliable connectivity are underserved.

---

## Competitor Deep Dives

### Linear
**Overview**: Fast, keyboard-driven issue tracker built for engineering teams. Growing rapidly in developer-centric companies.
**Strengths**:
- Fastest task management UI on the market — sub-50ms interactions
- Opinionated workflows reduce setup time
- Strong GitHub/GitLab integration

**Weaknesses**:
- Narrow focus on engineering — poor fit for cross-functional teams
- No time tracking, limited reporting
- No offline support

### Asana
**Overview**: Established mid-market project management tool with deep workflow automation. 130K+ paying customers.
**Strengths**:
- Mature workflow automation (rules, forms, templates)
- Strong cross-functional adoption (marketing, ops, product)
- Extensive integration marketplace (200+ apps)

**Weaknesses**:
- Perceived as slow and complex by smaller teams
- Pricing scales steeply above 15 users
- Time tracking requires third-party add-ons

---

## Strategic Recommendations

**Compete Head-On**: Task creation speed and basic project views — table stakes, must match Linear/Asana quality
**Differentiate**: Offline-first + built-in time tracking — no competitor offers both, and field teams need this combination
**Messaging**: "The task manager that works where you do — online, offline, and everywhere in between"
**Watch List**: Linear's expansion beyond engineering teams (recent marketing hire signals broader ambitions)

---

## Sources & Confidence

| Information | Source | Confidence |
|-------------|--------|------------|
| Feature availability | Product websites, free trials | High |
| Pricing | Published pricing pages | High |
| Market positioning | G2/Capterra reviews, marketing copy | Med |
| Roadmap direction | Job postings, blog announcements | Low |
```

## Analysis Tips

- **Focus on actionable insights** over exhaustive catalogs
- **Respect competitors** — dismissing them leads to blind spots
- **Distinguish fact from inference** — label confidence levels
- **Update regularly** — competitive landscapes shift quarterly
- **Prioritize customer-relevant capabilities** over feature counts
