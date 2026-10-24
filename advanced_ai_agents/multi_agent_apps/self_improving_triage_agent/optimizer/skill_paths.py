"""Where the triage-issue skill lives.

The skill (SKILL.md, references, deterministic scripts) is a standard
agent_skills/ folder; this app reads it and never the other way round. Set
TRIAGE_SKILL_DIR to point the app at a copy you are editing elsewhere.
"""

import os
import sys

APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.abspath(os.path.join(APP_ROOT, "..", "..", ".."))
SKILLS_ROOT = os.path.join(REPO_ROOT, "agent_skills")

SKILL_DIR = os.path.abspath(
    os.environ.get("TRIAGE_SKILL_DIR") or os.path.join(SKILLS_ROOT, "triage-issue"))
SKILL_MD = os.path.join(SKILL_DIR, "SKILL.md")
REFERENCES = os.path.join(SKILL_DIR, "references")
SKILL_SCRIPTS = os.path.join(SKILL_DIR, "scripts")

ROUTING_GOLDEN = os.path.join(REFERENCES, "golden_set.json")
RCA_GOLDEN = os.path.join(REFERENCES, "rca-golden-set.json")
RCA_RUBRIC = os.path.join(REFERENCES, "rca-rubric.json")

if SKILL_SCRIPTS not in sys.path:
    sys.path.insert(0, SKILL_SCRIPTS)
