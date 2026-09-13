# Check catalog

How to read a finding. The scanner prints `SEVERITY`, `CHECK`, `file:line`,
a message, and an evidence snippet. This file is the meaning of each check
id. Sources: ClawHavoc (Jan 2026) and the OWASP Agentic Skills Top 10.

Lines that would otherwise match a pattern (including this file) carry the
inline suppress marker so the auditor can describe attacks without failing
its own scan. skillscan:allow

## CRITICAL

| Id | What matched | What to do |
|---|---|---|
| `EXEC01` | Remote content piped into a shell (`curl`/`wget` → `sh`, or PowerShell `iex`) | Do not run it. This is the ClawHavoc delivery shape. |
| `EXEC02` | `base64 --decode` piped into a shell or interpreter | Treat as a staged payload. Decode offline if you must, never pipe. |
| `OBF02` | `exec`/`eval`/`Function` over `base64`/`atob`/`fromhex` data | Staged payload. Read the decoded bytes before trusting the file. |
| `LURE01` | Install/prerequisite section tells the user or agent to fetch and run a remote script | The #1 ClawHavoc vector. Lived in fenced "Prerequisites" blocks. |
| `EXFIL01` | Same file touches credentials/environment **and** makes network calls | Standard exfil shape. Review every line of that file. |
| `CRED01` | Reads SSH keys, AWS creds, or the macOS keychain | Credential harvest. Confirm the skill has a legitimate reason. |

## WARN

| Id | What matched | What to do |
|---|---|---|
| `LURE02` | A fetch command in `SKILL.md` outside an install heading | Verify the URL is pinned and the destination is intended. |
| `LURE03` | Prose that says to run a command to "activate" / "initialize" / "enable" | Install-time execution lure, even without a pipe. |
| `OBF01` | Long base64-like literal (≥120 chars) | Encoded payloads hide from review. Decode before trusting. |
| `NET01` | Network call in a script, not declared in frontmatter `compatibility` | Either declare it or remove it. Description-only mentions do not count. |
| `CRED01` | Credential-bearing dotfiles (netrc / npmrc / pypirc), gcloud, browser stores, wallets, agent env files | Same family as CRITICAL `CRED01`, lower confidence. |
| `CRED02` | Dumps the whole process environment | Easy secret leak if combined with any output channel. |
| `PIN01` | Unpinned pip package install | Version can drift to a compromised release. Prefer an exact pin or a lockfile. |
| `META01`–`META03` | Missing frontmatter, missing/invalid `name`, or `name` ≠ directory | Agents cannot discover the skill safely; name mismatch is a typosquat signal. |
| `META04` | Missing `description` | The description is the entire trigger surface. |

## INFO

| Id | What matched | What to do |
|---|---|---|
| `META05` | Description longer than 1024 characters | Spec limit. Trim it. |
| `PIN01` (npm) | Unpinned `npm install` | Prefer an exact version or a lockfile. |
| `NET01` (declared) | Network call with `compatibility` declaring network | Expected. Still confirm the destination. |
| downgraded WARN | Hit inside a markdown code fence, or under `evals/` | Illustrative or test data. Confirm it is not loaded at runtime. |

CRITICAL patterns are **never** downgraded for being inside a fence.
Install lures were documented as copy-pasteable commands.

## Verdicts

The JSON `verdict` field:

- `REJECT-PENDING-REVIEW` — at least one CRITICAL
- `REVIEW-WARNINGS` — no CRITICAL, at least one WARN
- `PASS` — no CRITICAL, no WARN (INFO may still be present)

Exit code `1` only on CRITICAL. WARN does not fail CI. That is deliberate:
the gate blocks install-lure and staged-payload shapes; warnings stay
reviewable so documentation-heavy skills are not punished for quoting them.
