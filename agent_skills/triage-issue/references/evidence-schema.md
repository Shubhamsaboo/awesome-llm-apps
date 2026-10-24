# Evidence Schema

Load this when reading telemetry. One shape for GCP and AWS, so the rubric and
the golden set stay vendor-neutral.

## Get a bundle

```bash
gcloud logging read '<filter>' --format=json | \
  python scripts/normalize_evidence.py - --symptom "checkout 500s" -o bundle.json

aws logs get-query-results --query-id <id> > raw.json
python scripts/normalize_evidence.py raw.json -o bundle.json
```

The vendor is auto-detected from the payload shape; pass `--vendor` to override.

## Shape

```json
{
  "vendor": "gcp | aws",
  "query": "the query that produced these logs",
  "symptom": "one line on what looks wrong",
  "symptom_window": {"start": "ISO-8601 UTC", "end": "ISO-8601 UTC"},
  "entry_count": 5,
  "severity_counts": {"ERROR": 3, "WARN": 2},
  "trace_ids": ["7f3a9c1e88"],
  "services": ["checkout"],
  "deploys": [{"ts": "...", "ref": "svc@1.2.3", "note": "..."}],
  "links": [{"url": "https://console.cloud.google.com/logs/query;...", "label": "the failing trace"}],
  "code": [{"path": "checkout/orders/repository.py", "ref": "4f2a9c1",
            "start_line": 18, "text": "class OrderRepository:\n    ..."}],
  "entries": [
    {
      "ts": "2026-09-18T14:02:11.123456+00:00",
      "severity": "DEBUG | INFO | WARN | ERROR | CRITICAL",
      "service": "checkout",
      "message": "HikariPool-1 - Connection is not available…",
      "trace_id": "7f3a9c1e88",
      "attributes": {"http_status": 500, "env": "staging"}
    }
  ]
}
```

Every entry has the same six keys on every vendor. Vendor-specific fields land
in `attributes` rather than being dropped.

`links` and `code` are what an RCA may cite, and both are optional. A link must
parse (`scripts/log_links.py`); `start_line` is the real line number of the
snippet's first line, so `path:line` citations can be checked. Attach them with
`--link URL[|label]` and `--code path[:start-end][@ref]`. Grounding grades the
citations; see `grounding.md`.

## What each adapter maps from

| Normalized | GCP | AWS |
|---|---|---|
| `ts` | `timestamp` | `@timestamp`, or epoch ms |
| `severity` | `severity` | `level`, else inferred from the message |
| `service` | `resource.labels.container_name` | `@logStream` |
| `message` | `jsonPayload.message`, `textPayload` | `@message` |
| `trace_id` | `trace` (prefix stripped) | `traceId` |

`projects/<p>/traces/<id>` is reduced to `<id>`, so the same trace correlates
across vendors.

## Reading a bundle

- **Start at the first non-retryable ERROR**, not the loudest one. Routing and the
  causal chain both hinge on which error came first.
- **Use `trace_ids` to group.** One trace showing the whole request beats fifty
  unrelated error lines.
- **Check `deploys` against `symptom_window`.** An empty `deploys` list is
  evidence too: it rules out a deploy trigger.
- **Treat `attributes` as load-bearing.** `rows_examined` vs `rows_returned`, or
  `duration_ms` across sibling spans, is usually where the mechanism shows up.
- **Never cite an entry that is not in the bundle.** `ev_no_fabrication` fails the
  whole RCA for one invented log line, and rightly so.

## Truncation

`render_evidence()` ranks CRITICAL → ERROR → WARN → INFO → DEBUG before
truncating, and reports how many entries it dropped. Errors survive; heartbeat
noise does not. If you need more than the default 40 entries, raise
`max_entries` rather than pre-filtering, so the drop stays visible.

## When the bundle is empty

An empty or missing bundle is not a thin RCA — it is the
`insufficient_evidence` path. Load `references/intake-ticket.md` and produce an
evidence request with the query to run.
