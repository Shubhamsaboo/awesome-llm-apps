# Research report schema

The validator accepts one UTF-8 JSON object with these fields:

```json
{
  "question": "What is being investigated?",
  "searched_at": "2026-08-15",
  "providers": ["host_web_search", "host_page_open", "scholar_search_mixed"],
  "unavailable_providers": [],
  "sources": [
    {
      "id": "s1",
      "url": "https://example.org/primary-study",
      "publisher": "Example Institute",
      "source_type": "primary"
    }
  ],
  "claims": [
    {
      "id": "c1",
      "text": "A bounded, checkable claim.",
      "kind": "sourced",
      "confidence": "low",
      "source_ids": ["s1"],
      "independent_source_count": 1,
      "conflict": false
    }
  ],
  "gaps": ["Independent replication is not available."]
}
```

## Rules

- `question` and `searched_at` are non-empty strings.
- `providers` contains the actual capability names used, including native host
  tools, and at least two unique names. Repeated queries through one capability
  still count once. Record unavailable capabilities separately.
- Each source has a unique ID, an HTTP(S) URL, a publisher, and a
  `source_type` of `primary`, `secondary`, or `aggregator`.
- Each claim has a unique ID, non-empty text, `kind` of `sourced` or
  `inference`, confidence of `high`, `medium`, or `low`, one or more valid
  `source_ids`, and a non-negative integer `independent_source_count`.
- High confidence requires at least three independent sources; medium requires
  at least two; low requires at least one.
- Set `conflict` to `true` when credible evidence disagrees. A conflicting
  claim cannot be high confidence.
- `gaps` is an array of non-empty strings.

The validator checks internal consistency only. It does not fetch URLs, judge
credibility, detect hidden common sources, or prove claims true.
