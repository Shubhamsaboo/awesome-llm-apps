# Anchor Heuristics and Limitations

## How a "block" is anchored across commits

Git does not track a stable identity for a block of code across history —
line numbers shift as unrelated code is added or removed elsewhere in the
file. To compare "the same spot" across many commits, the detector anchors
each changed block to up to two lines of unchanged context immediately
before it and up to two lines immediately after it, then hashes that
context. As long as the surrounding lines stay stable, the anchor stays
stable even when line numbers shift.

This is a heuristic, not a guarantee:

- If the surrounding context itself changes (for example a function is
  renamed), the anchor breaks and the tool treats the next change as a new
  location rather than a continuation. This under-counts flips; it does not
  over-count them.
- Anchors are scoped per file path. A file rename starts a fresh history —
  the detector does not follow renames (plain `git log`, not
  `git log --follow`), by design, to avoid attributing unrelated pre-rename
  history to the wrong block.
- Pure whitespace-only edits (trailing whitespace) are ignored; everything
  else is compared as exact text after that normalization. A block that
  changes through paraphrase rather than reverting to byte-identical text is
  not detected — the detector deliberately avoids semantic similarity, to
  stay deterministic and explainable.

## What counts as a flip

Given the ordered sequence of states a block held over time, a flip is
recorded when a state reappears at least two changes after it was last
seen — the block moved away from a state and later returned to it. Two
consecutive edits (state A to state B) are not a flip; only a genuine
return (A to B, then back to A) counts.

## Performance bounds and why they exist

Walking full per-commit content for every tracked file in a large repository
is prohibitively slow. By default, the detector first runs one cheap
`git log --name-only` pass to find files touched at least three times (in
the `--since` window, if given), ranks them by change frequency, and only
performs the expensive per-commit walk on the top `--max-files` files
(default 300). Each file's walk is further capped at
`--max-commits-per-file` (default 200, keeping the most recent window) so
one unusually hot file cannot dominate the run.

Pass explicit `--paths` to skip discovery entirely and analyze exact files
or directories — this is both faster and exhaustive for that scope, with no
frequency threshold or cap applied.

## Known false positives and negatives

- Auto-generated files (lockfiles, snapshots, formatter output) can
  oscillate mechanically with no human disagreement behind it. Scope
  `--paths` to hand-written source, or read the sample states before
  concluding there was a real debate.
- A block that is reformatted (reindented, reflowed) without changing
  meaning registers as a normal change, not a flip, unless it happens to
  return to byte-identical prior text.
- Squash-merged or rebased history changes the commit graph the detector
  reads; a flip detected against rewritten history reflects that rewritten
  history, not necessarily the original chronology of decisions.
- A high flip count from a single author in a short window is usually rapid
  iteration, not disagreement. Weigh `authors` and the time span alongside
  `flip_count` before calling something contentious.
