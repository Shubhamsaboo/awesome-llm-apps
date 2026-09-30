---
name: metamask-agent-wallet
description: Use when the user asks anything about blockchain wallets, transactions, signing, token transfers, supported chains, wallet balances, perpetual futures trading, prediction markets, token swaps, cross-chain bridges, market data, token discovery, decoding EVM calldata, DeFi earn/yield vaults, installing or removing third-party `mm` CLI plugins, or authentication via the MetaMask Agentic CLI; also when an HTTP request returns 402 Payment Required / x402, when an MCP tool call returns an x402 payment-required result, or the agent needs to pay for a paywalled API, endpoint, file, tool, or resource. Single entry point for all mm CLI operations.
license: MIT
compatibility: "Requires the MetaMask Agent Wallet CLI (mm, npm @metamask/agent-wallet 7.x) and Python 3 for the helper scripts. The mm CLI makes network calls to MetaMask services and the chains in use. scripts/x402_pay.py makes HTTPS requests only to the paywalled URL or MCP challenge the user asks to pay. scripts/amount_to_hex.py runs offline."
metadata:
  author: metamask
  version: "7.7.2"
  cliVersion: "7.0.0"
---

# MetaMask Agentic CLI Skill

This skill documents the `mm` CLI surface for MetaMask Agent Wallet authentication, wallet lifecycle, balance queries, token transfers, message and typed-data signing, raw transactions, chain discovery, market data, token discovery, perpetual futures trading, prediction market trading, prediction trade/redeem history, token swaps, cross-chain bridges, DeFi earn/yield vaults, and EVM calldata decoding.

Use the routing table to select the relevant reference file. CLI behavior lives in `references/`. Repeatable operational patterns live in `workflows/`.

## Command Routing

Match the user's intent to a command and reference file, then read the reference before constructing a command. If intent spans multiple domains, load them sequentially in dependency order.

