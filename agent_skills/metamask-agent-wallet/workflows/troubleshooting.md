# Troubleshooting Workflow

Use this workflow when a command fails, hangs, prompts unexpectedly, or behaves differently in a terminal.

## Universal Triage

Run `mm doctor` first to inspect CLI version, skills, environment, and session health in one shot:

```bash
mm doctor
```

If you need more detail, run these in order:

```bash
mm --version
mm auth status
mm <failing-command> --help
```

If `auth status` reports anything other than authenticated, fix authentication before debugging downstream wallet, signing, swap, perps, or predict commands.

## Common Symptoms

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| `mm: command not found` | Binary not installed or not on `PATH` | Check install and PATH |
| `PLUGIN_BETA_DISABLED` on a plugin command or on `mm plugins install` | The plugin system is beta and off by default | Ask the user before running `mm config set experimentalPlugins true`. See `references/plugins.md` |
| `PLUGIN_UNVERIFIED_SOURCE` on install or link | The source is a `file:` spec, a git source, or a bare path rather than npm | Install from npm. For a plugin the user is building, set `experimentalAllowUnverifiedInstalls` to `true` |
| `PERMISSION_DENIED` from a plugin command | The capability was not approved, or the approval no longer matches the installed version and manifest | Run `mm plugins install <pkg>` so the user can approve the current manifest. See `references/plugins.md` |
| `UNSUPPORTED_NODE` on any command | Node.js runtime is older than 22.18 | Upgrade Node.js from https://nodejs.org/ or switch versions with nvm, fnm, or volta, then re-run |
| Async command returns a polling id and appears stuck | Request was dispatched without `--wait` | Use `mm wallet requests list` or `mm wallet requests watch <polling-id>` |
| Auth errors after previously working | Expired token | Check `mm auth status` and session file under `~/.metamask/` |
| `CHAIN_ID_MISMATCH` on typed data | Payload `domain.chainId` differs from `--chain-id` | Align the two chain IDs |
| `MNEMONIC_LOCKED` or `WRONG_PASSWORD` | BYOK mnemonic is encrypted and password was wrong or missing | Set the correct `MM_PASSWORD` environment variable and re-run |
| `ALREADY_ENCRYPTED` on `wallet password set` | Mnemonic already has a password | Use `mm wallet password change` instead |
| `NOT_ENCRYPTED` on `wallet password change/remove` | Mnemonic is not encrypted | Use `mm wallet password set` instead |
| `INSUFFICIENT_FUNDS` | Wallet lacks native gas or token balance | Fund the wallet or use gasless relay (ERC-20 transfers/swaps only on relay-supported chains) |
| `INSUFFICIENT_GAS` | No affordable swap quote; wallet lacks native gas | Fund native gas, or re-quote with `--strategy output` / `--all-quotes` to find a gasless option |
| `GASLESS_UNSUPPORTED` | Gasless relay not available on this chain | Fund native gas or use a different chain |
| `UNSUPPORTED_CHAIN` on swap or predict | Chain not supported for this feature | Run `mm chains list` and use a chain with the required feature |
| `QUOTE_PERSIST_FAILED` on `swap quote` | `~/.metamask/swap-quotes/` is not writable; the CLI already retried once | Run `mkdir -p "$HOME/.metamask/swap-quotes" && chmod u=rwx,go= "$HOME/.metamask/swap-quotes"`, then re-run the quote |
| `INVALID_DATA` on `price history` | Price API returned an empty or malformed body | Retry once, then check the asset is priced with `mm price spot --asset-ids <chain-id>/<asset-type>` |
| `INVALID_ASSET_ID` on `price spot` / `price history` / `token assets` | Malformed CAIP-19 id, or a bare chain id where a full asset id is required | Use `eip155:1/slip44:60` (or `erc20:0x…`). On `price spot` only, `eip155:1` expands to the native asset |
| `PREDICT_UNAVAILABLE_FOR_LEGAL_REASONS` | Polymarket HTTP 451 | Distinct from `PREDICT_GEOBLOCKED`. Run `mm predict geoblock` and do not retry trading from a restricted region |
| `REFUEL_UNSUPPORTED_ROUTE` | `--refuel` used on same-chain swap or native-destination bridge | Drop `--refuel` and re-run |
| `AMOUNT_TOO_LOW` or `AMOUNT_TOO_HIGH` | Amount outside provider's accepted range | Adjust the amount and re-quote |
| `SLIPPAGE_TOO_HIGH` or `SLIPPAGE_TOO_LOW` | Slippage outside accepted range for this route | Adjust `--slippage` and re-quote |
| `UNKNOWN_FLAG` with flag list | Unrecognized CLI flag | Check `mm <command> --help` for valid flags |
| `INVALID_CHAIN` | Unsupported or malformed chain ID | Run `mm chains list`; use chain name, numeric ID, or CAIP-2 (e.g. `eip155:1`) |
| `TRADING_MODE_APPROVAL_REJECTED` or `_EXPIRED` | MFA approval for trading mode change was rejected or timed out | Retry `mm wallet trading-mode set` and approve via MFA |
| `WALLET_POLICY_APPROVAL_REJECTED` or `_EXPIRED` | MFA approval for policy change was rejected or timed out | Retry `mm wallet policy set` and approve via MFA |
| `INVALID_POLICY_YAML` on `wallet policy set` | `--policy` was a fragment, list, bare string, or empty document instead of a full policy object | Start from `mm wallet policy get --json` or `mm wallet policy template`, edit that YAML, and pass the complete document with a top-level `schema_version` |
| `INVALID_LIMIT` on `tx history` | `--limit` above 50, the Accounts API page-size ceiling | Use `--limit 50` and page with `--after <endCursor>` |
| Command output contains `AWAITING_MFA` | MFA approval needed — see **MFA Approval Pauses** in `SKILL.md` | Approve via MetaMask Mobile (QR login) or email/dashboard (browser login). For QR login users: the MFA request appears in the notifications menu inside MetaMask Mobile. If push notifications are not showing, check that notifications are enabled in both MetaMask Mobile settings (Settings > Notifications) and at the device level (iOS/Android system settings). The notification permission may have been declined during MetaMask onboarding — re-enable it from the device settings. Regardless of push notification settings, the MFA request is always available in the MetaMask Mobile notifications menu |
| `JOB_TIMEOUT` | Wallet job poll timed out (default 10 minutes) | Approve on your paired device if prompted, or check `mm wallet requests list` before retrying |
| `TX_DENIED` | Transaction was denied via MFA | Retry the command and approve when prompted |
| `TX_EXPIRED` | Transaction MFA approval expired | Retry the command and approve promptly |
| `AUTH_FAILED` after a working session | Session token expired during operation | Run `mm login` to re-authenticate |
| `RELAY_TIMEOUT` on swap execute | Gasless relay MFA/signing timed out | Run `mm wallet requests watch <polling-id>` — the job may still complete. Do not re-run execute while the job is pending |
| `RATE_LIMITED` on perps commands | Hyperliquid rate limit (HTTP 429) | Wait briefly and retry |
| `ALREADY_LOGGED_OUT` on logout | No active session to sign out of | Run `mm login` to authenticate |
| `INVALID_EVM_ADDRESS` on transfer | Malformed recipient address | Check the `--to` address is a valid `0x`-prefixed 40-hex-char EVM address |

## Verbose Logging

Use `--verbose` when a command appears to hang or hides progress:

```bash
mm wallet balance --json --verbose
```

Structured logs and progress lines go to stderr; command results remain on stdout.

## Error Codes

For raw error-code meanings, load `../references/errors.md`. Relay CLI errors verbatim before explaining them.

## Reset Last

Use `mm reset` only after checking version, auth status, and the failing command's help output. Reset clears local session state and should not be the first troubleshooting step. Always ask the user for explicit confirmation before running reset. The command itself also prompts for confirmation; pass `--yes` to skip the prompt in non-interactive sessions.
