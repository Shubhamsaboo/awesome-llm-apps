# Perps Close Position Workflow

Use this workflow when the user wants to close a perpetual position.

Reference command syntax in `references/perps.md`.

## Flow

1. Check open positions.
2. Dry run the close.
3. Confirm with the user and close.

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

Preview the close before executing:

```bash
mm perps close --symbol BTC --dry-run
```

For partial close, include `--size <amount>`.

## Close

Remove `--dry-run` only after explicit user confirmation:

```bash
mm perps close --symbol BTC
mm perps close --symbol BTC --size 0.005
```

`--all` closes every open position. Require explicit confirmation that the user wants all positions closed.

```bash
mm perps close --all
```

Do not add `--yes` unless the user explicitly asked for unattended execution.
