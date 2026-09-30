# Perpetual Trading Commands

Use `perps` commands to trade perpetual futures on supported venues. Currently supported venue: `hyperliquid`.

## Common Flags

Most `perps` commands accept these flags (`list-venues` does not):

| Name | Required | Description |
| --- | --- | --- |
| `--venue` | No | Perpetual venue. Defaults to `hyperliquid` |
| `--network` | No | Target network: `mainnet` or `testnet`. Defaults to `mainnet` |

The `--yes` flag skips interactive confirmation on `open`, `close`, `modify`, and `cancel` only. On `deposit`, `transfer`, and `withdraw`, `--yes` is accepted but has no effect because those commands do not prompt. Perps commands do not use `--wait`. In BYOK mode with an encrypted mnemonic, state-changing commands also accept `--password` to unlock the mnemonic. Set `MM_PASSWORD` env var instead of passing inline.

## `perps markets` Command

List perpetual markets for a venue.

### Syntax

```bash
mm perps markets [--venue <venue>] [--network <network>] [--symbol <symbol>] [--symbols <list>] [--dex <name>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--venue` | No | Perpetual venue. Defaults to `hyperliquid`. Run `mm perps list-venues` to see options |
| `--network` | No | Target network: `mainnet` or `testnet`. Defaults to `mainnet` |
| `--symbol` | No | Filter to a single market symbol such as BTC |
| `--symbols` | No | Comma-separated market symbols to filter such as BTC,ETH,SOL |
| `--dex` | No | HIP-3 DEX name; omit for the main Hyperliquid DEX. Run `mm perps dexs` to see options |

### Example

```bash
mm perps markets --venue hyperliquid
mm perps markets --venue hyperliquid --symbol BTC
mm perps markets --venue hyperliquid --symbols BTC,ETH,SOL --network testnet
mm perps markets --venue hyperliquid --dex <name from mm perps dexs>
```

## `perps balance` Command

Show the connected wallet's perpetual account balances for a venue.

### Syntax

```bash
mm perps balance [--venue <venue>] [--network <network>] [--dex <dex>] [--all-dexes]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--venue` | No | Perpetual venue. Defaults to `hyperliquid` |
| `--network` | No | Target network: `mainnet` or `testnet`. Defaults to `mainnet` |
| `--dex` | No | HIP-3 DEX name. Omit to query only the main Hyperliquid DEX. Run `mm perps dexs` to see options |
| `--all-dexes` | No | Aggregate balances across all DEXs. Mutually exclusive with `--dex` |

### Example

```bash
mm perps balance --venue hyperliquid
mm perps balance --venue hyperliquid --network testnet
mm perps balance --venue hyperliquid --all-dexes
```

## `perps positions` Command

List open positions for the connected wallet on a venue.

### Syntax

```bash
mm perps positions [--venue <venue>] [--network <network>] [--dex <dex>] [--all-dexes]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--venue` | No | Perpetual venue. Defaults to `hyperliquid` |
| `--network` | No | Target network: `mainnet` or `testnet`. Defaults to `mainnet` |
| `--dex` | No | HIP-3 DEX name. Omit to query only the main Hyperliquid DEX. Run `mm perps dexs` to see options |
| `--all-dexes` | No | Aggregate positions across all DEXs. Mutually exclusive with `--dex` |

### Example

```bash
mm perps positions --venue hyperliquid
mm perps positions --venue hyperliquid --network testnet
mm perps positions --venue hyperliquid --all-dexes
```

## `perps quote` Command

Estimate entry price, notional, fees, and liquidation price without placing an order.

### Syntax

```bash
mm perps quote [--venue <venue>] --symbol <symbol> --side <side> --size <size> --leverage <leverage> [--type <type>] [--limit-px <price>] [--network <network>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--venue` | No | Perpetual venue. Defaults to `hyperliquid` |
| `--symbol` | Yes | Market symbol such as BTC, ETH, or SOL |
| `--side` | Yes | Position direction: `long` or `short` |
| `--size` | Yes | Size in base asset, human-readable such as 0.01 or 1 |
| `--leverage` | Yes | Leverage multiplier as a positive integer such as 5 or 10 |
| `--type` | No | Order type: `market` or `limit`. Defaults to `market` |
| `--limit-px` | If `--type limit` | Limit price, human-readable such as 60000 for BTC |
| `--network` | No | Target network: `mainnet` or `testnet`. Defaults to `mainnet` |

