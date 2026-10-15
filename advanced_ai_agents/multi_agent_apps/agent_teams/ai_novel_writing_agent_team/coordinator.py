"""The coordinator: it sequences the agents and runs the revision loop.

The pipeline is deliberately not a straight line. After the Draft Writer
finishes, the Continuity Critic audits the draft against the story bible. A
failing verdict does not just get printed — the coordinator feeds the critic's
`fix_instructions` back to the Draft Writer and re-drafts, up to
`max_revisions` times. Every agent writes to the same story bible, so the
second draft has strictly more established facts to respect than the first.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from agents import AGENTS, AgentResult, AgentRunner, parse_json_block


@dataclass
class StepEvent:
    """Progress ping emitted for each agent turn (consumed by the UI/logs)."""

    key: str
    name: str
    emoji: str
    status: str  # "running" | "done" | "revise"
    detail: str = ""
    result: AgentResult | None = None


@dataclass
class ChapterResult:
    """Everything the team produced for one chapter."""

    brief: str = ""
    beats: dict[str, Any] = field(default_factory=dict)
    scenes: dict[str, Any] = field(default_factory=dict)
    draft: str = ""
    critic: dict[str, Any] = field(default_factory=dict)
    revisions: int = 0
    tokens: int = 0
    timeline_of_steps: list[str] = field(default_factory=list)


class NovelTeam:
    """Coordinates the five agents for a single chapter."""

    def __init__(
        self,
        client: Any,
        model: str = "gpt-4o-mini",
        bible: Any = None,
        max_revisions: int = 2,
        on_event: Callable[[StepEvent], None] | None = None,
    ) -> None:
        if bible is None:
            from tools import StoryBible

            bible = StoryBible()
        self.client = client
        self.model = model
        self.bible = bible
        self.max_revisions = max_revisions
        self.on_event = on_event or (lambda event: None)
        self.results: dict[str, AgentResult] = {}
        self.chapter_tokens = 0

    # ------------------------------------------------------------------ #
    # internals
    # ------------------------------------------------------------------ #
    def _runner(self, chapter: int) -> AgentRunner:
        return AgentRunner(self.client, self.model, self.bible, chapter)

    def _ask(self, key: str, prompt: str, chapter: int, status: str = "done") -> AgentResult:
        spec = AGENTS[key]
        self.on_event(StepEvent(key, spec.name, spec.emoji, "running"))
        runner = self._runner(chapter)
        result = runner.run(spec, prompt)
        self.results[f"{key}:{chapter}:{len(self.results)}"] = result
        self.chapter_tokens += result.total_tokens
        detail = f"{result.total_tokens} tokens"
        if result.tools:
            detail = f"{len(result.tools)} tool calls · {detail}"
        self.on_event(StepEvent(key, spec.name, spec.emoji, status, detail, result))
        return result

    # ------------------------------------------------------------------ #
    # public API
    # ------------------------------------------------------------------ #
    def run_chapter(
        self,
        chapter: int = 1,
        goal: str = "",
        target_words: int = 1200,
        pov: str = "third person limited",
        genre: str = "",
        style: str = "",
        premise: str = "",
    ) -> ChapterResult:
        """Run the full team for one chapter and return the assembled result."""
        if premise:
            self.bible.premise = premise
        self.chapter_tokens = 0
        out = ChapterResult()
        brief_common = (
            f"Story premise:\n{self.bible.premise or '(none given)'}\n\n"
            f"Chapter {chapter} goal:\n{goal or '(advance the story)'}\n"
            f"Genre: {genre or 'unspecified'} · POV: {pov} · "
            f"Language/style: {style or 'match the premise'}\n"
        )

        # 1. Continuity Librarian ---------------------------------------- #
        librarian = self._ask(
            "librarian",
            brief_common
            + "\nGive the continuity brief for this chapter: established facts "
            "that matter, plus open threads that must not be contradicted.",
            chapter,
        )
        out.brief = librarian.text
        out.timeline_of_steps.append(f"📚 Continuity brief ({librarian.total_tokens} tokens)")

        # 2. Story Architect --------------------------------------------- #
        architect = self._ask(
            "architect",
            brief_common
            + f"\nContinuity brief:\n{out.brief}\n\nProduce the beat sheet JSON.",
            chapter,
        )
        out.beats = parse_json_block(architect.text) or {"raw": architect.text}
        beats = (out.beats.get("beats") or [])
        out.timeline_of_steps.append(
            f"🏛️ Beat sheet: {len(beats)} beats ({architect.total_tokens} tokens)"
        )

        # 3. Scene Designer ---------------------------------------------- #
        designer = self._ask(
            "designer",
            brief_common
            + f"\nBeats:\n{architect.text}\n\nProduce the scene cards JSON. "
            f"Total word budget: {target_words}.",
            chapter,
        )
        out.scenes = parse_json_block(designer.text) or {"raw": designer.text}
        scenes = out.scenes.get("scenes") or []
        out.timeline_of_steps.append(
            f"🎬 Scene cards: {len(scenes)} scenes ({designer.total_tokens} tokens)"
        )

        # 4. Draft Writer ------------------------------------------------- #
        draft_prompt = (
            brief_common
            + f"\nContinuity brief:\n{out.brief}"
            + f"\n\nBeat sheet:\n{architect.text}"
            + f"\n\nScene cards:\n{designer.text}"
            + f"\n\nWrite the full chapter now ({target_words} words, ±15%). "
            "Prose only — no headings, no notes."
        )
        drafter = self._ask("drafter", draft_prompt, chapter)
        out.draft = drafter.text
        out.timeline_of_steps.append(
            f"✍️ Draft: {len(out.draft)} chars, {len(drafter.tools)} tool calls"
        )

        # 5. Continuity Critic + revision loop ---------------------------- #
        revision = 0
        while True:
            critic = self._ask(
                "critic",
                brief_common
                + f"\nScene cards:\n{designer.text}"
                + f"\n\nDraft:\n{out.draft}"
                + "\n\nAudit the draft and return the verdict JSON.",
                chapter,
                status="done" if revision == 0 else "revise",
            )
            out.critic = parse_json_block(critic.text) or {"raw": critic.text}
            verdict = str(out.critic.get("verdict", "pass")).lower()
            high = [
                i
                for i in (out.critic.get("issues") or [])
                if str(i.get("severity", "")).lower() == "high"
            ]
            out.timeline_of_steps.append(
                f"🔍 Critic: {verdict} (score {out.critic.get('score', '?')}, "
                f"{len(high)} high-severity)"
            )

            if verdict == "pass" and not high:
                break
            if revision >= self.max_revisions:
                out.timeline_of_steps.append(
                    f"⚠️ revision limit reached ({self.max_revisions})"
                )
                break

            revision += 1
            fixes = out.critic.get("fix_instructions") or []
            self.on_event(
                StepEvent(
                    "drafter",
                    AGENTS["drafter"].name,
                    AGENTS["drafter"].emoji,
                    "revise",
                    f"revision {revision}: {len(fixes)} fixes",
                )
            )
            revised = self._ask(
                "drafter",
                brief_common
                + f"\nYour draft:\n{out.draft}"
                + "\n\nThe editor found these problems:\n- "
                + "\n- ".join(str(f) for f in fixes)
                + "\n\nRewrite the chapter applying every fix. Keep what works; "
                "output the complete revised chapter as prose only.",
                chapter,
            )
            out.draft = revised.text
            out.timeline_of_steps.append(
                f"✍️ Revision {revision}: {len(out.draft)} chars"
            )

        out.revisions = revision
        out.tokens = self.chapter_tokens

        # 6. Persist what this chapter established ------------------------- #
        self.bible.add_chapter_summary(
            f"Ch{chapter}: {(out.beats.get('chapter_title') or goal or '').strip()}"
        )
        return out
