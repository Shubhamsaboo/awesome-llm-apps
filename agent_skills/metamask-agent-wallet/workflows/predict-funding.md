# Predict funding workflow

Use this workflow to deposit or withdraw pUSD from the Predict deposit wallet.

Reference command syntax in `references/predict.md`.

## Flow

1. Check deposit wallet balance.
2. Deposit or withdraw.

## Check deposit wallet balance

```bash
mm predict balance --sync
```

## Deposit

If the user doesn't specify an amount, ask how much they want to deposit. Get the deposit wallet address from `mm predict status`, then check the user's Polygon balance.

```bash
mm wallet balance --chain-ids 137
```

### Has POL and pUSD on Polygon

Use `mm transfer` to send pUSD directly to the deposit wallet address. No conversion needed. Get the pUSD contract address from `mm wallet balance --chain-ids 137` output.

```bash
mm transfer --to <DEPOSIT_WALLET_ADDRESS> --amount <AMOUNT> --chain-id 137 --token <PUSD_CONTRACT_ADDRESS> --wait
```

Get the deposit wallet address from the `mm predict status` output.

### Has POL and USDC.e on Polygon

Run `mm predict deposit`. The CLI converts USDC.e to pUSD in the deposit wallet.

```bash
mm predict deposit --amount <AMOUNT> --wait
```

`--amount` is in USDC.e. The owner EOA needs enough USDC.e and POL for gas on Polygon.

### Has POL or another token on Polygon (but no USDC.e or pUSD)

Swap to pUSD on Polygon, then transfer directly to the deposit wallet. The owner EOA needs POL for gas.

```bash
mm swap quote --from <TOKEN> --to pUSD --amount <AMOUNT> --from-chain-id 137
mm swap execute --quote-id "$QUOTE_ID" # quote ID from the swap quote command
```

After the swap completes, check the balance to verify pUSD arrived

```bash
mm wallet balance --chain-ids 137
```

Get the pUSD contract address from the balance output, then transfer to the deposit wallet:

```bash
mm transfer --to <DEPOSIT_WALLET_ADDRESS> --amount <AMOUNT> --chain-id 137 --token <PUSD_CONTRACT_ADDRESS> --wait
```

Get the deposit wallet address from the `mm predict status` output.

### Has assets on another chain

Bridge to send pUSD directly to the deposit wallet address on Polygon.

```bash
mm swap quote --from <TOKEN> --to pUSD --amount <AMOUNT> --from-chain-id <SOURCE_CHAIN_ID> --to-chain-id 137 --to-address <DEPOSIT_WALLET_ADDRESS>
mm swap execute --quote-id "$QUOTE_ID" # quote ID from the swap quote command
```

Get the deposit wallet address from the `mm predict status` output. This avoids the extra deposit step.


## Withdraw

Withdraw pUSD from the deposit wallet to the owner EOA (default) or a specified address.

```bash
mm predict withdraw --amount <AMOUNT> --wait
mm predict withdraw --amount <AMOUNT> --to <RECIPIENT_ADDRESS> --wait
```

Confirm the amount and recipient with the user before executing. The CLI validates the amount against the on-chain deposit wallet balance before signing.
