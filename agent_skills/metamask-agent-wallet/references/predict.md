# Predict Commands

Use the `predict` commands to trade on prediction markets, specifically Polymarket via the CLOB.

## `predict mode` Command

Choose or display the current Predict trading mode.

### Syntax

```bash
mm predict mode [mainnet|testnet]
```

### Example

```bash
mm predict mode mainnet
mm predict mode testnet
mm predict mode
```

## `predict setup` Command

One-time Predict setup: creates trading credentials, deploys the deposit wallet, and sets approvals.

### Syntax

```bash
mm predict setup [--wait] [--password <password>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--wait` | No | Block until the job completes |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |

### Example

```bash
mm predict setup --wait
```

## `predict auth` Command

Create or refresh Predict trading credentials, including API key and CLOB signing.

### Syntax

```bash
mm predict auth [--refresh] [--password <password>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--refresh` | No | Force-create or refresh trading credentials |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |

### Example

```bash
mm predict auth
mm predict auth --refresh
```

## `predict approve` Command

Repair missing deposit-wallet approvals.

### Syntax

```bash
mm predict approve [--wait] [--password <password>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--wait` | No | Block until the job completes |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |

### Example

```bash
mm predict approve --wait
```

## `predict status` Command

Probe Predict back-end reachability for Gamma and CLOB, and report account setup status: deposit wallet address, on-chain deployment, stored CLOB credentials, and a `setupComplete` flag.

### Syntax

```bash
mm predict status
```

### Example

```bash
mm predict status
```

## `predict geoblock` Command

Check whether Polymarket access is geoblocked for your current IP. Returns `blocked`, `ip`, `country`, and `region`.

### Syntax

```bash
mm predict geoblock
```

### Example

```bash
mm predict geoblock
```

## `predict markets list` Command

List tradeable Predict markets with Gamma-style filters.

### Syntax

```bash
mm predict markets list [--slug <slug>] [--limit <n>] [--offset <n>] [--order <fields>] [--ascending] [--tag <tag>] [--liquidity-num-min <n>] [--liquidity-num-max <n>] [--volume-num-min <n>] [--volume-num-max <n>] [--start-date-min <datetime>] [--start-date-max <datetime>] [--end-date-min <datetime>] [--end-date-max <datetime>] [--active] [--closed]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--slug` | No | Market slug to filter by |
| `--limit` | No | Maximum markets to return, 1-500 |
| `--offset` | No | Market result offset, zero-based |
| `--order` | No | Comma-separated market fields to order by |
| `--ascending` | No | Sort markets in ascending order |
| `--tag` | No | Market tag or category, such as sports or politics |
| `--liquidity-num-min` | No | Minimum market liquidity |
| `--liquidity-num-max` | No | Maximum market liquidity |
| `--volume-num-min` | No | Minimum market volume |
| `--volume-num-max` | No | Maximum market volume |
| `--start-date-min` | No | Minimum market start date-time |
| `--start-date-max` | No | Maximum market start date-time |
| `--end-date-min` | No | Minimum market end date-time |
| `--end-date-max` | No | Maximum market end date-time |
| `--active` | No | Only include active markets |
| `--closed` | No | Include closed markets |

### Example

```bash
mm predict markets list --slug will-this-work --limit 5
mm predict markets list --tag sports --liquidity-num-min 10000 --limit 10
mm predict markets list --active --limit 50
```

## `predict markets search` Command

Search Predict markets with Polymarket public search.

### Syntax

