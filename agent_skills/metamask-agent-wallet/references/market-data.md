# Market Data Commands

Use `price` and `token` commands for read-only token metadata, token discovery, and price data.

## `price spot` Command

Fetch spot prices for one or more CAIP-19 assets.

### Syntax

```bash
mm price spot --asset-ids <asset-ids> [--vs <currency>] [--market-data]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--asset-ids` | Yes | Comma-separated CAIP-19 asset IDs. A bare CAIP-2 chain id such as `eip155:1` auto-completes to that chain's native asset (`eip155:1/slip44:60`). Malformed ids return `INVALID_ASSET_ID` |
| `--vs` | No | Quote currency. Defaults to `usd` |
| `--market-data` | No | Include market cap, supply, and change percent |

### Example

```bash
mm price spot --asset-ids "eip155:1/slip44:60,eip155:137/slip44:966"
mm price spot --asset-ids eip155:1
mm price spot --asset-ids "eip155:1/slip44:60" --vs eur
mm price spot --asset-ids "eip155:1/slip44:60" --market-data
```

## `price history` Command

Fetch historical prices for an asset.

### Syntax

```bash
mm price history --chain-id <caip2-chain-id> [--asset-type <asset-type>] [--time-period <period>] [--interval <interval>] [--from <unix>] [--to <unix>] [--vs <currency>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--chain-id` | Yes | CAIP-2 chain ID, such as `eip155:1`. Run `mm price networks` to see supported chains |
| `--asset-type` | No | CAIP-19 asset type, such as `slip44:60` for ETH or `erc20:0x...` for ERC-20 tokens. Defaults to the chain's native asset. Invalid types return `INVALID_ASSET_ID` |
| `--time-period` | No | Time period, such as `1d`, `7d`, `30d`, `2M`, `1y`, or `3y` |
| `--interval` | No | Sampling interval: `5m`, `15m`, `30m`, `hourly`, or `daily` |
| `--from` | No | Start time as a Unix timestamp in seconds. Use with `--to` instead of `--time-period` for custom ranges |
| `--to` | No | End time as a Unix timestamp in seconds. Use with `--from` instead of `--time-period` for custom ranges |
| `--vs` | No | Quote currency code. Defaults to `usd`. Run `mm price currencies` to see options |

### Example

```bash
mm price history --chain-id eip155:1 --time-period 7d --interval daily
mm price history --chain-id eip155:1 --asset-type slip44:60 --time-period 7d --interval daily
```

## `price currencies` Command

List supported quote currencies.

### Syntax

```bash
mm price currencies
```

### Example

```bash
mm price currencies
```

## `price networks` Command

List CAIP-2 networks supported by the price API.

### Syntax

```bash
mm price networks
```

### Example

```bash
mm price networks
```

## `token list` Commands

List popular, trending, or top-gainer tokens.

### Syntax

```bash
mm token list popular [--chain-id <chain>]
mm token list trending [--chain-id <chain>]
mm token list top-gainer [--chain-id <chain>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--chain-id` | No | Chain id, CAIP-2 id, or configured chain key. Defaults to the active wallet chain, or `eip155:1` if none is selected |

### Example

```bash
mm token list popular --chain-id 1
mm token list trending --chain-id 1
mm token list top-gainer --chain-id 1
```

## `token list search` Command

Search tokens by query.

### Syntax

```bash
mm token list search <query> [--chain-ids <chains>] [--limit <n>] [--after <cursor>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `<query>` | Yes | Search query by symbol or name, such as USDC or Wrapped Ether. Positional argument; `--query` is also accepted |
| `--chain-ids` | No | Comma-separated chain IDs, CAIP-2 IDs, or configured chain keys. Defaults to the active wallet chain, or `eip155:1` if none is selected |
| `--limit` | No | Maximum results. Defaults to 10, range 1-500 |
| `--after` | No | Pagination cursor |

### Example

```bash
mm token list search USDC --chain-ids 1,137 --limit 25
mm token list search "Wrapped Ether" --chain-ids eip155:8453
```

### Notes

- Quote multi-word queries so they arrive as a single positional argument.
- With no query, the command returns `MISSING_QUERY`; it never prompts for one.

## `token networks` Command

List networks supported by token APIs.

### Syntax

```bash
mm token networks
```

### Example

```bash
mm token networks
```

## `token assets` Command

Fetch asset metadata for one or more CAIP-19 assets.

### Syntax

```bash
mm token assets --asset-ids <asset-ids> [--include-market-data] [--include-token-security-data] [--include-labels] [--include-aggregators] [--include-coingecko-id] [--include-occurrences] [--include-rwa-data]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--asset-ids` | Yes | Comma-separated CAIP-19 asset IDs, such as `eip155:1/erc20:0xa0b8...`. Run `mm token networks` to see supported chains. Bare CAIP-2 chain ids are rejected with `INVALID_ASSET_ID`; pass a full asset id |
| `--include-market-data` | No | Include market cap, volume, and price data |
| `--include-token-security-data` | No | Include token security signals such as scam risk and honeypot detection |
| `--include-labels` | No | Include token labels and categories |
| `--include-aggregators` | No | Include aggregator sources that list this token |
| `--include-coingecko-id` | No | Include the CoinGecko identifier for cross-referencing |
| `--include-occurrences` | No | Include occurrence count across chains |
| `--include-rwa-data` | No | Include real-world asset data |

### Example

```bash
mm token assets --asset-ids "eip155:1/erc20:0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48,eip155:137/slip44:966"
mm token assets --asset-ids "eip155:1/erc20:0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48" --include-market-data --include-token-security-data --include-labels
mm token assets --asset-ids "eip155:1/slip44:60" --include-aggregators --include-coingecko-id --include-rwa-data
```
