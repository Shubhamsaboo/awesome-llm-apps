# Swap workflow

Use this workflow when the user wants to swap tokens on the same chain.

Reference command syntax in `references/swap.md`.

## Flow

1. Quote.
2. Confirm with the user.
3. Execute and track status.

Don't skip the quote review step. The user needs to see output amount, fees, route, and slippage before executing.

## Quote

Always use `--all-quotes` to show all available routes so the user can compare and choose:

```bash
mm swap quote --from ETH --to USDC --amount 1 --from-chain-id 1 --all-quotes
```

Required flags: `--from`, `--to`, `--amount`, and `--from-chain-id`.

`--to-address` isn't supported for same-chain swaps. Output always goes to the signer's wallet.

Persist the quote id for execution. Show the quote to the user before execution.
Confirm source token, destination token, amount, chain, and present the following from the quote:

- Output amount — `destAssetAmount` converted to human-readable units
- Min output — `minDestAssetAmount` (worst case after slippage)
- Price impact — `priceData.priceImpact` as percentage; warn if above 1%
- Fee (USD) — `feeData.metabridge.usd`
- Slippage — `slippage` as percentage
- USD value — `priceData.totalToAmountUsd`
- Gasless relay fee — `gasIncludedBreakdown.gaslessRelayFee.usd` (only when `gasIncluded: true`)
- Route — `protocols` list

## Execute

```bash
mm swap execute --quote-id "$QUOTE_ID"
```

Prefer executing by quote ID. Re-quote-and-execute flags exist, but quote ID execution keeps the reviewed quote tied to the submitted action.

## Status

```bash
mm swap status --quote-id "$QUOTE_ID"
```

## Quote Strategies

Use `--strategy` to control how quotes are ranked. The value is a comma-separated priority list from: `cost`, `speed`, `impact`, `output`. Default is `cost,speed`.

```bash
mm swap quote --from ETH --to USDC --amount 1 --from-chain-id 1 --strategy speed,output
```

Use `--all-quotes` to show all candidate quotes for comparison (no execute prompt):

```bash
mm swap quote --from ETH --to USDC --amount 1 --from-chain-id 1 --all-quotes
```

## Gasless Swaps

Swaps can be automatically routed through a gasless relay when the wallet has insufficient native gas for the transaction. The CLI detects this and routes through the relay on supported chains. Gasless swaps trigger MFA approval flows.

## ERC-7821 Batch Execution

On eligible chains and accounts, the CLI automatically batches approval + trade into a single transaction (ERC-7821). The user sees "Approval and swap submitted as a single transaction." No flag is needed.

## Edge cases

- Quote expired: re-quote and ask the user to review the new quote. If the user previously chose a specific route, re-quote with `--all-quotes`, find the matching route by `bridgeId`/`protocols`, and execute that specific `--quote-id`. Never pass `--yes` when a specific route was requested.
- `--all-quotes` and `--yes` cannot be used together (`INVALID_SWAP_PARAMS`).
- Insufficient balance: surface the error verbatim.
- `INSUFFICIENT_GAS`: no affordable quote found. Advise the user to fund native gas, or re-quote with `--strategy output` / `--all-quotes` to find a gasless option.
- Insufficient gas: the CLI may automatically route through a gasless relay if the chain supports it. If `GASLESS_UNSUPPORTED`, advise the user to fund native gas.
- `AMOUNT_TOO_LOW` / `AMOUNT_TOO_HIGH`: the amount is outside the provider's accepted range. Adjust the amount and re-quote.
- `SLIPPAGE_TOO_HIGH` / `SLIPPAGE_TOO_LOW`: adjust `--slippage` and re-quote.
- Slippage exceeded: only increase `--slippage` if the user explicitly accepts more slippage. Always warn the user if slippage is increased above 1% that it will affect the minimum received.
- Missing chain: use `mm chains list` before guessing a chain ID.
- `UNSUPPORTED_CHAIN`: the chain does not support swaps. Run `mm chains list` and pick a chain with the `swap` feature.
- MFA required: gasless swaps and policy-protected operations require MFA approval. When stdout contains `AWAITING_MFA`, follow **MFA Approval Pauses** in `SKILL.md`; guide the user to approve via their configured auth method.
