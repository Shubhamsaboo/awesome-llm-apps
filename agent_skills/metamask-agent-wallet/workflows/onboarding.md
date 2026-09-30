# Onboarding Workflow

Use this workflow when the user is setting up the MetaMask Agentic CLI for the first time.

Reference command syntax in `references/auth.md` and `references/wallet.md`.

## Flow

1. Check CLI installation.
2. Login.
3. Initialize wallet mode.
4. Verify readiness.
5. Show wallet address.

## Check CLI Installation

```bash
mm --version
```

If this fails, the CLI is not installed. Guide the user to install it with `npm install -g @metamask/agent-wallet@latest` before proceeding. The CLI requires Node.js 22.18 or later; on an older runtime every command exits with `UNSUPPORTED_NODE`.

Then run the version compatibility check from the skill `Preflight` section: compare the installed `major.minor` against the pinned `cliVersion` and the latest published release, and warn the user if they are out of sync.

## Login Flow

Ask the user which login method they want to use: MetaMask Mobile QR or browser (Google or Email). QR (`mm login qr`) is available on all environments, including production, but it needs an interactive terminal — in a headless session it returns `NO_TTY`, so use browser login there.

### Login

```bash
mm login browser --no-wait
```

Use `--no-wait` for non-interactive environments. The command prints a sign-in URL; the user completes sign-in in the browser using Google or Email.

### Verify

Once the user completes sign-in, verify with:

```bash
mm login --token "<TOKEN>"
```

## Initialize Project

First check whether the project is already initialized with `mm doctor` (read its `initialized` boolean):

```bash
mm doctor
```

If `initialized` is `true`, skip this step.

For server-wallet mode, if the account already has a remote wallet, `mm init` syncs it and reuses the existing trading mode — no trading-mode prompt. For BYOK mode, if a trading mode is already set server-side for the wallet, it is loaded without prompting.

Otherwise, ask the user which wallet mode they want:
- `server-wallet` (recommended) — keys are hosted by MetaMask infrastructure. No need to manage private keys or mnemonics.
- `byok` — bring your own mnemonic. The user manages their own keys locally.

Ask the user which trading mode they want (applies to both server-wallet and BYOK):
- `guard` — enforces outflow and whitelist policies. When a policy is violated, the CLI requires MFA confirmation before proceeding.
- `beast` — skips all policy checks and confirmations. Useful for scripting or experienced users who want faster execution.

Server wallet:

```bash
mm init --wallet server-wallet --mode guard
```

BYOK:

Never pass `--mnemonic` or `--password` as inline flags. Always instruct the user to set environment variables instead. The user runs these `read` commands in their own terminal, so the secret never appears in the command line, shell history, or this conversation.

```bash
read -rs MM_MNEMONIC && export MM_MNEMONIC   # paste the phrase; nothing is echoed or saved to history
mm init --wallet byok --mode guard
```

If the user wants to encrypt their mnemonic with a password during init:

```bash
read -rs MM_MNEMONIC && export MM_MNEMONIC   # paste the phrase; nothing is echoed or saved to history
read -rs MM_PASSWORD && export MM_PASSWORD   # type the password; nothing is echoed or saved to history
mm init --wallet byok --mode guard
```

If the mnemonic was stored unencrypted, suggest setting a password afterward:

```bash
mm wallet password set
```

Once the mnemonic is encrypted, all subsequent operations that need the private key require the `MM_PASSWORD` environment variable to be set. Never instruct the user to pass `--password` inline.

## Verify Readiness

```bash
mm doctor
```

Confirm `mm doctor` reports both `authenticated: true` and `initialized: true` with no blocking hints before proceeding. (`mm auth status` reports only authentication and does not reflect initialization, so it cannot confirm readiness on its own.)

## Show Wallet Address

```bash
mm wallet address
```