### Example

```bash
mm perps quote --venue hyperliquid --symbol BTC --side long --size 0.01 --leverage 5
mm perps quote --venue hyperliquid --symbol ETH --side short --size 1 --leverage 10 --type limit --limit-px 2500
```

## `perps open` Command

Open a new perpetual position by placing an order.

### Syntax

```bash
mm perps open [--venue <venue>] --symbol <symbol> --side <side> --size <size> --leverage <leverage> [--type <type>] [--limit-px <price>] [--max-slippage-bps <bps>] [--network <network>] [--dry-run] [--yes] [--password <password>] [--wallet-timeout <seconds>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--venue` | No | Perpetual venue. Defaults to `hyperliquid` |
| `--symbol` | Yes | Market symbol such as BTC, ETH, or SOL |
| `--side` | Yes | Position direction: `long` or `short` |
| `--size` | Yes | Size in base asset, human-readable such as 0.01 or 1 |
| `--leverage` | Yes | Leverage multiplier as a positive integer such as 5 or 10 |
| `--type` | No | Order type: `market` or `limit`. Defaults to `market` |
| `--limit-px` | If `--type limit` | Limit price; required when `--type` is `limit` such as 60000 for BTC |
| `--max-slippage-bps` | No | Slippage cap in basis points for IOC market pricing such as 50 |
| `--network` | No | Target network: `mainnet` or `testnet`. Defaults to `mainnet` |
| `--dry-run` | No | Validate and preview the order without signing or submitting |
| `--yes` | No | Skip interactive confirmation |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |
| `--wallet-timeout` | No | Seconds to wait per wallet job including MFA and signing, max 600. Overrides config `walletTimeoutSeconds` |

### Example

```bash
mm perps open --venue hyperliquid --symbol BTC --side long --size 0.01 --leverage 5
mm perps open --venue hyperliquid --symbol ETH --side short --size 1 --leverage 10 --type limit --limit-px 2500
mm perps open --venue hyperliquid --symbol BTC --side long --size 0.05 --leverage 3 --dry-run
```

## `perps orders` Command

List resting orders for the connected wallet on a venue.

### Syntax

```bash
mm perps orders [--venue <venue>] [--network <network>] [--dex <dex>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--venue` | No | Perpetual venue. Defaults to `hyperliquid` |
| `--network` | No | Target network: `mainnet` or `testnet`. Defaults to `mainnet` |
| `--dex` | No | HIP-3 DEX name. Omit to query only the main Hyperliquid DEX. Run `mm perps dexs` to see options |

### Example

```bash
mm perps orders --venue hyperliquid
mm perps orders --venue hyperliquid --network testnet
mm perps orders --venue hyperliquid --dex <name from mm perps dexs>
```

## `perps close` Command

Close one position, part of a position, or all open positions.

### Syntax

```bash
mm perps close [--venue <venue>] [--symbol <symbol>] [--size <size>] [--all] [--max-slippage-bps <bps>] [--network <network>] [--dry-run] [--yes] [--password <password>] [--wallet-timeout <seconds>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--venue` | No | Perpetual venue. Defaults to `hyperliquid` |
| `--symbol` | Yes, unless `--all` | Market symbol to close such as BTC or ETH |
| `--size` | No | Partial close size in base asset such as 0.5; omit for full close. Not allowed with `--all` |
| `--all` | No | Close all open positions; mutually exclusive with `--symbol` |
| `--max-slippage-bps` | No | Slippage cap in basis points for IOC pricing such as 50 |
| `--network` | No | Target network: `mainnet` or `testnet`. Defaults to `mainnet` |
| `--dry-run` | No | Preview the close action without signing or submitting |
| `--yes` | No | Skip interactive confirmation |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |
| `--wallet-timeout` | No | Seconds to wait per wallet job including MFA and signing, max 600. Overrides config `walletTimeoutSeconds` |

