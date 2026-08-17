# md-review

Scenario-aware Markdown document review with weighted scoring. **Finds bugs and logic errors that would break downstream implementation first**, then checks scenario-specific completeness — style and formatting are secondary.

## What it does

Reviews ONE Markdown document per invocation across 14 document scenarios (PRD, API spec, GDD, TDD, ADR, BRD, MRD, FSD, GDO, LDD, Concept, TLD, TCD) or in generic mode, scoring across 6 weighted dimensions:

| Dimension | Weight |
|---|---|
| Logic (bug detection) | 30% |
| Scenario completeness | 25% |
| Sections | 15% |
| References | 10% |
| Redundancy | 10% |
| Format | 10% |

## Usage

```text
/md-review <path> [scenario] [--dimensions 1,2,3,4,5,6] [--format full|summary|fix] [--solo] [--pass-threshold N] [--output file] [json]
```

- `<scenario>` — one of the 14 scenarios; omit for generic mode
- `--solo` — non-interactive CI mode; exit codes: `0` = no P0 (blocking/bug-level issue) and score ≥ threshold (default 75), `1` = P0 issues or below threshold, `2` = error
- `--format fix` — applies only safe mechanical fixes automatically (link-text repairs, filler-word removal, echo-title removal); judgment calls are reported unfixed
- Every report ends with a machine-readable `MD-REVIEW-SUMMARY` block for CI parsing

## Structure

```text
md-review/
├── SKILL.md                  skill definition (workflow + phases 0-6)
├── references/               5 review-rules files + 14 per-scenario checklists
├── scripts/                  5 python helpers (probe, analyze, extract_refs, score, path-gate)
└── example/                  report, review-plan, fix-plan, summary and delta templates
```

All helpers are read-only analyzers; nothing leaves the machine, no network calls.

## Testing

The skill ships a self-contained regression suite in its source repository ([viggo-pod/md-review](https://github.com/viggo-pod/md-review), MIT): `bash evals/run_self_test.sh` runs 5/5 checks (script verification, clean-doc precision, error-path protocol, registry integrity, step-numbering detection). Development benchmark: 212/213 runs passed (99.5%), 100% of injected defects detected.

## License

MIT
