# Earn Commands

Use the `earn` commands to browse DeFi yield vaults, view positions, supply tokens, and withdraw. Powered by LiFi's earn API.

## `earn markets` Command

List available earn vaults with APY and TVL data. Requires authentication and a completed `init`.

### Syntax

```bash
mm earn markets [--chain-id <chain-id>] [--token <symbol|address>] [--protocol <name>] [--min-tvl <usd>] [--sort apy|tvl] [--limit <n>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--chain-id` | No | EVM chain ID to filter results, such as 1 for Ethereum or 8453 for Base |
| `--token` | No | Filter by token symbol or address, such as USDC |
| `--protocol` | No | Filter by protocol name, such as aave, compound, or morpho |
| `--min-tvl` | No | Minimum TVL in USD. Must be a positive number |
| `--sort` | No | Sort order: `apy` or `tvl`. Defaults to `apy` |
| `--limit` | No | Maximum number of vaults to return |

### Example

```bash
mm earn markets
mm earn markets --chain-id 8453
mm earn markets --chain-id 1 --protocol aave --min-tvl 100000
```

### Output

Each vault includes: address, chainId, name, protocol, underlying tokens, APY with base/reward/total breakdown, 7-day and 30-day APY, TVL in USD, and whether it supports deposits via `isTransactional` and withdrawals via `isRedeemable`.

## `earn positions` Command

List current earn positions and deposited balances for a wallet. Requires authentication and a completed `init`.

### Syntax

```bash
mm earn positions [--chain-id <chain-id>] [--address <address>] [--token <symbol|address>] [--protocol <name>] [--vault <address>] [--min-usd <n>] [--sort usd] [--limit <n>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--chain-id` | No | EVM chain ID to filter positions |
| `--address` | No | Account address. Defaults to the currently selected wallet |
| `--token` | No | Filter by token symbol or address |
| `--protocol` | No | Filter by protocol name |
| `--vault` | No | Filter by vault contract address |
| `--min-usd` | No | Hide positions below this USD balance |
| `--sort` | No | Sort order: `usd` for descending balance |
| `--limit` | No | Maximum number of positions to return |

### Example

```bash
mm earn positions
mm earn positions --chain-id 8453
mm earn positions --address 0x742d35Cc6634C0532925a3b844Bc9e7595f2bD18
```

### Output

Each position includes: chainId, vault address, protocol name, asset with address/symbol/decimals/name, balance in USD, and balance in native token units.

## `earn supply` Command

Supply tokens to an earn vault to earn yield. Requires authentication. Handles ERC-20 approval automatically. Supports cross-chain deposits.

### Syntax

```bash
mm earn supply --token <symbol|address> --amount <amount> --chain-id <chain-id> [--vault <address>] [--protocol <name>] [--min-tvl <usd>] [--from-chain-id <chain-id>] [--from-token <symbol|address>] [--wait] [--password <password>] [--wallet-timeout <seconds>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--token` | Yes, unless `--vault` | Underlying token symbol or contract address, such as USDC |
| `--amount` | Yes | Human-readable amount to supply, such as 100. Must be a positive number |
| `--chain-id` | Yes | Destination EVM chain ID where the vault lives |
| `--vault` | No | Vault contract address. If omitted, auto-selects the best vault for the token |
| `--protocol` | No | Restrict vault auto-selection to a specific protocol, such as aave or compound |
| `--min-tvl` | No | Minimum TVL in USD for vault auto-selection |
| `--from-chain-id` | No | Source chain ID for cross-chain deposits |
| `--from-token` | No | Source token symbol or address for cross-chain deposits. Required when `--from-chain-id` differs from `--chain-id` |
| `--wait` | No | Poll after deposit to confirm the position is reflected, up to ~45s. Without `--wait`, the CLI shows a hint to check positions shortly |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |
| `--wallet-timeout` | No | Seconds to wait per wallet job including MFA and signing, max 600. Overrides config `walletTimeoutSeconds` |

### Validation Rules

- Either `--token` or `--vault` must be provided.
- When `--from-chain-id` differs from `--chain-id`, `--from-token` is required.

### Example

```bash
mm earn supply --token USDC --amount 100 --chain-id 8453
mm earn supply --token USDC --amount 100 --chain-id 8453 --protocol aave
mm earn supply --vault 0xabc...def --amount 50 --chain-id 1
mm earn supply --token USDC --amount 100 --chain-id 8453 --from-chain-id 1 --from-token USDC
```

## `earn withdraw` Command

Withdraw tokens from an earn vault. Requires authentication. Handles LP token approval automatically.

### Syntax

```bash
mm earn withdraw --token <symbol|address> --amount <amount> --chain-id <chain-id> [--vault <address>] [--protocol <name>] [--all] [--password <password>] [--wallet-timeout <seconds>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--token` | Yes, unless `--vault` | Underlying token symbol or contract address |
| `--amount` | Yes, unless `--all` | Human-readable amount to withdraw. Must be a positive number |
| `--chain-id` | Yes | EVM chain ID of the vault |
| `--vault` | No | Vault contract address. If omitted, auto-selects by token |
| `--protocol` | No | Restrict vault auto-selection to a specific protocol |
| `--all` | No | Withdraw the full balance. Mutually exclusive with `--amount` |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |
| `--wallet-timeout` | No | Seconds to wait per wallet job including MFA and signing, max 600. Overrides config `walletTimeoutSeconds` |

### Validation Rules

- Either `--token` or `--vault` must be provided.
- Either `--amount` or `--all` must be provided.
- The vault must be redeemable with `isRedeemable: true`. If not, the CLI returns `NOT_REDEEMABLE`.

### Example

```bash
mm earn withdraw --token USDC --amount 50 --chain-id 8453
mm earn withdraw --token USDC --all --chain-id 8453
mm earn withdraw --vault 0xabc...def --all --chain-id 1
```

## Notes

- Use `mm earn markets` to discover available vaults before supplying.
- Use `mm earn positions` to check current deposits before withdrawing.
- If `--vault` is omitted, the CLI auto-selects the best vault for the token on the specified chain. Use `--protocol` to narrow the selection.
- Cross-chain supply is supported: set `--from-chain-id` and `--from-token` to deposit from a different chain. The CLI routes through LiFi and polls until the cross-chain transaction completes, with a timeout of 10 minutes.
- The CLI handles ERC-20 approvals automatically for both supply and withdraw operations.
