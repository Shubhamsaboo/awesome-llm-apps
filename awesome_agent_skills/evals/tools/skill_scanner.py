#!/usr/bin/env python3
"""
[vendored] Repo-side CI copy. Origin: the agent-security-auditor skill (revamp
branch). If that skill ever ships on main, make it the single source of truth.
skill_scanner.py — static security scanner for agent skills.

Scans one skill directory (or a tree of them) for the attack patterns seen in
real skill supply-chain campaigns (ClawHavoc, Jan 2026) and mapped to the
OWASP Agentic Skills Top 10 (AST01-AST10).

Usage:
    python3 skill_scanner.py <path-to-skill-or-skills-dir>
    python3 skill_scanner.py <path> --json

Python 3.8+, stdlib only, makes no network calls, never executes scanned code.

Exit codes: 0 = no CRITICAL findings, 1 = at least one CRITICAL, 2 = usage error.

Lines containing the marker "skillscan" + ":allow" (written as one word with a
colon) are skipped, so scanners and docs that *describe* attack patterns can
suppress self-matches.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

VERSION = "1.0.0"
SEV_RANK = {"CRITICAL": 3, "WARN": 2, "INFO": 1}
SCAN_EXTS = {".md", ".markdown", ".py", ".sh", ".bash", ".zsh", ".js", ".mjs",
             ".cjs", ".ts", ".ps1", ".rb", ".pl", ".txt", ".yaml", ".yml",
             ".json", ".toml"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".mypy_cache"}
MAX_FILE_BYTES = 1_000_000
SUPPRESS_MARKER = "skillscan" + ":allow"  # built at runtime so this file can be scanned

NETWORK_DECLARE_WORDS = ("network", "internet", "http", "online", "api access", "web access")

# ---------------------------------------------------------------------------
# Pattern tables. Each entry: (compiled regex, check id, severity, message)
# ---------------------------------------------------------------------------

PIPE_SHELL_PATTERNS = [
    (re.compile(r"(?:curl|wget)\b[^\n|]{0,200}\|\s*(?:sudo\s+)?(?:ba|z|da|fi)?sh\b"),  # skillscan:allow
     "EXEC01", "CRITICAL", "Remote script piped directly into a shell (curl/wget to shell)"),  # skillscan:allow
    (re.compile(r"(?i)(?:iwr|irm|invoke-webrequest|downloadstring)[^\n]{0,160}\|\s*iex\b"),  # skillscan:allow
     "EXEC01", "CRITICAL", "PowerShell download piped into Invoke-Expression (iex)"),
    (re.compile(r"(?i)\biex\b[^\n]{0,160}(?:downloadstring|invoke-webrequest|\biwr\b|\birm\b)"),  # skillscan:allow
     "EXEC01", "CRITICAL", "Invoke-Expression executing downloaded content"),
    (re.compile(r"base64\s+(?:-d|-D|--decode)\b[^\n]{0,120}\|\s*(?:sudo\s+)?(?:ba|z)?sh\b"),  # skillscan:allow
     "EXEC02", "CRITICAL", "base64-decoded data piped into a shell"),
    (re.compile(r"\|\s*base64\s+(?:-d|-D|--decode)\b[^\n]{0,80}\|\s*(?:python3?|node|perl|ruby)\b"),  # skillscan:allow
     "EXEC02", "CRITICAL", "base64-decoded data piped into an interpreter"),
]

OBFUSCATION_EXEC_PATTERNS = [
    (re.compile(r"(?:\bexec|\beval|\bcompile)\s*\([^\n]{0,160}(?:b64decode|base64|fromhex|codecs\.decode|rot13)"),  # skillscan:allow
     "OBF02", "CRITICAL", "exec/eval of decoded (base64/hex/rot13) data — classic staged payload"),
    (re.compile(r"(?:\beval|new\s+Function)\s*\([^\n]{0,160}(?:atob|Buffer\.from)\s*\("),  # skillscan:allow
     "OBF02", "CRITICAL", "JavaScript eval/Function over decoded data — classic staged payload"),
    (re.compile(r"(?:python3?|node)\s+-[ce]\s+[^\n]{0,60}(?:b64decode|base64|atob)"),  # skillscan:allow
     "OBF02", "CRITICAL", "Interpreter one-liner decoding embedded data"),
]

LONG_B64_RE = re.compile(r"[A-Za-z0-9+/]{120,}={0,2}")
HEX_ONLY_RE = re.compile(r"^[0-9a-fA-F]+$")

NET_PATTERNS = [
    (re.compile(r"^\s*(?:import|from)\s+(?:requests|httpx|aiohttp|urllib3?|websockets?|socket|http\b)"),
     "python network import"),
    (re.compile(r"\burllib\.request\b|\bhttp\.client\b|\bsocket\.(?:socket|create_connection)\b"),
     "python network API call"),
    (re.compile(r"\bfetch\s*\(|\baxios\b|\bXMLHttpRequest\b|new\s+WebSocket\s*\("),
     "JavaScript network API call"),
    (re.compile(r"\b(?:curl|wget)\s+(?:-[A-Za-z-]+\s+)*[\"']?https?://"),
     "curl/wget invocation"),
    (re.compile(r"\b(?:nc|ncat|netcat)\s+[\w.-]+\s+\d{2,5}\b"),
     "raw netcat connection"),
]

CRED_PATTERNS = [
    (re.compile(r"~/\.ssh\b|/\.ssh/|id_rsa\b|id_ed25519\b"),  # skillscan:allow
     "CRED01", "CRITICAL", "Reads SSH key material (SSH dir, id_rsa, id_ed25519)"),  # skillscan:allow
    (re.compile(r"\.aws/credentials|\.aws/config"),  # skillscan:allow
     "CRED01", "CRITICAL", "Reads AWS credential files"),
    (re.compile(r"(?i)security\s+(?:find-generic-password|find-internet-password|dump-keychain)"),
     "CRED01", "CRITICAL", "Queries the macOS keychain from a script"),
    (re.compile(r"\.netrc\b|\.npmrc\b|\.pypirc\b"),  # skillscan:allow
     "CRED01", "WARN", "Touches credential-bearing dotfiles (netrc/npmrc/pypirc)"),  # skillscan:allow
    (re.compile(r"gcloud/(?:credentials|application_default_credentials)"),
     "CRED01", "WARN", "Reads gcloud credential files"),
    (re.compile(r"(?i)(?:Login Data|Cookies)['\"]|browser.{0,20}profile.{0,20}(?:passw|cookie)"),  # skillscan:allow
     "CRED01", "WARN", "References browser credential/cookie stores"),
    (re.compile(r"(?i)(?:exodus|electrum|phantom|solana)[^\n]{0,40}(?:wallet|keystore|id\.json)"),  # skillscan:allow
     "CRED01", "WARN", "References cryptocurrency wallet storage"),
    (re.compile(r"expanduser\([^)\n]{0,60}\.env|\$HOME/[^\s\"']{0,40}\.env\b|~/\.(?:claude|clawdbot|openclaw|config/openai)(?!/(?:skills|plugins)\b)[^\s\"']{0,30}"),
     "CRED01", "WARN", "Reads agent/home .env or agent config directories"),
    (re.compile(r"dict\(os\.environ\)|os\.environ\.items\(\)|os\.environ\.copy\(\)"),
     "CRED02", "WARN", "Enumerates the entire process environment (all env vars at once)"),
    (re.compile(r"JSON\.stringify\(process\.env\)|Object\.(?:entries|keys)\(process\.env\)"),
     "CRED02", "WARN", "Serializes the entire process environment"),
    (re.compile(r"(?<![\w-])printenv\b|\benv\s*\|\s*(?:curl|nc|base64)"),  # skillscan:allow
     "CRED02", "WARN", "Dumps the process environment in a shell"),
]

PIN_PATTERNS = [
    (re.compile(r"\bpip3?\s+install\b(?![^\n#]*(?:==|--require-hashes|-r\s|-e\s|\.\s*$))"),  # skillscan:allow
     "PIN01", "WARN", "Unpinned pip install — version can drift to a compromised release"),  # skillscan:allow
    (re.compile(r"\bnpm\s+install\s+(?:-g\s+)?(?!.*@\d)[a-z@][\w@/.-]*\s*$"),
     "PIN01", "INFO", "Unpinned npm install — prefer exact versions or a lockfile"),
]

LURE_HEADING_RE = re.compile(
    r"(?i)^#{1,6}\s.*\b(prerequisite|installation|install|setup|set\s?up|"
    r"before you begin|getting started|activation|activate|first run|initiali[sz])")
FETCH_CMD_RE = re.compile(r"(?i)\b(?:curl|wget|iwr|irm|invoke-webrequest)\b[^\n]*https?://")  # skillscan:allow
LURE_PROSE_RE = re.compile(
    r"(?i)\b(?:run|execute|paste|copy)\b.{0,60}\b(?:command|script|one-?liner|snippet|installer)\b"
    r".{0,120}\b(?:initiali[sz]e|activate|unlock|register|verify|before (?:first )?use|to enable|to install|to set ?up)")

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class Finding:
    def __init__(self, skill, check, severity, file, line, message, evidence):
        self.skill, self.check, self.severity = skill, check, severity
        self.file, self.line, self.message = file, line, message
        self.evidence = evidence.strip()[:160]

    def as_dict(self):
        return {"skill": self.skill, "check": self.check, "severity": self.severity,
                "file": self.file, "line": self.line, "message": self.message,
                "evidence": self.evidence}


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return None


def parse_frontmatter(text):
    """Minimal YAML-ish frontmatter parser (top-level keys only). Returns dict or None."""
    m = re.match(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", text, re.S)
    if not m:
        return None
    fm, current = {}, None
    for line in m.group(1).splitlines():
        km = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if km:
            current = km.group(1).lower()
            fm[current] = km.group(2).strip().strip("\"'")
        elif current is not None and line[:1] in (" ", "\t"):
            fm[current] = (fm[current] + " " + line.strip()).strip()
    for key, val in fm.items():
        if val[:1] in (">", "|"):
            fm[key] = val[1:].lstrip("-+ ").strip()
    return fm


def discover_skills(root):
    """Return a list of skill directories (dirs containing SKILL.md)."""
    root = Path(root)
    if root.is_file() and root.name == "SKILL.md":
        return [root.parent]
    if root.is_dir() and (root / "SKILL.md").is_file():
        return [root]
    found = []
    if root.is_dir():
        for dirpath, dirs, files in os.walk(root):
            dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
            if "SKILL.md" in files:
                found.append(Path(dirpath))
                dirs[:] = []  # don't descend into nested skills
    return found


def iter_scan_files(skill_dir, include_fixtures=False):
    for dirpath, dirs, files in os.walk(skill_dir):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        if not include_fixtures:
            # A skill's own evals/fixtures/ may hold deliberately malicious test
            # payloads; scanning them as part of the skill produces false alarms.
            # Pass --include-fixtures (or target the fixture dir) to scan them.
            rel = Path(dirpath).relative_to(skill_dir)
            if rel.parts and rel.parts[0] == "evals" and "fixtures" in dirs:
                dirs.remove("fixtures")
        for name in sorted(files):
            p = Path(dirpath) / name
            if p.suffix.lower() not in SCAN_EXTS and Path(dirpath).name != "scripts":
                continue
            try:
                if p.stat().st_size > MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            yield p


def network_declared(fm):
    blob = " ".join(str(fm.get(k, "")) for k in ("compatibility", "description")).lower() if fm else ""
    compat = str(fm.get("compatibility", "")).lower() if fm else ""
    # Only an explicit compatibility declaration counts; description mentions are informative.
    return any(w in compat for w in NETWORK_DECLARE_WORDS), any(w in blob for w in NETWORK_DECLARE_WORDS)


def scan_skill(skill_dir, include_fixtures=False):
    skill_dir = Path(skill_dir).resolve()
    skill_name = skill_dir.name
    findings = []
    skill_md = skill_dir / "SKILL.md"
    text = read_text(skill_md) or ""
    fm = parse_frontmatter(text)

    def add(check, sev, file, line, msg, evidence):
        findings.append(Finding(skill_name, check, sev, str(file.relative_to(skill_dir)),
                                line, msg, evidence))

    # --- Check 6: frontmatter hygiene -------------------------------------
    if fm is None:
        add("META01", "WARN", skill_md, 1,
            "SKILL.md has no YAML frontmatter (--- block). Agents cannot discover this skill safely.", text[:80])
    else:
        name = fm.get("name", "")
        if not name:
            add("META02", "WARN", skill_md, 1, "Frontmatter is missing 'name'.", "")
        elif name != skill_dir.name:
            add("META03", "WARN", skill_md, 1,
                "Frontmatter name '%s' != directory name '%s' — typosquat/impersonation signal, and many runtimes will refuse to load it." % (name, skill_dir.name), name)
        if name and not NAME_RE.match(name):
            add("META02", "WARN", skill_md, 1,
                "Frontmatter name '%s' violates spec (lowercase a-z, 0-9, hyphens)." % name, name)
        desc = fm.get("description", "")
        if not desc:
            add("META04", "WARN", skill_md, 1, "Frontmatter is missing 'description'.", "")
        elif len(desc) > 1024:
            add("META05", "INFO", skill_md, 1, "Description exceeds 1024 chars (spec limit).", desc[:60])

    net_declared, net_mentioned = network_declared(fm)

    # --- SKILL.md prose: install-lure detection (Check 2) ------------------
    lines = text.splitlines()
    in_fence = False
    lure_window_until = -1
    for i, line in enumerate(lines, 1):
        if SUPPRESS_MARKER in line:
            continue
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence and LURE_HEADING_RE.match(line):
            lure_window_until = i + 20
        if in_fence and FETCH_CMD_RE.search(line):
            if i <= lure_window_until:
                add("LURE01", "CRITICAL", skill_md, i,
                    "Install/prerequisite section tells the user or agent to fetch and run a remote script. This was the #1 ClawHavoc delivery vector.", line)
            else:
                add("LURE02", "WARN", skill_md, i,
                    "SKILL.md contains a command that fetches remote content; verify the destination and pin it.", line)
        if not in_fence and LURE_PROSE_RE.search(line):
            add("LURE03", "WARN", skill_md, i,
                "Prose instructs running a command/script to 'initialize/activate/enable' — install-time execution lure pattern.", line)

    # --- Per-file pattern scans (Checks 1, 3, 4, 5, 7) ----------------------
    for path in iter_scan_files(skill_dir, include_fixtures=include_fixtures):
        content = read_text(path)
        if content is None:
            continue
        is_skill_md = path == skill_md
        is_markdown = path.suffix.lower() in (".md", ".markdown")
        file_has_net = False
        file_has_cred = False
        in_doc_fence = False
        for i, line in enumerate(content.splitlines(), 1):
            if is_markdown and line.lstrip().startswith("```"):
                in_doc_fence = not in_doc_fence
                continue
            if SUPPRESS_MARKER in line:
                continue

            # WARN-tier findings inside a markdown code example are usually
            # illustrative snippets, not instructions — downgrade to INFO so
            # documentation-heavy skills stay reviewable. CRITICAL patterns are
            # NEVER downgraded here: ClawHavoc install lures lived precisely in
            # fenced "Prerequisites" blocks.
            def doc_sev(sev):
                return "INFO" if (in_doc_fence and sev == "WARN") else sev

            def doc_msg(sev, msg):
                if in_doc_fence and sev == "WARN":
                    return msg + " (inside a documentation code example — verify it is illustrative, not an instruction to the agent)"
                return msg

            for rx, check, sev, msg in PIPE_SHELL_PATTERNS + OBFUSCATION_EXEC_PATTERNS:
                if rx.search(line):
                    add(check, doc_sev(sev), path, i, doc_msg(sev, msg), line)
            for token in LONG_B64_RE.findall(line):
                if not HEX_ONLY_RE.match(token):
                    add("OBF01", doc_sev("WARN"), path, i,
                        doc_msg("WARN", "Long base64-like literal (%d chars) — encoded payloads hide from review. Decode it before trusting this file." % len(token)), token[:60] + "...")
            for rx, check, sev, msg in CRED_PATTERNS:
                if rx.search(line):
                    add(check, doc_sev(sev), path, i, doc_msg(sev, msg), line)
                    # Fenced commands are still executable instructions to an
                    # agent, so they count toward the EXFIL01 cross-signal.
                    file_has_cred = True
            for rx, sev_msg in NET_PATTERNS:
                if rx.search(line):
                    file_has_net = True
                    if not is_skill_md:
                        sev = "INFO" if (net_declared or in_doc_fence) else "WARN"
                        extra = ("declared via 'compatibility'" if net_declared else
                                 ("inside a documentation code example" if in_doc_fence else
                                  "not declared in frontmatter 'compatibility'"))
                        add("NET01", sev, path, i,
                            "Script makes network calls (%s), %s." % (sev_msg, extra), line)
            for rx, check, sev, msg in PIN_PATTERNS:
                if rx.search(line):
                    add(check, doc_sev(sev), path, i, doc_msg(sev, msg), line)
        if file_has_net and file_has_cred:
            add("EXFIL01", "CRITICAL", path, 0,
                "Same file both touches credentials/environment and makes network calls — the standard exfiltration shape. Review it line by line.", "")

    # Eval/test data is expected to quote attack-shaped text (trigger prompts,
    # rubric examples). It is not runtime content, so keep it visible but
    # informational rather than failing the scan.
    for f in findings:
        if f.file.startswith("evals/") and f.severity != "INFO":
            f.severity = "INFO"
            f.message += " (found in evals/ test data — expected to quote attack patterns; verify it is not loaded at runtime)"

    # Deduplicate identical findings
    seen, unique = set(), []
    for f in findings:
        key = (f.check, f.file, f.line, f.message)
        if key not in seen:
            seen.add(key)
            unique.append(f)
    unique.sort(key=lambda f: (-SEV_RANK[f.severity], f.file, f.line))
    return unique


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Static security scanner for agent skills (OWASP AST01-AST10 aligned).")
    ap.add_argument("path", help="A skill directory (containing SKILL.md), a SKILL.md file, "
                                 "or a parent directory holding many skills.")
    ap.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    ap.add_argument("--include-fixtures", action="store_true",
                    help="Also scan evals/fixtures/ inside each skill (skipped by "
                         "default because fixtures may be deliberately malicious "
                         "test payloads).")
    args = ap.parse_args(argv)

    root = Path(args.path).expanduser()
    if not root.exists():
        print("error: path does not exist: %s\n"
              "Fix: pass the skill directory itself (the one containing SKILL.md), "
              "e.g. python3 skill_scanner.py PATH/skills/some-skill" % root, file=sys.stderr)  # skillscan:allow
        return 2
    skills = discover_skills(root)
    if not skills:
        print("error: no SKILL.md found under %s\n"
              "Fix: agent skills are directories with a SKILL.md at their root. "
              "If you meant to scan a single file, name it SKILL.md or pass its parent directory." % root,
              file=sys.stderr)
        return 2

    all_findings = []
    for sd in sorted(skills):
        all_findings.extend(scan_skill(sd, include_fixtures=args.include_fixtures))

    counts = {"CRITICAL": 0, "WARN": 0, "INFO": 0}
    for f in all_findings:
        counts[f.severity] += 1

    if args.json:
        print(json.dumps({
            "scanner": "skill_scanner", "version": VERSION,
            "root": str(root), "skills_scanned": [str(s) for s in sorted(skills)],
            "findings": [f.as_dict() for f in all_findings],
            "summary": counts,
            "verdict": "REJECT-PENDING-REVIEW" if counts["CRITICAL"] else
                       ("REVIEW-WARNINGS" if counts["WARN"] else "PASS"),
        }, indent=2))
    else:
        print("agent-skill security scan v%s — %d skill(s) under %s\n" % (VERSION, len(skills), root))
        by_skill = {}
        for f in all_findings:
            by_skill.setdefault(f.skill, []).append(f)
        for sd in sorted(skills):
            fs = by_skill.get(sd.name, [])
            print("=== %s (%s) ===" % (sd.name, sd))
            if not fs:
                print("  clean — no findings\n")
                continue
            for f in fs:
                loc = "%s:%s" % (f.file, f.line) if f.line else f.file
                print("  [%s] %s %s\n      %s" % (f.severity, f.check, loc, f.message))
                if f.evidence:
                    print("      > %s" % f.evidence)
            print()
        print("Summary: %d CRITICAL, %d WARN, %d INFO" %
              (counts["CRITICAL"], counts["WARN"], counts["INFO"]))
        if counts["CRITICAL"]:
            print("Verdict guidance: CRITICAL findings present — do not install/run this skill "
                  "until a human reviews every flagged line. See references/skill-supply-chain.md.")
        elif counts["WARN"]:
            print("Verdict guidance: warnings present — read each flagged file before approving. "
                  "A clean pattern scan is necessary but not sufficient (OWASP AST08).")
        else:
            print("Verdict guidance: no pattern hits. Still read SKILL.md end-to-end — "
                  "natural-language attacks evade pattern scanners (OWASP AST08).")
    return 1 if counts["CRITICAL"] else 0


if __name__ == "__main__":
    sys.exit(main())
