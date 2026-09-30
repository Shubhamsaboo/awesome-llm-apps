# Predict history workflow

Use this workflow to review closed Predict positions, past trades, and redemptions.

Reference command syntax in `references/predict.md`.

## Modes

`mm predict history` has three modes selected by `--type`, and several flags are only valid in some of them. Pick the mode first, then the flags.

| Mode | Rows | Flags allowed on top of `--limit` / `--offset` / `--sort-direction` |
| --- | --- | --- |
| `closed`, the default | Closed positions with realized PnL | `--sort-by realizedpnl\|title\|price\|avgprice\|timestamp`. `--limit` max 50 |
| `trade` | Trade fills | `--sort-by timestamp\|tokens\|cash`, `--side buy\|sell`, `--start`, `--end` |
| `redeem` | Redeem claims | `--sort-by timestamp\|tokens\|cash`, `--start`, `--end` |

Passing a flag outside its mode is a hard error, not a silent ignore: `--side` on closed or redeem returns `INVALID_SIDE`, `--start` / `--end` on closed returns `INVALID_INPUT`, and a cross-mode `--sort-by` returns `INVALID_SORT_BY`.

## List closed positions

```bash
mm predict history --toon
```

Closed rows carry realized PnL, average entry price, settlement price, and size.

## List trades

```bash
mm predict history --type trade --toon
```

Each trade row includes a settlement `result` (`won`, `lost`, or `pending`) and, if redeemed, the `amountWon` payout. Use `--side buy` or `--side sell` to filter by direction.

## List redemptions

```bash
mm predict history --type redeem --toon
```

## Inspect a specific market

Drill into history for a single condition:

```bash
mm predict history get <CONDITION_ID> --toon
mm predict history get <CONDITION_ID> --type redeem --toon
```

## Paginate results

When `hasMore` is `true`, use the next-page hint from the CLI output:

```bash
mm predict history --limit 50 --offset 50 --toon
mm predict history --type trade --limit 100 --offset 100 --toon
```

## Filter by time range

Unix timestamps scope the window, and only for `--type trade` or `--type redeem`:

```bash
mm predict history --type trade --start 1719792000 --end 1719878400 --toon
```

## Sort results

```bash
mm predict history --sort-by realizedpnl --sort-direction desc --toon
mm predict history --type trade --sort-by cash --sort-direction desc --toon
```
