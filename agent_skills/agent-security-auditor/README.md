# Agent Security Auditor

**The same `skill_scanner` CI runs on this repo, as an installable offline skill.**

Point it at a skill folder. It reports ClawHavoc-style install lures, remote
fetch piped into a shell, undeclared network calls, credential harvesting,
obfuscated payloads, and unpinned installs. Stdlib only, no network, never
executes scanned code.

Contributors can run the checks locally that the `security-scan` job runs in
GitHub Actions. The pattern tables live in this skill. CI reaches them
through a trampoline next to the other eval tools.

![Agent Security Auditor demo](https://github.com/mvanhorn/awesome-llm-apps/releases/download/demo-assets/agent-security-auditor.gif)

## What it flags

| Severity | Examples |
|---|---|
| **CRITICAL** | Remote script piped into a shell; `exec`/`eval` of decoded data; credential files plus network in the same file; install/prereq blocks that fetch and run a remote script |
| **WARN** | Undeclared network calls; SSH/AWS/keychain reads; long base64 blobs; unpinned pip packages; install-shaped "run this to activate" prose |
| **INFO** | Documented network when `compatibility` declares it; hits inside `evals/` test data; WARN patterns inside markdown examples |

A clean report is necessary, not sufficient. Read `SKILL.md` anyway.
Natural-language attacks do not match regexes (OWASP AST08).

## Install (10 seconds)

```bash
npx skills add https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/agent_skills/agent-security-auditor
```

The [skills CLI](https://skills.sh) installs it into whichever agents you have
(Claude Code, Codex, Cursor, Copilot, Antigravity, and others); or copy this
folder into your agent's skills dir. Then: *"scan this skill before I
install it"*.

Standalone, no agent required:

```bash
python3 agent-security-auditor/scripts/audit.py /path/to/some-skill
```

In a clone of this repo (same scanner CI uses):

```bash
python3 agent_skills/evals/tools/skill_scanner.py agent_skills
python3 agent_skills/agent-security-auditor/scripts/audit.py agent_skills
```

## Scope and privacy

Everything runs locally: Python 3.8+, stdlib only, zero network calls,
read-only. It reads text files under the given path; it does not eval them
and it does not fetch the URLs it flags. Prove it works before installing,
from a clone of this repo:

```bash
python3 agent_skills/evals/agent-security-auditor/test_auditor.py
```

Limits: static patterns only. It will not catch a prompt that never matches a
regex, and it is not a CVE audit of the skill's dependencies.

## Files

```
agent-security-auditor/              # ← this is all that gets copied
├── SKILL.md                         # agent instructions: when to scan, how to verdict
├── README.md                        # this file
├── scripts/audit.py                 # CLI wrapper (same flags as the scanner)
├── scripts/skill_scanner.py          # canonical scanner (CI imports this file)
└── references/
    ├── checks.md                   # check ids, severity, what to do
    └── skill-supply-chain.md        # why these patterns exist; scanner limits
```

Part of [awesome-llm-apps](https://github.com/Shubhamsaboo/awesome-llm-apps) · Apache-2.0 · Last verified: September 2026
