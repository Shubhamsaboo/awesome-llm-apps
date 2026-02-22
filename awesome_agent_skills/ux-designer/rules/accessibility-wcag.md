# Rule: WCAG Compliance Checklist

**Priority:** CRITICAL
**Category:** Accessibility

## Description

Web Content Accessibility Guidelines (WCAG) provide the standard for accessible digital experiences. Meeting WCAG AA is the minimum bar for professional UX work.

## Guidelines

### Perceivable
- **Color contrast:** 4.5:1 for normal text, 3:1 for large text (18px bold or 24px regular)
- **Text alternatives:** All images have descriptive alt text; decorative images use `alt=""`
- **Captions:** Video content includes synchronized captions
- **Adaptable:** Content meaning is preserved when CSS is disabled or layout changes

### Operable
- **Keyboard accessible:** Every interactive element is reachable and usable via keyboard
- **Focus visible:** Focus indicators are clearly visible (minimum 2px, high contrast)
- **Skip links:** Provide "Skip to main content" for keyboard users
- **Touch targets:** Minimum 44×44 CSS pixels for touch interfaces
- **No time traps:** Users can extend or disable time limits
- **No seizure triggers:** No content flashes more than 3 times per second

### Understandable
- **Labels:** All form inputs have visible, associated labels
- **Error identification:** Errors are clearly described in text (not just color)
- **Error prevention:** Confirm destructive actions; allow undo
- **Consistent navigation:** Navigation order is the same across pages
- **Language:** Page language is declared in HTML (`lang` attribute)

### Robust
- **Semantic HTML:** Use proper elements (`<button>`, `<nav>`, `<main>`, `<header>`)
- **ARIA:** Use ARIA roles only when semantic HTML is insufficient
- **Valid markup:** HTML validates without critical errors
- **Compatibility:** Test with at least 2 screen readers (VoiceOver, NVDA)

## Testing Checklist

- [ ] Run automated audit (Axe, Lighthouse)
- [ ] Keyboard-only navigation test (Tab, Enter, Escape, Arrow keys)
- [ ] Screen reader walkthrough (VoiceOver or NVDA)
- [ ] Zoom to 200% — no content loss or overlap
- [ ] High contrast mode — all content remains visible
- [ ] Reduced motion preference — animations disabled or reduced

## Common Mistakes
- Adding `aria-label` to elements that already have visible text labels
- Using `<div>` and `<span>` for interactive elements instead of `<button>` and `<a>`
- Hiding focus outlines with `outline: none` without providing an alternative
- Relying on placeholder text as the only label for form fields
- Using color alone to indicate errors, status, or required fields
