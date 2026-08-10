# Redundancy Rules — Detailed Rules for Redundancy Detection

## Word-Level Redundancy

### Filler-Word Replacement Table

Replace the following verbose phrases with concise versions:

| Verbose phrase | Concise phrase | Tokens saved |
|---|---|---|
| "in order to" | "To" | 2 |
| "due to the fact that" | "Because" | 4 |
| "at this point in time" | "Now" | 4 |
| "in the event that" | "If" | 3 |
| "for the purpose of" | "To" / "For" | 3 |
| "a large number of" | "Many" | 3 |
| "in close proximity to" | "Near" | 3 |
| "it is important to note that" | "Note:" | 5 |
| "with the exception of" | "Except" | 3 |
| "in spite of the fact that" | "Although" | 4 |
| "on a regular basis" | "Regularly" | 2 |
| "in the near future" | "Soon" | 3 |
| "a majority of" | "Most" | 2 |
| "are able to" | "Can" | 2 |
| "is responsible for" | "Handles" / "manages" | 3 |

### Unnecessary Hedges

Flag these weakening qualifiers:

- "very" — "very important" → "critical", "very large" → "massive"
- "quite" — "quite useful" → just "useful"
- "rather" — "rather complex" → just "complex"
- "somewhat" — "somewhat difficult" → just "difficult"
- "really" / "definitely" — usually deletable
- "literally" — almost always redundant
- "actually" — almost always redundant (unless emphasizing a contrast)
- "basically" — "Basically, it works like this" → "It works like this"

