# UX Designer — Complete Agent Rules

This document compiles all rules, guidelines, and best practices for the UX Designer skill, organized by priority.

---

## Priority 1: User Research (CRITICAL)

### Rule: Conducting User Interviews

**Why:** Design decisions grounded in real user data lead to products that people actually want to use. Assumptions lead to costly redesigns.

**Guidelines:**
- Always start with research before opening a design tool
- Use open-ended questions that don't lead the participant
- Follow the "5 Whys" technique to uncover root motivations
- Record sessions (with consent) for team review
- Synthesize findings into themes, not individual anecdotes

**Good Interview Questions:**
- "Walk me through the last time you [did the task]."
- "What was the hardest part of that experience?"
- "What did you try before finding this solution?"

**Bad Interview Questions:**
- "Don't you think this feature would be useful?" (leading)
- "Would you use a product that does X?" (hypothetical, unreliable)
- "Do you like this design?" (opinion, not behavior-based)

**Synthesis Process:**
1. Review all session notes and recordings
2. Extract key observations as individual data points
3. Cluster observations into themes using affinity mapping
4. Identify patterns that appear across multiple participants
5. Prioritize insights by frequency and impact
6. Create actionable recommendations tied to specific findings

### Rule: Creating Effective Personas

**Why:** Personas keep the team aligned on who they're designing for and prevent "designing for everyone" (which means designing for no one).

**Guidelines:**
- Base personas on real research data, never assumptions
- Limit to 3-5 primary personas per product
- Include goals, pain points, behaviors, and context
- Make personas specific enough to guide decisions
- Update personas as you learn more about users

**Anti-Patterns:**
- Demographic-only personas (age, gender, income without behavioral data)
- Aspirational personas (who you wish your users were)
- Too many personas (dilutes focus)
- Stale personas (never updated after initial creation)

---

## Priority 2: Accessibility (CRITICAL)

### Rule: WCAG Compliance

**Why:** Accessible design isn't optional — it's a legal requirement in many jurisdictions and a moral imperative. It also improves usability for everyone.

**WCAG AA Requirements (Minimum Standard):**
- **Perceivable:** Content must be presentable in ways all users can perceive
  - Color contrast: 4.5:1 for normal text, 3:1 for large text (18px+ bold or 24px+)
  - Text alternatives for non-text content
  - Captions for audio/video content
  - Content adaptable to different presentations without losing meaning

- **Operable:** Interface must be navigable by all users
  - All functionality available via keyboard
  - Sufficient time to read and interact with content
  - No content that causes seizures (no flashing more than 3 times per second)
  - Clear navigation and wayfinding
  - Minimum touch target size of 44×44 CSS pixels

- **Understandable:** Content and interface must be comprehensible
  - Readable text at appropriate levels
  - Predictable page behavior and navigation
  - Input assistance with clear labels and error prevention

- **Robust:** Content must work with current and future technologies
  - Valid, semantic HTML
  - Compatible with assistive technologies
  - Proper ARIA roles and attributes when semantic HTML is insufficient

### Rule: Inclusive Design Patterns

**Why:** Designing for edge cases often improves the experience for all users.

**Guidelines:**
- Design for one-handed use on mobile
- Support both light and dark color modes
- Provide text alternatives for every visual-only communication
- Ensure forms work with autofill and password managers
- Support zoom up to 200% without content loss
- Never rely solely on color to convey meaning (use icons, text, or patterns as well)
- Respect user preferences for reduced motion
- Design for variable content lengths (internationalization)

---

## Priority 3: Usability & Information Architecture (HIGH)

### Rule: Navigation Structure Design

**Why:** If users can't find it, it doesn't exist. Navigation is the backbone of usability.

**Guidelines:**
- Limit primary navigation to 5-7 items maximum
- Use card sorting to validate category names with real users
- Follow the "three-click rule" as a heuristic (most tasks achievable in 3 actions)
- Provide breadcrumbs for deep hierarchies
- Include a search function for content-heavy products
- Make the current location always clear

**Navigation Patterns:**
- **Top bar:** Best for 3-7 primary sections on desktop
- **Side nav:** Best for deep hierarchies or tools with many sections
- **Bottom bar:** Best for mobile apps with 3-5 primary actions
- **Hamburger menu:** Use sparingly; hides navigation and reduces discoverability
- **Tabs:** Best for switching between related views at the same level

### Rule: Content Organization

**Why:** Well-organized information reduces cognitive load and helps users accomplish their goals faster.

