# Perps open position workflow

Use this workflow when the user wants to open a new perpetual position.

Reference command syntax in `references/perps.md`.

## Flow

1. Check balance and deposit if needed.
2. Quote the position.
3. Dry run.
4. Confirm with the user and open.

## Confirm symbol

If the user doesn't mention a token symbol, list available markets and confirm with the user:

```bash
mm perps markets
```

## Check balance

`--venue` defaults to `hyperliquid`. You can omit it.

```bash
mm perps balance
```

If available margin is zero or insufficient, deposit USDC before proceeding. Hyperliquid only supports deposits from Arbitrum mainnet (`eip155:42161`).

Check the user's Arbitrum balance for USDC and ETH (for gas).

```bash
mm wallet balance --chain-ids 42161
```

### No ETH and no USDC on Arbitrum

Inform the user that ETH on Arbitrum is required for gas. Without ETH, no on-chain transaction is possible. Bridge from another chain.

```bash
mm swap quote --from <TOKEN> --to ETH --amount 0.001 --from-chain-id <SOURCE_CHAIN_ID> --to-chain-id 42161
mm swap execute --quote-id "$QUOTE_ID" # quote ID from the swap quote command
```

Once the user has ETH for gas, swap or bridge to get USDC on Arbitrum.

```bash
mm swap quote --from <TOKEN> --to USDC --amount <AMOUNT> --from-chain-id <SOURCE_CHAIN_ID> --to-chain-id 42161
mm swap execute --quote-id "$QUOTE_ID" # quote ID from the swap quote command
```

### Has ETH or another token on Arbitrum (but no USDC)

Swap to USDC on Arbitrum.

```bash
mm swap quote --from <TOKEN> --to USDC --amount <AMOUNT> --from-chain-id 42161
mm swap execute --quote-id "$QUOTE_ID" # quote ID from the swap quote command
```

### Has ETH and USDC on Arbitrum

Deposit USDC directly into Hyperliquid.

```bash
mm perps deposit --amount <AMOUNT> --asset USDC
```


## Quote

Always quote before opening:

```bash
mm perps quote --symbol BTC --side long --size 0.01 --leverage 5
```

Show the user estimated entry, notional, fees, liquidation price, side, size, leverage, and venue before proceeding.

## Dry run

Preview the order before signing:

```bash
mm perps open --symbol BTC --side long --size 0.01 --leverage 5 --dry-run
```

For limit orders, include `--type limit --limit-px <price>`.

`--max-slippage-bps` is the slippage cap in basis points for IOC market pricing.

## Open

Remove `--dry-run` only after explicit user confirmation:

```bash
mm perps open --symbol BTC --side long --size 0.01 --leverage 5
```

Don't add `--yes` unless the user explicitly asked for unattended execution.
