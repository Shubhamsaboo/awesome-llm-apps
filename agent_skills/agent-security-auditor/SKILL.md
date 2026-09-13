---
name: agent-security-auditor
description: >-
  Runs this repo's skill_scanner locally: a stdlib-only offline static scan of
  an agent skill (or a tree of SKILL.md folders) for ClawHavoc-style install
  lures, curl-to-shell, undeclared network calls, credential harvesting,
  obfuscated payloads, and unpinned installs, mapped to the OWASP Agentic
  Skills Top 10 (AST01-AST10). Use when the user asks to security-scan a skill,
  audit a SKILL.md before installing, check for install lures or skill
  supply-chain issues, run the same skill_scanner CI gate locally, or says
  "scan this skill" / "is this skill safe to install".
license: Apache-2.0
metadata:
  author: "Matt Van Horn"
  version: "1.0.0"
  source: "https://github.com/Shubhamsaboo/awesome-llm-apps"
---

# Agent Security Auditor

Same checks GitHub Actions runs on every `agent_skills/**` change, as an
installable skill. Point it at a skill folder (or a tree of them). It prints
findings. It never executes the scanned files and it never talks to the
network.

The pattern tables live in `scripts/skill_scanner.py`. CI imports that
same module through a trampoline next to the other eval tools, so a
local run and the `security-scan` job cannot drift.

## When to use

- The user wants to security-scan a skill, a `SKILL.md`, or a skills tree
- Before installing a skill, including one from this repo
- The user mentions install lures, ClawHavoc, skill supply-chain, or
  `skill_scanner`
- A contributor wants the CI security gate without pushing a PR

## When not to use

- CVE audits of application dependencies — that is `pip-audit` / `npm audit`
  / dependency-doctor, not this
- Pentesting a web app, host, or cloud account
- Reviewing a voice ramble or an echo brief — that is thinking-out-loud
- Executing a skill to "see if it is malicious" — this scanner is static;
  never run untrusted skill scripts to evaluate them

## Run it

From this skill directory:

```bash
python3 scripts/audit.py /path/to/some-skill
python3 scripts/audit.py /path/to/some-skill --json
```

In a clone of this repo, these are the same scanner:

```bash
python3 agent_skills/agent-security-auditor/scripts/audit.py agent_skills
python3 agent_skills/evals/tools/skill_scanner.py agent_skills
```

Useful flags (passed through to the scanner):

- `--json` — machine-readable report (`findings`, `summary`, `verdict`)
- `--include-fixtures` — also scan a skill's own evals fixtures directory
  (skipped by default; those dirs may hold deliberate test payloads)

Exit codes: `0` = no CRITICAL findings, `1` = at least one CRITICAL, `2` =
usage error (path missing, or no `SKILL.md` under the path).

The scan is read-only. It does not install the skill, does not fetch URLs, and
does not eval scanned code.

## Reading the report

Load `references/checks.md` for the check-id catalog and
`references/skill-supply-chain.md` before writing the verdict. Present
findings high-to-low severity:

1. **CRITICAL** — do not install or run the skill until a human has read every
   flagged line. Typical hits: remote fetch piped into a shell (ClawHavoc
   delivery), `exec`/`eval` of decoded payloads, credential files plus
   network in the same file.
2. **WARN** — read the file before approving. Undeclared network, credential
   touches, long base64 blobs, unpinned installs, install-shaped prose.
3. **INFO** — documented, still worth a glance. Documentation code examples
   and `evals/` test data are downgraded to INFO on purpose.

A clean scan is necessary and not sufficient. Natural-language attacks
bypass pattern scanners (OWASP AST08). After a clean run, still read
`SKILL.md` end-to-end.

## Writing the verdict

Turn the scanner output into a short report the user can act on:

1. **Census.** Skills scanned, counts by severity, the scanner `verdict`
   (`PASS` / `REVIEW-WARNINGS` / `REJECT-PENDING-REVIEW`).
2. **Findings.** One block per finding: severity, check id, file:line, the
   scanner's message, and the evidence line. Do not paraphrase away a
   CRITICAL. Quote the evidence.
3. **What to do.** CRITICAL → do not install. WARN → name the files to read.
   PASS → say the pattern scan is clean, then remind them to read `SKILL.md`.
4. **Limits.** This is a static pattern scan of the skill folder. It does not
   prove the skill is safe, does not check PyPI/npm advisories, and does not
   catch prompts that never match a regex.

If the user asked about one skill, scan that folder, not the whole tree. If
they asked whether "our CI would catch this", run the scanner on the same
path CI uses (`agent_skills`) and say so.

## Gotchas

- **Self-matches.** Docs and the scanner that *describe* attack patterns
  suppress a line with the marker `skillscan` + `:allow` (one word, with a
  colon). Do not add that marker to a skill you are reviewing.
- **Fixtures.** A skill's own evals fixtures directory is skipped unless
  `--include-fixtures`. Targeting the fixture directory itself still scans it.
- **Markdown fences.** WARN hits inside a fenced example are downgraded to
  INFO. CRITICAL patterns are never downgraded: ClawHavoc lures lived in
  fenced "Prerequisites" blocks.
- **Name vs directory.** Frontmatter `name` must equal the folder name.
  A mismatch is a typosquat signal (`META03`).

## Files

- `scripts/audit.py` — CLI entry point (stdlib, offline, read-only)
- `scripts/skill_scanner.py` — the canonical scanner CI imports
- `references/checks.md` — check ids, severity, what to do
- `references/skill-supply-chain.md` — why these patterns exist, and the
  limits of a pattern scan
