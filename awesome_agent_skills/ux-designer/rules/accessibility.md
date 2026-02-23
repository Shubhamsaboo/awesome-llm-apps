# Rule: Accessibility & Inclusive Design

**Priority:** CRITICAL
**Category:** Accessibility

## Description

Accessible design is a legal requirement in many jurisdictions and a moral imperative. Inclusive design goes further — proactively considering the full range of human diversity (ability, language, culture, context) so that experiences work for everyone.

## WCAG AA Requirements (Minimum Standard)

### Perceivable
- **Color contrast:** 4.5:1 for normal text, 3:1 for large text (18px bold or 24px+)
- **Text alternatives:** All images have descriptive alt text; decorative images use `alt=""`
- **Captions:** Video content includes synchronized captions
- **Adaptable:** Content meaning preserved when CSS is disabled or layout changes

### Operable
- **Keyboard accessible:** Every interactive element reachable and usable via keyboard
- **Focus visible:** Focus indicators clearly visible (minimum 2px, high contrast)
- **Skip links:** Provide "Skip to main content" for keyboard users
- **Touch targets:** Minimum 44×44 CSS pixels for touch interfaces
- **No time traps:** Users can extend or disable time limits
- **No seizure triggers:** No content flashes more than 3 times/second

### Understandable
- **Labels:** All form inputs have visible, associated labels
- **Error identification:** Errors described in text, not just color
- **Error prevention:** Confirm destructive actions; allow undo
- **Consistent navigation:** Same navigation order across pages
- **Language:** Page language declared in HTML (`lang` attribute)

### Robust
- **Semantic HTML:** Use proper elements (`<button>`, `<nav>`, `<main>`, `<header>`)
- **ARIA:** Use ARIA roles only when semantic HTML is insufficient
- **Compatibility:** Test with at least 2 screen readers (VoiceOver, NVDA)

## Inclusive Design Patterns

### Motor & Physical
- Design for one-handed mobile use (key actions within thumb reach)
- Provide generous tap targets (minimum 44×44px, ideally 48×48px)
- Avoid hover-only interactions (no hover on touch devices)

### Visual
- Never use color as the only means of conveying information
- Support both light and dark modes
- Allow text resizing up to 200% without layout breakage

### Cognitive
- Use plain language (6th-8th grade reading level for general audiences)
- Break complex tasks into smaller, clearly labeled steps
- Minimize choices per screen to reduce cognitive load

### Situational & Cultural
- Design for poor network conditions (offline states, loading indicators)
- Design layouts supporting RTL languages and text expansion (30-40% more space)
- Avoid culturally specific metaphors or color meanings

## Testing Checklist

- [ ] Automated audit (Axe, Lighthouse)
- [ ] Keyboard-only navigation (Tab, Enter, Escape, Arrow keys)
- [ ] Screen reader walkthrough (VoiceOver or NVDA)
- [ ] Zoom to 200% — no content loss or overlap
- [ ] High contrast mode — all content remains visible
- [ ] Reduced motion preference — animations disabled or reduced

## Common Mistakes
- Using `<div>` and `<span>` for interactive elements instead of `<button>` and `<a>`
- Hiding focus outlines with `outline: none` without providing an alternative
- Relying on placeholder text as the only label for form fields
- Using color alone to indicate errors, status, or required fields
- Assuming all users have a mouse and precise cursor control
- Testing only with the latest devices and fast internet
