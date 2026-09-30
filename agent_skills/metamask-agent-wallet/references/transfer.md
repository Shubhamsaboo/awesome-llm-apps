# Transfer Commands

Use `transfer` to send native token or ERC-20 tokens from the active wallet.

## `transfer` Command

Transfer native currency or ERC-20 tokens to a recipient address.

### Syntax

```bash
mm transfer --to <address> --amount <value> --chain-id <id> --token <symbol-or-address> [--wait] [--wallet-timeout <seconds>] [--password <password>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--to` | Yes | Recipient hex address, such as 0x742d...f2bD18. ENS is not supported. |
| `--amount` | Yes | Human-readable amount to transfer, such as 0.5 or 100 |
| `--chain-id` | Yes | EVM chain ID as a positive integer, such as 1 or 137 |
| `--token` | Yes | Token symbol or ERC-20 contract address, such as ETH, USDC, or 0xa0b8.... Token symbols are resolved via the token search API |
| `--wait` | No | Block until the transfer completes. In server-wallet mode only, BYOK returns immediately |
| `--wallet-timeout` | No | Seconds to wait per wallet job including MFA and signing, max 600. Overrides config `walletTimeoutSeconds` |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |

### Example

```bash
mm transfer --to 0x742d...f2bD18 --amount 0.5 --chain-id 1 --token ETH
mm transfer --to 0x742d...f2bD18 --amount 100 --chain-id 137 --token USDC
mm transfer --to 0x742d...f2bD18 --amount 1.0 --chain-id 1 --token ETH --toon
```

## Gasless Transfers

ERC-20 transfers can be routed through a gasless relay when the wallet has insufficient native gas. The CLI automatically detects this and routes through the relay. Gasless transfers are only available on supported chains. If the chain does not support gasless relay, the CLI returns `GASLESS_UNSUPPORTED`.

Gasless transfers are not supported for native token transfers such as ETH or POL. They only apply to ERC-20 token transfers.

## Notes

- If the chain is not mentioned by the user, ask for the chain.
- Use `mm chains list` to discover supported chain IDs.
- In server-wallet mode, transfer returns a `pollingId` when `--wait` is omitted. See `references/polling.md` to track requests.
- Gasless transfers trigger MFA approval flows. When stdout contains `AWAITING_MFA` (see **MFA Approval Pauses** in `SKILL.md`), guide the user to approve out of band before tracking with `mm wallet requests watch <polling-id>`.
