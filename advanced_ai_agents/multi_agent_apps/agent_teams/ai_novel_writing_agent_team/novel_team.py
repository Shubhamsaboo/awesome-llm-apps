#!/usr/bin/env python3
"""Run the AI Novel Writing Agent Team from the command line.

This is the primary entry point and it makes real model calls: every agent
(librarian, architect, designer, drafter, critic) is an LLM request, and the
drafter/critic loop can send the chapter back for revision.

    export OPENAI_API_KEY=sk-...
    python novel_team.py \
        --premise "A night-shift tram driver finds a passenger who is not on any timetable." \
        --goal "She decides whether to report him." \
        --chapters 2 --words 900 --out out

Any OpenAI-compatible endpoint works — point OPENAI_BASE_URL at it (or pass
--base-url) and pick a model with --model.

Want to see the plan without spending a token? `--dry-run` prints the agent
line-up and the exact prompts that would be sent, and calls nothing.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from coordinator import NovelTeam, StepEvent
from tools import StoryBible

DEFAULT_PREMISE = (
    "The last tram of the night, in a city that is quietly being rebuilt around "
    "the people who live in it. A driver who has memorised every timetable "
    "starts noticing a passenger who boards but never appears on her sheets."
)


def build_client(args: argparse.Namespace) -> object:
    """Create an OpenAI-compatible client, or exit with a helpful message."""
    try:
        from openai import OpenAI
    except ImportError:  # pragma: no cover - dependency hint
        sys.exit("Missing dependency. Run: pip install -r requirements.txt")

    api_key = args.api_key or os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        sys.exit(
            "No API key found. Set OPENAI_API_KEY (or pass --api-key).\n"
            "Tip: `python novel_team.py --dry-run` shows the plan without any key."
        )
    base_url = args.base_url or os.getenv("OPENAI_BASE_URL") or None
    return OpenAI(api_key=api_key, base_url=base_url)


def log_event(event: StepEvent) -> None:
    """One line per agent turn, printed as the team works."""
    icon = {"running": "…", "done": "✓", "revise": "↻"}.get(event.status, "·")
    detail = f" — {event.detail}" if event.detail else ""
    print(f"  {icon} {event.emoji} {event.name}{detail}", flush=True)


def print_plan(args: argparse.Namespace) -> None:
    """--dry-run: show the pipeline and prompts, call nothing."""
    from agents import AGENTS

    print("Pipeline (no model calls in --dry-run):")
    order = ["librarian", "architect", "designer", "drafter", "critic"]
    for i, key in enumerate(order, 1):
        spec = AGENTS[key]
        tools = ", ".join(spec.tools) or "none"
        print(f"  {i}. {spec.emoji} {spec.name}  [temp {spec.temperature}, tools: {tools}]")
    print(f"  ↻ revision loop: {args.revisions} max (critic verdict 'revise' -> drafter)")
    print("\nChapter brief that would be sent to the team:")
    print(f"  premise : {args.premise[:100]}...")
    print(f"  goal    : {args.goal}")
    print(f"  chapters: {args.chapters} · words/chapter: {args.words} · pov: {args.pov}")
    print("\nDrop --dry-run (and set OPENAI_API_KEY) to actually run the team.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Multi-agent novel writing team (real LLM calls by default)."
    )
    parser.add_argument("--premise", default=DEFAULT_PREMISE, help="Story premise.")
    parser.add_argument("--goal", default="", help="What this chapter must achieve.")
    parser.add_argument("--chapters", type=int, default=1, help="How many chapters.")
    parser.add_argument("--words", type=int, default=900, help="Words per chapter.")
    parser.add_argument("--pov", default="third person limited")
    parser.add_argument("--genre", default="literary fiction")
    parser.add_argument("--style", default="")
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    parser.add_argument("--base-url", default=None, help="OpenAI-compatible base URL.")
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--revisions", type=int, default=2, help="Max revision rounds.")
    parser.add_argument("--out", default="out", help="Directory for artifacts.")
    parser.add_argument("--dry-run", action="store_true", help="Print the plan only.")
    args = parser.parse_args()

    if args.dry_run:
        print_plan(args)
        return 0

    client = build_client(args)
    bible = StoryBible(title=args.premise.split(".")[0][:60], premise=args.premise)
    team = NovelTeam(
        client=client, model=args.model, bible=bible,
        max_revisions=args.revisions, on_event=log_event,
    )

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    total_tokens = 0

    for chapter in range(1, args.chapters + 1):
        goal = args.goal or f"Chapter {chapter}: advance the premise and expose a new complication."
        print(f"\nChapter {chapter} — {goal}")
        result = team.run_chapter(
            chapter=chapter, goal=goal, target_words=args.words, pov=args.pov,
            genre=args.genre, style=args.style,
        )
        chapter_path = out_dir / f"chapter_{chapter:02d}.md"
        chapter_path.write_text(result.draft, encoding="utf-8")
        (out_dir / f"chapter_{chapter:02d}_beats.json").write_text(
            json.dumps(result.beats, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (out_dir / f"chapter_{chapter:02d}_scenes.json").write_text(
            json.dumps(result.scenes, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (out_dir / f"chapter_{chapter:02d}_critic.json").write_text(
            json.dumps(result.critic, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        total_tokens += result.tokens
        print(f"\n  ── draft ──\n{result.draft[:600]}"
              + ("…" if len(result.draft) > 600 else ""))
        verdict = result.critic.get("verdict", "?")
        print(f"\n  critic verdict: {verdict} "
              f"(score {result.critic.get('score', '?')}, revisions {result.revisions}"
              f", {result.tokens} tokens)")

    (out_dir / "story_bible.json").write_text(bible.to_json(), encoding="utf-8")
    print(f"\nWrote {args.chapters} chapter(s) + artifacts to {out_dir.resolve()}")
    print(f"Model calls used ~{total_tokens} tokens across the team.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
