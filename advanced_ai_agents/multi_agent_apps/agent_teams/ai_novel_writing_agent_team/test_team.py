"""Offline tests for the coordinator — no API calls, no network.

Run:  python test_team.py

Two behaviours are covered:
1. The critic's `revise` verdict sends the chapter back to the Draft Writer
   and the loop stops as soon as a later verdict passes.
2. Agent tool calls really mutate the shared story bible.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from coordinator import NovelTeam
from tools import StoryBible

BRIEF = "Canon so far: Ilse drives tram 118; the passenger is not on any sheet."
BEATS = '{"chapter_title": "Last Run", "beats": [{"id": 1, "purpose": "decide", "action": "she reports him", "turn": "she doesn\'t", "pov": "3rd"}]}'
SCENES = '{"scenes": [{"beat_ids": [1], "setting": "cab", "goal": "decide", "obstacle": "fear", "turn": "silence", "sensory_anchors": ["bell", "coin"], "target_words": 300}]}'


def _text(content: str) -> Any:
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content, tool_calls=None))],
        usage=SimpleNamespace(prompt_tokens=10, completion_tokens=20),
    )


def _tool_call(name: str, args: str) -> Any:
    call = SimpleNamespace(id="call_1", function=SimpleNamespace(name=name, arguments=args))
    message = SimpleNamespace(content="", tool_calls=[call])
    return SimpleNamespace(
        choices=[SimpleNamespace(message=message)],
        usage=SimpleNamespace(prompt_tokens=5, completion_tokens=5),
    )


class FakeClient:
    """Scripted stand-in for an OpenAI client.

    Responds by agent role, and flips the critic's verdict to `revise` the first
    time so the revision path is exercised.
    """

    def __init__(self, verdicts: list[str]) -> None:
        self.verdicts = verdicts
        self.critic_calls = 0
        self.drafter_calls = 0
        self.tool_round_done = False
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, *, model: str, messages: list[dict], **kwargs: Any) -> Any:
        system = messages[0]["content"]
        if "You are the Continuity Librarian." in system:
            return _text(BRIEF)
        if "You are the Story Architect." in system:
            return _text(BEATS)
        if "You are the Scene Designer." in system:
            return _text(SCENES)
        if "You are the Draft Writer." in system:
            self.drafter_calls += 1
            if not self.tool_round_done:
                # First drafter turn: use a tool, then answer on the next round.
                self.tool_round_done = True
                return _tool_call(
                    "record_entity",
                    '{"name": "Ilse Renner", "kind": "character", "traits": "tram driver"}',
                )
            return _text(f"DRAFT v{self.drafter_calls}")
        if "You are the Continuity Critic" in system:
            verdict = self.verdicts[min(self.critic_calls, len(self.verdicts) - 1)]
            self.critic_calls += 1
            if verdict == "pass":
                return _text('{"verdict": "pass", "score": 9, "issues": [], "fix_instructions": []}')
            return _text(
                '{"verdict": "revise", "score": 6, "issues": [{"severity": "high", '
                '"quote": "x", "problem": "y"}], "fix_instructions": ["add tension"]}'
            )
        raise AssertionError("unexpected agent")


def test_revision_loop_runs_and_stops() -> None:
    client = FakeClient(verdicts=["revise", "pass"])
    bible = StoryBible(premise="test")
    team = NovelTeam(client=client, model="stub", bible=bible, max_revisions=2)
    result = team.run_chapter(chapter=1, goal="decide", target_words=200)

    assert result.revisions == 1, f"expected 1 revision, got {result.revisions}"
    # 3 model invocations for the drafter: one tool round + one answer for the
    # first draft, then one more for the revision.
    assert client.drafter_calls == 3, f"drafter ran {client.drafter_calls} times"
    assert client.critic_calls == 2, f"critic ran {client.critic_calls} times"
    assert result.draft == "DRAFT v3", result.draft  # v3 = the revision's output
    assert result.critic["verdict"] == "pass"
    print("✓ revision loop: revise -> rewrite -> pass (1 revision, drafter ran twice)")


def test_tool_calls_update_story_bible() -> None:
    client = FakeClient(verdicts=["pass"])
    bible = StoryBible(premise="test")
    team = NovelTeam(client=client, model="stub", bible=bible, max_revisions=0)
    result = team.run_chapter(chapter=1, goal="decide", target_words=200)

    assert "Ilse Renner" in bible.entities, bible.entities.keys()
    assert bible.entities["Ilse Renner"]["kind"] == "character"
    drafter_result = next(r for r in team.results.values() if r.key == "drafter")
    assert drafter_result.tools and drafter_result.tools[0].name == "record_entity"
    assert result.tokens > 0
    print("✓ tools: drafter's record_entity call mutated the shared story bible")


if __name__ == "__main__":
    test_revision_loop_runs_and_stops()
    test_tool_calls_update_story_bible()
    print("\nAll offline tests passed.")