| User Intent | Command | Reference |
| --- | --- | --- |
| Check authentication status | `mm auth status` | [auth.md](references/auth.md) |
| Login in MetaMask Agentic CLI | `mm login` | [auth.md](references/auth.md) |
| Choose a wallet mode and set up policies | `mm init` | [auth.md](references/auth.md) |
| Show current init settings | `mm init show` | [auth.md](references/auth.md) |
| Sign in via QR code with MetaMask Mobile | `mm login qr` | [auth.md](references/auth.md) |
| Sign in via browser (Google or Email) | `mm login browser` | [auth.md](references/auth.md) |
| Sign out | `mm logout` | [auth.md](references/auth.md) |
| Reset CLI session | `mm reset` | [auth.md](references/auth.md) |
| Show CLI configuration | `mm config get` | [auth.md](references/auth.md) |
| Set CLI configuration | `mm config set` | [auth.md](references/auth.md) |
| Set BYOK mnemonic encryption password | `mm wallet password set` | [auth.md](references/auth.md) |
| Change BYOK mnemonic encryption password | `mm wallet password change` | [auth.md](references/auth.md) |
| Remove BYOK mnemonic encryption password | `mm wallet password remove` | [auth.md](references/auth.md) |
| Interpret raw CLI error codes | `AuthError`, `ValidationError`, `WALLET_ERROR` | [errors.md](references/errors.md) |
| Inspect CLI, skills, environment, and session health | `mm doctor` | [doctor.md](references/doctor.md) |
| List installed CLI plugins | `mm plugins` | [plugins.md](references/plugins.md) |
| Inspect an installed CLI plugin | `mm plugins inspect` | [plugins.md](references/plugins.md) |
| Install a CLI plugin | `mm plugins install` | [plugins.md](references/plugins.md) |
| Update a CLI plugin | `mm plugins update` | [plugins.md](references/plugins.md) |
| Uninstall a CLI plugin | `mm plugins uninstall` | [plugins.md](references/plugins.md) |
| Remove all user-installed CLI plugins | `mm plugins reset` | [plugins.md](references/plugins.md) |
| Link a local plugin directory for development | `mm plugins link` | [plugins.md](references/plugins.md) |
| Enable or disable the plugin beta | `mm config set experimentalPlugins` | [plugins.md](references/plugins.md) |
| Decode EVM calldata into a human-readable intent | `mm decode` | [decode.md](references/decode.md) |
| Create a wallet | `mm wallet create` | [wallet.md](references/wallet.md) |
| List all wallets | `mm wallet list` | [wallet.md](references/wallet.md) |
| Switch active wallet | `mm wallet select` | [wallet.md](references/wallet.md) |
| Show active wallet details | `mm wallet show` | [wallet.md](references/wallet.md) |
| Show active wallet address | `mm wallet address` | [wallet.md](references/wallet.md) |
| Check the active wallet balance | `mm wallet balance` | [wallet.md](references/wallet.md) |
| Show a QR code and address to fund the active wallet | `mm wallet add-fund` | [wallet.md](references/wallet.md) |
| Show current trading mode | `mm wallet trading-mode get` | [wallet.md](references/wallet.md) |
| Set trading mode to guard or beast | `mm wallet trading-mode set` | [wallet.md](references/wallet.md) |
| View wallet policy | `mm wallet policy get` | [wallet.md](references/wallet.md) |
| Set wallet policy | `mm wallet policy set` | [wallet.md](references/wallet.md) |
| Show project policy template | `mm wallet policy template` | [wallet.md](references/wallet.md) |
| Sign a plaintext message | `mm wallet sign-message` | [signing.md](references/signing.md) |
| Sign EIP-712 typed data | `mm wallet sign-typed-data` | [signing.md](references/signing.md) |
| Send a raw EVM transaction | `mm wallet send-transaction` | [transaction.md](references/transaction.md) |
| Transfer native tokens or ERC-20 tokens | `mm transfer` | [transfer.md](references/transfer.md) |
| List supported chains by the CLI | `mm chains list` | [chain.md](references/chain.md) |
| List pending wallet requests | `mm wallet requests list` | [polling.md](references/polling.md) |
| Watch a wallet polling id | `mm wallet requests watch` | [polling.md](references/polling.md) |
| Query spot or historical prices | `mm price ...` | [market-data.md](references/market-data.md) |
| Discover tokens, token networks, or token metadata | `mm token ...` | [market-data.md](references/market-data.md) |
| List perpetual markets | `mm perps markets` | [perps.md](references/perps.md) |
| Check perps account balance | `mm perps balance` | [perps.md](references/perps.md) |
| List open perpetual positions | `mm perps positions` | [perps.md](references/perps.md) |
| Get a quote for a perpetual order | `mm perps quote` | [perps.md](references/perps.md) |
| List resting perpetual orders | `mm perps orders` | [perps.md](references/perps.md) |
| Open a perpetual position | `mm perps open` | [perps.md](references/perps.md) |
| Close a perpetual position | `mm perps close` | [perps.md](references/perps.md) |
| Modify leverage, take-profit, or stop-loss | `mm perps modify` | [perps.md](references/perps.md) |
| Cancel a resting perps order | `mm perps cancel` | [perps.md](references/perps.md) |
| Deposit USDC into a perps venue | `mm perps deposit` | [perps.md](references/perps.md) |
| Withdraw USDC from a perps venue | `mm perps withdraw` | [perps.md](references/perps.md) |
| Transfer USDC between spot and perp accounts | `mm perps transfer` | [perps.md](references/perps.md) |
| List perpetual futures venues | `mm perps list-venues` | [perps.md](references/perps.md) |
| List available DEXs for a venue | `mm perps dexs` | [perps.md](references/perps.md) |
| Set Predict trading mode | `mm predict mode` | [predict.md](references/predict.md) |
| One-time Predict setup | `mm predict setup` | [predict.md](references/predict.md) |
| Create or refresh Predict credentials | `mm predict auth` | [predict.md](references/predict.md) |
| Repair Predict approvals | `mm predict approve` | [predict.md](references/predict.md) |
| Check Predict back-end status and account setup | `mm predict status` | [predict.md](references/predict.md) |
| Check if Polymarket is geoblocked for your IP | `mm predict geoblock` | [predict.md](references/predict.md) |
| List prediction markets | `mm predict markets list` | [predict.md](references/predict.md) |
| Search prediction markets | `mm predict markets search` | [predict.md](references/predict.md) |
| Inspect a prediction market | `mm predict markets get` | [predict.md](references/predict.md) |
| List Polymarket events | `mm predict events list` | [predict.md](references/predict.md) |
| Inspect a Polymarket event | `mm predict events get` | [predict.md](references/predict.md) |
| List Polymarket event series | `mm predict series list` | [predict.md](references/predict.md) |
| Inspect a Polymarket event series | `mm predict series get` | [predict.md](references/predict.md) |
| List Polymarket tags | `mm predict tags list` | [predict.md](references/predict.md) |
| Inspect a Polymarket tag | `mm predict tags get` | [predict.md](references/predict.md) |
| Preview a prediction order cost | `mm predict quote` | [predict.md](references/predict.md) |
| Place a prediction market order | `mm predict place` | [predict.md](references/predict.md) |
| Cancel prediction orders | `mm predict cancel` | [predict.md](references/predict.md) |
| View prediction market positions | `mm predict positions` | [predict.md](references/predict.md) |
| View open prediction orders | `mm predict orders` | [predict.md](references/predict.md) |
| Show full Predict portfolio snapshot | `mm predict portfolio` | [predict.md](references/predict.md) |
| List redeemable winning positions | `mm predict redeem list` | [predict.md](references/predict.md) |
| Redeem winning positions | `mm predict redeem` | [predict.md](references/predict.md) |
| Check Predict deposit wallet balance | `mm predict balance` | [predict.md](references/predict.md) |
| Fund Predict deposit wallet | `mm predict deposit` | [predict.md](references/predict.md) |
| Withdraw pUSD from Predict deposit wallet | `mm predict withdraw` | [predict.md](references/predict.md) |
| Fetch prediction order book | `mm predict book` | [predict.md](references/predict.md) |
| Watch a Predict job | `mm predict watch` | [predict.md](references/predict.md) |
| List Predict trade or redeem history | `mm predict history` | [predict.md](references/predict.md) |
| Inspect Predict history for a specific market | `mm predict history get` | [predict.md](references/predict.md) |
| Look up a transaction by hash | `mm tx` | [tx-history.md](references/tx-history.md) |
| List recent transactions for the active wallet | `mm tx history` | [tx-history.md](references/tx-history.md) |
| Get a swap or bridge quote | `mm swap quote` | [swap.md](references/swap.md) |
| Execute a token swap or bridge | `mm swap execute` | [swap.md](references/swap.md) |
| Check swap or bridge status | `mm swap status` | [swap.md](references/swap.md) |
| Bridge tokens to another chain | `mm swap execute` | [swap.md](references/swap.md) |
| Pay an HTTP `402` / x402 paywalled request | `python3 scripts/x402_pay.py` | [x402.md](references/x402.md) |
| Pay an x402-gated MCP tool call | `python3 scripts/x402_pay.py` | [x402.md](references/x402.md) |
| List earn vaults and APYs | `mm earn markets` | [earn.md](references/earn.md) |
| View earn vault positions | `mm earn positions` | [earn.md](references/earn.md) |
| Supply tokens to an earn vault | `mm earn supply` | [earn.md](references/earn.md) |
| Withdraw tokens from an earn vault | `mm earn withdraw` | [earn.md](references/earn.md) |

