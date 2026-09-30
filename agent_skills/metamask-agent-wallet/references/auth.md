# Authentication Commands

Use these commands to initialize wallet mode, sign in, inspect authentication status, and clear local session state.

## `init` Command

Initialize the project by selecting wallet mode and trading mode. Requires an authenticated session. Run `mm login` first.

### Syntax

```bash
mm init [--wallet <mode>] [--mode <mode>] [--mnemonic <phrase>] [--password <password>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--wallet` | No | Wallet mode: `server-wallet` or `byok` |
| `--mode` | No | Trading mode: `guard` or `beast` |
| `--mnemonic` | No | BIP-39 mnemonic phrase for BYOK wallet. Never pass inline. Set `MM_MNEMONIC` env var instead. |
| `--password` | No | Password to encrypt the BYOK mnemonic at rest. Never pass inline. Set `MM_PASSWORD` env var instead. If omitted in interactive mode, the CLI prompts. If omitted in non-interactive mode, mnemonic is stored unencrypted. |

### Example

```bash
mm init
mm init --wallet server-wallet --mode beast
read -rs MM_MNEMONIC && export MM_MNEMONIC   # paste the phrase; nothing is echoed or saved to history
mm init --wallet byok --mode guard

read -rs MM_MNEMONIC && export MM_MNEMONIC   # paste the phrase; nothing is echoed or saved to history
read -rs MM_PASSWORD && export MM_PASSWORD   # type the password; nothing is echoed or saved to history
mm init --wallet byok --mode guard
```

### Note

- In server-wallet mode, if the account already has a remote EVM wallet, `mm init` syncs it and loads the existing trading mode instead of prompting for a new trading mode or creating a wallet. Use `mm wallet policy get` to view the wallet policy.
- In BYOK mode, `mm init` registers the wallet server-side and prompts for trading mode (`guard` or `beast`). If a trading mode is already set server-side, it is loaded without prompting. The `--mode` flag skips the prompt in non-interactive/scripted use. Server-side registration must succeed — if it fails, the CLI throws `WALLET_NOT_REGISTERED` and rolls back the wallet mode so subsequent commands are blocked by the init gate.

## `init show` Command

Display the current initialization settings (wallet mode, trading mode). Use `mm wallet policy get` to view the wallet policy separately.

### Syntax

```bash
mm init show
```

### Supported Flags

This command does not support additional flags beyond output format options.

### Example

```bash
mm init show
```

## `login` Command

Sign in to the CLI. On a TTY, bare `mm login` shows a method picker (MetaMask Mobile QR or browser). QR is recommended but not auto-selected. `mm login browser` covers both Google and Email — the user picks interactively in the browser.

### Syntax

```bash
mm login [qr | browser] [--token <token>] [--timeout <seconds>] [--otp-pair] [--no-wait]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--token` | No | Pre-minted CLI token in `cliToken:cliRefreshToken` format. Can also be set via the `MM_CLI_TOKEN` env var |
| `--timeout` | No | Seconds to wait for QR or browser callback |
| `--otp-pair` | No | Use the legacy MWP 6-digit pairing-code flow for browser login instead of the default paste-token flow. Only valid with `browser`. Cannot be combined with `--no-wait` or `--token` |
| `--no-wait` | No | Print the sign-in URL and exit without waiting, for non-interactive or CI use. Not supported with QR login or `--otp-pair`. Complete later with `mm login --token` |

### Example

```bash
mm login browser
mm login browser --no-wait
mm login browser --otp-pair
mm login --token "cliToken:cliRefreshToken"
```

### Note

- `mm login browser`, the default, opens the dashboard URL and prompts the user to paste a CLI token in `cliToken:cliRefreshToken` format. This is the recommended flow for agents.
- `mm login browser --otp-pair` restores the legacy MWP 6-digit pairing-code flow.
- If already authenticated, the CLI returns `ALREADY_AUTHENTICATED`. Run `mm logout` first, then log in again.
- `mm login qr`, scan with MetaMask Mobile, is available on all environments, including production.
- Pairing codes tolerate `-` and whitespace separators, so `608-225` is equivalent to `608225`.
- Use `mm login browser --no-wait` for non-interactive/CI flows. The command prints a sign-in URL; the user completes login in the browser via Google or Email. Bare `mm login --no-wait` fails without a TTY because no method is selected.
- `--no-wait` is not supported with QR login or `--otp-pair`. Complete authentication later with `mm login --token`.
- After a successful login in server-wallet mode, the CLI automatically syncs existing wallets from the server. Run `mm wallet list` immediately — no need to re-run `mm init`. In BYOK mode, no sync occurs; run `mm init` to configure the wallet.

## `auth status` Command

Show the current authentication status.

### Syntax

```bash
mm auth status [--toon]
```

### Supported Flags

This command does not support additional flags beyond output format options.

### Example

```bash
mm auth status
mm auth status --toon
```

## `logout` Command

Sign out and clear auth credentials plus local init state, wallet selection, and stored BYOK mnemonic. Prompts for confirmation before signing out. If no active session exists, returns `reason: ALREADY_LOGGED_OUT` with a hint to run `mm login`, exit 0, not an error.

