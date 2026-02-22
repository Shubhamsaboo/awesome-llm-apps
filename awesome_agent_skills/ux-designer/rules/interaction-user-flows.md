# Rule: User Flow Best Practices

**Priority:** HIGH
**Category:** Interaction Design

## Description

User flows map the path a user takes to complete a task. Well-designed flows minimize friction and guide users to success with clear progress and recovery paths.

## Guidelines

### Design Principles
- Map the happy path first, then design for errors and edge cases
- Minimize steps — every additional step loses a percentage of users
- Provide clear progress indicators for flows with 3+ steps
- Allow users to go backward without losing entered data
- Auto-save form data at each step when possible
- Confirm all destructive actions with clear, specific consequences

### Flow Mapping
- Start with the user's entry point and goal
- Document every screen, decision point, and action
- Include error states and recovery paths at each step
- Note where users might drop off and design for retention
- Map alternative paths (e.g., social login vs. email login)

### Multi-Step Flows
- Show total steps and current position (step 2 of 4)
- Allow skipping optional steps
- Summarize entered data before final submission
- Provide a confirmation screen with next steps after completion
- Send confirmation via email or notification for important transactions

### Error Recovery
- Detect errors as early as possible (inline validation)
- Explain what went wrong in plain language
- Tell the user how to fix it
- Preserve all valid input — never clear the form on error
- Offer alternative paths when the primary path fails

## Examples

### Good Flow: Checkout
```
Cart → Shipping → Payment → Review → Confirmation
  ↑       ↑          ↑        ↑
  [Back]  [Back]     [Back]   [Edit]

- Progress bar visible at all times
- Each step validates before proceeding
- Review screen shows everything before final commit
- Confirmation includes order number, email, and estimated delivery
```

### Bad Flow: Checkout
```
Cart → Login Required → Shipping → Re-enter email → Payment → Surprise fees → Submit
                                                                    ↓
                                                               [No going back]
```

## Common Mistakes
- Requiring account creation before the user sees any value
- Hiding total cost until the final step
- Dead ends with no clear next action
- Loops where the user returns to the same screen without progress
- Missing feedback after the final action (did it work?)
