# Perps Modify Position Workflow

Use this workflow when the user wants to modify leverage, take-profit, or stop-loss on an existing position.

Reference command syntax in `references/perps.md`.

## Flow

1. Check open positions.
2. Dry run the modification.
3. Confirm with the user and modify.

## Confirm Symbol

If the user does not mention a token symbol, list open positions and confirm with the user:

```bash
mm perps positions
```

## Check Positions

`--venue` defaults to `hyperliquid`. It can be omitted.

```bash
mm perps positions
```

## Dry Run

Preview the modification before executing:

```bash
mm perps modify --symbol BTC --leverage 10 --dry-run
mm perps modify --symbol ETH --tp 3000 --sl 2000 --dry-run
```

At least one of `--leverage`, `--tp`, or `--sl` must be provided.

## Modify

Remove `--dry-run` only after explicit user confirmation:

```bash
mm perps modify --symbol BTC --leverage 10
mm perps modify --symbol ETH --tp 3000 --sl 2000
```

Do not add `--yes` unless the user explicitly asked for unattended execution.
