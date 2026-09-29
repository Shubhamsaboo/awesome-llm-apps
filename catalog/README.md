# Template catalog

`templates.json` is a machine projection of the root README "Browse all templates" list. The README stays the human catalog. This JSON exists so the list can be queried without scraping markdown.

Regenerate after the README already links a directory:

```bash
python3 catalog/lint.py --write
```

CI (`.github/workflows/catalog.yml`) runs `python3 catalog/test_lint.py` and `python3 catalog/lint.py --check --strict`. That job fails when:

- a README-listed path is missing on disk
- `templates.json` does not match regeneration
- a first-class template directory is neither listed in the README nor present in `unlisted-allowlist.txt`

`unlisted-allowlist.txt` is how nested crash-course lessons (and a few known tree mismatches) stay out of the catalog without adding a contributing guide. Optional `tags` on each row are best-effort keyword probes; missing tags are not a failure.