### Validation Rules

- `--size` is not allowed with `--all`.

### Example

```bash
mm perps close --venue hyperliquid --symbol BTC
mm perps close --venue hyperliquid --symbol ETH --size 0.5
mm perps close --venue hyperliquid --all
mm perps close --venue hyperliquid --symbol BTC --dry-run
```

## `perps modify` Command

Modify leverage, take-profit, or stop-loss for an existing position.

### Syntax

```bash
mm perps modify [--venue <venue>] --symbol <symbol> [--leverage <leverage>] [--tp <price>] [--sl <price>] [--network <network>] [--dry-run] [--yes] [--password <password>] [--wallet-timeout <seconds>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--venue` | No | Perpetual venue. Defaults to `hyperliquid` |
| `--symbol` | Yes | Market symbol such as BTC, ETH, or SOL |
| `--leverage` | No | New leverage multiplier as a positive integer such as 5 or 10 |
| `--tp` | No | Take-profit trigger price, human-readable such as 3000 or 2500.50 |
| `--sl` | No | Stop-loss trigger price, human-readable such as 2000 or 1800.75 |
| `--network` | No | Target network: `mainnet` or `testnet`. Defaults to `mainnet` |
| `--dry-run` | No | Preview the modify action without signing or submitting |
| `--yes` | No | Skip interactive confirmation |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |
| `--wallet-timeout` | No | Seconds to wait per wallet job including MFA and signing, max 600. Overrides config `walletTimeoutSeconds` |

### Validation Rules

- At least one of `--leverage`, `--tp`, or `--sl` must be provided.

### Example

```bash
mm perps modify --venue hyperliquid --symbol BTC --leverage 10
mm perps modify --venue hyperliquid --symbol ETH --tp 3000 --sl 2000
mm perps modify --venue hyperliquid --symbol BTC --leverage 3 --dry-run
```

## `perps cancel` Command

Cancel a resting perps order.

### Syntax

```bash
mm perps cancel [--venue <venue>] --order-id <id> [--symbol <symbol>] [--network <network>] [--dry-run] [--yes] [--password <password>] [--wallet-timeout <seconds>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--venue` | No | Perpetual venue. Defaults to `hyperliquid`. Run `mm perps list-venues` to see options |
| `--order-id` | Yes | Venue order ID to cancel. Must be a positive integer |
| `--symbol` | No | Market symbol, speeds up cancel by avoiding an open-order lookup. For example BTC or ETH |
| `--network` | No | Target network: `mainnet` or `testnet`. Defaults to `mainnet` |
| `--dry-run` | No | Preview the cancel action without signing or submitting |
| `--yes` | No | Skip interactive confirmation |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |
| `--wallet-timeout` | No | Seconds to wait per wallet job including MFA and signing, max 600. Overrides config `walletTimeoutSeconds` |

### Example

```bash
mm perps cancel --venue hyperliquid --order-id 12345
mm perps cancel --venue hyperliquid --order-id 12345 --symbol BTC
mm perps cancel --venue hyperliquid --order-id 12345 --dry-run
mm perps cancel --venue hyperliquid --order-id 12345 --yes
```

## `perps deposit` Command

Deposit USDC into a perpetual venue.

### Syntax

```bash
mm perps deposit [--venue <venue>] --amount <amount> [--asset <asset>] [--source-chain-id <chain>] [--network <network>] [--dry-run] [--yes] [--password <password>] [--wallet-timeout <seconds>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--venue` | No | Perpetual venue. Defaults to `hyperliquid`. Run `mm perps list-venues` to see options |
| `--amount` | Yes | Human-readable USDC amount to deposit such as 100 or 50.5 |
| `--asset` | No | Deposit asset. Defaults to `USDC` |
| `--source-chain-id` | No | Source chain as a CAIP-2 ID or decimal chain ID. Defaults to Arbitrum for the selected network: `eip155:42161` on mainnet, `eip155:421614` on testnet |
| `--network` | No | Target network: `mainnet` or `testnet`. Defaults to `mainnet` |
| `--dry-run` | No | Preview the transaction without signing or submitting |
| `--yes` | No | Skip interactive confirmation |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |
| `--wallet-timeout` | No | Seconds to wait per wallet job including MFA and signing, max 600. Overrides config `walletTimeoutSeconds` |

