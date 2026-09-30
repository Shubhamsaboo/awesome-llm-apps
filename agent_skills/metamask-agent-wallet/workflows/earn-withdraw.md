# Earn Withdraw Workflow

Use this workflow when the user wants to withdraw tokens from a DeFi earn vault.

Reference command syntax in `references/earn.md`.

## Flow

1. Check positions.
2. Confirm with the user.
3. Withdraw.

## Check Positions

List current earn positions to see what the user has deposited:

```bash
mm earn positions
mm earn positions --chain-id 8453
```

Show the user their positions with balance and protocol info.

## Withdraw

Partial withdrawal:

```bash
mm earn withdraw --token USDC --amount 50 --chain-id 8453
```

Full withdrawal:

```bash
mm earn withdraw --token USDC --all --chain-id 8453
```

With a specific vault:

```bash
mm earn withdraw --vault 0xabc...def --all --chain-id 1
```

## Confirm

Before executing, confirm with the user: token, amount (or full balance), chain, and vault/protocol.

## Edge cases

- `NOT_REDEEMABLE`: the vault does not support withdrawals. Inform the user and suggest checking other vaults.
- `VAULT_NOT_FOUND`: no matching vault. Run `mm earn positions` to check current positions.
- `INSUFFICIENT_FUNDS`: trying to withdraw more than the deposited balance. Use `--all` to withdraw the full amount.
- `EXECUTE_FAILED`: if the message names MFA approval and `mm wallet requests watch`, follow MFA Approval Pauses in `SKILL.md`. Otherwise the transaction reverted — retry or check the transaction on the block explorer.
- `QUOTE_FAILED`: LiFi returned no executable transaction. Try a different amount or vault.
