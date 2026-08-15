# Worker Brief Format

Every worker dispatch is one stateless call (an agy CLI run, or a
Gemini API request on the fallback path) containing this brief.
The worker has no memory, no follow-ups, and sees nothing but this text.
Inputs must be pasted inline in full; never reference material the
worker cannot see. For code subtasks that means the entrypoint, file
layout, and exact run commands; otherwise workers invent their own.

```
You are a worker completing ONE subtask of a larger project. This brief
is everything you get. No follow-ups are possible.

SUBTASK: <one-line goal>
INPUTS: <everything needed, inline and complete>
ACCEPTANCE CRITERIA (output fails if any fail):
1. <criterion>
2. <criterion>
3. <criterion>
OUTPUT FORMAT: <exact structure, length, style>

Rules: do only the subtask, no scope expansion, no editorializing. If an
input is missing or contradictory, write INPUT GAP plus one line naming
it at the top, then proceed with what you have. Return only the
deliverable, no preamble.
```

Redispatch rule: when a result comes back FIX, send a new brief that
quotes the failed criterion and names the specific failure. Never reply
to the old call; every dispatch is fresh.
