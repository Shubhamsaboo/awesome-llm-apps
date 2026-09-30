# Swap & Bridge Commands

Use the `swap` commands to perform same-chain token swaps or cross-chain bridges. When `--from-chain-id` and `--to-chain-id` differ, the CLI automatically routes through a bridge.

## `swap quote` Command

Get a swap or bridge quote showing expected output, fees, and route.

### Syntax

```bash
mm swap quote --from <token> --to <token> --amount <amount> --from-chain-id <chain-id> [--to-chain-id <chain-id>] [--to-address <address>] [--slippage <percent>] [--refuel] [--strategy <priorities>] [--all-quotes] [--yes] [--wallet-timeout <seconds>] [--password <password>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--from` | Yes | Source token symbol, such as ETH, POL, or USDC |
| `--to` | Yes | Destination token symbol, such as USDC or USDT |
| `--amount` | Yes | Human-readable amount to swap, such as 0.5 or 100 |
| `--from-chain-id` | Yes | Source EVM chain ID, such as 1 for Ethereum or 137 for Polygon |
| `--to-chain-id` | No | Destination EVM chain ID. Defaults to `--from-chain-id` for same-chain swaps |
| `--to-address` | No | Recipient address for bridged output tokens. Only valid for cross-chain swaps. Defaults to the signer's wallet |
| `--slippage` | No | Maximum slippage as a percentage, 0-100. Defaults to 0.5 |
| `--refuel` | No | Bundle a small destination native-gas top-up into a cross-chain quote. Only valid when `--to-chain-id` differs from `--from-chain-id`. See [Refuel](#refuel) |
| `--strategy` | No | Quote ranking priority as a comma-separated list. Options: `cost` for lowest total cost, `speed` for fastest execution, `impact` for lowest price impact, `output` for highest output amount. Default: `cost,speed`. First value is the primary sort key |
| `--all-quotes` | No | Show all candidate quotes, not just the recommended one. Compare-only, no execute prompt |
| `--yes` | No | Skip interactive confirmation and execute immediately after quoting |
| `--wallet-timeout` | No | Seconds to wait per wallet job including MFA and signing, max 600. Overrides config `walletTimeoutSeconds` |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |

### Example

```bash
mm swap quote --from ETH --to USDC --amount 0.5 --from-chain-id 1
mm swap quote --from USDC --to USDT --amount 100 --from-chain-id 137
mm swap quote --from ETH --to USDC --amount 1 --from-chain-id 1 --to-chain-id 137
mm swap quote --from ETH --to USDC --amount 0.5 --from-chain-id 1 --slippage 1
mm swap quote --from ETH --to pUSD --amount 0.5 --from-chain-id 1 --to-chain-id 137 --to-address 0x742d...f2bD18
mm swap quote --from ETH --to USDC --amount 1 --from-chain-id 1 --to-chain-id 42161 --refuel
mm swap quote --from ETH --to USDC --amount 1 --from-chain-id 1 --strategy speed,output
mm swap quote --from ETH --to USDC --amount 1 --from-chain-id 1 --all-quotes
mm swap quote --from ETH --to USDC --amount 1 --from-chain-id 1 --yes
```

## Unavailable Quote

When the bridge returns zero routes for an actionable reason, `mm swap quote` returns a soft unavailable outcome with exit code 0 instead of failing. The JSON output has this shape:

```json
{
  "kind": "unavailable",
  "reason": "<reason>",
  "message": "<explanation>",
  "hint": "<suggested fix>"
}
```

Possible `reason` values:

| Reason | Meaning | Suggested action |
| --- | --- | --- |
| `NO_QUOTES` | No routes found for this request | Try a different token pair or route |
| `AMOUNT_TOO_HIGH` | Amount too high for available liquidity | Lower `--amount` |
| `AMOUNT_TOO_LOW` | Amount below the provider minimum | Increase `--amount` |
| `SLIPPAGE_TOO_HIGH` | Slippage too high | Lower `--slippage` |
| `SLIPPAGE_TOO_LOW` | Slippage too low | Increase `--slippage` |
| `TOKEN_NOT_SUPPORTED` | Token not supported for this route | Try a different token |
| `RWA_GEO_RESTRICTED` | This asset is restricted in your region | N/A |
| `RWA_NATIVE_TOKEN_UNSUPPORTED` | This RWA can't be traded against the native token | Use a non-native token |
| `RWA_MARKET_UNAVAILABLE` | This RWA market is currently unavailable | Retry later |

When you receive an unavailable outcome, surface the `message` and `hint` to the user and suggest adjusting the parameters per the table above. Do not treat this as an error. Only `QUOTE_RETRY`, a transient bridge hiccup, is a hard error with exit 1 — re-run the same quote to retry.

## Quote Presentation

When presenting a quote to the user, always show these fields:

| Field | Source | Description |
| --- | --- | --- |
| Output amount | `destAssetAmount`, convert from atomic units using `destAsset.decimals` | Expected destination token amount |
| Min output | `minDestAssetAmount`, convert from atomic units | Minimum received after slippage |
| Price impact | `priceData.priceImpact` as a percentage | How much the trade moves the pool price. Warn if above 1% |
| Fee (USD) | `feeData.metabridge.usd` | MetaBridge fee in USD |
| Slippage | `slippage` as a percentage | Maximum slippage tolerance |
| USD value | `priceData.totalToAmountUsd` | Estimated USD value of the output |
| Gasless relay fee | `gasIncludedBreakdown.gaslessRelayFee.usd` | Relay fee in USD. Only present when `gasIncluded` or `gasIncluded7702` is `true` |
| Route | `protocols` | DEX or aggregators used |
| Fee tier | `tierName` or `vipTier` | VIP fee tier name or level, when available |
| Warnings | `warnings` | Any CLI warnings, such as low swap value |

Show the gasless relay fee only when present, `gasIncluded: true`. Show the fee tier only when `tierName` or `vipTier` is present. The fee bps shown in `quoteBpsFee` may reflect VIP-discounted rates rather than the base rate in `baseBpsFee`.

When presenting multiple quotes (`--all-quotes`):

1. Show a summary comparison table with route, output amount, relay fee (if gasless), and price impact for all quotes. Mark the recommended quote.
2. Show the full detail breakdown (all fields above) for the recommended quote.
3. If the user picks a different route, show its full details before executing.

## `swap execute` Command

Execute a swap or bridge, either by referencing a previous quote ID or by providing parameters for an automatic re-quote and execute.

### Syntax

```bash
mm swap execute --quote-id <id> [--wallet-timeout <seconds>] [--password <password>]
mm swap execute --from <token> --to <token> --amount <amount> --from-chain-id <chain-id> [--to-chain-id <chain-id>] [--to-address <address>] [--slippage <percent>] [--refuel] [--strategy <priorities>] [--wallet-timeout <seconds>] [--password <password>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--quote-id` | Yes (unless re-quote args given) | Quote ID returned by `mm swap quote`. If omitted, provide `--from`, `--to`, `--amount`, and `--from-chain-id` to re-quote |
| `--from` | Yes (unless `--quote-id`) | Source token symbol |
| `--to` | Yes (unless `--quote-id`) | Destination token symbol |
| `--amount` | Yes (unless `--quote-id`) | Amount to swap |
| `--from-chain-id` | Yes (unless `--quote-id`) | Source EVM chain ID |
| `--to-chain-id` | No | Destination EVM chain ID. Defaults to `--from-chain-id` for same-chain swaps |
| `--to-address` | No | Recipient address for bridged output tokens. Only valid for cross-chain swaps. Defaults to the signer's wallet. Persisted quotes retain the recipient for `--quote-id` execution |
| `--slippage` | No | Maximum slippage as a percentage, 0-100. Defaults to 0.5 |
| `--refuel` | No | Bundle a destination native-gas top-up into a cross-chain re-quote. Only valid when `--to-chain-id` differs from `--from-chain-id`. Ignored when executing by `--quote-id` because the persisted quote already carries the flag. See [Refuel](#refuel) |
| `--strategy` | No | Quote ranking priority for re-quote mode, comma-separated: cost, speed, impact, output. Default: `cost,speed`. Ignored when executing by `--quote-id` |
| `--wallet-timeout` | No | Seconds to wait per wallet job including MFA and signing, max 600. Overrides config `walletTimeoutSeconds` |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |

### Validation Rules

- Either `--quote-id` OR the full set of re-quote flags (`--from`, `--to`, `--amount`, `--from-chain-id`) must be provided.
- When `--quote-id` is given, re-quote flags are ignored.
- `--all-quotes` and `--yes` cannot be used together on `swap quote`. Returns `INVALID_SWAP_PARAMS`.

### Example

```bash
mm swap execute --quote-id <quote-id>
mm swap execute --from ETH --to USDC --amount 0.5 --from-chain-id 1
mm swap execute --from USDC --to USDT --amount 100 --from-chain-id 137 --to-chain-id 137 --slippage 1
```

## `swap status` Command

Check the status of a previously executed swap or bridge by its quote ID.

### Syntax

```bash
mm swap status --quote-id <id> [--tx-hash <hash>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--quote-id` | Yes | Quote ID returned by `mm swap quote` |
| `--tx-hash` | No | Source transaction hash. Overrides the stored hash from execute |

### Example

```bash
mm swap status --quote-id <quote-id>
mm swap status --quote-id <quote-id> --tx-hash 0xabc...123
```

## Refuel

Refuel bundles a small amount of the destination chain's native gas token into a cross-chain quote, so the recipient lands with gas to spend even if they arrive with a zero native balance. This is useful when bridging to a chain where the recipient holds none of the gas token, such as bridging USDC to Arbitrum with no ETH there.

- Opt-in only. Refuel is never enabled automatically — pass `--refuel` to request it.
- Cross-chain only. `--refuel` is only meaningful when `--to-chain-id` differs from `--from-chain-id`. It has no effect on same-chain swaps.
- Not for native-asset destinations. Do not use `--refuel` when the destination token is the destination chain's native gas asset, such as bridging ETH from Base into ETH on Arbitrum. There is nothing to top up, and the backend returns 0 quotes for the route — surfaced as a `NO_QUOTES` error. Only use `--refuel` when bridging into a non-native token such as USDC.
- Best-effort. Only some bridge aggregators offer a gas top-up. When `--refuel` is set, the CLI prefers a quote that includes the top-up; if no aggregator offers one for that route, it falls back to the best regular quote (no error).
- Output. When a refuel-bearing quote is selected, the quote includes a `refuel` step describing the native-gas top-up with source amount spent and destination native amount received, and the resolved request shows `refuel: true`.

```bash
# Bridge USDC to Arbitrum and top up ETH for gas on arrival
mm swap quote --from USDC --to USDC --amount 50 --from-chain-id 1 --to-chain-id 42161 --refuel
```

## Expired Quotes and User-Selected Routes

When the user has chosen a specific route, such as "use Across", and the original quote expires before execution:

1. Never pass `--yes` on a re-quote. It executes the recommended quote, which may differ from the user's chosen route.
2. Re-quote with `--all-quotes` to get fresh quotes from all routes.
3. Find the quote matching the user's chosen route by `bridgeId` or `protocols`.
4. Execute with that specific `--quote-id`.
5. If the chosen route is no longer available in the new quotes, inform the user and ask them to pick from the available options.

## Notes

- If the chain is not mentioned by the user, ask for the chain.
- Use `mm chains list` to discover supported chain IDs.
- Same-chain swap: omit `--to-chain-id`, which defaults to `--from-chain-id`.
- Cross-chain bridge: set `--to-chain-id` to a different chain than `--from-chain-id`. The CLI automatically routes through a bridge.
- The typical flow is: `mm swap quote` to preview, then `mm swap execute --quote-id <id>` to submit.
- You can skip the quote step by passing all swap parameters directly to `mm swap execute`.
- Use `mm swap status --quote-id <id>` to track progress after execution.
- If the user asks to "bridge" tokens, use the `swap` commands with different `--from-chain-id` and `--to-chain-id` values.
- If the user is bridging to a chain where they hold no native gas token, suggest `--refuel` to top up gas on the destination (cross-chain only). See [Refuel](#refuel).
- After execution, track swap progress with `mm swap status --quote-id <id>`.
- Swaps can be automatically routed through a gasless relay when the wallet has insufficient native gas. The CLI detects this and routes through the relay on supported chains. If the chain does not support gasless relay, the CLI returns `GASLESS_UNSUPPORTED`.
- If the MFA/signing step times out during a gasless relay swap, the CLI returns `RELAY_TIMEOUT`, not `SWAP_ERROR`, with a recovery hint to run `mm wallet requests watch <polling-id>` — the job may still complete. For sequential multi-leg swaps, `JOB_TIMEOUT` is returned instead. The gasless relay respects `--wallet-timeout`, default 10 minutes.
- Use `--strategy` to control quote ranking priority, such as `speed,output` to prioritize speed then output amount.
- ERC-7821 batch execution: on eligible chains and accounts, the CLI automatically batches approval + trade into a single `execute()` transaction. The user sees "Approval and swap submitted as a single transaction." No flag is needed — this is automatic when supported.
- Intelligent quote selection: the CLI automatically skips quotes the wallet cannot cover gas for and prefers gasless (EIP-7702) quotes when native balance is low. If no affordable quote exists, `INSUFFICIENT_GAS` is returned with guidance to add native gas or use `--strategy output` / `--all-quotes` to find a gasless option.
