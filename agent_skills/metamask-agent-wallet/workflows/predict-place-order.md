# Predict place order workflow

Use this workflow to quote and place a prediction market order.

Reference command syntax in `references/predict.md`.

## Flow

1. Check setup and balance.
2. Inspect the market to get the outcome token ID.
3. Quote the order.
4. Confirm with the user and place.

## Check setup and balance

Verify that Predict is fully set up and get the deposit wallet address:

```bash
mm predict status
```

Check `setupComplete` is `true`. If not, follow `predict-setup.md` to run first-time setup.

Then check the deposit wallet balance:

```bash
mm predict balance --sync
```

If the balance is zero or insufficient for the order, follow `predict-funding.md` to deposit funds. Use the deposit wallet address from `mm predict status` when funding.

## Get outcome token ID

If the user hasn't already identified the market, follow `predict-markets.md` to find and inspect it.

```bash
mm predict markets get --market <MARKET_SLUG_OR_ID> --toon
```

Map the user's intended outcome to the correct token ID from the market detail.

## Quote

Preview the order cost and fill before placing:

```bash
mm predict quote \
  --token-id <OUTCOME_TOKEN_ID> \
  --side buy --size 100 --limit-price 0.55
```

Show the user the estimated cost and fill.

## Place

After the user confirms token ID, outcome, side, size, price, and order type:

```bash
mm predict place \
  --token-id <OUTCOME_TOKEN_ID> \
  --side buy --size 100 --price 0.55 \
  --order-type GTC
```

`--order-type` is one of `GTC`, `GTD`, `FOK`, or `FAK`. `--post-only` only applies to GTC/GTD. `--expiration` is unix seconds for GTD.

## Safety notes

- Placing orders between a market's end date and its final UMA resolution carries major financial risk. Prices during this window don't reflect true odds and arbitrage strategies can fail if UMA resolves unexpectedly. If the order creation time is after the market end date but before UMA resolution, warn the user about potential financial loss and get explicit confirmation before proceeding.
- Prices are 0-1 floats. Treat `--price 1` as suspicious unless the user explicitly confirms.
- Trades are signed by the deposit wallet address from `mm predict status`, not the connected owner EOA.
- Always inspect the market to map the user's intended outcome to the correct token ID.
