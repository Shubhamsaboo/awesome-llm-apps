# Chain Commands

Use `chains` commands to discover supported blockchain networks.

## `chains list` Command

List all supported EVM blockchain networks (EIP-155).

### Syntax

```bash
mm chains list [--toon]
```

### Supported Flags

This command does not support additional flags beyond output format options.

### Example

```bash
mm chains list
mm chains list --toon
```

## Supported Namespaces

| Namespace | Notes |
| --- | --- |
| `eip155` | Major EVM chains, such as Ethereum, Polygon, Arbitrum, Optimism, BSC, Monad, HyperEVM, Sei, MegaETH, and Arc |
