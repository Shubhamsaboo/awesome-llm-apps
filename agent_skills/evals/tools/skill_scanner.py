#!/usr/bin/env python3
"""CI trampoline for the agent-security-auditor scanner.

The pattern tables and CLI live in the installable skill:

    agent_skills/agent-security-auditor/scripts/skill_scanner.py

This file re-exports that module and forwards ``python3 …/skill_scanner.py``
so existing workflow commands and docs keep working. Do not add checks here.
"""

import importlib.util
import os
import sys

_CANONICAL = os.path.normpath(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "..",
        "agent-security-auditor",
        "scripts",
        "skill_scanner.py",
    )
)


def _load():
    if not os.path.isfile(_CANONICAL):
        raise FileNotFoundError(
            "canonical skill scanner missing at %s" % _CANONICAL
        )
    spec = importlib.util.spec_from_file_location(
        "agent_security_auditor_scanner", _CANONICAL
    )
    if spec is None or spec.loader is None:
        raise ImportError("cannot load canonical scanner from %s" % _CANONICAL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_mod = _load()

# Re-export the public API so `import skill_scanner` from this path matches
# the skill module. Tests assert VERSION and scan_skill stay identical.
VERSION = _mod.VERSION
Finding = _mod.Finding
scan_skill = _mod.scan_skill
discover_skills = _mod.discover_skills
parse_frontmatter = _mod.parse_frontmatter
main = _mod.main
CANONICAL_PATH = _CANONICAL


if __name__ == "__main__":
    sys.exit(main())
