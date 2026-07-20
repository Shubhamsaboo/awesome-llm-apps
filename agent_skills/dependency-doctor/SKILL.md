---
name: dependency-doctor
description: >-
  Checks requirements.txt, pyproject.toml, and package.json dependency manifests
  for surface-level direct-dependency footguns: standard-library shadowing pins,
  abandoned backports, unpinned dependencies, and obvious intra-manifest
  conflicts, plus opt-in PyPI yanked releases. Use when the user asks to check a
  manifest for dependency problems, asks why dependencies won't install or
  whether anything is wrong with their dependencies, wants a dependency autopsy,
  or suspects dependency manifest rot. Runs offline by default as a local tool
  for the user's own project, not repository CI.
license: Apache-2.0
compatibility: "Python 3.11+. Offline by default. Network access to pypi.org occurs only when the user explicitly approves --online."
metadata:
  author: "Matt Van Horn"
  version: "1.0.0"
  source: "https://github.com/Shubhamsaboo/awesome-llm-apps"
---

# Dependency Doctor

Inspect one dependency manifest on the user's machine for direct, surface-level
footguns. Explain each finding in plain language, then offer a small,
reviewable fix. This does not diagnose a failed pip or uv resolution.

This is a local developer tool for a project the user chooses. It is not a
repository-wide lint rule, a CI gate, or a proposal to enforce dependency
policy across unrelated apps.

## When to use

- The user asks to check, audit, diagnose, or autopsy a dependency manifest
- The user wants to rule out direct-manifest issues before deeper install debugging
- The user suspects stale pins, backports, duplicate entries, or dependency rot
- The user asks whether anything looks wrong with their dependencies

## When not to use

- Installing the current dependencies without diagnosing them
- Upgrading every package or adding a new package
- A full vulnerability audit. Use `pip-audit`, `npm audit`, or the project's
  approved security scanner for CVE coverage
- Creating a repo-wide CI check. This skill is user-invoked and local

## Choose the manifest

Use the path the user names. If no path is given and several manifests exist,
ask which one to inspect. Do not sweep the repository or edit anything merely
because the skill was triggered.

Supported inputs:

- `requirements.txt`
- `pyproject.toml` using PEP 621 or common Poetry dependency tables
- `package.json` dependency sections

## Run the offline diagnosis

From this skill directory:

```bash
python3 scripts/dep_doctor.py /path/to/requirements.txt --json
```

The default path is fully offline. It reads only the selected manifest. The
report shape is:

```json
{
  "file": "/path/to/requirements.txt",
  "findings": [
    {
      "severity": "high",
      "kind": "stdlib-shadowing",
      "package": "pathlib",
      "line": 4,
      "why": "...",
      "fix": "..."
    }
  ],
  "summary": {
    "total": 1,
    "by_severity": {"high": 1},
    "by_kind": {"stdlib-shadowing": 1},
    "online": false
  }
}
```

The offline checks cover:

- Python standard-library names published as packages
- Known backports that should not be installed on supported Python versions
- Dependencies without a usable version constraint
- Repeated package entries
- Conflicting exact pins for the same package

For `package.json`, Python-specific standard-library and backport checks do not
apply. The doctor still checks unpinned values and repeated dependency entries.

## Explain the diagnosis

Read `references/dependency-pitfalls.md` before presenting findings. Lead with
high severity items, then medium and low. For each finding, include:

1. Package and source line
2. What can break
3. The suggested fix

Do not call every range a conflict. The deterministic core reports conflicting
constraints only when exact pins disagree. Compatible constraints split across
multiple lines are duplicate entries that should be combined.

If there are no findings, say what was checked and note the limits. A clean
report is not a CVE audit or a full dependency resolver.

## Optional PyPI yank check

The online check sends package names and exact pinned versions to `pypi.org`.
Ask for permission before enabling it, even if the user previously requested an
offline diagnosis.

```bash
python3 scripts/dep_doctor.py /path/to/requirements.txt --json --online
```

It reports an exact Python release only when every file for that release is
marked yanked. Network failures become low-severity findings instead of hiding
the offline diagnosis.

## Offer fixes, do not apply them silently

After explaining the report, offer a focused edit. Wait for approval before
changing the manifest.

- Remove standard-library packages from supported Python projects
- Remove obsolete backports, or add a Python-version marker when an old runtime
  genuinely needs one
- For an unpinned dependency, inspect the working environment's installed
  version, confirm it is intended, and propose an exact reviewed pin
- Keep one entry for duplicates and combine compatible constraints
- For conflicting exact pins, inspect dependents before choosing a version
- Replace a yanked pin with a tested, non-yanked release

After any approved edit, rerun the offline diagnosis and the project's existing
install or test command. Do not introduce a new CI gate.

## Files

- `scripts/dep_doctor.py`: stdlib-only manifest parser and diagnosis engine
- `references/dependency-pitfalls.md`: reasoning guide for the reported risks
