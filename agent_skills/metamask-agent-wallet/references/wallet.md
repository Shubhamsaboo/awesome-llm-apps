# Wallet Commands

Use the `wallet` commands to create, list, select, inspect wallets, and check balances.

## `wallet create` Command

Create a new wallet under the authenticated account.

### Syntax

```bash
mm wallet create [--chain-namespace <namespace>] [--name <name>] [--trading-mode <mode>] [--password <password>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--chain-namespace` | No | Wallet chain namespace: `evm`, EIP-155. Allowed: `evm` |
| `--name` | No | Display name for the wallet |
| `--trading-mode` | No | `guard` enforces outflow/whitelist policies and blocks malicious transactions. `beast` skips policy checks but still blocks malicious transactions. Allowed: `guard` or `beast` |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |

### Example

```bash
mm wallet create --chain-namespace evm
mm wallet create --chain-namespace evm --name "Trading"
mm wallet create --chain-namespace evm --name "Fast Trading" --trading-mode beast
```

### Notes

- A project can hold at most 100 wallets. Once that limit is reached, `mm wallet create` returns `WALLET_LIMIT_EXCEEDED`. Run `mm wallet list` and reuse an existing wallet with `mm wallet select` instead.

## `wallet list` Command

List all wallets associated with the authenticated account.

### Syntax

```bash
mm wallet list [--chain-namespace <namespace>] [--toon]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--chain-namespace` | No | Filter by namespace: `evm`, EIP-155. Allowed: `evm` |

### Example

```bash
mm wallet list
mm wallet list --chain-namespace evm --toon
```

## `wallet select` Command

Switch the active wallet used for subsequent commands.

### Syntax

