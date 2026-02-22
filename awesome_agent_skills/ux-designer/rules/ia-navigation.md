# Rule: Navigation Structure Design

**Priority:** HIGH
**Category:** Information Architecture

## Description

Navigation is the primary wayfinding mechanism in any digital product. Well-designed navigation reduces time-to-task and prevents users from feeling lost.

## Guidelines

### Structure
- Limit primary navigation to 5-7 items
- Use clear, descriptive labels (nouns for sections, verbs for actions)
- Group related items logically based on user mental models, not org charts
- Validate navigation labels with card sorting and tree testing
- Provide breadcrumbs for hierarchies deeper than 2 levels

### Patterns
- **Global navigation:** Persistent across all pages; contains top-level sections
- **Local navigation:** Context-specific; shows sub-sections within the current area
- **Utility navigation:** Account, settings, help — secondary but always accessible
- **Contextual navigation:** Related content links within the page body

### Mobile Considerations
- Use bottom navigation for 3-5 primary actions (most reachable on mobile)
- Reserve hamburger menus for secondary navigation only
- Highlight the current section in the navigation bar
- Ensure navigation doesn't consume more than 20% of the viewport

### Search as Navigation
- Include search for products with more than 50 content items
- Provide autocomplete suggestions based on popular queries
- Show recent searches for returning users
- Display helpful empty states when search returns no results

## Common Mistakes
- Organizing navigation by internal team structure instead of user needs
- Using jargon or branded terminology that users don't understand
- Hiding essential navigation behind a hamburger menu on desktop
- Not indicating the current page in the navigation
- Deep nesting that requires more than 3 clicks to reach important content
