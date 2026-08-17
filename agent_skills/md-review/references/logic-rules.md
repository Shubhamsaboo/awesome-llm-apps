# Logic Rules — Detailed Rules for Logical Consistency (Bug Detection)

This dimension carries 30% weight and is the core of md-review. **Prioritize finding bugs that would break downstream implementation** rather than pure style issues.

## Bug-Level Detection Checklist (P0, must report)

Mark all of the following as 🔴 Error, because they can break the implementation code:

### Formula and Calculation Errors
- [ ] Are all variables in formulas defined? (undefined variables = the implementer cannot code)
- [ ] Are formula units consistent? (e.g., mixing seconds vs. milliseconds)
- [ ] Is the evaluation order unambiguous? (missing parentheses)
- [ ] Can the divisor be zero? (division by zero = runtime crash)
- [ ] Can formula results fall outside the expected range? (overflow/underflow)
- [ ] Do formulas match their prose description? (text says A, formula computes B)

### Number and Parameter Contradictions
- [ ] Does the same parameter have different values in different sections? (defaults / maximums / thresholds / cooldowns)
- [ ] Unit conversion errors? (e.g., "1.5x" written as "150%x" with different meanings)
- [ ] Percent vs. multiplier mixing? ("increase by 20%" vs. "multiply by 1.2" differ semantically)
- [ ] Boundary value contradictions? ("max 100" conflicting with an example "101")
- [ ] Version numbers / dependency versions inconsistent across locations

### Missing Edge Conditions (bug hotbed)
- [ ] Are null/None/empty lists handled?
- [ ] Are zero/negative/over-limit inputs handled?
- [ ] Are timeouts explicitly defined? (timeout duration, retry count, backoff strategy)
- [ ] Is there a concurrency conflict strategy? (optimistic lock / pessimistic lock / version number)
- [ ] Are data-volume limits stated? (per table / per request / concurrent connections)
- [ ] Are exception paths described? (failure behavior, not just the success path)
- [ ] Does every mechanism/feature state its boundary behavior where it is introduced? (a feature that depends on an unstated rule — e.g. a respawn feature with no death/failure rule, a continue feature with no state-restoration rule — cannot be implemented and is a P0 bug source)
- [ ] Do scalability assumptions ("scale horizontally later", "support X in the future") have reserved interfaces or explicit unimplemented markers?

### Flow and State Errors
- [ ] Is the operation order reasonable? (auth before business logic, validation before persistence)
- [ ] Is the data flow closed-loop? (input → process → output → storage, nothing appearing/disappearing)
  - [ ] Does every data flow have a clear source and sink?
  - [ ] Are data transformation steps traceable? (input → process → output → storage)
  - [ ] Does data "appear from nowhere"? (output without a stated source)
  - [ ] Does data "disappear without a trace"? (input without a stated destination)
  - [ ] Is every step of the data flow covered by a document section?
- [ ] Are there circular dependencies? (A depends on B, B depends on A)
- [ ] Are state transitions missing from the state machine? (state X unreachable from state Y)
- [ ] Dead branches / unreachable logic
- [ ] Do async operations have callbacks/notifications? (no callback = hang)
- [ ] Do concurrent operations have explicit ordering guarantees or conflict handling?

### Interface Definition Conflicts
- [ ] Are the same interface's parameters / return values / error codes consistent across sections?
- [ ] Do interface parameters cover all required fields?
- [ ] Is the error code definition complete? (success / failure / partial success)
- [ ] Is backward compatibility considered for interface changes?

## Internal Consistency Checks

### Terminology Consistency
- [ ] Is the same concept named consistently throughout? (e.g., "login" and "sign-in" used interchangeably for the same thing)
- [ ] Are abbreviations expanded on first use?
- [ ] Is capitalization of proper nouns consistent?
- [ ] Is the same feature described consistently across locations?
- [ ] Do proper nouns give their full name and abbreviation on first appearance? (e.g., "React (a UI library by Facebook)")
- [ ] Is English terminology capitalization unified? (e.g., "MySQL" not mixed "mysql"/"Mysql")

### Data Consistency
- [ ] Are numbers/values consistent across locations?
  - Example: one place says "supports 100 concurrent connections", another says "supports 1000"
- [ ] Is the timeline self-consistent?
  - Example: A is released in May, but B (which depends on A) was completed in March
- [ ] Are default values consistent across locations?
- [ ] Are limits/constraints consistent across locations?

### Behavior Consistency
- [ ] Is the judgment logic for the same condition consistent?
- [ ] Is error handling consistent?
- [ ] Is permission control described consistently?

## Logical Fallacy Detection

### Causal Fallacy
- **Signature**: B happened after A, therefore A caused B
- **Example**: "User growth increased 50% after we deployed the new version, so the new version drove the growth"
- **Check**: Are there other factors that could explain the result?

### Overgeneralization
- **Signature**: Generalizing from a limited sample to a universal conclusion
- **Example**: "Two users reported this issue, so all users have it"
- **Check**: Is the sample size sufficient? Are there counterexamples?

### False Dichotomy
- **Signature**: Offering only two options, ignoring other possibilities
- **Example**: "We either use microservices or stay on a monolith"
- **Check**: Is there a third or further option?

### Circular Reasoning
- **Signature**: The conclusion appears as a premise
- **Example**: "This solution is good because it is best practice; it is best practice because this solution is good"
- **Check**: Is the argument's conclusion assumed as a premise?

### Slippery Slope
- **Signature**: Accepting A inevitably leads to Z, skipping the intermediate argumentation
- **Example**: "If we allow remote work, the team will completely fall apart"
- **Check**: Is every step from A to Z reasonably argued?

### Appeal to Authority
- **Signature**: Relying solely on the word of an authority figure/organization as evidence
- **Example**: "The CEO thinks this solution is best"
- **Check**: Is there substantive evidence besides the authority's opinion?

### Straw Man
- **Signature**: Distorting the opponent's view to make it easier to refute
- **Example**: "Opponents think we shouldn't optimize performance → they think performance doesn't matter"
- **Check**: Does the refuted view accurately represent the original?

## Argument Quality Checks

### Claims and Evidence
- [ ] Does every important claim have sufficient supporting evidence?
- [ ] Does the evidence come from reliable sources?
- [ ] Are there unsourced assertions? ("according to statistics...", "research shows...")
- [ ] Is the source of data/statistics clear?

### Weak Argument Markers
- Flag arguments that use these vague phrases:
  - "As everyone knows..." — not everyone knows
  - "Obviously..." — if it's not obvious, the phrase masks insufficient argumentation
  - "It's not hard to see that..." — leaving the reader to conclude
  - "One might say..." — a preamble to a straw man

### Objections and Rebuttals
- [ ] Are possible rebuttals considered?
- [ ] Is there a response to known objections?
- [ ] Are both "pros" and "cons" listed? (rather than only one side)

## Convention Consistency

- [ ] Does the document content conflict with declared conventions or standards referenced in the document set (e.g., style guides, interface contracts, process rules)?
- [ ] Does the described practice match previously established decisions in the reviewed documents?

## Scoring Guide

| Finding | Deduction |
|---|---|
| Self-contradictory statements | -3 |
| Terminology inconsistency | -1 per occurrence |
| Data/number inconsistency | -2 per occurrence |
| Logical fallacy | -2 each |
| Unsourced assertion | -1 each |
| Unconsidered rebuttal | -1 |
| Vague statement (multiple interpretations) | -0.5 per occurrence |
