# Transaction Commands

Use `mm tx` to look up a transaction by hash, or `mm tx history` to list recent transactions for the active wallet or specific addresses.

## `tx` command

Look up a transaction by hash.

### Syntax

```bash
mm tx --hash <hash> [--chain-id <chain-id-or-caip2>]
```

### Supported flags

| Name | Required | Description |
| --- | --- | --- |
| `--hash` | Yes | 0x-prefixed transaction hash |
| `--chain-id` | No | Chain ID or CAIP-2, such as `1` or `eip155:1`. When omitted, common EVM chains are probed |

### Example

```bash
mm tx --hash 0xabc123...
mm tx --hash 0xabc123... --chain-id 137
mm tx --hash 0xabc123... --chain-id eip155:1
```

## `tx history` command

### Syntax

```bash
mm tx history [--addresses <addrs>] [--chain-ids <chains>] [--type <filter>] [--limit <n>] [--after <cursor>]
```

### Supported flags

| Name | Required | Description |
| --- | --- | --- |
| `--addresses` | No | Comma-separated EVM wallet addresses to include. Defaults to all EVM wallets for your account |
| `--chain-ids` | No | Comma-separated chain filters, such as `1,137` or `eip155:1`. Run `mm chains list` to see options |
| `--type` | No | Filter by direction: `in`, `out`, or `self`, or by transaction category/type |
| `--limit` | No | Maximum number of transactions to return, 1-50. Default 50 |
| `--after` | No | Forward pagination cursor. Pass the `endCursor` from a previous response to fetch the next page |

### Example

```bash
mm tx history
mm tx history --limit 10 --toon
mm tx history --chain-ids 1,8453
mm tx history --type out
mm tx history --addresses 0x742d...f2bD18 --chain-ids 137 --limit 50
mm tx history --limit 50 --after eyJhbGciOi...
```

### Output

Each history row includes enriched metadata:

| Field | Description |
| --- | --- |
| `chainName` | Human-readable chain name, such as "Ethereum" or "Polygon" |
| `chainId` | Numeric chain ID, such as 1 or 137 |
| `explorerUrl` | Block explorer link to the transaction |
| `protocol` | Protocol metadata when available, such as "swap", "transfer", or "earn" |

When a pending CLI job matches an indexed transaction hash, the original CLI intent is preserved in the output.

The result also carries pagination metadata when more indexed history is available:

| Field | Description |
| --- | --- |
| `hasNextPage` | Present and `true` when the indexer reports another page after this one |
| `endCursor` | Opaque cursor for the next page. Pass it back as `--after` |

Both fields are omitted when there is no next page. JSON and toon output carry them as fields; text output renders them as a footer with the next-page command.

### Pagination

To page through history, read `endCursor` from the response and re-run the command with `--after`:

```bash
mm tx history --limit 50 --toon
mm tx history --limit 50 --after <endCursor> --toon
```

Keep the other filters identical across pages. Stop when `hasNextPage` is absent.

### Notes

- If you omit `--addresses`, the command queries all EVM wallets for your account.
- Addresses must be 0x-prefixed EVM addresses.
- `--limit` must be between 1 and 50, the Accounts API page-size ceiling. Values outside this range return an `INVALID_LIMIT` error. To read more than 50 transactions, page with `--after`.
- The first page merges locally tracked pending CLI jobs with indexed history. Pages fetched with `--after` return indexed history only, so a pending transaction appears only on the first page.
- If your account has no EVM wallets, the command returns a `NO_HISTORY_WALLETS` error.
