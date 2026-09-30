# Login Workflow

Use this workflow when the user needs to log in to the CLI.

Reference command syntax in `references/auth.md`.

## Flow

1. Ask the user which login method they want: MetaMask Mobile QR or browser (Google / Email).
2. Execute login.
3. Verify with token.

## Login

Always use `--no-wait` for browser login since the agent runs non-interactively:

```bash
mm login browser --no-wait
```

The command prints a sign-in URL and exits. The user opens the URL in a browser, signs in via Google or Email, and receives a CLI token. Complete login with:

```bash
mm login --token "<TOKEN>"
```

`mm login qr` (scan with MetaMask Mobile) keeps the CLI attached to the relay, so it does not support `--no-wait`.

## Confirm

Run `mm doctor` to verify the session is ready. It reports `authenticated` and `initialized` booleans. Do not proceed until both are `true`. If `initialized` is `false`, follow `workflows/onboarding.md` to run `mm init`.

```bash
mm doctor
```

