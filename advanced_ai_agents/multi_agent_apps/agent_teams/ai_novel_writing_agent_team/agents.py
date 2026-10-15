"""The five agents of the team, plus the runner that executes them.

Each agent is a real LLM call with its own system prompt, temperature and tool
access. Agents that need to inspect or update shared state (the story bible)
are given tools; the runner executes a standard OpenAI tool-calling loop, so an
agent can call several tools before it answers.

Nothing in this file is specific to one novel: the team is configured purely by
the premise / goal you pass in.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from tools import TOOL_SCHEMAS, build_dispatcher


# --------------------------------------------------------------------------- #
# Result objects
# --------------------------------------------------------------------------- #
@dataclass
class ToolTrace:
    """One tool call an agent made, kept for the UI / logs."""

    name: str
    args: dict[str, Any]
    result: str


@dataclass
class AgentResult:
    """Everything one agent produced."""

    key: str
    name: str
    text: str
    tools: list[ToolTrace] = field(default_factory=list)
    prompt_tokens: int = 0
    completion_tokens: int = 0
    rounds: int = 1

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


# --------------------------------------------------------------------------- #
# Agent specifications
# --------------------------------------------------------------------------- #
BASE_RULES = """You work inside a team of specialist agents that write a novel one
chapter at a time. Absolute rules:

- Never contradict the story bible. If a fact is missing, invent it once and
  record it with your tools so later agents see the same fact.
