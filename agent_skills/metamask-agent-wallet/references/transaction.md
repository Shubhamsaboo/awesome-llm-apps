# Transaction Commands

Use `wallet send-transaction` to send raw EVM transactions with the active wallet.

## `wallet send-transaction` Command

Send a raw EVM transaction using the active wallet.

### Syntax

```bash
mm wallet send-transaction --chain-id <id> --payload '<JSON>' [--wait] [--password <password>] [--wallet-timeout <seconds>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--chain-id` | Yes | EVM chain ID as a positive integer, such as 1 or 137 |
| `--payload` | Yes | Transaction as a JSON string with at least a `to` address, such as `'{"to":"0x...","value":"0x0"}'}` |
| `--wait` | No | Block until the transaction completes. In server-wallet mode only, BYOK returns immediately |
| `--intent` | No | Human-readable summary of what the transaction does, forwarded with the request |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |
| `--wallet-timeout` | No | Seconds to wait per wallet job including MFA and signing, max 600. Overrides config `walletTimeoutSeconds` |

### Example

```bash
mm wallet send-transaction --chain-id 1 --payload '{"to":"0x742d...","value":"0xde0b6b3a7640000","data":"0x"}' --intent "Send 1 ETH to 0x742d...f2bD18"
mm wallet send-transaction --chain-id 1 --payload '{"to":"0x...","value":"0x0","data":"0xabcdef"}' --wait
mm wallet send-transaction --chain-id 1 --payload '...' --toon
```

## Transaction Payload

The `--payload` flag takes a JSON string with transaction fields:

```json
{
  "to": "0x742d35Cc6634C0532925a3b844Bc9e7595f2bD18",
  "value": "0xde0b6b3a7640000",
  "data": "0x"
}
```

Optional fields: `gas`, `nonce`, `maxFeePerGas`, `maxPriorityFeePerGas`. The `value` field must be 0x-prefixed hex, not a decimal wei string.

To convert a human-readable amount into that hex value, use the helper script in this skill. `$SKILL_DIR` is the folder containing `SKILL.md`; call it by full path, since the shell working directory is not stable between commands:

```bash
python3 "$SKILL_DIR/scripts/amount_to_hex.py" <amount> <decimals>
python3 "$SKILL_DIR/scripts/amount_to_hex.py" 1.5 18   # -> 0x14d1120d7b160000
```

The script exits with an error instead of rounding when the amount has more decimal places than the token supports, is negative, or is not a number. Surface that error to the user and ask for a corrected amount.

## Notes

- If the chain is not mentioned by the user, ask for the chain.
- When the `data`/calldata is unfamiliar or was not constructed by you, decode it first with `mm decode --payload <0x-calldata>` and confirm the intent before sending. See `references/decode.md`.
- In server-wallet mode, send-transaction returns a `pollingId` when `--wait` is omitted. See `references/polling.md` to track requests.
