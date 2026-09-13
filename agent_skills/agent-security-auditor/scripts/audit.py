#!/usr/bin/env python3
"""Run the same agent-skill security scan that CI runs.

The check tables live in ``skill_scanner.py`` beside this file. When this
skill is still inside a clone of awesome-llm-apps, GitHub Actions reaches
that same module through ``agent_skills/evals/tools/skill_scanner.py``.
When the skill is installed standalone, this bundled copy is the scanner.

Python 3.8+, stdlib only, no network, never executes scanned code.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from skill_scanner import main  # noqa: E402


if __name__ == "__main__":
    sys.exit(main())
