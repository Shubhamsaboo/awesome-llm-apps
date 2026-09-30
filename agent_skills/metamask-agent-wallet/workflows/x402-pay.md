# x402 pay workflow (buyer)

Use this when an HTTP request returns `402 Payment Required` (x402), or the user asks to
fetch/pay for a paywalled API, endpoint, file, or resource. For a paid MCP tool call, use
[x402-mcp.md](x402-mcp.md) instead.

`scripts/x402_pay.py` does the payment. Command details are in `references/x402.md`. Call it by
its full path inside this skill's directory (`$SKILL_DIR` is the folder containing `SKILL.md`), not
a bare `scripts/...`, because the shell working directory is not stable between commands. It is a
script, not an `mm` command, so do not pass `--toon`/`--format`; it always prints JSON.

## Flow

1. Inspect the resource.
2. Show the payment to the user and get approval.
3. Pay.
4. Report the settlement and return the resource.

## Inspect

```bash
python3 "$SKILL_DIR/scripts/x402_pay.py" inspect <url>
```

Prints the payment requirement(s) as JSON: asset, human-readable amount, network, `payTo`,
resource, and an `approvalId` for each option. This is read-only and does not spend.

## Confirm

Show the user the asset, amount, network, `payTo`, and resource URL from the inspect output, and
get explicit approval. Keep the `approvalId` of the option they approve. A signature authorizes a
real token debit.

## Pay

```bash
python3 "$SKILL_DIR/scripts/x402_pay.py" pay <url> --confirm --approved <approvalId>
```

Add `--asset <contract>` or `--network <network>` if the `402` offered more than one eligible
option. For a non-GET resource add `--method` (and `--data` for a body); the same request is
replayed with the payment attached. On success the script prints `"status": "settled"`, the
settlement transaction, and the resource body.

## Edge cases

- `error` with "no eligible option": the server offered no `exact`-scheme payment on a network mm
  supports. Show the offered options to the user.
- `error` with "multiple eligible options": the server offered the same scheme on several networks
  or assets (e.g. Base and Polygon). Rerun `pay` with `--network` or `--asset` to choose one.
- `error` mentioning "permit2": the only options use the Permit2 transfer method, which this skill
  does not sign (it supports EIP-3009 only). Tell the user it is unsupported.
- `error` with "terms differ from the approved ones": the server changed the offer after
  `inspect`. Nothing was signed. Show the user the new terms from the error, get approval again,
  and rerun `pay` with the new `approvalId`.
- `"status": "paid_unverified"`: the server returned the resource but no settlement receipt.
  The authorization was sent and may still settle. Do not pay again. Tell the user settlement is
  unconfirmed and check the wallet's transaction history.
- `error` with "payment not accepted": surface it. Do not rerun blindly; rerunning makes a new
  payment.
- `error` with "not a standard x402 challenge": the endpoint returned a 402 in a different payment
  scheme (for example pay-first then send a transaction hash). This skill supports the standard
  x402 exact scheme only. Tell the user it is unsupported rather than trying to pay.
- Encrypted BYOK mnemonic: set `MM_PASSWORD` so signing is non-interactive.
- Unknown network: the network is not in `mm chains list`; confirm the chain is supported.
