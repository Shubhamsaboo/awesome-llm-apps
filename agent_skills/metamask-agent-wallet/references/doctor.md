# Doctor command

Use `mm doctor` to inspect CLI version, AI skills / plugin install, environment, and session health. This command does not require authentication or initialization.

## `doctor` command

### Syntax

```bash
mm doctor
mm doctor --json
mm doctor --toon
```

### Supported flags

This command does not support additional flags beyond output format options.

### Output

| Field | Type | Description |
| --- | --- | --- |
| `cli` | string | Installed CLI version (`@metamask/agent-wallet`) |
| `env` | string | Current environment (`prod`, `dev`, or `uat`) |
| `authenticated` | boolean | Whether the CLI session is valid (Hydra token valid or refreshed) |
| `initialized` | boolean | Whether you have run `mm init` (wallet mode and trading mode are set for server wallets) |
| `recommendedSkills` | object | Installed MetaMask AI skill status for `metamask-agent-wallet` and `metamask-agent-workflows` |
| `compatible` | boolean or null | Whether the installed CLI version is compatible with the installed skills. `null` if no skills are detected |
| `skillSource` | string or null | `plugin` (marketplace plugin), `skills-cli` (installed with the `skills` CLI), or `null` |
| `agentHost` | string or null | Detected calling agent host (`claude-code`, `cursor`, `codex`, `antigravity`, `grok`, …) or `null` |
| `installSource` | string or null | First-touch channel from `~/.metamask/attribution.json`, or `null` |
| `hints` | string[] | Actionable guidance, for example missing skills, auth issues, init needed, or version mismatch |

### Skill detection

`mm doctor` resolves skills in this order:

1. `MM_PLUGIN_ROOT/skills/<name>/SKILL.md` (set by the plugin session-start hook)
2. Claude / Cursor plugin caches under `~/.claude/plugins` and `~/.cursor/plugins`
3. Global skills lock file (`~/.agents/.skill-lock.json` or `$XDG_STATE_HOME/skills/.skill-lock.json`), then project/global `.agents/skills`

When the lock file exists but contains no MetaMask entries, it falls back to scanning the current project for installed `metamask-agent-wallet` / `metamask-agent-workflows` skills. It parses `SKILL.md` frontmatter for the skill `version` and `cliVersion` metadata, then checks the CLI `major.minor` against the skill `cliVersion` requirement.

When skills come from the plugin, upgrade hints point at the marketplace and pin `npm install -g @metamask/agent-wallet@<cliVersion>` instead of the `skills` CLI.

### Example

```bash
mm doctor
mm doctor --json
mm doctor --toon
```

### Notes

- Use as the first step in troubleshooting to check if CLI, auth, init, and skills are healthy.
- Run after a CLI upgrade to verify skill compatibility.
- Use in CI or scripting to confirm environment and session state.
- Do not run wallet write commands until `authenticated: true` and `initialized: true`. Follow `workflows/onboarding.md` / `workflows/login.md` when hints say so.
