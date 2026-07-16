# Dependency Doctor Agent Skill

Dependency Doctor inspects one dependency manifest and explains common sources
of install drift and runtime breakage. It is a local, user-invoked development
tool, not a repository CI rule.

## What it checks

- Python standard-library shadowing pins such as `pathlib==1.0.1`
- Obsolete backports such as `dataclasses`, `typing`, `enum34`, and `futures`
- Dependencies with no usable version constraint
- Duplicate entries and conflicting exact pins
- Fully yanked PyPI releases when `--online` is explicitly enabled

The offline core supports `requirements.txt`, PEP 621 or Poetry
`pyproject.toml`, and `package.json`. It uses only the Python standard library.

## Install

```bash
npx skills add https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/agent_skills/dependency-doctor
```

Then ask your agent: `check my requirements.txt for dependency problems`.

## Run the script directly

```bash
python3 agent_skills/dependency-doctor/scripts/dep_doctor.py requirements.txt --json
```

The default command makes no network calls. To check exact Python pins for
fully yanked PyPI releases, opt in:

```bash
python3 agent_skills/dependency-doctor/scripts/dep_doctor.py requirements.txt --json --online
```

The doctor reports findings and suggested fixes but does not edit the manifest.
Run the eval from a clone before installing:

```bash
python3 agent_skills/evals/dependency-doctor/test_dep_doctor.py
```

## Scope

This focused check does not resolve a complete dependency graph and does not
query a vulnerability database. Use the project's approved audit tool for CVE
coverage. Ask before enabling the PyPI lookup or applying any suggested fix.

Apache-2.0. Last verified: July 2026.