**Guidelines:**
- Group related items together (Gestalt principle of proximity)
- Use progressive disclosure — show only what's needed at each step
- Place the most important content and actions in high-visibility areas
- Follow established conventions (logo top-left, search top-right, etc.)
- Use consistent labeling and terminology throughout

---

## Priority 4: Interaction Design (HIGH)

### Rule: User Flow Best Practices

**Why:** A well-designed flow minimizes friction and guides users to successful task completion.

**Guidelines:**
- Map the happy path first, then design for errors and edge cases
- Minimize the number of steps to complete a task
- Provide clear progress indicators for multi-step flows
- Allow users to go back without losing data
- Auto-save form data when possible
- Confirm destructive actions with clear consequences
- Provide meaningful feedback for every user action

**Common Flow Problems:**
- Dead ends (no next action available)
- Loops (user returns to the same screen without progress)
- Forced registration before value is demonstrated
- Unclear calls to action (what should I do next?)
- Missing error recovery paths

### Rule: Microcopy Guidelines

**Why:** Interface text is often the difference between a user completing a task and abandoning it.

**Guidelines:**
- Use verbs for buttons ("Create Account" not "Submit")
- Keep labels short but descriptive
- Write error messages that explain the problem AND the solution
- Use the user's language, not internal jargon
- Be consistent — one term for one concept everywhere
- Front-load important information in sentences
- Write for scanning, not reading

---

## Priority 5: Visual Design (MEDIUM)

### Rule: Visual Hierarchy Principles

**Why:** Visual hierarchy directs attention and communicates importance without requiring the user to think about it.

**Guidelines:**
- Use size, color, contrast, and spacing to establish hierarchy
- Limit to 2-3 font sizes per screen for clarity
- Use whitespace generously to reduce visual clutter
- Align elements to a consistent grid
- Make primary actions visually dominant (larger, higher contrast)
- De-emphasize secondary actions to reduce decision fatigue

**Hierarchy Techniques:**
1. **Size:** Larger elements attract attention first
2. **Color/Contrast:** High contrast draws the eye
3. **Position:** Top-left (in LTR languages) gets scanned first
4. **Whitespace:** Isolation creates emphasis
5. **Typography:** Weight and style differentiate content levels

### Rule: Design System Foundations

**Why:** A design system ensures consistency, speeds up design work, and reduces developer ambiguity.

**Core Components:**
- **Color palette:** Primary, secondary, neutral, semantic (success, error, warning, info)
- **Typography scale:** A modular scale with defined sizes, weights, and line heights
- **Spacing system:** Consistent spacing units (4px or 8px base grid)
- **Component library:** Buttons, inputs, cards, modals, navigation, and other reusable patterns
- **Iconography:** Consistent style, size, and stroke weight
- **Motion guidelines:** Easing curves, durations, and when to animate

**Guidelines:**
- Document every component with usage guidelines and examples
- Include do/don't examples for each component
- Specify states for all interactive components (default, hover, active, focus, disabled, error)
- Define responsive behavior for each component
- Version the design system and communicate changes

---

## Cross-Functional Collaboration

### Working with Product Managers
- Share research findings early and often
- Align on user needs vs. business goals
- Co-create prioritization frameworks
- Use data to support design decisions in priority discussions

### Working with Developers
- Provide detailed specs with all states and edge cases documented
- Use developer-friendly tools and naming conventions
- Be available during implementation for questions
- Review implemented designs against specs before release
- Discuss technical constraints early in the design process

### Working with UX Researchers
- Collaborate on research plans and interview scripts
- Attend research sessions to build empathy
- Co-analyze findings and identify patterns together
- Use research findings to validate or invalidate design hypotheses

### Working with Stakeholders
- Present design rationale, not just deliverables
- Frame feedback requests around specific questions
- Use prototypes to make abstract ideas concrete
- Connect design decisions to business metrics

---

## Tools & Workflow

### Recommended Tools (2025-2026)
- **Design:** Figma (primary), Sketch (macOS alternative)
- **Prototyping:** Figma prototyping, ProtoPie (advanced interactions)
- **Research:** Maze, UserTesting, Lookback
- **Handoff:** Figma Dev Mode, Zeplin
- **Documentation:** Notion, Confluence
- **Analytics:** Hotjar, FullStory, Google Analytics

### Design File Organization
- Use consistent naming conventions for pages and frames
- Organize by flow or feature, not by fidelity level
- Maintain a "Components" page as the source of truth
- Archive old explorations instead of deleting
- Include version notes on major iterations
