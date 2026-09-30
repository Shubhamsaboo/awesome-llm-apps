# Predict manage orders workflow

Use this workflow to view, cancel, or manage open Predict orders and positions.

Reference command syntax in `references/predict.md`.

## View orders

```bash
mm predict orders
mm predict orders --market <CONDITION_ID>
```

## View positions

```bash
mm predict positions
mm predict positions --market <CONDITION_ID>
```

## Cancel orders

Cancel a single order:

```bash
mm predict cancel --order-id <ORDER_ID>
```

Cancel by market or asset:

```bash
mm predict cancel --market <CONDITION_ID>
mm predict cancel --asset <OUTCOME_TOKEN_ID>
```

Cancel all open orders:

```bash
mm predict cancel --all
```

`predict cancel --all` cancels every open order. Require explicit confirmation from the user before executing.

## Watch async jobs

```bash
mm predict watch --id <JOB_ID> --wait
```

Use this for setup, approve, deposit, withdraw, redeem, and order jobs that haven't reached a terminal state.