## Workflows

CLI behavior lives in `references/`. Repeatable patterns live in `workflows/`. Load a workflow file when the user's request is a pattern, not a single command.

| Pattern | Workflow |
| --- | --- |
| First time setup and onboarding | [onboarding.md](workflows/onboarding.md) |
| Login flow | [login.md](workflows/login.md) |
| Troubleshooting decision tree | [troubleshooting.md](workflows/troubleshooting.md) |
| Swap quote-review-execute flow | [swap.md](workflows/swap.md) |
| Bridge quote-review-execute flow | [bridge.md](workflows/bridge.md) |
| Open a perpetual position flow | [perps-open-position.md](workflows/perps-open-position.md) |
| Close a perpetual position flow | [perps-close-position.md](workflows/perps-close-position.md) |
| Modify a perpetual position flow | [perps-modify-position.md](workflows/perps-modify-position.md) |
| Predict first-time setup and credentials | [predict-setup.md](workflows/predict-setup.md) |
| Deposit or withdraw pUSD from Predict wallet | [predict-funding.md](workflows/predict-funding.md) |
| Search and browse prediction markets | [predict-markets.md](workflows/predict-markets.md) |
| Quote and place a prediction order | [predict-place-order.md](workflows/predict-place-order.md) |
| View or cancel Predict orders and positions | [predict-manage-orders.md](workflows/predict-manage-orders.md) |
| View Predict portfolio and redeem winnings | [predict-portfolio.md](workflows/predict-portfolio.md) |
| View Predict trade and redeem history | [predict-history.md](workflows/predict-history.md) |
| Token discovery, prices, and market data | [market-data.md](workflows/market-data.md) |
| Supply tokens to earn yield | [earn-supply.md](workflows/earn-supply.md) |
| Withdraw tokens from an earn vault | [earn-withdraw.md](workflows/earn-withdraw.md) |
| Pay an HTTP `402` (x402) paywalled request | [x402-pay.md](workflows/x402-pay.md) |
| Pay an x402-gated MCP tool call | [x402-mcp.md](workflows/x402-mcp.md) |

