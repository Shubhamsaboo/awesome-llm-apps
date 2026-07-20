# 🧩 Agent Skills

**Drop-in skills for Claude Code, Codex, Cursor, OpenClaw, Hermes, Antigravity, and any [SKILL.md](https://agentskills.io)-compatible agent.**

A skill is a folder with a `SKILL.md` file — plus scripts and references — that your agent discovers and loads on demand. One skill works across Claude Code, Codex, Cursor, and other coding agents.

## The bar

Most "skills" on registries are text-only prompt dumps — advice the model already knows, wrapped in frontmatter. Skills here have to earn their place:

- **Real scripts** — deterministic work runs as code, not as token generation
- **Researched references** — deep content loads on demand, with sources
- **Evidence over vibes** — every claim a skill makes must be checkable
- **Local and private by default** — no network calls unless declared, nothing leaves your machine
- **Tested before shipped** — on real inputs, not just happy-path fixtures

## Skills

| Skill | What it does |
|---|---|
| [🧠 advisor-orchestrator-worker](advisor-orchestrator-worker/) | Turns your agent into the orchestrator of a three-tier model team: cheap stateless workers in parallel, expensive advisor consulted only at commitment boundaries, verification gates between every step — budgeted so a run can't burn a hole in your API bill |
| [🏺 commit-archaeologist](commit-archaeologist/) | Reconstructs why a file or code region exists from local git history, including its introducing commit, later edits, repeated companion files, current authorship, and intent clues |
| [⚰️ project-graveyard](project-graveyard/) | Scans your machine for dead side projects, autopsies why each one died from its git history (deploy fear, payments wall, killed by a newer project), shows your personal death patterns, and resurrects the one with a pulse — with relapse tracking on every resurrection it prescribes |
| [🔭 scope-creep-detector](scope-creep-detector/) | Checks a diff against its stated intent, flags unrelated files and scope signals, and recommends what to keep, split, or justify |
| [♾️ self-improving-agent-skills](self-improving-agent-skills/) | Automatically optimizes agent skills using Gemini and ADK |

More coming, released one at a time.

## ⚡ Install

One command, any agent — the [skills CLI](https://skills.sh) detects what you have installed (Claude Code, Codex, Cursor, Copilot, Antigravity, OpenClaw, Hermes, and other coding agents) and puts the skill in the right place:

```bash
npx skills add https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/agent_skills/<skill>
```

Prefer manual? Clone the repo and copy the skill folder into your agent's skills dir:

| Agent | Skills dir |
|---|---|
| Claude Code | `~/.claude/skills/` |
| Codex | `~/.codex/skills/` |
| Cursor | `~/.cursor/skills/` |
| GitHub Copilot / VS Code | `~/.copilot/skills/` |
| Antigravity CLI | `.agents/skills/` in your project |
| OpenClaw | `~/.openclaw/skills/` |
| Hermes | `~/.hermes/skills/` (also reads `~/.agents/skills/`) |

Team install: put the skill in `.agents/skills/` inside your repo — it's the shared project-level dir most 2026 agents read (Codex, Cursor, Copilot, Antigravity; Claude Code uses `.claude/skills/`).

## Before you install any skill — including ours

Skills run with your agent's permissions: your shell, your files, your credentials. Treat them like software, not documents. Read the `SKILL.md` and every script before installing, from us or anyone. Skills here declare any network use up front and ship no install-time execution — nothing asks your agent to `curl | bash` anything, ever.

Every skill also has an executable eval in [`evals/`](evals/) — run it from the clone before installing, and note what you *don't* copy: the skill folder contains only what runs at runtime.
