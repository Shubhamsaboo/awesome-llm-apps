#!/usr/bin/env python3
"""Score an RCA with the triage-issue skill's scorer, on this app's backends.

Same arguments and exit codes as `agent_skills/triage-issue/scripts/score_rca.py`
(see its --help). This wrapper adds what the app has and the standalone skill
does not: the Claude Code backend (`--model claude_code/sonnet`) and a trace per
run, so CLI scores appear in the app's Sessions tab.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "optimizer"))
import skill_paths  # noqa: E402  (puts the skill's scripts first on sys.path)
import score_rca  # noqa: E402  (the skill's module, not this wrapper; checked below)
import telemetry  # noqa: E402
from skill_optimizer import SkillOptimizer  # noqa: E402

if os.path.dirname(os.path.realpath(score_rca.__file__)) != os.path.realpath(skill_paths.SKILL_SCRIPTS):
    sys.exit(f"Imported the wrong score_rca module: {score_rca.__file__}")


def _trace(name, client):
    return telemetry.span(name, **{"triage.model": client.model, "triage.backend": client.backend})


if __name__ == "__main__":
    sys.exit(score_rca.main(
        make_client=lambda model, key, n: SkillOptimizer(model=model, api_key=key, concurrency=n),
        trace=_trace,
    ))
