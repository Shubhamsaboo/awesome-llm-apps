# Predict markets workflow

Use this workflow to search, browse, and inspect prediction markets on Polymarket.

Reference command syntax in `references/predict.md`.

## Flow

1. Search or browse markets.
2. Inspect the selected market to get outcome token IDs.

## Search markets

```bash
mm predict markets search "Knicks NBA Finals" --limit 5 --toon
```

Search can return loosely related markets, so always inspect the selected market before quoting.

If search is noisy, list active markets and filter manually:

```bash
mm predict markets list --active --limit 50 --toon
```

## Browse by topic

Use events, series, and tags to browse by topic. Resolve a tag slug or ID first, then filter:

```bash
mm predict tags list --limit 50 --toon
mm predict events list --tag-slug sports --active --limit 10 --toon
mm predict events get <EVENT_SLUG_OR_ID> --toon
mm predict series list --recurrence weekly --limit 10 --toon
```

These browse commands don't return outcome token IDs. Drill into a specific market with `mm predict markets get` before quoting or placing.

## Inspect a market

```bash
mm predict markets get --market <MARKET_SLUG_OR_ID> --toon
```

The market detail prints outcome token IDs. Outcome token IDs aren't market IDs. Use the token ID for `quote`, `place`, `book`, and `balance --token-id`.
