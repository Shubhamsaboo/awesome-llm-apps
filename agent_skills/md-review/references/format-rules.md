# Format Rules — Detailed Rules for Format (Basic Checks Only)

This dimension carries only 10% of the overall weight. Detailed linting (item-by-item MD spec checks) is handled by the editor's linting tooling (e.g., a VS Code extension, if installed); this file covers only **formatting issues that affect rendering correctness** (readability issues are handled by external tooling and are not checked here).

## Rendering-Critical Formatting Issues (must report)

### Headings
- Heading-level skips (H1 → H3 skipping H2) — affects document structure comprehension and table-of-contents generation
- Multiple H1 headings (the document title should be the unique H1)
- No blank line before/after headings (may be parsed as body text)

### Code Blocks
- Unclosed fenced code blocks (opening/closing backtick counts differ) — subsequent content may be swallowed into the code block
- Unclosed inline code (single backtick) — affects rendering

### Numbered Lists (step-numbering breaks)
- **Gap in a contiguous ordered list** (1, 2, 4): a step number is skipped — in procedures (test steps, build steps, process flows) this usually means a step was deleted or forgotten; flag it
- **Duplicate number in a contiguous ordered list** (1, 2, 2, 3): numbering error in the source
- **Do NOT flag** (precision): a new list that legitimately restarts at 1 after a reset boundary (blank line, heading, table, or code block); identifier-style numbers (T-1, TC-1, REQ-001) are not ordered lists; single-item lists
- A step-numbering gap in a **semantic procedure** (test steps, build/deploy steps, process flows) should ALSO be reported under Logic as a broken/missing step — the gap often hides a deleted or forgotten step

### Links and Images
- Incomplete `[text](url)` syntax (missing parentheses)
- Relative paths not starting with `./` or `../` (likely wrong paths)

## Scoring Guide (format dimension, out of 100)

| Finding | Deduction |
|---|---|
| Heading-level skip | -5 per occurrence |
| Multiple H1s | -10 |
| Step-numbering break (gap or duplicate) in an ordered list | -3 per occurrence |
| Incomplete link syntax | -5 per occurrence |

Format dimension floor: as long as a rendering-level error exists (unclosed code block), the format score cannot exceed 60; only minor issues score 80-95.
