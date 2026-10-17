"""Tools that the novel-writing agents actually call.

Two kinds of tools are exposed here:

1. A small in-memory "story bible" (entities + timeline events). Agents *write*
   to it as they invent characters, places and plot events, and later agents
   *read* from it so the story stays consistent across chapters. This is what
   turns a chain of prompt builders into agents that share state.
2. Pure-Python text utilities (word budget tracking, repeated-phrase
   detection) so the drafter can check its own output without spending tokens.

Every tool returns a plain string, which is what the model sees as the tool
result. The OpenAI function-calling schemas live next to the implementations
so they cannot drift apart.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Callable


# --------------------------------------------------------------------------- #
# Story bible: shared long-term memory for the agent team
# --------------------------------------------------------------------------- #
@dataclass
class StoryBible:
    """Entities and timeline events accumulated across the whole session.

    Agents mutate this object while they work, so anything an agent invents is
    visible to every later agent (and to the continuity critic).
    """

    title: str = "Untitled"
    premise: str = ""
    entities: dict[str, dict[str, Any]] = field(default_factory=dict)
    timeline: list[dict[str, Any]] = field(default_factory=list)
    chapter_summaries: list[str] = field(default_factory=list)

    # -- writes ------------------------------------------------------------ #
    def add_entity(
        self,
        name: str,
        kind: str = "character",
        traits: str = "",
        notes: str = "",
        chapter: int = 1,
    ) -> dict[str, Any]:
        """Insert or update an entity. Returns the stored record."""
        key = name.strip()
        record = self.entities.get(key)
        if record is None:
            record = {
                "name": key,
                "kind": kind,
                "traits": traits,
                "notes": notes,
                "first_seen_chapter": chapter,
            }
            self.entities[key] = record
        else:
            # Merge instead of overwrite: later agents often add detail only.
            if traits:
                record["traits"] = f"{record['traits']}; {traits}".strip("; ")
            if notes:
                record["notes"] = f"{record['notes']}; {notes}".strip("; ")
        return record

    def add_timeline_event(
        self, chapter: int, event: str, entities: list[str] | None = None
    ) -> dict[str, Any]:
        """Append an event to the chapter timeline."""
        entry = {
            "chapter": chapter,
            "event": event.strip(),
            "entities": [e.strip() for e in (entities or []) if e.strip()],
        }
        self.timeline.append(entry)
        return entry

    def add_chapter_summary(self, summary: str) -> None:
        """Record a one-paragraph summary so future chapters keep the thread."""
        if summary.strip():
            self.chapter_summaries.append(summary.strip())

    # -- reads ------------------------------------------------------------- #
    def find_entities(self, query: str, limit: int = 8) -> list[dict[str, Any]]:
        """Case-insensitive substring search over name, traits and notes."""
        needle = query.strip().lower()
        if not needle:
            return []
        hits = []
        for record in self.entities.values():
            haystack = " ".join(
                str(record.get(k, "")) for k in ("name", "kind", "traits", "notes")
            ).lower()
            if needle in haystack:
                hits.append(record)
        return hits[:limit]

    def recap(self, chapter: int | None = None, limit: int = 20) -> str:
        """Human-readable recap of facts relevant to an upcoming chapter."""
        lines: list[str] = []
        if self.chapter_summaries:
            lines.append("PREVIOUS CHAPTERS")
            lines.extend(f"- {s}" for s in self.chapter_summaries[-5:])
        if self.entities:
            lines.append("\nKNOWN ENTITIES")
            lines.extend(
                f"- {r['name']} ({r['kind']}): {r['traits']} {r['notes']}".strip()
                for r in list(self.entities.values())[:limit]
            )
        if self.timeline:
            lines.append("\nTIMELINE")
            events = self.timeline
            if chapter is not None:
                events = [e for e in events if e["chapter"] <= chapter]
            lines.extend(
                f"- ch{e['chapter']}: {e['event']}" for e in events[-limit:]
            )
        return "\n".join(lines) if lines else "(the story bible is still empty)"

    def to_json(self) -> str:
        """Serialise the bible; the continuity critic reads this verbatim."""
        return json.dumps(
            {
                "title": self.title,
                "premise": self.premise,
                "entities": list(self.entities.values()),
                "timeline": self.timeline,
                "chapter_summaries": self.chapter_summaries,
            },
            ensure_ascii=False,
            indent=2,
        )


# --------------------------------------------------------------------------- #
# Text utilities
# --------------------------------------------------------------------------- #
def count_words(text: str) -> int:
    """Count words for both space-separated and CJK text."""
    cjk = len(re.findall(r"[\u4e00-\u9fff]", text))
    latin = len(re.findall(r"[A-Za-z0-9']+", text))
    return cjk + latin


def text_stats(text: str) -> dict[str, Any]:
    """Cheap structural stats the drafter can use to self-check."""
    sentences = [s for s in re.split(r"[.!?。！？\n]+", text) if s.strip()]
    lengths = [count_words(s) for s in sentences] or [0]
    return {
        "words": count_words(text),
        "characters": len(text),
        "sentences": len(sentences),
        "paragraphs": len([p for p in text.split("\n\n") if p.strip()]),
        "avg_sentence_words": round(sum(lengths) / len(lengths), 1),
        "longest_sentence_words": max(lengths),
    }


def find_repeated_phrases(text: str, ngram: int = 3, top_k: int = 12) -> list[str]:
    """Return the most repeated n-grams — a cheap proxy for AI-smell."""
    words = re.findall(r"[A-Za-z']+|[\u4e00-\u9fff]{2,}", text.lower())
    if len(words) < ngram:
        return []
    grams = Counter(
        " ".join(words[i : i + ngram]) for i in range(len(words) - ngram + 1)
    )
    return [f"{g} (x{c})" for g, c in grams.most_common(top_k) if c > 1][:top_k]


# --------------------------------------------------------------------------- #
# Tool schemas (OpenAI function-calling format) + dispatcher
# --------------------------------------------------------------------------- #
TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "bible_search",
            "description": (
                "Search the story bible for characters, places or objects whose "
                "name, traits or notes match a query. Use before inventing new "
                "names or referring to past events."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Name or keyword."}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "bible_recap",
            "description": "Return the full recap (chapters, entities, timeline).",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "bible_dump",
            "description": "Return the raw JSON of the story bible for auditing.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "record_entity",
            "description": "Save a character, place or object so later agents stay consistent.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "kind": {
                        "type": "string",
                        "enum": ["character", "place", "object", "faction"],
                    },
                    "traits": {"type": "string", "description": "Short factual traits."},
                    "notes": {"type": "string", "description": "Optional extra detail."},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "record_event",
            "description": "Append a plot event to the chapter timeline.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chapter": {"type": "integer"},
                    "event": {"type": "string"},
                    "entities": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Names involved in the event.",
                    },
                },
                "required": ["chapter", "event"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "text_stats",
            "description": "Word / sentence / paragraph counts for a draft so far.",
            "parameters": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "repetition_check",
            "description": "Find frequently repeated short phrases (AI-smell detector).",
            "parameters": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        },
    },
]


def build_dispatcher(bible: StoryBible, chapter: int) -> Callable[[str, dict], str]:
    """Bind a story bible + chapter number to a `name -> str` tool executor."""

    def dispatch(name: str, args: dict[str, Any]) -> str:
        try:
            if name == "bible_search":
                hits = bible.find_entities(str(args.get("query", "")))
                return json.dumps(hits, ensure_ascii=False) if hits else "no matches"
            if name == "bible_recap":
                return bible.recap(chapter)
            if name == "bible_dump":
                return bible.to_json()
            if name == "record_entity":
                rec = bible.add_entity(
                    name=str(args.get("name", "")).strip(),
                    kind=str(args.get("kind", "character")),
                    traits=str(args.get("traits", "")),
                    notes=str(args.get("notes", "")),
                    chapter=chapter,
                )
                return f"stored entity: {rec['name']}"
            if name == "record_event":
                rec = bible.add_timeline_event(
                    chapter=int(args.get("chapter", chapter)),
                    event=str(args.get("event", "")),
                    entities=list(args.get("entities") or []),
                )
                return f"stored event for chapter {rec['chapter']}"
            if name == "text_stats":
                return json.dumps(text_stats(str(args.get("text", ""))))
            if name == "repetition_check":
                found = find_repeated_phrases(str(args.get("text", "")))
                return json.dumps(found) if found else "no notable repetition"
            return f"error: unknown tool '{name}'"
        except Exception as exc:  # tools must never crash the agent loop
            return f"error: {type(exc).__name__}: {exc}"

    return dispatch
