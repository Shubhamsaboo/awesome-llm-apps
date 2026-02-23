# UX Designer — Complete Agent Rules

This document compiles all rules, guidelines, and best practices for the UX Designer skill, organized by priority.

---

## Priority 1: User Research (CRITICAL)

> Full details: [rules/research.md](rules/research.md)

### Conducting User Interviews
- Always start with research before opening a design tool
- Use open-ended questions: *"Walk me through the last time you [did the task]"*
- Follow the "5 Whys" technique to uncover root motivations
- Synthesize findings into themes using affinity mapping, not individual anecdotes

### Creating Effective Personas
- Base on real research data, never assumptions
- Limit to 3-5 primary personas per product
- Include goals, pain points, behaviors, and context
- Update as you learn more about users

**Anti-Patterns:** Demographic-only personas · Aspirational personas · Too many personas · Stale personas

---

## Priority 2: Accessibility (CRITICAL)

> Full details: [rules/accessibility.md](rules/accessibility.md)

### WCAG AA Requirements
- **Perceivable:** Color contrast 4.5:1 for text, 3:1 for large text; alt text for images; captions for video
- **Operable:** Full keyboard access; 44×44px touch targets; visible focus states; no seizure triggers
- **Understandable:** Visible form labels; descriptive error messages; consistent navigation
- **Robust:** Semantic HTML; ARIA only when needed; screen reader compatible

### Inclusive Design
- Design for one-handed mobile use
- Support light/dark modes and 200% zoom
- Use plain language (6th-8th grade reading level)
- Never use color as the only indicator of meaning
- Design for RTL languages and text expansion

---

## Priority 3: Information Architecture (HIGH)

> Full details: [rules/information-architecture.md](rules/information-architecture.md)

### Navigation
- Limit primary navigation to 5-7 items
- Group by user mental models, not org charts
- Use breadcrumbs for hierarchies deeper than 2 levels
- Mobile: bottom nav for 3-5 primary actions; hamburger for secondary only

### Content Organization
- **Progressive disclosure:** Show only what's needed; reveal details on demand
- **Scannability:** Clear headings, short paragraphs, visual breaks
- Place the most important content in high-visibility areas
- Validate labels with card sorting and tree testing

---

## Priority 4: Interaction Design (HIGH)

> Full details: [rules/interaction-design.md](rules/interaction-design.md)

### User Flows
- Map the happy path first, then errors and edge cases
- Minimize steps; provide progress indicators for 3+ step flows
- Allow going back without losing data; auto-save when possible
- Confirm destructive actions with specific consequences

### Microcopy
- Use specific verbs for buttons: "Save Draft", "Create Account" (not "Submit", "OK")
- Error messages: explain what happened AND how to fix it
- Confirmation dialogs: asymmetric labels ("Delete Project" / "Keep Project", not "Yes" / "No")
- Empty states: explain why it's empty and what to do

**Common flow problems:** Dead ends · Loops · Forced registration before value · Missing error recovery

---

## Priority 5: Visual Design (MEDIUM)

> Full details: [rules/visual-design.md](rules/visual-design.md)

### Visual Hierarchy
1. **Size** — larger elements attract attention first
2. **Contrast** — high contrast for key actions
3. **Color** — saturated for emphasis, muted for secondary
4. **Position** — top-left scanned first (LTR); F-pattern / Z-pattern
5. **Whitespace** — isolation creates emphasis

### Design System Essentials
- **Color:** Primary, secondary, neutral, semantic (success/error/warning/info)
- **Typography:** 3-4 sizes per screen, consistent scale ratio
- **Spacing:** 8px base grid applied consistently
- **Components:** Document purpose, states, variants, responsive behavior, accessibility

---

## Cross-Functional Collaboration

### Working with Product Managers
- Share research findings early; align on user needs vs. business goals
- Use data to support design decisions in priority discussions

### Working with Developers
- Provide detailed specs with all states and edge cases
- Be available during implementation; review against specs before release

### Working with Stakeholders
- Present design rationale, not just deliverables
- Use prototypes to make abstract ideas concrete

---

## Tools & Workflow

### Recommended Tools (2025-2026)
- **Design:** Figma (primary), Sketch (macOS)
- **Prototyping:** Figma prototyping, ProtoPie
- **Research:** Maze, UserTesting, Lookback
- **Analytics:** Hotjar, FullStory, Google Analytics
