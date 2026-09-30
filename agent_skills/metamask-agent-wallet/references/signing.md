# Signing Commands

Use `wallet sign-message` and `wallet sign-typed-data` to produce
cryptographic signatures with the active wallet.

## `wallet sign-message` Command

Sign a plaintext message with the active wallet.

### Syntax

```bash
mm wallet sign-message --message <text> --chain-id <id> [--wait] [--password <password>] [--wallet-timeout <seconds>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--chain-id` | Yes | EVM chain ID as a positive integer, such as 1 or 137. If not mentioned, ask the user. |
| `--message` | Yes | Plain-text message to sign |
| `--wait` | No | Block until the signature request completes. In server-wallet mode only, BYOK returns immediately |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |
| `--wallet-timeout` | No | Seconds to wait per wallet job including MFA and signing, max 600. Overrides config `walletTimeoutSeconds` |

### Example

```bash
mm wallet sign-message --message "Hello, world!" --chain-id 1
mm wallet sign-message --message "Hello" --chain-id 1 --wait
```

## `wallet sign-typed-data` Command

Sign EIP-712 typed data with the active wallet.

### Syntax

```bash
mm wallet sign-typed-data --chain-id <id> --payload '<JSON>' [--wait] [--password <password>] [--wallet-timeout <seconds>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--chain-id` | Yes | EVM chain ID as a positive integer, such as 1 or 137 |
| `--payload` | Yes | EIP-712 typed data as a JSON string with `domain`, `types`, `primaryType`, and `message` |
| `--wait` | No | Block until the signature request completes. In server-wallet mode only, BYOK returns immediately |
| `--intent` | No | Human-readable summary of what is being signed, forwarded with the request |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |
| `--wallet-timeout` | No | Seconds to wait per wallet job including MFA and signing, max 600. Overrides config `walletTimeoutSeconds` |

### Example

```bash
mm wallet sign-typed-data --chain-id 1 --payload '{"types":...,"primaryType":...,"domain":...,"message":...}'
mm wallet sign-typed-data --chain-id 137 --payload '{"types":...}' --wait --intent "Approve 10 USDC"
```

## EIP-712 Typed Data

The `--payload` must be valid JSON with these required fields:
- `types` -- type definitions
- `primaryType` -- the main type being signed
- `domain` -- domain separator containing name, version, chainId, and verifyingContract
- `message` -- the actual data to sign

## Notes

- If the Chain is not mentioned by the user, ask for the chain.
- In server-wallet mode, signing returns a `pollingId` when `--wait` is omitted. See `references/polling.md` to track requests.