### Syntax

```bash
mm logout [--yes]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--yes` | No | Skip the confirmation prompt, for non-interactive or scripted use |

### Example

```bash
mm logout
mm logout --yes
```

## `config get` Command

Show persisted CLI configuration. Does not require authentication.

### Syntax

```bash
mm config get [env|verbose|format|walletTimeoutSeconds|experimentalPlugins|experimentalAllowUnverifiedInstalls]
```

### Supported Keys

| Key | Description |
| --- | --- |
| `env` | Target API environment: `prod`, `dev`, or `uat`. Defaults to `prod` when unset |
| `verbose` | Whether verbose logging is persisted, `true` or `false` |
| `format` | Default output format: `json`, `text`, or `toon` |
| `walletTimeoutSeconds` | Default wallet job timeout in seconds, 1-600 |
| `experimentalPlugins` | Enable the beta `mm plugins` system, `true` or `false`. Defaults to `false`. When false, plugin commands fail with `PLUGIN_BETA_DISABLED` |
| `experimentalAllowUnverifiedInstalls` | Allow `file:`, git, and `mm plugins link` sources, `true` or `false`. Required in addition to `experimentalPlugins` for those sources |

Omit the key to return all values.

### Example

```bash
mm config get
mm config get env
```

## `config set` Command

Persist a CLI configuration value in `~/.metamask/config.json`. Does not require authentication.

### Syntax

```bash
mm config set <env|verbose|format|walletTimeoutSeconds|experimentalPlugins|experimentalAllowUnverifiedInstalls> <value>
```

### Supported Keys

| Key | Values |
| --- | --- |
| `env` | `prod`, `dev`, or `uat` |
| `verbose` | `true` or `false` |
| `format` | `json`, `text`, or `toon` |
| `walletTimeoutSeconds` | Positive integer, 1-600 |
| `experimentalPlugins` | `true` or `false` |
| `experimentalAllowUnverifiedInstalls` | `true` or `false` |

### Overrides

Persisted values can be overridden per invocation without changing `~/.metamask/config.json`:

| Key | Override |
| --- | --- |
| `env` | `MM_ENV` environment variable |
| `verbose` | `--verbose` / `-v` flag |
| `format` | `--format`, `--json`, `--toon`, etc. |

### Example

```bash
mm config set env prod
mm config set env dev
mm config set env uat
mm config set format toon
mm config set experimentalPlugins true
```

### Note

- Switch environments at any time with `mm config set env <prod|dev|uat>`.
- Non-prod sessions are stored in env-scoped files under `~/.metamask/`, such as `session.dev.json` and `session.uat.json`; prod uses `session.json`.
- The plugin system is off by default. For plugin install and run, set `experimentalPlugins` to `true`. For local `file:` / git / `plugins link`, also set `experimentalAllowUnverifiedInstalls`.

## `reset` Command

Clear the local CLI session entirely, including auth credentials, wallet state, mnemonic, swap quotes, and persisted config. Prompts for confirmation before resetting.

### Syntax

```bash
mm reset [--yes]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--yes` | No | Skip the confirmation prompt, for non-interactive or scripted use |

### Example

```bash
mm reset
mm reset --yes
```

## `wallet password set` Command

Set a password to encrypt the BYOK mnemonic at rest. Only available in BYOK mode when the mnemonic is currently unencrypted.

### Syntax

```bash
mm wallet password set [--new <password>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--new` | No | New password. Never pass it inline. Omit it so the CLI prompts interactively. |

### Example

```bash
mm wallet password set
```

The CLI prompts for the new password. Do not pass `--new` with a value, because it would appear in shell history, process listings, and the agent transcript.

## `wallet password change` Command

Change the BYOK mnemonic encryption password. Only available when the mnemonic is currently encrypted.

### Syntax

```bash
mm wallet password change [--current <password>] [--new <password>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--current` | No | Current password. Never pass it inline. Omit it so the CLI prompts interactively. |
| `--new` | No | New password. Never pass it inline. Omit it so the CLI prompts interactively. |

### Example

```bash
mm wallet password change
```

The CLI prompts for the current and new passwords. Do not pass `--current` or `--new` with a value.

## `wallet password remove` Command

Remove the BYOK mnemonic encryption password, storing the mnemonic as plaintext. Only available when the mnemonic is currently encrypted.

### Syntax

```bash
mm wallet password remove [--current <password>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--current` | No | Current password. Never pass it inline. Omit it so the CLI prompts interactively. |

### Example

```bash
mm wallet password remove
```

The CLI prompts for the current password. Do not pass `--current` with a value.

## Wallet Modes

| Mode | Behavior |
| --- | --- |
| `server-wallet` | Keys hosted by MetaMask infrastructure. Signing and transaction operations return async job handles with a `pollingId`. |
| `byok` | Bring your own local mnemonic. Keys are held locally and signing is done on-device, but operations still go through a job-polling loop and return a `pollingId`. If the mnemonic is encrypted with a password, the CLI requires `MM_PASSWORD` to unlock before any operation that needs the private key. |
