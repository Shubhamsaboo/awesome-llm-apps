# Predict portfolio workflow

Use this workflow to view the Predict portfolio or redeem winning positions.

Reference command syntax in `references/predict.md`.

## View portfolio

Get a single snapshot of balance, open positions, and redeemable winnings:

```bash
mm predict portfolio --toon
```

## Redeem winnings

After a market resolves, list and claim winning positions:

```bash
mm predict redeem list --toon
```

Redeem a single position:

```bash
mm predict redeem <CONDITION_ID> --wait
```

Redeem all winning positions:

```bash
mm predict redeem --all --wait
```

`predict redeem --all` redeems every winning position. Confirm the target (condition ID or `--all`) with the user before executing. With `--wait`, the CLI polls for the redemption transaction receipt.

## View trade history

To review past trades and their settlement outcomes, see [predict-history.md](predict-history.md).