## Global Flags

Every `mm` command accepts these flags:

| Flag | Short | Description |
| --- | --- | --- |
| `--format` | `-f` | Output format: `text`, `json`, or `toon`. Defaults to `text` in TTY, `json` when piped |
| `--json` | | Shorthand for `--format=json` |
| `--toon` | | Shorthand for `--format=toon` |
| `--verbose` | `-v` | Show debug logs on stderr. Use for troubleshooting |

Always use `--toon` for command output unless the user explicitly requests a different format.

The `mm plugins` commands are the exception. They come from oclif and accept none of these global flags, so `mm plugins --toon` fails with `Nonexistent flag: --toon`. Use `--json` or plain text there. See [plugins.md](references/plugins.md).

## Preflight

Run these checks before the first CLI operation in a session, in order.

### 1. Version compatibility


This skill is written for `@metamask/agent-wallet` v7.0.0, as specified by `cliVersion` in the frontmatter. The CLI requires Node.js 22.18 or later; on an older runtime every command exits 1 with `UNSUPPORTED_NODE` before the CLI loads. Check the installed version:

```bash
mm --version
```

The installed version is the value after `@metamask/agent-wallet/`, such as `@metamask/agent-wallet/7.0.0 darwin-arm64 node-v22.18.0`. Compare its `major.minor` against the pinned `cliVersion`. Optionally check the latest published version (best-effort, skip silently on network failure):

```bash
npm view @metamask/agent-wallet version
```

If the installed `major.minor` differs from the pinned `cliVersion`, or the installed version is behind the latest release, warn the user once and continue:

> Version mismatch: installed CLI `<installed>`, this skill targets `<cliVersion>`, latest release is `<latest>`. Command syntax in this skill may be inaccurate until they are aligned. Update the CLI with `npm install -g @metamask/agent-wallet@latest`, then update the skills from `MetaMask/agent-skills` with the same tool that installed them, such as the plugin manager or the `skills` CLI.

Run this check once per session. Do not block operations on it.

### 2. Readiness gate — authentication and initialization

`mm doctor` is the single readiness check. Run it before the first CLI operation in a session:

```bash
mm doctor
```

It reports an `authenticated` boolean, an `initialized` boolean, and a list of `hints`. Do not run any other command until `mm doctor` reports both `authenticated: true` and `initialized: true`. Authentication and initialization are independent gates: a session can be authenticated while the project has no wallet mode selected, in which case any command that needs a wallet aborts before running with `NOT_INITIALIZED` — "Project not initialized." with hint: Run `mm init` to set up wallet and trading modes.

A project counts as initialized only when a wallet mode is set — and, for `server-wallet`, a trading mode is set as well. `byok` needs only the wallet mode. Do not use `mm init show` as the check: it requires an initialized project and throws `NOT_INITIALIZED` on an uninitialized one rather than reporting state.

Remediate, then re-run `mm doctor` and confirm a clean result before doing anything else:

- `authenticated: false` → follow `workflows/login.md`, or `workflows/onboarding.md` for first-time setup, to run `mm login`.
- `authenticated: true` and `initialized: false` → follow `workflows/onboarding.md` to run `mm init` and select a wallet mode. For server-wallet, also select a trading mode.

## Safety Rules

These rules apply to every operation, regardless of which reference or workflow is active.

### Input Validation

Before constructing any command, validate all user-provided values:

