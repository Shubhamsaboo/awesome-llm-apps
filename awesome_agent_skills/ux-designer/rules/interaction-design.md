# Rule: Interaction Design

**Priority:** HIGH
**Category:** Interaction Design

## Description

Interaction design covers user flows and microcopy — the two elements that most directly determine whether users complete tasks or abandon them.

## User Flow Best Practices

### Design Principles
- Map the happy path first, then design for errors and edge cases
- Minimize steps — every additional step loses a percentage of users
- Provide clear progress indicators for flows with 3+ steps
- Allow users to go backward without losing entered data
- Auto-save form data at each step when possible
- Confirm all destructive actions with clear, specific consequences

### Multi-Step Flows
- Show total steps and current position (step 2 of 4)
- Allow skipping optional steps
- Summarize entered data before final submission
- Send confirmation via email/notification for important transactions

### Error Recovery
- Detect errors as early as possible (inline validation)
- Explain what went wrong in plain language and how to fix it
- Preserve all valid input — never clear the form on error
- Offer alternative paths when the primary path fails

### Good vs. Bad Flow

```
✅ Cart → Shipping → Payment → Review → Confirmation
    ↑       ↑          ↑        ↑
    [Back]  [Back]     [Back]   [Edit]
  Progress bar visible · Each step validates · Review before commit

❌ Cart → Login Required → Shipping → Re-enter email → Payment → Surprise fees → Submit
                                                                      ↓
                                                                 [No going back]
```

## Microcopy Guidelines

### Buttons & CTAs
- Use specific verbs: "Save Draft", "Send Message", "Create Account"
- Avoid generic labels: "Submit", "OK", "Click Here"
- For destructive actions, name the consequence: "Delete Project" not "Confirm"

### Error Messages
- Explain what happened AND how to fix it
- Be specific: "Password must be at least 8 characters" not "Invalid input"
- Don't blame the user: "We couldn't find that page" not "You entered a wrong URL"

### Empty States
- Explain why it's empty and what to do next
- Example: "No projects yet. Create your first project to get started." + [Create Project]

### Confirmation Dialogs
- Use asymmetric button labels: "Delete Project" / "Keep Project" (not "Yes" / "No")
- Mention if the action is irreversible
- Provide context: "Delete 'Marketing Plan'? All files and comments will be permanently removed."

| Context | ❌ Weak | ✅ Strong |
|---------|---------|----------|
| Save button | Submit | Save Changes |
| Delete dialog | "Are you sure?" / Yes / No | "Delete 'Q4 Report'? This can't be undone." / Delete / Cancel |
| Empty inbox | No messages | You're all caught up! New messages will appear here. |
| Form error | Invalid | Enter a valid email address (e.g., name@example.com) |

## Common Mistakes
- Requiring account creation before the user sees any value
- Dead ends with no clear next action
- Using "Yes" and "No" for destructive action confirmations
- Inconsistent terminology (using "remove", "delete", and "trash" for the same action)
- Missing feedback after the final action (did it work?)
