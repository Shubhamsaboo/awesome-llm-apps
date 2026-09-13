# How test impact evidence is ranked

The mapper never claims a test will fail, and it never claims the shortlist is
complete coverage. It ranks tests by checkable ties to the diff.

## Evidence kinds

| Kind | Weight | What it means |
|---|---|---|
| `path` | 8 | A conventional test path for the changed source file exists in the tree (`src/foo.py` → `tests/test_foo.py`, `foo_test.go`, `foo.test.ts`, and similar). |
| `self` | 7 | The changed file is itself a test. Recommend it; do not look past it. |
| `import` | 5 | The test file imports the changed module (Python `from`/`import`, JS/TS `import`/`require`). |
| `importer` | 4 | A reverse-import walk (default depth 3) reached the test through another source file. The `detail` names the intermediate. |
| `symbol` | 3 | A public `def`/`class`/`function`/`func` on a changed hunk appears as a whole word in the test. Names shorter than 4 characters and `_private` helpers are ignored. |
| `cochange` | 2 | Recent `git log --name-only` for the changed file lists this test. Correlation, not causation. Disable with `--no-history`. |
| `name` | 1 | The test basename shares a stem token with the source file, without a conventional path pair. Weak; never treat as sufficient alone if stronger evidence exists elsewhere. |

A test's `score` is the sum of unique evidence rows. Rank by score, then path.

## Path conventions the script actually checks

For `billing/invoice.py` (and the same stem under `src/`, `lib/`, `app/`, `pkg/`):

- `tests/test_invoice.py`, `test/test_invoice.py`, `tests/invoice_test.py`
- `tests/billing/test_invoice.py`
- `billing/test_invoice.py`, `billing/invoice_test.py`
- JS/TS: `invoice.test.ts`, `invoice.spec.js`, `__tests__/invoice.test.ts`

A candidate only counts if that file exists in the walk. The script does not
invent missing tests.

## Limits (say these out loud when they matter)

- Walks at most 4000 code files; skips `node_modules`, `.venv`, `dist`, and similar.
- Import parsing is regex, not a language parser. Dynamic imports, `importlib`, and generated paths are invisible.
- Reverse-import depth is `--max-depth` (default 3). Deeper dependents are omitted.
- Symbol hits can false-positive on a common name (`process`, `handle`). Prefer `path` and `import` when both exist.
- Co-change uses the last 40 commits that touched the file. A noisy history inflates `cochange`. Use `--no-history` then.
- Binary files, docs, and YAML are `other`. They show up in `unmapped` unless a test path also changed.

## Git is read-only

Diffs are collected with `--no-ext-diff --no-textconv` so configured converters
do not run. The script never `add`s, `commit`s, `checkout`s, or writes inside
the target repository.

## What to tell the user

- Strong: "`tests/test_invoice.py` is the conventional pair of `billing/invoice.py` and imports `compute_total`."
- Strong: "`docs/guide.md` has no test evidence."
- Weak: "This change is fully covered." The mapper cannot see runtime paths, mocks, or tests it failed to parse.

If `recommended` is empty and `unmapped` contains source files, say that no
test was tied to the diff and offer to run the suite or add a test. Do not
fill the gap with a guess.