| Flag | Validation rule |
| --- | --- |
| `--to`, `--address` | Must match `^0x[0-9a-fA-F]{40}$` |
| `--amount` | Human-readable decimal such as 0.5 or 100. Must match `^\d+\.?\d*$`. Reject spaces, semicolons, pipes, backticks, or shell metacharacters |
| `--chain-id` | Must be a positive integer (`^\d+$`) |
| `--payload` for send-transaction | Must be valid JSON. No unescaped shell metacharacters outside the JSON structure |
| `--payload` for decode | Must be 0x-prefixed hex calldata, matching `^0x[0-9a-fA-F]+$` |
| `--token` | Must be a valid hex address or known symbol |
| `--leverage` | Must be a positive integer (`^\d+$`) |
| `--size` | Human-readable positive decimal such as 0.01 or 1. Scientific notation and host-locale grouping/decimals are accepted and canonicalized by the CLI. Reject shell metacharacters. Malformed values return `INVALID_AMOUNT` |
| `--venue` | Must be `hyperliquid` |
| `--side` for perps | Must be `long` or `short` |
| `--order-id` | Must be a positive integer (`^\d+$`) |
| `--token-id` | Must be a non-empty outcome token ID string |
| `--price`, `--limit-price` | Must be a positive number in range `(0, 1]` |
| `--order-type` | Must be one of `GTC`, `GTD`, `FOK`, `FAK` |
| `--side` for predict | Must be `buy` or `sell` |
| `--slippage` | Must be a number between 0 and 100 |
| `--tick-size` | Must be one of `0.1`, `0.01`, `0.005`, `0.0025`, `0.001`, `0.0001` |
| `--from-chain-id`, `--to-chain-id` | Must be a positive integer EVM chain ID |
| `--to-address` | Must match `^0x[0-9a-fA-F]{40}$`. Only valid for cross-chain swaps (`--to-chain-id` differs from `--from-chain-id`); rejected for same-chain swaps |
| `--refuel` | Boolean flag, no value. Only meaningful for cross-chain swaps where `--to-chain-id` differs from `--from-chain-id`. No effect on same-chain swaps |
| `--strategy` | Comma-separated list from: `cost`, `speed`, `impact`, `output` |
| `--wallet-timeout` | Must be a positive integer between 1 and 600 |
| `--password` | Must be a non-empty string. Never log, display, or store the value. |
| Plugin spec for `mm plugins install` | An npm package name, optionally `name@version` or `name@tag`. Reject spaces and shell metacharacters. `file:`, git, and bare `owner/repo` specs are unverified sources and are refused unless the user has enabled dev mode |
| x402 `asset` | Must be a valid contract address on a network returned by `mm chains list`. The currency choice is the server's offer confirmed by the user; the script keeps no currency allowlist. |
| x402 `payTo` / authorization `to` | Must match `^0x[0-9a-fA-F]{40}$` and equal the recipient in the `402` |
| x402 `value` | Atomic-unit integer that exactly equals the offered amount. The `exact` scheme is not a maximum |
| x402 resource URL | Must be `https://`. Reject a `402` reached via an unexpected cross-host redirect |
| x402 MCP challenge | x402 v2 only. The signed `payment` object goes, as-is, in `_meta["x402/payment"]` of the retried tool call; a repeated `isError` result is a new challenge, never re-sign it without new user approval |

Do not pass unvalidated user input into any command.

### Confirmation Requirements

| Operation type | Confirmation rule |
| --- | --- |
| Transfers | Always confirm recipient, amount, token, and chain before executing |
| Raw transactions | Always confirm transaction payload, chain, recipient, value, and calldata summary before executing |
| Message signing | Always show exact message and chain before signing |
| Typed-data signing | Always show domain, primary type, chain, verifying contract, and message summary before signing |
| Swaps / bridges | Always confirm from/to tokens, amount, source/destination chain, slippage, quoted output, recipient address if `--to-address` is set, and the destination gas top-up if `--refuel` is set before executing |
| x402 payments | Always confirm asset, decimals-correct amount, network, `payTo`, and resource URL or MCP tool before signing the authorization — over HTTP with `pay --confirm --approved <approvalId>`, over MCP with `mcp-sign --confirm --approved <approvalId>`. The script refuses to sign if the offer changed after the user approved it. One payment attempt per resource, never auto-retry a payment. Autonomous auto-pay is not supported. |
| Perps trading | Always confirm symbol, side, size, leverage, venue, order type, and limit price if present before executing |
| Perps deposit/withdraw | Always confirm amount, asset, venue, network, and destination where applicable before executing |
| Predict trading | Always confirm token ID, side, size, price, order type, market, and outcome before executing |
| Predict deposit | Always confirm amount before executing |
| Predict withdraw | Always confirm amount and recipient before executing. `--to` defaults to owner EOA |
| Predict redeem | Always confirm the target, either condition ID or `--all`, before executing. `--all` redeems every winning position |
| Earn supply | Always confirm token, amount, chain, vault/protocol, and APY before executing. For cross-chain supply, also confirm source chain and source token |
| Earn withdraw | Always confirm token, amount or full balance, chain, and vault/protocol before executing |
| Plugin install, update, or link | Always show package name, version, declared command ids, `dataAccess`, and every requested capability, and name `wallet-submit` and `network-manage` as sensitive. Get explicit approval before installing. Never pass `--accept-permissions` for a manifest the user has not reviewed |
| Plugin uninstall or reset | Always confirm which packages are affected. `mm plugins reset` removes every user-installed and linked plugin |
| Enabling the plugin beta or unverified installs | Always confirm before running `mm config set experimentalPlugins true` or `mm config set experimentalAllowUnverifiedInstalls true` |
| Commands added by a plugin | Treat these as third-party code running with CLI privileges. Apply the same confirmation rules as the equivalent host operation |
| Cancel-all operations | Always confirm scope and exact destructive effect before executing |
| Wallet policy changes | Broadening policy changes require MFA approval; non-broadening changes apply immediately |
| Trading mode changes | Broadening from guard to beast requires MFA approval. Tightening from beast to guard applies immediately |
| Auth / wallet management | Can run directly. `reset` is the exception and requires explicit user confirmation |
| Read-only queries | Can run directly |

