"""
Personas package for Decepticon red team agent personalities.

This package contains specialized persona prompts that define the expertise,
tools, and methodologies for each type of red team specialist agent.
"""

from .reconnaissance_persona import RECONNAISSANCE_PERSONA_PROMPT
from .initial_access_persona import INITIAL_ACCESS_PERSONA_PROMPT
from .planner_persona import PLANNER_PERSONA_PROMPT
from .summary_persona import SUMMARY_PERSONA_PROMPT
from .supervisor_persona import SUPERVISOR_PERSONA_PROMPT

__all__ = [
    'RECONNAISSANCE_PERSONA_PROMPT',
    'INITIAL_ACCESS_PERSONA_PROMPT', 
    'PLANNER_PERSONA_PROMPT',
    'SUMMARY_PERSONA_PROMPT',
    'SUPERVISOR_PERSONA_PROMPT'
]
