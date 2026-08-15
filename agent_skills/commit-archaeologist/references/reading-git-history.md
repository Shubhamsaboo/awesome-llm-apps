# Reading git history without inventing intent

The dig report separates facts from signals. Use this guide before turning it
into a narrative.

## File history and line history answer different questions

File mode uses `git log --follow` and asks how the tracked file evolved. Line
mode uses git line-log and asks which commits shaped the current selected lines.
A line-mode timeline can start long after the file was created. Call its oldest
entry the region's introducing commit, not automatically the file's creator.

Line-log follows patches backward. Large rewrites, copied code, and some renames
can break the chain. When an origin looks too recent, compare it with file mode
and say that the earlier ancestry is uncertain.

## Authorship has two meanings

The `authors` list holds both current blamed-line counts and commit counts in the
selected timeline. Current blame answers who last shaped surviving lines.
Timeline authorship answers who committed the historical changes. Neither fact
alone proves who designed the behavior.

Use precise language:

- Strong: "Ada introduced the selected lines in `a1b2c3d`."
- Strong: "Seven current lines are blamed to Ada."
- Weak: "Ada designed the system this way." This needs message or issue evidence.

## Timeline categories are routing hints

The script labels messages as `feat`, `fix`, `refactor`, `revert`, `hotfix`,
`merge`, or `other`. These labels make the narrative easier to scan. They are
keyword classifications, not proof that a refactor preserved behavior or that a
commit labeled fix solved the root cause.

Read subject, body, and changed files together. A refactor followed by a revert
is more informative than either label alone.

## Co-change is correlation

`co_changed` includes files that crossed a threshold within the selected
timeline. Repetition is useful because a helper changed beside the target in
several commits for a reason more often than by accident.

Treat it as a clue:

- Repeated test co-changes can reveal the behavior the code protects.
- Repeated schema or migration co-changes can reveal a data constraint.
- Repeated configuration co-changes can reveal a deployment constraint.
- Generated or formatting commits can create meaningless co-change patterns.

Say "often changed with" until the code confirms a dependency.

## Intent signals and confidence

Issue or PR references point to likely external context. Revert, workaround,
temporary, and TODO words are direct evidence that the commit author framed the
change that way. They still do not say whether the condition remains true.

Use these confidence levels:

- **High:** explicit constraint language plus repeated supporting changes, or a
  revert that clearly names the behavior being restored.
- **Medium:** message category, changed files, and timeline shape agree, but no
  message states the rationale directly.
- **Low:** sparse history, generic subjects, bulk rewrites, or conflicting clues.

Keep quotes short and traceable to the commit. When the evidence only shows what
changed, report what changed and leave the why open.

## Change-risk checklist

Before recommending an edit, check:

1. Did a prior commit try the same change and get reverted?
2. Do tests, schemas, migrations, or configs repeatedly move with the region?
3. Does a workaround or temporary marker name an external constraint?
4. Does current blame hide an older introducing author after a mechanical edit?
5. Does file mode show ancestry that line mode could not retain?

The safest report names the evidence, the inference, and what would confirm it.
