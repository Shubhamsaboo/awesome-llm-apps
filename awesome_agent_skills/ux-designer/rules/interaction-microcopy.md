# Rule: Microcopy Guidelines

**Priority:** HIGH
**Category:** Interaction Design

## Description

Microcopy is the small text that guides users through an interface — button labels, tooltips, error messages, empty states, and confirmation dialogs. Great microcopy reduces confusion and builds trust.

## Guidelines

### Buttons & CTAs
- Use specific verbs that describe the action: "Save Draft", "Send Message", "Create Account"
- Avoid generic labels: "Submit", "OK", "Click Here", "Next"
- Match the button label to the user's intent, not the system's action
- For destructive actions, name the consequence: "Delete Project" not "Confirm"

### Error Messages
- Explain what happened in plain language
- Tell the user how to fix it
- Be specific: "Password must be at least 8 characters" not "Invalid input"
- Don't blame the user: "We couldn't find that page" not "You entered a wrong URL"
- Place error messages near the field that caused them

### Empty States
- Explain why it's empty
- Tell the user what to do to fill it
- Provide a clear call-to-action
- Example: "No projects yet. Create your first project to get started." + [Create Project] button

### Confirmation Dialogs
- State the action and its consequences clearly
- Use asymmetric button labels: "Delete Project" / "Keep Project" (not "Yes" / "No")
- Mention if the action is irreversible
- Provide context: "Delete 'Marketing Plan'? All files and comments will be permanently removed."

### Loading States
- Use specific messages when possible: "Saving your changes..." rather than "Loading..."
- For long waits, explain what's happening: "Analyzing 1,247 responses..."
- Consider skeleton screens over spinners for content-heavy pages

### Tooltips & Helper Text
- Keep tooltips under 150 characters
- Use helper text for persistent guidance, tooltips for supplementary info
- Don't hide critical information in tooltips — it should be visible by default
- Format: Explain what it is, then why it matters

## Examples

| Context | Weak | Strong |
|---------|------|--------|
| Save button | Submit | Save Changes |
| Delete dialog | "Are you sure?" / Yes / No | "Delete 'Q4 Report'? This can't be undone." / Delete / Cancel |
| Empty inbox | No messages | You're all caught up! New messages will appear here. |
| Form error | Invalid | Enter a valid email address (e.g., name@example.com) |
| 404 page | Page not found | We can't find that page. It may have been moved or deleted. |

## Common Mistakes
- Using technical jargon ("Error 422: Unprocessable Entity")
- Writing error messages that only say what's wrong, not how to fix it
- Using "Yes" and "No" for destructive action confirmations
- Inconsistent terminology (using "remove", "delete", and "trash" for the same action)
- Placeholder text that disappears on focus, serving as the only label
