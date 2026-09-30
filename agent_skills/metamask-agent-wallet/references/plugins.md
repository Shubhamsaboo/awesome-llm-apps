# Plugins commands

Third-party npm packages can add first-class `mm` commands that appear in `mm help` and in the REPL. The `mm plugins` commands manage them. This system is beta and off by default.

This reference covers CLI plugins only. It is unrelated to the agent skills install that `mm doctor` reports as `skillSource`. See [doctor.md](doctor.md) for that.

## Trust model

Read this before installing anything. Plugins run in-process and unsandboxed, with the same privileges as the CLI. Install-time consent is the real trust boundary. Capability gates and the hidden session and mnemonic store are defense in depth, and a malicious package can import the SDK directly.

| Rule | Detail |
| --- | --- |
| Never install without explicit user approval | Show the package name, version, declared commands, data access, and requested capabilities, then ask. Approval for one package never carries over to another |
| Never bypass the consent prompt | Pass `--accept-permissions` only when the user has already reviewed the manifest and the environment cannot show a prompt |
| Treat sensitive capabilities as high risk | The consent screen marks `wallet-submit` and `network-manage` with a warning sign. Call them out explicitly |
| Keep unverified installs off | Enable `experimentalAllowUnverifiedInstalls` only for a plugin the user is building |
| Apply host confirmation rules to plugin commands | A plugin command that signs or submits is still a write operation. Confirm it the way you confirm `mm transfer`, and run `mm decode` on unfamiliar calldata |

Signing from a plugin still routes through MetaMask policy and stays MFA gated.

## Enabling the beta

Installing a plugin and running a plugin command are both blocked until the user enables the feature.

```bash
mm config set experimentalPlugins true
```

A local source needs a second key as well. Local sources are `file:` specs, relative paths, absolute paths, git sources, and `mm plugins link`.

```bash
mm config set experimentalAllowUnverifiedInstalls true
```

Both keys live in `~/.metamask/config.json` and are documented in [auth.md](auth.md). Run `mm config get` to read the current state before assuming either key is on.

Setting `experimentalPlugins` back to `false` leaves plugins installed and makes their commands fail with `PLUGIN_BETA_DISABLED`.

```bash
mm config set experimentalPlugins false
```

## Commands

| Intent | Command | Beta gate |
| --- | --- | --- |
| List installed plugins | `mm plugins` | No |
| Show a plugin's version, location, and commands | `mm plugins inspect <plugin>` | No |
| Install from npm | `mm plugins install <pkg>` | Yes |
| Update installed plugins | `mm plugins update [<pkg>]` | Yes |
| Link a local directory for development | `mm plugins link <path>` | Yes, and unverified installs as well |
| Remove one plugin | `mm plugins uninstall <plugin>` | No |
| Remove every user-installed and linked plugin | `mm plugins reset` | Yes |

Listing, inspecting, and uninstalling are never beta gated, so the user can always see what is installed and remove it.

`mm plugins add` is an alias of install. `mm plugins remove` and `mm plugins unlink` are aliases of uninstall.

### Output format

These commands come from oclif rather than the host command layer, so the global `--format` and `--toon` flags do not apply. `mm plugins --toon` fails with `Nonexistent flag: --toon`. Use `--json` or plain text instead.

| Command | Flags |
| --- | --- |
| `mm plugins` | `--json`, `--core` to include core plugins |
| `mm plugins inspect` | `--json`, `--verbose` |
| `mm plugins install` | `--json`, `--force`, `--silent`, `--verbose`, `--accept-permissions` |
| `mm plugins update` | `--verbose` |
| `mm plugins link` | `--install`, `--verbose` |
| `mm plugins uninstall` | `--verbose` |
| `mm plugins reset` | `--hard`, `--reinstall` |

The host help cannot resolve `mm plugins install --help`. Use the colon form instead, such as `mm plugins:install --help`.

## Install flow

1. Check the gate with `mm config get`. If `experimentalPlugins` is `false`, ask the user before setting it to `true`.

2. Preview the package before installing it. The consent screen is built from the `mm` block in the package's `package.json`, and the CLI reads that block with this call.

   ```bash
   npm view <pkg> --json
   ```

   Surface every command id, every `dataAccess` entry, and every capability to the user. Capabilities come from both `mm.capabilities` and `mm.commands[].capabilities`.

3. Install one package at a time so each consent screen is reviewed on its own.

   ```bash
   mm plugins install @acme/mm-report
   ```

   The permission screen prints on stderr and the confirm prompt defaults to No. Declining exits with `PERMISSION_DENIED` and changes nothing.

4. A non-TTY session cannot show that prompt, and neither can a run that passes `--json`. Both fail with `PERMISSION_DENIED` unless `--accept-permissions` is passed. Add that flag only after the user has approved the reviewed manifest.

   ```bash
   mm plugins install @acme/a @acme/b --accept-permissions
   ```

   One `--accept-permissions` consents to every package named in the command, so prefer separate commands.

5. Verify with `mm plugins` and `mm plugins inspect <plugin>`, then run the new command.

Installs fail closed. If the npm registry is unreachable or the package cannot be resolved, nothing is installed and the CLI reports `PLUGIN_METADATA_UNAVAILABLE`. Plugin lifecycle scripts such as `postinstall` never run, because the CLI forces `npm_config_ignore_scripts` to `true` on every plugin install, update, link, reset, and uninstall.

