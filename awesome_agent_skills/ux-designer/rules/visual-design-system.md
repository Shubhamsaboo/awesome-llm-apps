# Rule: Design System Foundations

**Priority:** MEDIUM
**Category:** Visual Design

## Description

A design system is a collection of reusable components, guidelines, and standards that ensure consistency across a product. It speeds up design and development while maintaining quality.

## Guidelines

### Core Elements
- **Color palette:** Primary, secondary, neutral, and semantic colors with defined usage rules
- **Typography:** Font families, size scale, weight usage, and line heights
- **Spacing:** A base unit (typically 4px or 8px) applied consistently throughout
- **Grid:** Column structure, gutters, and margins for each breakpoint
- **Elevation:** Shadow levels to indicate depth and layering
- **Border radius:** Consistent rounding (e.g., 4px for subtle, 8px for cards, full for pills)

### Component Library
Every component should document:
- **Purpose:** When and why to use it
- **Anatomy:** Labeled parts of the component
- **States:** Default, hover, active, focus, disabled, loading, error
- **Variants:** Size options, style variations, with/without icons
- **Usage guidelines:** Do's and don'ts with visual examples
- **Responsive behavior:** How it adapts across breakpoints
- **Accessibility:** Keyboard behavior, ARIA attributes, screen reader announcements

### Essential Components
- Buttons (primary, secondary, tertiary, destructive)
- Text inputs (single line, textarea, with validation states)
- Select / Dropdown
- Checkbox and Radio
- Toggle / Switch
- Cards
- Modals and Dialogs
- Toast / Snackbar notifications
- Navigation components (tabs, breadcrumbs, sidebar)
- Tables and Lists
- Loading indicators (spinner, skeleton, progress bar)

### Governance
- Assign design system ownership (dedicated team or rotating responsibility)
- Version components and document breaking changes
- Establish a contribution process for new components
- Conduct regular audits to identify inconsistencies
- Measure adoption through component usage analytics

## Common Mistakes
- Building a design system before understanding actual product needs
- Creating components that are too rigid to accommodate real use cases
- Not documenting when to use (and when NOT to use) each component
- Maintaining separate design and code component libraries that drift apart
- Over-engineering components for hypothetical future needs
