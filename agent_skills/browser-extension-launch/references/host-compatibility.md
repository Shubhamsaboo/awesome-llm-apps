# Agent host compatibility

Read this when installing, resuming on a different agent, or resolving a missing tool or child skill. The shared workflow is host-neutral; installation paths, tool names, permission prompts, and browser automation vary by host.

## Verified Skill CLI targets

The public repository root contains one valid `SKILL.md`. Skill CLI 1.7.0 discovered it and installed the complete folder for these targets in an isolated project:

| Agent target | Skill CLI id | Installed through |
| --- | --- | --- |
| Codex | `codex` | shared `.agents/skills` |
| Claude Code | `claude-code` | `.claude/skills` plus shared skill files |
| Cursor | `cursor` | shared `.agents/skills` |
| GitHub Copilot | `github-copilot` | shared `.agents/skills` |
| OpenCode | `opencode` | shared `.agents/skills` |

Install for all five:

```bash
npx skills add xiehuan123/browser-extension-launch \
  --skill browser-extension-launch \
  --agent codex claude-code cursor github-copilot opencode
```

Use `-g` for user-level installation. Current Skill CLI 1.7.0 requires Node.js 22.20+. Other supported agents can use `--agent '*'`; do not claim a host is verified until its installation and required runtime capabilities have been exercised.

## Capability contract

Before doing project work, identify the host and verify these capabilities separately:

1. Read and write the project and skill resources.
2. Run local commands in the project directory.
3. Load or control a real browser environment capable of exercising an unpacked extension and its native entry point.
4. Preserve project state and evidence across turns or sessions.
5. Invoke installed child skills, or execute an explicitly documented portable fallback.

Installing this skill does not grant those tools. A host lacking file or shell access can only provide guidance. A host lacking controlled extension-capable browser automation cannot certify a working delivery; keep acceptance blocked or deliver source only when the user explicitly chooses that scope.

## Child skill adapters

Prefer the named child skills because their reviewed workflows are the reference implementation. Discover installed skills first. When missing and the host supports Skill CLI, install from the pinned public sources in `required-skills.json`, targeting the current agent.

- `chrome-extensions`, `extension-create`, `diagnosing-bugs`, `code-review`, and the complex-project chain have public sources recorded in the dependency manifest.
- `product-designer` has no verified portable public source in the current manifest. On hosts where it is absent, `product-loop.md` is the approved portable fallback. Record that fallback instead of claiming the named skill ran.
- A host-native skill may replace a named child only when its actual instructions cover the same outcome and constraints. Record its source, what was read, produced artifacts, and any gaps.

Never install by guessing a similarly named repository. Do not overwrite a customized skill. If installation requires the host to restart, save progress and verify discovery after restart.

## Browser tool adapters

The acceptance contract is provider-neutral even though `playwright-mcp.md` is the reference setup:

- Prefer Playwright MCP when it can load the current extension and operate the native entry point.
- Chrome DevTools MCP, another browser MCP, or a controlled browser harness is acceptable only after capability probing shows it covers the required actions.
- Record the selected provider, browser version, package fingerprint, native entry evidence, core flow, reopen behavior, and repeat use.
- Webpage screenshots, a directly opened popup HTML file, mocked Chrome APIs, and static package checks do not replace native extension acceptance.

Use the acceptance gate's provider and user-choice fields. If no provider can exercise the needed native browser surface, explain the concrete gap and keep the affected delivery state blocked.