### Overuse Detection
- Same word/phrase appearing 3+ times in one paragraph → flag
- Same word/phrase appearing 7+ times on one page → suggest a synonym
- Domain-specific terms excepted (e.g., API names can't be replaced)

## Structural Redundancy

### Echo Headings
- **Definition**: a heading immediately followed by an explanatory sentence starting with "This section"
- **Example**:
  - `## Troubleshooting` + "This section describes troubleshooting steps"
- **Fix**: delete the lead-in sentence; the heading already says it

### Repeated Introductions
- Multiple sections each re-introducing the same background knowledge → should be introduced once at the document start
- Every chapter and section repeating the same context → explain once, in one place

### Repeated Examples
- 3 examples with 95% identical commands, differing only in parameters → merge into one example with a comment
  ```markdown
  # ❌ Redundant
  az storage account create -n myaccount1 -g mygroup -l eastus
  az storage account create -n myaccount2 -g mygroup -l eastus
  az storage account create -n myaccount3 -g mygroup -l eastus

  # ✅ Concise
  az storage account create -n NAME -g mygroup -l eastus
  # Examples: myaccount1, myaccount2, myaccount3
  ```

### Mergable Similar Sections
- Adjacent sections with highly similar topics → consider merging
- Example: `## Windows Installation`, `## macOS Installation`, `## Linux Installation`
- Merge into `## Installation`, distinguishing with subsections or tabs

## Semantic Duplication Checks

### Duplicate Paragraphs
- Same paragraph appearing > 1 time in the document → keep one, delete or reference the rest
- Different sections expressing the same idea with different wording (>80% semantic similarity) → merge and unify the phrasing
- Example code duplicating what the prose already explains → delete the duplicate

### Over-Detail
- Copied install instructions for a common library (should link to the official docs) → replace with a one-line link
- Explained common-sense concepts (e.g., "what is a REST API", "what is a database") → delete, unless the target reader genuinely needs it
- Generic best practices unrelated to the current system → delete or move to an appendix
- "Filler statements" (correct but information-free, e.g., "this solution uses mature industry technology") → delete

### Irrelevant Content
- Paragraphs unrelated to the document topic → flag and suggest deletion
- Leftover template placeholder text → mark as incomplete

## Decorative Elements

### Emoji Usage
- **SHOULD**: no more than 3 decorative emoji
- **Allowed**:
  - Status indicators in tables (✅ ❌ ⚠️)
  - Conveying actual meaning (not purely decorative)
- **Not allowed**:
  - Emoji around headings 🙅 → `# 🚀 Getting Started 🎉`
  - Emoji at the start of every paragraph 🙅
  - Multiple consecutive emoji 🙅

### Dividers
- Consecutive `---` dividers → two adjacent headings are already a natural break; no divider needed
- **Suggestion**: only when emphasizing a topic switch, and no more than 1 per page

## Reader-Focused Writing

Readers have limited working memory and attention; documents that bury the action, pad with preamble, or wander into tangents lose them. These checks complement the redundancy rules above — they remove the same fluff from the reader's perspective.

- [ ] **Action-first lead**: does the document put the actionable content first instead of an announcing opener? Flag openers like "In this document, we will...", "This section describes..."
- [ ] **No closing pleasantries / recaps**: does it end with "Hope this helps", "Let me know if you have questions", or a full recap paragraph instead of stopping at the conclusion?
- [ ] **No tangents**: are there "by the way" asides or secondary topics offered mid-document instead of a separate section or appendix?
- [ ] **Lists capped at 5**: is any list over 5 items split into "do now" vs "later" (or ranked top 5) rather than one unranked wall?
- [ ] **Specific time/effort estimates**: are vague "soon", "a while", "some work" replaced with concrete units ("~15 minutes", "1-2 hours")?
- [ ] **Hedging without information**: are "perhaps", "might", "could possibly" deleted unless they carry real uncertainty?
- [ ] **Literal over figurative**: are idioms ("circle back", "get the ball rolling") replaced with the literal action?
- [ ] **Buried next step**: is the next action stated explicitly at the end rather than implied?

## Token Optimization

### Calculation Standard
- Approximately 4 characters = 1 token (Chinese estimated by character count)
- Report format: `current: X tokens | potential: Y tokens | savings: Z tokens (Z%)`

### Large Content Handling
| Content type | Suggestion | Threshold |
|---|---|---|
| Tables | move to a reference file | 10+ rows |
| Code blocks | trim examples | 20+ lines |
| Long lists | compress or split | 15+ items |
| Inline docs | move to a reference file | 100+ lines |

### Format Optimization
- **List → table**: when list items have multiple attributes
  ```markdown
  # ❌ Verbose list
  - Storage: min 3, max 24 chars, lowercase only, globally unique
  - Key Vault: min 3, max 24 chars, alphanumeric + hyphens, globally unique

  # ✅ Concise table
  | Resource | Min | Max | Allowed | Global |
  |----------|-----|-----|---------|--------|
  | Storage | 3 | 24 | a-z, 0-9 | Yes |
  | Key Vault | 3 | 24 | a-z, 0-9, - | Yes |
  ```

- **Code block → inline code**: single-line commands don't need a code block
  ````markdown
  # ❌ Code block
  Run the server:
  ```bash
  npm start
  ```

  # ✅ Inline code
  Run the server: `npm start`
  ````

## Scoring Guide

| Finding | Deduction |
|---|---|
| Filler words (in order to, etc.) | -0.5 per occurrence |
| Unnecessary hedges | -0.5 each |
| Echo headings | -1 per occurrence |
| Repeated examples (>90% identical) | -1.5 per group |
| Decorative emoji (more than 3) | -0.5 each |
| Redundant lead-in paragraphs | -1 per occurrence |
| Mergable similar sections | -2 |
| Large content that should move to references | -1 per occurrence |
| Announcing openers / preamble paragraphs | -1 per occurrence |
| Closing pleasantries / recap paragraphs | -1 per occurrence |
| Tangents ("by the way" asides) | -1 per occurrence |
| Lists over 5 items left ungrouped | -1.5 each |
| Vague time/effort estimates | -1 per occurrence |
| Hedging adverbs without information | -0.5 per occurrence |
| Idioms replacing literal action | -0.5 per occurrence |
| Buried next action | -1 per occurrence |
