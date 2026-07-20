---
name: commit-archaeologist
description: >-
  Reconstructs why code exists from local git history, including the introducing
  commit, later changes, current authors, repeated companion files, and likely
  intent. Use when the user asks "why does this code exist", "who wrote this
  function and why", or to "explain the history of this function" before a
  rewrite, refactor, or risky edit. Runs entirely locally.
license: Apache-2.0
metadata:
  author: "Matt Van Horn"
  version: "1.0.0"
  source: "https://github.com/Shubhamsaboo/awesome-llm-apps"
---

# Commit Archaeologist

`git blame` names the last person to touch a line. This skill reconstructs the
reason the line exists. It traces a file or current line range through local git
history, identifies its origin and later edits, finds files that repeatedly
changed beside it, and extracts intent clues from commit messages.

Everything runs locally. No network calls, API keys, or repository writes.

## When to use

- The user asks why a block, function, or file exists
- The user wants to know who introduced code and what changed afterward
- A rewrite or refactor needs historical constraints and change risks
- A workaround, temporary branch, or surprising design choice needs context

## When not to use

- The user only wants raw blame output or a commit list
- The task is to squash, delete, or rewrite git history
- The repository is remote and has not been cloned locally
- The question is about project-wide architecture rather than one file or region

## Gather the target

Get the repository path and tracked file path. Use a line range when the user
names a current block or function. If either path is missing, ask only for the
missing value. Do not scan sibling repositories.

Paths should be relative to the repository and use forward slashes. Line ranges
use inclusive current line numbers such as `40-72`.

## Run the dig

From this skill directory:

```bash
python3 scripts/archaeologist.py /path/to/repo src/cache.py --lines 40-72 --json
```

For the complete history of a file, omit `--lines`:

```bash
python3 scripts/archaeologist.py /path/to/repo src/cache.py --json
```

The script is read-only. With a range it uses git line-log; without one it uses
file history with rename following. It also reads current authorship with blame.
If it rejects a path or range, report that error and ask for a corrected target.

Before interpreting the JSON, read
`references/reading-git-history.md`. Its confidence rules prevent blame
ownership, correlation, and commit-message hints from becoming false certainty.

## Read the JSON

- `region`: normalized repository, current and historical paths, mode, range,
  and co-change threshold
- `introduced_by`: oldest commit in the selected history
- `timeline`: commits ordered oldest to newest, with category, changed files,
  and detected renames
- `co_changed`: files present beside the target in enough selected commits
- `authors`: current blamed lines and historical commit counts, kept separate
- `intent_signals`: issue references, reverts, workarounds, temporary markers,
  and unfinished-work markers found in commit messages

An empty signal list means the messages do not say why. It does not mean the
change had no reason.

## Write the report

Turn the JSON into a short "why this code exists" report:

1. **Bottom line.** One or two sentences with the most likely explanation and
   a confidence label: high, medium, or low.
2. **Origin.** Introducing hash, date, author, subject, and the neighboring
   files that make the initial purpose clearer.
3. **Timeline.** Oldest to newest. Group mechanical edits when they do not
   change the story, but preserve reverts, fixes, and workarounds.
4. **Companion files.** Explain repeated co-changes as a coupling clue. Do not
   treat a one-off file in `changed_files` as a dependency.
5. **Intent evidence.** Quote short commit subjects or signal words. Label any
   conclusion beyond those facts as an inference.
6. **Change risk.** Name the constraints, companion files, and unresolved
   temporary choices worth checking before an edit.

Keep hashes short in prose, but preserve enough characters to identify them.
Do not dump the full JSON unless the user asks.

## Evidence rules

- Current blame ownership is not proof of original authorship.
- The oldest selected commit is the region's introduction, not always the
  file's first commit.
- Repeated co-change suggests coupling; it does not prove a dependency.
- Commit categories are message heuristics, not verified issue types.
- "Temporary" and "workaround" are strong intent clues, but only the message
  author or linked discussion can confirm whether the constraint still applies.
- If the history is thin or messages are vague, say "the history shows" and
  "likely" instead of inventing a design rationale.

## Follow-ups

End by offering one relevant follow-up, such as:

- "Want me to assess whether this looks deliberate or accidental?"
- "Want me to map what could break if this region changes?"

For a deliberate-choice question, weigh repeated edits, issue references,
reverts, and explicit constraint words. For a change-risk question, inspect the
repeated co-change files and the last behavior-changing commits before proposing
edits. Do not modify code until the user asks.

## Files

- `scripts/archaeologist.py`: offline git history walker and JSON report builder
- `references/reading-git-history.md`: interpretation and confidence guide