### Credential Safety

- Never store, log, or display private keys, mnemonics, passwords, or auth tokens.
- Never pass `--password` or `--mnemonic` as inline flags. Always instruct the user to set the `MM_PASSWORD` and `MM_MNEMONIC` environment variables instead to avoid exposing secrets in shell history.

### Suspicious Content Warnings

Flag to the user before proceeding if a signing payload or transaction contains:

- URLs or contract addresses the user did not provide
- `permit`, `approve`, `setApprovalForAll`, or allowance-like fields
- Unusually large values or unfamiliar contract interactions

When raw calldata is unfamiliar or was not constructed by you, run `mm decode --payload <0x-calldata>` first and confirm the decoded intent with the user before signing or sending. See [decode.md](references/decode.md).

## Async Model

In both server-wallet and BYOK mode, signing and transaction commands go through a job-polling loop and return a `pollingId`. Handle this consistently:

1. Prefer `--wait` to block until complete.
2. If not using `--wait`, inform the user of the `pollingId` and how to track it:
   - `mm wallet requests list`
   - `mm wallet requests watch <polling-id>`
3. In BYOK mode, the local key signs locally but the operation still produces a pending job and a `pollingId`. If the mnemonic is password-encrypted, the user must set `MM_PASSWORD` environment variable to unlock it for the operation.

Transfers, swaps, perps, predict orders, and predict withdraws attach a human-readable `intent` summary to their wallet request, such as `Transfer 0.5 ETH to 0x...` or `Withdraw 10 pUSD to 0x...`. When surfacing a pending request from `wallet requests list` or `wallet requests watch`, show the `intent` summary so the user can confirm what they are approving.

## MFA Approval Pauses

Wallet jobs that need out-of-band MFA approval pause in `AWAITING_MFA`. **Detect this pause by scanning command stdout for the literal token `AWAITING_MFA`.** Do not infer MFA from free-text alone on older CLIs; from CLI v6.1.5 onward every output mode emits the token consistently.

| Output mode | How to detect |
| --- | --- |
| `--json` / piped stdout | An NDJSON line containing `"_notice":{"kind":"AWAITING_MFA",...}` |
| Plain TTY or Ink REPL | A stdout line containing `[AWAITING_MFA]`, e.g. `⚠ [AWAITING_MFA] Approve in MetaMask mobile.` |

When `AWAITING_MFA` appears:

1. Treat the command as **waiting for user approval**, not failed, hung, or complete.
2. Surface the human instruction from the notice to the user.
3. If a `pollingId` is present in the notice or command output, tell the user they can track completion with `mm wallet requests watch <polling-id>`.
4. Do **not** retry the same wallet operation while the job is still pending.
5. On `mm swap execute`, `mm earn supply`, or `mm earn withdraw`, an MFA pause with no hash yet may return `EXECUTE_FAILED` with a message naming the approval wait and `mm wallet requests watch <polling-id>` — that is still an MFA pause, not a missing hash.

For approval surfaces and recovery steps, see [troubleshooting.md](workflows/troubleshooting.md).

## Response Style

- Route silently. Do not announce which reference you are loading.
- Surface errors from commands verbatim. Do not mask or reword them.
- If a command fails, check `mm <command> --help` and guide from there.