### What must hold for an install to succeed

| Requirement | Error when violated |
| --- | --- |
| Package name and version resolve | `PLUGIN_NOT_FOUND` |
| The `mm` block in `package.json` is a valid manifest, with `schemaVersion` 1, a `minCliVersion`, and at least one command | `PLUGIN_MANIFEST_INVALID` |
| The running CLI satisfies `minCliVersion` | `PLUGIN_CLI_VERSION` |
| No command id collides with a built-in `mm` command | `PLUGIN_ID_COLLISION` |
| The package declares neither `oclif.hooks` nor `oclif.plugins` | `PLUGIN_HOOKS_FORBIDDEN` |
| The package ships a prebuilt `oclif.manifest.json` | `PLUGIN_MANIFEST_FILE_MISSING`, and the CLI removes the plugin again |
| Each command class extends `PluginCommand` | `PLUGIN_INVALID_BASE` |
| No sealed lifecycle member is overridden | `PLUGIN_SEALED_OVERRIDE` |
| The source is npm, unless dev mode is on | `PLUGIN_UNVERIFIED_SOURCE` |

## Capabilities

Capabilities are declared per command in the manifest and approved at install time.

| Capability | Grants | Sensitive |
| --- | --- | --- |
| `wallet-read` | Read services for accounts, balances, prices, tokens, fees, and swap quotes, plus an authenticated public client for raw EVM RPC reads | No |
| `wallet-submit` | The wallet executor for signing and submitting. Every use is audited, and policy and MFA gates still apply | Yes |
| `network-manage` | The network registry | Yes |

`mnemonic-read` and `config-write` are reserved and are not part of the beta schema. A manifest that declares either one fails validation. The CLI session and the mnemonic store are host only, so a plugin that reaches for them gets `PERMISSION_DENIED`.

The consent screen also lists the `dataAccess` entries for each command. The full set is `accounts`, `balances`, `prices`, `tokens`, `network`, `fees`, `swap-quotes`, `session`, and `mnemonic`. That list is disclosure only. Enforcement happens through capabilities.

## Approvals and repeat consent

An approved install writes a record under `plugins` in `~/.metamask/config.json`. The record holds `version`, `integrity`, `manifestHash`, `approvedCapabilities`, `approvedCommandIds`, and `approvedAt`.

A fresh consent prompt appears whenever the version or the manifest hash changes, including on `mm plugins update`. Until the new manifest is approved, the plugin's commands run with zero capabilities, and any call that needs one fails with `PERMISSION_DENIED`. The same downgrade applies when the approval record is missing, and when the command id is missing from `approvedCommandIds`.

When a plugin command returns `PERMISSION_DENIED`, do not retry it. Run `mm plugins install <pkg>` or `mm plugins update <pkg>` so the user can approve the current manifest, then run the command again.

## Uninstall

```bash
mm plugins uninstall @acme/mm-report
```

This removes the plugin code and deletes its approval record from `~/.metamask/config.json`. It is not beta gated and does not prompt for consent, so it still works after `experimentalPlugins` is set back to `false`. The argument is the installed package name, with or without a version or dist tag suffix.

Reset removes everything the user installed or linked.

```bash
mm plugins reset
```

`mm plugins reset` is beta gated and destructive across all plugins. Show the `mm plugins` output and confirm the scope with the user first.

If the user wants the commands gone but the packages kept, set `experimentalPlugins` to `false` instead of uninstalling.

## Where things live

| What | Where |
| --- | --- |
| Plugin code | The oclif data directory. On macOS that is `~/Library/Application Support/mm/node_modules/<pkg>` and on Linux it is `~/.local/share/mm/node_modules/<pkg>` |
| Approvals and beta flags | `~/.metamask/config.json`, under the `plugins`, `experimentalPlugins`, and `experimentalAllowUnverifiedInstalls` keys |
| Host peer symlink | A link inside the data directory points `@metamask/agent-wallet` at the running CLI. The CLI creates it so a plugin import of `@metamask/agent-wallet/plugin` resolves to the same in-process instance |

Manage all of this through the commands above. Never hand-edit `~/.metamask/config.json`, and never delete files under `~/.metamask/`, because that directory also holds wallets, the session, and the BYOK mnemonic.

## Local development

Use these steps only for a plugin the user is building.

```bash
mm config set experimentalPlugins true
mm config set experimentalAllowUnverifiedInstalls true
mm plugins install file:/path/to/mm-plugin-hello.tgz --accept-permissions
mm plugins link /path/to/mm-plugin-hello
```

These sources show an unverified source banner ahead of the capability screen. A local install and a link both still write an approval record, built from the `package.json` on disk. A bare path such as `acme/mm-hello` reads as a GitHub slug rather than a directory, and the CLI refuses it unless dev mode is on.

## Notes

- Plugin commands respect `requiresAuth` and `requiresInit`, and both default to `true`. Most plugin commands therefore need `mm login` and `mm init` first, exactly like host commands. Run the `mm doctor` readiness gate before invoking one.
- A user-installed plugin overrides a core plugin of the same name.
- `mm plugins` lists user plugins only. Add `--core` to include the bundled oclif plugins.
- `MM_NPM_LOG_LEVEL` sets the npm log level for these installs, and `MM_NPM_REGISTRY` sets the npm registry.