### Example

```bash
mm perps deposit --venue hyperliquid --amount 100 --asset USDC
mm perps deposit --venue hyperliquid --amount 100 --asset USDC --dry-run
```

## `perps withdraw` Command

Withdraw USDC from a perpetual venue.

### Syntax

```bash
mm perps withdraw [--venue <venue>] --amount <amount> [--asset <asset>] [--destination <address>] [--network <network>] [--dry-run] [--include-spot] [--yes] [--password <password>] [--wallet-timeout <seconds>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--venue` | No | Perpetual venue. Defaults to `hyperliquid`. Run `mm perps list-venues` to see options |
| `--amount` | Yes | Human-readable USDC amount to withdraw such as 50 or 25.5 |
| `--asset` | No | Withdrawal asset. Defaults to `USDC` |
| `--destination` | No | EVM destination address. Defaults to your connected wallet |
| `--network` | No | Target network: `mainnet` or `testnet`. Defaults to `mainnet` |
| `--dry-run` | No | Preview the withdrawal without signing or submitting |
| `--include-spot` | No | Move free spot USDC to perp before withdrawing if needed |
| `--yes` | No | Skip interactive confirmation |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |
| `--wallet-timeout` | No | Seconds to wait per wallet job including MFA and signing, max 600. Overrides config `walletTimeoutSeconds` |

### Example

```bash
mm perps withdraw --venue hyperliquid --amount 50 --asset USDC
mm perps withdraw --venue hyperliquid --amount 50 --asset USDC --include-spot
mm perps withdraw --venue hyperliquid --amount 50 --asset USDC --destination 0x742d35Cc6634C0532925a3b844Bc9e7595f2bD18
```

## `perps transfer` Command

Transfer USDC between spot and perp accounts on a perpetual venue.

### Syntax

```bash
mm perps transfer [--venue <venue>] --amount <amount> --direction <direction> [--asset <asset>] [--network <network>] [--dry-run] [--yes] [--password <password>] [--wallet-timeout <seconds>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--venue` | No | Perpetual venue. Defaults to `hyperliquid` |
| `--amount` | Yes | Human-readable USDC amount to transfer such as 100 or 50.5 |
| `--direction` | Yes | Transfer direction: `spot-to-perp` or `perp-to-spot` |
| `--asset` | No | Transfer asset. Defaults to `USDC` |
| `--network` | No | Target network: `mainnet` or `testnet`. Defaults to `mainnet` |
| `--dry-run` | No | Preview the transfer without signing or submitting |
| `--yes` | No | Skip interactive confirmation |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |
| `--wallet-timeout` | No | Seconds to wait per wallet job including MFA and signing, max 600. Overrides config `walletTimeoutSeconds` |

### Example

```bash
mm perps transfer --venue hyperliquid --amount 100 --direction spot-to-perp --asset USDC
mm perps transfer --venue hyperliquid --amount 50 --direction perp-to-spot --asset USDC
```

## `perps list-venues` Command

List available perpetual futures venues.

### Syntax

```bash
mm perps list-venues
```

### Supported Flags

This command does not support additional flags beyond output format options.

### Example

```bash
mm perps list-venues
```

## `perps dexs` Command

List available DEX identifiers a venue exposes. For Hyperliquid, this includes the main DEX and any HIP-3 builder-deployed DEXs.

### Syntax

```bash
mm perps dexs [--venue <venue>] [--network <network>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--venue` | No | Perpetual venue. Defaults to `hyperliquid` |
| `--network` | No | Target network: `mainnet` or `testnet`. Defaults to `mainnet` |

### Example

```bash
mm perps dexs --venue hyperliquid
```

## Notes

- If the user does not mention a token symbol, use `mm perps markets` to list available markets and confirm the symbol with the user before proceeding.
