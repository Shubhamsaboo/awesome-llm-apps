# Market Data Workflow

Use this workflow when the user wants to look up token prices, discover tokens, or explore market data.

Reference command syntax in `references/market-data.md`.

## Find a Token

If the user mentions a token by name or symbol, search for it first to get the correct asset ID:

```bash
mm token list search "USDC" --chain-ids 1
```

To browse popular, trending, or top-gainer tokens on a chain:

```bash
mm token list popular --chain-id 1
mm token list trending --chain-id 1
mm token list top-gainer --chain-id 1
```

Use `mm token networks` to discover which chains support token data.

## Get Token Metadata

Once you have the CAIP-19 asset ID, fetch detailed metadata:

```bash
mm token assets --asset-ids "eip155:1/erc20:0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48" --include-market-data --include-token-security-data
```

## Get Spot Price

Fetch the current price for one or more tokens:

```bash
mm price spot --asset-ids "eip155:1/slip44:60"
mm price spot --asset-ids eip155:1
mm price spot --asset-ids "eip155:1/slip44:60,eip155:137/slip44:966" --vs eur --market-data
```

Use `mm price networks` to discover supported CAIP-2 chain IDs and `mm price currencies` to list quote currencies.

## Get Historical Price

Fetch historical price data for an asset:

```bash
mm price history --chain-id eip155:1 --time-period 7d --interval daily
mm price history --chain-id eip155:1 --asset-type slip44:60 --time-period 7d --interval daily
```

Common time periods: `1d`, `7d`, `30d`, `2M`, `1y`, `3y`. Intervals: `5m`, `15m`, `30m`, `hourly`, `daily`.

For a custom date range, use `--from` and `--to` with Unix timestamps instead of `--time-period`.

## Edge Cases

- If the chain is not mentioned by the user, ask for the chain.
- Use `mm chains list` to discover supported chain IDs.
- If a token search returns no results, try broader chains or alternate names.
- CAIP-19 asset IDs follow the format `eip155:<chainId>/slip44:<coinType>` for native tokens or `eip155:<chainId>/erc20:<contractAddress>` for ERC-20s.
- On `mm price spot`, a bare CAIP-2 chain id such as `eip155:1` is accepted and expands to the native asset. `mm token assets` still requires a full CAIP-19 id.
- On `mm price history`, omit `--asset-type` to use the chain's native asset.
- Use `--include-token-security-data` on `token assets` to surface scam or risk signals before the user trades an unfamiliar token.
