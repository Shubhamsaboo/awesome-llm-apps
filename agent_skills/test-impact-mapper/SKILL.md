---
name: test-impact-mapper
description: >-
  Maps a local git diff to an evidence-backed shortlist of likely tests to run.
  Pairs changed source files with conventional test paths, reverse-import
  dependents, mentioned symbols, and optional git co-change history. Use
  when the user asks which tests to run after a code change, which tests a
  diff impacts, what tests cover a change, for a test impact map, a
  regression shortlist, or to avoid running the full suite. Operates locally
  and offline.
license: Apache-2.0
metadata:
  author: "Matt Van Horn"
  version: "1.0.0"
  source: "https://github.com/Shubhamsaboo/awesome-llm-apps"
---

# Test Impact Mapper

A one-file change should not mean running the entire suite, and it should not
mean guessing. This skill reads a local git diff and returns a ranked shortlist
of tests with the evidence that tied each test to the change.

Everything runs locally. The script makes no network calls and does not change
the working tree, index, commits, or branches.

## When to use

- After editing code, when the user asks which tests to run
- When a diff should produce a regression shortlist instead of `pytest` on everything
- When the user wants a test impact map for a working, staged, or branch diff
- When an agent needs a bounded, checkable set of tests before claiming a change is covered

## When not to use

- Running the suite, collecting coverage percentages, or debugging a flake
- Writing new tests, generating fixtures, or mutating the tree
- Reviewing whether a diff grew beyond its stated intent (that is `scope-creep-detector`)
- Reconstructing why a line exists (that is `commit-archaeologist`)

## Run the mapper

Run from this skill directory and point `--repo` at the target repository.

Working tree diff:

```bash
python3 scripts/impact_map.py --repo /path/to/repo --json
```

Staged diff:

```bash
python3 scripts/impact_map.py --repo /path/to/repo --staged --json
```

Branch diff against a merge base:

```bash
python3 scripts/impact_map.py --repo /path/to/repo --base main --json
```

Saved diff or stdin:

```bash
python3 scripts/impact_map.py --repo /path/to/repo --diff change.diff --json
git diff --staged | python3 scripts/impact_map.py --repo /path/to/repo --diff - --json
```

`--limit` caps the shortlist (default 20). `--max-depth` bounds the reverse-import
walk (default 3). `--no-history` skips git co-change evidence when history is
noisy or the clone is shallow.

## Interpret the JSON

Read [references/mapping-rules.md](references/mapping-rules.md) before treating
a path as required. The mapper is triage evidence, not a coverage proof.

- `recommended`: ranked tests, each with `score`, `evidence[]`, and the changed files that produced the hit
- `unmapped`: changed paths with no test evidence (docs, config, or a coverage gap)
- `changed_files`: every path in the diff, labeled `source`, `test`, or `other`
- `stats`: files changed, tests discovered, mapped vs unmapped counts

Evidence kinds, strongest first: `path`, `self`, `import`, `importer`, `symbol`,
`cochange`, `name`. Quote the `detail` string. Do not invent tests that are not
in `recommended`.

Empty `recommended` is evidence too. Say that no test was tied to the diff,
not that the change is untested in some deeper sense the script cannot see.

## Recommend what to run

1. Run the `recommended` tests in score order. Name the paths.
2. For each, cite one piece of evidence (conventional pair, import, symbol).
3. Call out `unmapped` source files as likely coverage gaps. Do not silently drop them.
4. Do not claim the shortlist is equivalent to the full suite.

Prefer the shortlist over the full suite when evidence exists. If the only
changed files are tests, say so and recommend those tests (`self`), not a
broader hunt.

Never run tests, edit files, or open a pull request without the user asking.

## Write the impact report

Use this compact structure:

1. Diff source (working / staged / base / saved diff)
2. Changed files, with source vs test vs other
3. Recommended tests, ranked, with evidence
4. Unmapped changes
5. Suggested command using the recommended paths (pytest, go test, etc.)

Name file paths. If a high-score test is itself in the diff, say that the
change already touched the test. Ask before running anything.

## Files

- `scripts/impact_map.py`: deterministic diff parser, reverse-import walk, and ranker
- `references/mapping-rules.md`: evidence kinds, path conventions, and limits