- Output only your own deliverable. No preamble such as "Sure, here is...".
- Match the requested language of the story (the premise's language)."""


@dataclass
class AgentSpec:
    key: str
    name: str
    emoji: str
    system_prompt: str
    temperature: float
    tools: tuple[str, ...] = ()
    expects_json: bool = False


AGENTS: dict[str, AgentSpec] = {
    "librarian": AgentSpec(
        key="librarian",
        name="Continuity Librarian",
        emoji="📚",
        temperature=0.2,
        tools=("bible_search", "bible_recap"),
        system_prompt=f"""{BASE_RULES}

You are the Continuity Librarian. Before a chapter is planned you gather what
the story already established and hand the other agents a tight brief.

Use `bible_recap` to read the current state, then `bible_search` for any name or
place mentioned in the chapter goal. Report only facts that exist in the bible
plus the open threads a writer must not contradict. Be concise and factual.""",
    ),
    "architect": AgentSpec(
        key="architect",
        name="Story Architect",
        emoji="🏛️",
        temperature=0.7,
        expects_json=True,
        system_prompt=f"""{BASE_RULES}

You are the Story Architect. You turn a chapter goal into a beat sheet of 3-6
beats. Every beat must change something: a decision, a piece of information, a
relationship, or the reader's understanding. No filler, no recap.

Return ONLY JSON in this shape:
{{"chapter_title": "...", "beats": [{{"id": 1, "purpose": "...", "action": "...",
"turn": "...", "pov": "..."}}]}}
`turn` is what is different by the end of the beat.""",
    ),
    "designer": AgentSpec(
        key="designer",
        name="Scene Designer",
        emoji="🎬",
        temperature=0.6,
        expects_json=True,
        system_prompt=f"""{BASE_RULES}

You are the Scene Designer. You convert beats into concrete scene cards a
drafter can write from. Each card names the setting, the goal and obstacle, the
emotional turn, and specific sensory anchors (objects, sounds, physical detail)
— never generic mood words.

Return ONLY JSON in this shape:
{{"scenes": [{{"beat_ids": [1], "setting": "...", "goal": "...", "obstacle": "...",
"turn": "...", "sensory_anchors": ["...", "..."], "target_words": 400}}]}}""",
    ),
    "drafter": AgentSpec(
        key="drafter",
        name="Draft Writer",
        emoji="✍️",
        temperature=0.8,
        tools=("record_entity", "record_event", "bible_search", "text_stats"),
        system_prompt=f"""{BASE_RULES}

You are the Draft Writer. You write the chapter as finished prose — scene by
scene, following the scene cards, hitting the word budget within 15%.

Craft rules:
- Dialogue carries the conflict; keep exchanges short and let characters talk
  past each other when they are hiding something.
- Concrete over abstract. Use the sensory anchors instead of explaining mood.
- Vary sentence length. Never open consecutive paragraphs the same way.
- No clichés ("a chill ran down her spine"), no summarising what just happened.

As you write, use `record_entity` for every new character, place or object and
`record_event` for each beat you complete, so the story bible stays current.
Use `text_stats` to check your running length before you finish.""",
    ),
    "critic": AgentSpec(
        key="critic",
        name="Continuity Critic",
        emoji="🔍",
        temperature=0.2,
        tools=("bible_dump", "repetition_check"),
        expects_json=True,
        system_prompt=f"""{BASE_RULES}

You are the Continuity Critic — the gate before a chapter is accepted. You do
not rewrite; you audit and prescribe.

Check the draft against the story bible (`bible_dump`) and the scene cards for:
1. Contradictions with recorded entities, traits or timeline events.
2. Beats or scene cards that were skipped or reversed.
3. Repeated phrasing and filler (`repetition_check`).
4. Characters knowing things they were never told.

Return ONLY JSON in this shape:
{{"verdict": "pass" | "revise", "score": 0-10, "issues": [{{"severity":
"high"|"medium"|"low", "quote": "...", "problem": "..."}}], "fix_instructions":
["..."]}}
Pass only if there is no high-severity issue. `fix_instructions` must be
specific edits the Draft Writer can apply without asking questions.""",
    ),
}


# --------------------------------------------------------------------------- #
# Runner
# --------------------------------------------------------------------------- #
class AgentRunner:
    """Executes one agent spec with an OpenAI-compatible client."""

    def __init__(
        self,
        client: Any,
        model: str,
        bible: Any,
        chapter: int,
        max_tool_rounds: int = 6,
    ) -> None:
        self.client = client
        self.model = model
        self.bible = bible
        self.chapter = chapter
        self.max_tool_rounds = max_tool_rounds
        self.dispatch = build_dispatcher(bible, chapter)

    def run(self, spec: AgentSpec, user_prompt: str) -> AgentResult:
        """Run the agent, executing any tools it asks for, and return its text."""
        tool_schemas = [
            s
            for s in TOOL_SCHEMAS
            if s["function"]["name"] in spec.tools
        ]
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": spec.system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        result = AgentResult(key=spec.key, name=spec.name, text="")

        for round_index in range(1, self.max_tool_rounds + 1):
            kwargs: dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "temperature": spec.temperature,
            }
            if tool_schemas:
                kwargs["tools"] = tool_schemas
                kwargs["tool_choice"] = "auto"

            response = self.client.chat.completions.create(**kwargs)
            choice = response.choices[0]
            message = choice.message
            usage = getattr(response, "usage", None)
            if usage is not None:
                result.prompt_tokens += getattr(usage, "prompt_tokens", 0) or 0
                result.completion_tokens += (
                    getattr(usage, "completion_tokens", 0) or 0
                )
            result.rounds = round_index

            tool_calls = getattr(message, "tool_calls", None) or []
            if not tool_calls:
                result.text = (message.content or "").strip()
                return result

            # Record the assistant turn verbatim, then answer each tool call.
            messages.append(
                {
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": [
                        {
                            "id": call.id,
                            "type": "function",
                            "function": {
                                "name": call.function.name,
                                "arguments": call.function.arguments,
                            },
                        }
                        for call in tool_calls
                    ],
                }
            )
            for call in tool_calls:
                try:
                    args = json.loads(call.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                output = self.dispatch(call.function.name, args)
                result.tools.append(ToolTrace(call.function.name, args, output))
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": output[:4000],
                    }
                )

        # Ran out of tool rounds: force a final answer with no tools.
        final = self.client.chat.completions.create(
            model=self.model, messages=messages, temperature=spec.temperature
        )
        result.text = (final.choices[0].message.content or "").strip()
        return result


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def parse_json_block(text: str) -> dict[str, Any]:
    """Extract the first JSON object from a model reply (tolerates code fences)."""
    cleaned = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE)
    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}