```bash
mm wallet select [<address>] [--chain-namespace <namespace>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `<address>` | No | Wallet address, 0x-prefixed hex. Positional argument. Omit it in a TTY to pick from the wallet list |
| `--chain-namespace` | No | Filter by namespace: `evm`, EIP-155. Allowed: `evm` |

### Example

```bash
mm wallet select 0x742d35Cc6634C0532925a3b844Bc9e7595f2bD18
```

### Notes

- Pass the address. Omitting it falls back to an interactive picker that needs a TTY; in a headless session the command returns `MISSING_WALLET_REF` with a hint to run `mm wallet list`.
- A malformed address returns `INVALID_EVM_ADDRESS`; an address that is not in the account roster returns `WALLET_NOT_FOUND`. Run `mm wallet list` to get valid addresses.
- If `--chain-namespace` is passed and the wallet belongs to a different namespace, the command returns `WRONG_NAMESPACE`.

## `wallet show` Command

Display details for a specific wallet or the currently active wallet.

### Syntax

```bash
mm wallet show [--chain-namespace <namespace>] [--id <id>] [--address <address>] [--name <name>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--chain-namespace` | No | Filter by namespace: `evm`, EIP-155. Allowed: `evm` |
| `--id` | No | Wallet ID |
| `--address` | No | Wallet address, 0x-prefixed hex |
| `--name` | No | Wallet display name |

### Example

```bash
mm wallet show
mm wallet show --address 0x742d...f2bD18
```

## `wallet address` Command

Print the address of the currently active wallet.

### Syntax

```bash
mm wallet address [--chain-namespace <namespace>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--chain-namespace` | No | Wallet chain namespace: `evm`, EIP-155. Allowed: `evm` |

### Example

```bash
mm wallet address
mm wallet address --chain-namespace evm
```

## `wallet add-fund` Command

Show a QR code and address to fund the currently active wallet. In interactive mode (TTY or REPL), renders an ASCII QR code plus the address. In headless mode (`--json`, piped stdout), outputs the address only.

### Syntax

```bash
mm wallet add-fund [--chain-namespace <namespace>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--chain-namespace` | No | Wallet chain namespace: `evm`, EIP-155. Allowed: `evm` |

### Example

```bash
mm wallet add-fund
mm wallet add-fund --toon
```

## `wallet trading-mode get` Command

Show the current trading mode and active wallet address for the selected wallet.

### Syntax

```bash
mm wallet trading-mode get [--chain-namespace <namespace>] [--address <address>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--chain-namespace` | No | Wallet chain namespace: `evm`, EIP-155. Allowed: `evm` |
| `--address` | No | Wallet address, 0x-prefixed hex |

### Example

```bash
mm wallet trading-mode get
mm wallet trading-mode get --address 0x742d...f2bD18
```

## `wallet trading-mode set` Command

Set the trading mode for the active wallet. Broadening changes (guard → beast) require MFA approval; tightening changes (beast → guard) apply immediately. Returns `confirmed` when applied, or `pending_approval` while awaiting MFA.

### Syntax

```bash
mm wallet trading-mode set <guard|beast> [--chain-namespace <namespace>] [--address <address>] [--wait] [--wallet-timeout <seconds>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `<mode>` | Yes | `guard` enforces outflow/whitelist policies and blocks malicious transactions. `beast` skips policy checks but still blocks malicious transactions |
| `--chain-namespace` | No | Wallet chain namespace: `evm`, EIP-155. Allowed: `evm` |
| `--address` | No | Wallet address, 0x-prefixed hex |
| `--wait` | No | Block until MFA approval completes. Use `--no-wait` to return immediately with the request ID |
| `--wallet-timeout` | No | Seconds to wait per wallet job including MFA and signing, max 600. Overrides config `walletTimeoutSeconds` |

### Example

```bash
mm wallet trading-mode set guard
mm wallet trading-mode set beast --wait
mm wallet trading-mode set beast --wallet-timeout 300
```

## `wallet policy get` Command

Show the policy YAML for the active server wallet. Server-wallet mode only; in BYOK mode it returns `WRONG_WALLET_MODE`.

### Syntax

```bash
mm wallet policy get
```

### Example

```bash
mm wallet policy get
mm wallet policy get --toon
```

## `wallet policy set` Command

Set the policy for the active wallet. Broadening policy changes, such as increasing outflow limits, require MFA approval; non-broadening changes, such as tightening limits, apply immediately. Returns `confirmed` when applied immediately, or `pending_approval` when MFA is required.

### Syntax

```bash
mm wallet policy set --policy <yaml> [--wait] [--wallet-timeout <seconds>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--policy` | Yes | Complete policy YAML document to apply |
| `--wait` | No | Block until MFA approval completes. Use `--no-wait` to return immediately with the request ID |
| `--wallet-timeout` | No | Seconds to wait per wallet job including MFA and signing, max 600. Overrides config `walletTimeoutSeconds` |

### Example

```bash
mm wallet policy get --json
mm wallet policy set --policy "$(cat policy.yaml)"
mm wallet policy set --policy "$(cat policy.yaml)" --wait
```

### Notes

- `--policy` takes a full policy document, not a fragment. Read the current document from the `policy` field of `mm wallet policy get --json`, or start from `mm wallet policy template`, edit it, and pass the whole YAML object back. It must be a YAML mapping with a top-level `schema_version`.
- A list, bare string, or empty document returns `INVALID_POLICY_YAML`.

## `wallet policy template` Command

Show the project policy template.

### Syntax

```bash
mm wallet policy template
```

### Supported Flags

This command does not support additional flags beyond output format options.

### Example

```bash
mm wallet policy template
mm wallet policy template --toon
```

## `wallet balance` Command

Show native and token balances for the active wallet.

### Syntax

```bash
mm wallet balance [--currency <code>] [--chain-ids <chains>] [--token <token>] [--address <address>] [--testnet] [--testnet-chain-ids <ids>] [--token-contracts <addresses>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--currency` | No | Fiat currency code for price conversion, such as usd or eur |
| `--chain-ids` | No | Comma-separated chain filters, such as `1,137` or `eip155:1`. Run `mm chains list` to see options |
| `--token` | No | Filter by token symbol, contract address, or CAIP-19 asset ID, such as USDC or 0xa0b8... |
| `--address` | No | Wallet address, 0x-prefixed hex |
| `--testnet` | No | Read balances via RPC on Arbitrum Sepolia, Amoy, and Sepolia testnets |
| `--testnet-chain-ids` | No | Comma-separated EVM testnet chain IDs for on-chain RPC balance reads, such as `421614,80002` |
| `--token-contracts` | No | Comma-separated ERC-20 contract addresses for testnet RPC chains, 0x-prefixed hex. Use with `--testnet-chain-ids` to read specific token balances on testnets |

### Example

```bash
mm wallet balance
mm wallet balance --chain-ids 8453
mm wallet balance --token USDC
mm wallet balance --currency eur
mm wallet balance --testnet
mm wallet balance --testnet-chain-ids 421614 --token-contracts 0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48
```
