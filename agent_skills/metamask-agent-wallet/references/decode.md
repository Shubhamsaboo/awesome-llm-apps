# Decode Commands

Use `decode` to turn raw EVM calldata into a human-readable intent before signing or sending a transaction. Requires authentication and a completed `init`.

## `decode` Command

Decode hex-encoded EVM calldata into its function name, parameters, and a plain-language summary.

### Syntax

```bash
mm decode --payload <0x-calldata> [--toon]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--payload` | Yes | Hex-encoded EVM calldata to decode, such as `0x095ea7b3...` |

### Output

| Field | Description |
| --- | --- |
| `functionName` | Decoded function name, when the selector is recognized |
| `params` | Array of decoded parameters, each with `name` and `value` |
| `intent` | Plain-language summary of the call, such as `Call approve(spender: 0x..., amount: ...)` |

### Example

```bash
mm decode --payload 0x095ea7b3000000000000000000000000... --toon
```

## Notes

- Use this before `mm wallet send-transaction` whenever the calldata is unfamiliar or was not constructed by you, to confirm what the transaction actually does.
- If the selector is not recognized, `intent` falls back to `Call unknown function`. Treat unrecognized calldata as higher risk and warn the user before proceeding.
