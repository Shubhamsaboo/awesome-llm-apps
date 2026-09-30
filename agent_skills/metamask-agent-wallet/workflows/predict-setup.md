# Predict setup workflow

Use this workflow for first-time Predict setup, refreshing credentials, or repairing approvals.

Reference command syntax in `references/predict.md`.

## Flow

1. Choose Predict mode.
2. Run one-time setup.
3. Verify status.

## Choose mode

```bash
mm predict mode mainnet
```

Replace `mainnet` with `testnet` if the user wants to paper trade.

## Run setup

```bash
mm predict setup --wait
```

This blocks until credential, deposit-wallet, and approval jobs complete. Without `--wait`, track returned jobs with `mm predict watch --id <JOB_ID> --wait`.

The owner EOA needs POL on Polygon for gas to complete the setup transactions.

Polymarket is geoblocked in some regions. `predict setup` checks the caller's IP first and aborts with `PREDICT_GEOBLOCKED` before any wallet interaction if the region is restricted. Polymarket HTTP 451 maps to `PREDICT_UNAVAILABLE_FOR_LEGAL_REASONS` instead of generic `PREDICT_ERROR`. To check region status independently:

```bash
mm predict geoblock
```

## Verify status

Confirm `setupComplete` is `true` and note the deposit wallet address:

```bash
mm predict status
```

## Refresh credentials or approvals

If credentials or approvals look stale later:

```bash
mm predict auth --refresh
mm predict approve --wait
```

Then verify with `mm predict status`.