```bash
mm predict markets search <query> [--limit <n>] [--page <n>] [--sort <field>] [--ascending] [--search-tags] [--events-status] [--recurrence <recurrence>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `<query>` | Yes | Search string |
| `--limit` | No | Results per type. Defaults to 10 |
| `--page` | No | Search result page |
| `--sort` | No | Search sort field |
| `--ascending` | No | Sort search results in ascending order |
| `--search-tags` | No | Include tag matches in search results. Defaults to true; use `--no-search-tags` to disable |
| `--events-status` | No | Restrict to active events. Defaults to true; use `--no-events-status` for all |
| `--recurrence` | No | Filter by series recurrence: `annual`, `daily`, `weekly`, or `monthly` |

### Example

```bash
mm predict markets search "Knicks NBA Finals" --limit 5
mm predict markets search "election" --limit 5
```

## `predict markets get` Command

Inspect a specific market and show outcome token IDs needed for quoting and placing orders.

### Syntax

```bash
mm predict markets get --market <market>
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--market` | Yes | Market slug, ID, or condition ID. Run `mm predict markets search` or `mm predict markets list` to find markets |

### Example

```bash
mm predict markets get --market will-the-new-york-knicks-win-the-2026-nba-finals
mm predict markets get --market 0x713641f745d71f6ec61f906237ffca3c8583f251e49384429a63ceb0ccdb2d37
```

## `predict events list` Command

List Polymarket events, which are groupings of related markets, with Gamma-style filters.

### Syntax

```bash
mm predict events list [--tag-slug <slug>] [--tag-id <n>] [--active] [--closed] [--featured] [--order <field>] [--ascending] [--liquidity-min <n>] [--start-date-min <datetime>] [--start-date-max <datetime>] [--end-date-min <datetime>] [--end-date-max <datetime>] [--limit <n>] [--offset <n>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--tag-slug` | No | Filter by tag slug, such as sports or politics |
| `--tag-id` | No | Filter by tag ID from `mm predict tags list` |
| `--active` | No | Active events only |
| `--closed` | No | Include closed/resolved events |
| `--featured` | No | Only featured/trending events |
| `--order` | No | Sort field: `volume_24hr`, `volume`, `liquidity`, `start_date`, `end_date` |
| `--ascending` | No | Sort ascending. Defaults to descending |
| `--liquidity-min` | No | Minimum event liquidity |
| `--start-date-min` | No | Minimum event start date-time |
| `--start-date-max` | No | Maximum event start date-time |
| `--end-date-min` | No | Minimum event end date-time |
| `--end-date-max` | No | Maximum event end date-time |
| `--limit` | No | Maximum events to return, 1-500 |
| `--offset` | No | Result offset, zero-based |

### Example

```bash
mm predict events list --tag-slug sports --limit 10
mm predict events list --active --featured
```

## `predict events get` Command

Inspect a single Polymarket event by slug or ID.

### Syntax

```bash
mm predict events get <event>
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `<event>` | Yes | Event slug or ID |

### Example

```bash
mm predict events get some-event-slug
```

## `predict series list` Command

List Polymarket event series, which are recurring groupings of events.

### Syntax

```bash
mm predict series list [--recurrence <recurrence>] [--active] [--featured] [--tag-slug <slug>] [--limit <n>] [--offset <n>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--recurrence` | No | Filter by recurrence: `annual`, `daily`, `weekly`, or `monthly` |
| `--active` | No | Active series only |
| `--featured` | No | Only featured series |
| `--tag-slug` | No | Filter by tag slug |
| `--limit` | No | Maximum series to return, 1-500 |
| `--offset` | No | Result offset, zero-based |

### Example

```bash
mm predict series list --recurrence weekly --limit 10
```

## `predict series get` Command

Inspect a single event series by ID.

### Syntax

```bash
mm predict series get <id>
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `<id>` | Yes | Series ID |

### Example

```bash
mm predict series get 12345
```

## `predict tags list` Command

List Polymarket tags, useful for `--tag-slug` / `--tag-id` filters on events and markets.

### Syntax

```bash
mm predict tags list [--limit <n>] [--offset <n>] [--is-carousel]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--limit` | No | Maximum tags to return, 1-500 |
| `--offset` | No | Result offset, zero-based |
| `--is-carousel` | No | Only carousel tags |

### Example

```bash
mm predict tags list --limit 50
```

## `predict tags get` Command

Fetch a single Polymarket tag by numeric ID or slug.

### Syntax

```bash
mm predict tags get <tag>
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `<tag>` | Yes | Tag ID as integer or slug string |

### Example

```bash
mm predict tags get sports
mm predict tags get 100
```

## `predict quote` Command

Preview order cost and fill before placing.

### Syntax

```bash
mm predict quote --token-id <token-id> --side <side> --size <size> [--limit-price <price>] [--tick-size <tick>] [--password <password>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--token-id` | Yes | Outcome token ID. Run `mm predict markets get --market <slug>` to get token IDs |
| `--side` | Yes | Order side: `buy` or `sell` |
| `--size` | Yes | Order size in shares, human-readable, such as 1 or 100 |
| `--limit-price` | No | Execution price per share, between 0 and 1 |
| `--tick-size` | No | Market tick size override: `0.1`, `0.01`, `0.005`, `0.0025`, `0.001`, or `0.0001`. Defaults to the CLOB tick for the token |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |

### Example

```bash
mm predict quote --token-id <token-id> --side buy --size 1
mm predict quote --token-id <token-id> --side sell --size 5 --limit-price 0.60
mm predict quote --token-id <token-id> --side buy --size 10 --tick-size 0.01
```

## `predict place` Command

Place a Predict order supporting GTC/GTD limit and FOK/FAK market types.

### Syntax

```bash
mm predict place --token-id <token-id> --side <side> --size <size> --price <price> [--tick-size <tick>] [--order-type <type>] [--post-only] [--expiration <unix>] [--password <password>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--token-id` | Yes | Outcome token ID. Run `mm predict markets get --market <slug>` to get token IDs |
| `--side` | Yes | Order side: `buy` or `sell` |
| `--size` | Yes | Order size in shares, human-readable, such as 1 or 100 |
| `--price` | Yes | Worst price per share between 0 and 1; limit price for GTC/GTD, worst fill for FOK/FAK |
| `--tick-size` | No | Market tick size override: `0.1`, `0.01`, `0.005`, `0.0025`, `0.001`, or `0.0001`. Defaults to the CLOB tick for the token |
| `--order-type` | No | Order type: `GTC`, `GTD`, `FOK`, or `FAK`. Defaults to `GTC` |
| `--post-only` | No | Reject if the order would cross the book. Not supported with FOK/FAK orders |
| `--expiration` | If `GTD` | Expiration as a Unix timestamp in seconds. Only valid for GTD orders |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |

### Validation Rules

- `--post-only` cannot be used with FOK or FAK orders.
- `--expiration` is only valid for GTD orders.

### Example

```bash
mm predict place --token-id <token-id> --side buy --size 1 --price 0.80
mm predict place --token-id <token-id> --side buy --size 5 --price 1 --order-type FOK
mm predict place --token-id <token-id> --side sell --size 2 --price 0.7 --order-type GTD --expiration 1735689600
```

## `predict cancel` Command

Cancel Predict orders by ID, market, asset, or all open orders.

### Syntax

```bash
mm predict cancel [<order-id>] [--order-id <id>] [--all] [--market <condition-id>] [--asset <token-id>] [--password <password>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `<order-id>` | Yes, unless `--all`, `--market`, or `--asset` is used | Order ID to cancel |
| `--order-id` | No | Same as positional `<order-id>` |
| `--all` | No | Cancel all open orders |
| `--market` | No | Cancel orders for a given market condition ID |
| `--asset` | No | Cancel orders for a specific outcome token ID |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |

### Validation Rules

- Use only one of `--order-id`, `--all`, or `--market`/`--asset`. Market and asset can be combined as one target.

### Example

```bash
mm predict cancel <order-id>
mm predict cancel --order-id <order-id>
mm predict cancel --all
mm predict cancel --market <condition-id>
mm predict cancel --asset <token-id>
```

## `predict positions` Command

View your Predict positions.

### Syntax

```bash
mm predict positions [--market <id>] [--password <password>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--market` | No | Market slug, ID, or condition ID. Run `mm predict markets search` or `mm predict markets list` to find markets |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |

### Example

```bash
mm predict positions
mm predict positions --market <condition-id>
```

## `predict portfolio` Command

Full portfolio snapshot: deposit wallet pUSD balance, open positions with estimated value, and outstanding redeemable winnings.

### Syntax

```bash
mm predict portfolio [--password <password>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |

### Example

```bash
mm predict portfolio
```

## `predict redeem list` Command

List all redeemable winning positions in your deposit wallet, with position size and market question.

### Syntax

```bash
mm predict redeem list [--password <password>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |

### Example

```bash
mm predict redeem list
```

## `predict redeem` Command

Redeem winning tokens after market resolution. Redeem one position by condition ID, or all redeemable positions with `--all`. With `--wait`, polls for the transaction receipt.

### Syntax

```bash
mm predict redeem [<condition-id>] [--all] [--wait] [--password <password>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `<condition-id>` | Yes, unless `--all` is used | Market condition ID to redeem |
| `--all` | No | Redeem all redeemable positions |
| `--wait` | No | Block until the redemption transaction is confirmed |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |

### Validation Rules

- Provide either a `<condition-id>` or `--all`, not both.

### Example

```bash
mm predict redeem 0xABC123... --wait
mm predict redeem --all --wait
```

## `predict orders` Command

View open Predict orders.

### Syntax

```bash
mm predict orders [--market <condition-id>] [--cursor <cursor>] [--password <password>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--market` | No | Market slug, ID, or condition ID. Run `mm predict markets search` or `mm predict markets list` to find markets |
| `--cursor` | No | Pagination cursor from a previous response |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |

### Example

```bash
mm predict orders
mm predict orders --market <condition-id>
```

## `predict balance` Command

Check deposit wallet funds, approvals, and setup status.

### Syntax

```bash
mm predict balance [--token-id <token-id>] [--sync] [--password <password>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--token-id` | No | Outcome token ID. Run `mm predict markets get --market <slug>` to get token IDs |
| `--sync` | No | Refresh balances and allowances before reading |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |

### Example

```bash
mm predict balance --sync
mm predict balance --token-id <token-id> --sync
```

## `predict withdraw` Command

Withdraw pUSD from your Predict deposit wallet to your owner EOA or another address. Validates the amount against the on-chain deposit wallet balance before signing. Uses the Polymarket Relayer batch mechanism.

### Syntax

```bash
mm predict withdraw --amount <amount> [--to <address>] [--wait] [--password <password>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--amount` | Yes | pUSD amount to withdraw, human-readable, such as 0.1, 5, or 100 |
| `--to` | No | Recipient address. Defaults to your owner EOA |
| `--wait` | No | Block until the job completes |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |

### Example

```bash
mm predict withdraw --amount 10 --wait
mm predict withdraw --amount 5 --to 0xAbc... --wait
```

## `predict deposit` Command

Convert USDC.e from your EOA to pUSD in your Predict deposit wallet.

### Syntax

```bash
mm predict deposit --amount <amount> [--wait] [--password <password>] [--wallet-timeout <seconds>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--amount` | Yes | pUSD amount to deposit, human-readable, such as 5 or 100 |
| `--wait` | No | Block until the job completes |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |
| `--wallet-timeout` | No | Seconds to wait per wallet job including MFA and signing, max 600. Overrides config `walletTimeoutSeconds` |

### Example

```bash
mm predict deposit --amount 5 --wait
```

## `predict book` Command

Fetch the raw order book for an outcome token.

### Syntax

```bash
mm predict book <token-id> [--token-id <token-id>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `<token-id>` | Yes | Outcome token ID. Run `mm predict markets get --market <slug>` to get token IDs |
| `--token-id` | No | Same as positional `<token-id>` |

### Example

```bash
mm predict book --token-id <token-id>
```

## `predict watch` Command

Watch a setup, approval, deposit, withdraw, or order job until it completes.

### Syntax

```bash
mm predict watch <id> [--id <id>] [--wait] [--password <password>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `<id>` | Yes | Job or transaction ID to watch |
| `--id` | No | Same as positional `<id>` |
| `--wait` | No | Block until the job completes |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |

### Example

```bash
mm predict watch <job-id> --wait
mm predict watch --id <job-id> --wait
```

## `predict history` Command

List closed Predict positions by default, or trade/redeem activity with `--type trade|redeem`.

### Syntax

```bash
mm predict history [--type <type>] [--limit <n>] [--offset <n>] [--start <unix>] [--end <unix>] [--sort-by <field>] [--sort-direction <dir>] [--side <side>] [--password <password>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--type` | No | History source: `closed` by default, `trade`, or `redeem` |
| `--limit` | No | Page size, 1-500. Closed max 50, trade/redeem default 100 |
| `--offset` | No | Pagination offset, zero-based |
| `--start` | No | Lower-bound activity time in unix seconds. Only applies to trade and redeem types |
| `--end` | No | Upper-bound activity time in unix seconds. Only applies to trade and redeem types |
| `--sort-by` | No | Sort field. For `--type closed`: `realizedpnl`, `title`, `price`, `avgprice`, or `timestamp`. For `--type trade` or `redeem`: `timestamp` by default, `tokens`, or `cash` |
| `--sort-direction` | No | Sort direction: `asc` or `desc` |
| `--side` | No | Filter trades by side: `buy` or `sell`. Only applies to `--type trade` |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |

### Output

**Closed positions** via `--type closed`, the default, include: condition ID, slug, outcome, realized PnL, average entry price, settlement price, size, and timestamps.

**Trade/redeem rows** via `--type trade` or `--type redeem` include:

| Field | Description |
| --- | --- |
| `conditionId` | Market condition ID |
| `slug` | Market slug, use with `mm predict markets get --market <slug>` |
| `eventSlug` | Parent event slug, if available |
| `outcome` | Outcome token label, such as "Yes" or "No" |
| `size` | Share count |
| `value` | USDC notional, either trade cost or redeem payout |
| `price` | Execution price per share |
| `at` | ISO timestamp |
| `timestamp` | Raw epoch seconds |
| `transactionHash` | Transaction hash |
| `side` | buy/sell, if available |
| `redeemed` | Trade rows only: whether any redeem activity exists for this condition |
| `result` | Trade rows only: settlement status `won`, `lost`, or `pending` |
| `amountWon` | Trade rows only, if redeemed: redeem payout in USDC |

Pagination: when `hasMore` is `true`, the CLI auto-generates a next-page command hint with the correct `--limit`, `--offset`, `--type`, `--start`, and `--end` values.

### Example

```bash
mm predict history
mm predict history --type trade --limit 10
mm predict history --type redeem --limit 10
mm predict history --type trade --side buy --sort-by cash --sort-direction desc
mm predict history --type closed --sort-by realizedpnl --sort-direction desc
mm predict history --type trade --start 1719792000 --end 1719878400
```

## `predict history get` Command

Show closed-position, trade, or redeem history for a specific market condition.

### Syntax

```bash
mm predict history get <condition-id> [--type <type>] [--password <password>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `<condition-id>` | Yes | Market condition ID |
| `--type` | No | History source: `closed` by default, `trade`, or `redeem` |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |

### Example

```bash
mm predict history get 0xABC123...
mm predict history get 0xABC123... --type trade
mm predict history get 0xABC123... --type redeem
```

## Notes

- Before trading, run `mm predict setup --wait` to initialize credentials, deploy the deposit wallet, and set approvals.
- `mm predict setup` aborts early with `PREDICT_GEOBLOCKED` if your IP resolves to a restricted region, before any wallet interaction. Use `mm predict geoblock` to check region status without running setup.
- Polymarket HTTP 451 maps to `PREDICT_UNAVAILABLE_FOR_LEGAL_REASONS`, not generic `PREDICT_ERROR`. It is distinct from `PREDICT_GEOBLOCKED`.
- Use `mm predict markets get --market <slug>` to get outcome token IDs required by `quote`, `place`, `book`, and `balance --token-id`.
- Use `mm predict events`, `mm predict series`, and `mm predict tags` to browse Polymarket content; tag slugs/IDs from `mm predict tags list` feed the `--tag-slug` / `--tag-id` filters on `events` and `markets`.
- After a market resolves, use `mm predict redeem list` to see winnings and `mm predict redeem <condition-id> --wait` or `--all` to claim them. `mm predict portfolio` shows balance, open positions, and redeemable winnings in one snapshot.
- Prices are per-share and must be in the range [0, 1].
- Side must be `buy` or `sell`.
- The `predict mode` command switches between `mainnet` and `testnet`.
- If the user does not specify a mode, the CLI uses the previously set mode.
- Use `mm predict history` to review closed positions by default, past trades via `--type trade`, or redemptions via `--type redeem`. Closed positions show realized PnL. Trade rows include a `result` field with values `won`, `lost`, or `pending` and, if redeemed, an `amountWon` payout. Use `mm predict history get <condition-id>` to drill into a specific market.
- Setup, approve, deposit, withdraw, redeem, and order flows can return job IDs. Track them with `mm predict watch <job-id> --wait`.
