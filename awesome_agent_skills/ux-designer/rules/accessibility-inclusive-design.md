# Rule: Inclusive Design Patterns

**Priority:** CRITICAL
**Category:** Accessibility

## Description

Inclusive design goes beyond compliance. It proactively considers the full range of human diversity — ability, language, culture, age, and context — to create experiences that work for everyone.

## Guidelines

### Motor & Physical
- Design for one-handed mobile use (place key actions within thumb reach)
- Provide generous tap targets (minimum 44×44px, ideally 48×48px)
- Avoid hover-only interactions (no hover on touch devices)
- Support both tap and swipe gestures with alternatives
- Allow form completion without precise clicking (large inputs, generous spacing)

### Visual
- Never use color as the only means of conveying information
- Support both light and dark modes
- Allow text resizing up to 200% without layout breakage
- Use sufficient contrast for all text and interactive elements
- Provide text labels alongside icons

### Cognitive
- Use plain language (aim for a 6th-8th grade reading level for general audiences)
- Break complex tasks into smaller, clearly labeled steps
- Provide clear progress indicators for multi-step processes
- Minimize cognitive load by reducing the number of choices per screen
- Use familiar patterns and conventions over novel interactions

### Situational
- Design for poor network conditions (offline states, loading indicators)
- Support use in bright sunlight (sufficient contrast)
- Account for one-handed use while holding something
- Consider noisy environments (don't rely solely on audio feedback)

### Cultural & Linguistic
- Design layouts that support RTL (right-to-left) languages
- Allow for text expansion (some languages need 30-40% more space)
- Avoid culturally specific metaphors, icons, or color meanings
- Use internationally recognized date, time, and number formats

## Examples

### Good
```
A toggle switch that uses both color AND a label to indicate state:
[●  ON  ] — green with "ON" text
[  OFF ○] — gray with "OFF" text
```

### Bad
```
A toggle that only uses color:
[●      ] — green (on? selected? active?)
[      ○] — red (off? error? disabled?)
```

## Common Mistakes
- Assuming all users have a mouse and precise cursor control
- Testing only with the latest devices and fast internet
- Using idioms or humor that don't translate across cultures
- Designing empty states that blame the user ("You haven't done anything yet!")
- Ignoring right-to-left language support until it's too late to fix
