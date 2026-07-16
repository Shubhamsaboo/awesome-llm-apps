# Scope signals

The classifier uses cheap, deterministic signals. They are review prompts, not
proof that a change is wrong or unrelated.

## Relatedness

The script tokenizes the stated intent and each changed path. It removes common
branch words such as `fix`, `feat`, and `change`, then computes:

`relatedness = shared intent/path tokens / usable intent tokens`

A file with at least one shared token enters `in_scope`. A file with no shared
tokens enters `likely_creep`. This deliberately favors recall. A zero score can
mean a vague intent or an indirect but necessary file, so verify the connection
before recommending a split.

## Subsystems

The first path component is the subsystem. Root files use `(root)`. Three or
more subsystems are worth naming in the report even if every path is justified.
Subsystem count is context, not a failure threshold.

## Added dependencies

The detector reads added lines in these formats:

- `requirements*.txt`
- dependency sections in `package.json`
- PEP 621 and Poetry dependency sections in `pyproject.toml`

If the same normalized package name is removed in the diff, the change is
treated as a version or constraint edit, not a new dependency. Lockfiles are
not parsed because generated transitive changes obscure the direct addition.

## Public API renames

A rename is a removed `def`, `async def`, or `class` declaration paired with a
nearby added declaration of the same kind in one hunk. The declarations must be
within 12 diff lines. This catches common renames but can confuse a deletion and
addition that happen to be adjacent. Confirm call sites before describing an
API break.

## Config, CI, and build edits

The signal covers:

- `.github/` paths as CI
- `Dockerfile`, Docker Compose, Make, CMake, Meson, and Procfile paths as build
- `.toml`, `.yml`, and `.yaml` files as config

These files often have legitimate cross-cutting reasons. Prefer `justify` when
the feature cannot pass tests, package, or deploy without the edit. Prefer
`split` when the edit changes infrastructure policy independently.

## Oversized hunks

Hunk churn is added lines plus removed lines. The default threshold is more
than 80 changed lines in one hunk. Context lines do not count. The threshold is
intended to expose mixed or hard-to-review edits, not enforce a PR size limit.

## Formatting-only files

A file is formatting-only when it has the same number of removed and added
lines and each pair becomes identical after all whitespace is removed. This is
intentionally narrow. Reordered imports, quote changes, and formatter rewrites
that move lines may not qualify.

## Recommendation matrix

| Evidence | Default action |
|---|---|
| Path overlaps intent and has no independent signal | Keep |
| No path overlap and a separate subsystem | Split |
| New dependency unrelated to intent | Split |
| Public API rename not required by intent | Split |
| CI or build edit required for the change to work | Justify |
| Formatting-only file mixed into a behavior change | Split |
| Oversized hunk containing one coherent algorithm | Keep or justify |
| Oversized hunk containing separable concerns | Split by hunk or file |

Always name the evidence. Do not turn a heuristic label into a claim about the
author's motivation.
