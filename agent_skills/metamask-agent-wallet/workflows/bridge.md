# Bridge workflow

Use this workflow when the user wants to bridge tokens across chains.

Reference command syntax in `references/swap.md`. The CLI uses the same `swap` commands for bridging. Set `--to-chain-id` to a different chain than `--from-chain-id`.

## Flow

1. Quote.
2. Confirm with the user.
3. Execute and track status.

Don't skip the quote review step. The user needs to see output amount, fees, route, and slippage before executing.

## Quote

Always use `--all-quotes` to show all available routes so the user can compare and choose:

```bash
mm swap quote --from ETH --to USDC --amount 1 --from-chain-id 1 --to-chain-id 137 --all-quotes
```

Required flags: `--from`, `--to`, `--amount`, `--from-chain-id`, and `--to-chain-id`.

If the user wants the bridged tokens sent to a different wallet on the destination chain, add `--to-address`:

```bash
mm swap quote --from ETH --to USDC --amount 1 --from-chain-id 1 --to-chain-id 137 --to-address 0x742d...f2bD18
```

If the recipient may have no native gas on the destination chain, add `--refuel` to bundle a destination gas top-up into the quote (cross-chain only, opt-in, best-effort — see `references/swap.md`). Do not add `--refuel` when the destination token is the destination chain's native gas asset (e.g. bridging into ETH on Arbitrum) — the backend returns 0 quotes in that case:

```bash
mm swap quote --from USDC --to USDC --amount 50 --from-chain-id 1 --to-chain-id 42161 --refuel
```

Persist the quote id for execution. Show the quote to the user before execution.
Confirm source token, destination token, amount, source chain, destination chain, recipient address (if `--to-address` was set), destination gas top-up (if `--refuel` was set), and present the following from the quote:

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
mm swap execute --quote-id "QUOTE_ID"
```

Prefer executing by quote ID. Re-quote-and-execute flags exist, but quote ID execution keeps the reviewed quote tied to the submitted action.

## Status

```bash
mm swap status --quote-id "QUOTE_ID"
mm swap status --quote-id "QUOTE_ID" --tx-hash 0xabc123
```

Use status polling for bridges where the destination side can lag behind the source transaction.

## ERC-7821 Batch Execution

On eligible chains and accounts, the CLI automatically batches approval + trade into a single transaction (ERC-7821). The user sees "Approval and swap submitted as a single transaction." No flag is needed.

## Edge cases

- Quote expired: re-quote and ask the user to review the new quote. If the user previously chose a specific route, re-quote with `--all-quotes`, find the matching route by `bridgeId`/`protocols`, and execute that specific `--quote-id`. Never pass `--yes` when a specific route was requested.
- `--all-quotes` and `--yes` cannot be used together (`INVALID_SWAP_PARAMS`).
- Insufficient balance: surface the error verbatim.
- `INSUFFICIENT_GAS`: no affordable quote found. Advise the user to fund native gas, or re-quote with `--strategy output` / `--all-quotes` to find a gasless option.
- Slippage exceeded: only increase `--slippage` if the user explicitly accepts more slippage. Always warn the user if slippage is increased above 1% that it will affect the minimum received.
- Missing chain: use `mm chains list` before guessing a chain ID.
- `REFUEL_UNSUPPORTED_ROUTE`: `--refuel` was used on a same-chain swap or when the destination token is the native gas asset. Drop `--refuel` and re-quote.
- Refuel into a native asset: if `--refuel` is set and the destination token is the destination chain's native gas asset, the CLI returns `REFUEL_UNSUPPORTED_ROUTE`. Re-quote without `--refuel`.
- `AMOUNT_TOO_LOW` / `AMOUNT_TOO_HIGH`: the amount is outside the provider's accepted range. Adjust the amount and re-quote.
- `UNSUPPORTED_CHAIN`: the chain does not support swaps. Run `mm chains list` and pick a chain with the `swap` feature.
- Insufficient gas: the CLI may automatically route through a gasless relay if the chain supports it (on supported chains). If `GASLESS_UNSUPPORTED`, advise the user to fund native gas.
- MFA required: gasless bridge operations require MFA approval. When stdout contains `AWAITING_MFA`, follow **MFA Approval Pauses** in `SKILL.md`; guide the user to approve via their configured auth method.
