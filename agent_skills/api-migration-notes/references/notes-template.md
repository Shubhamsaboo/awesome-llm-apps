# Migration notes template

After `scripts/oas_diff.py` prints JSON, write one `##` section per breaking change. The checker (`scripts/check_notes.py`) requires the change id and a before/after example.

Use either a heading tag or an HTML comment (both are valid; both may appear):

~~~~markdown
# Migration notes: {API title} {old version} → {new version}

{old file} → {new file}

Breaking: {n}. Additive: {n}. Deprecations: {n}.

## [BRK-001] Removed path /health
<!-- change: BRK-001 -->

**Who is affected:** Clients that call `GET /health`.

**What breaks:** The path is gone. Those requests will 404.

**What to change:** Stop calling `/health`. Use `{replacement}` if one exists.

### Before

```http
GET /health
```

### After

```http
GET /ready
```
~~~~

Rules the checker enforces:

1. Every `BRK-###` id from the differ must appear as `[BRK-###]` or `<!-- change: BRK-### -->`.
2. Ids that are not in the differ fail as `unknown`.
3. Each breaking section needs a Before label, an After label, and at least two fenced code blocks.
4. Additive (`ADD-###`) and deprecation (`DEP-###`) sections are optional. If present, their ids must still be known.

Suggested body for every breaking section:

- Who is affected (which clients, which operation)
- What breaks
- Before request and/or response
- After request and/or response
- The exact client change
