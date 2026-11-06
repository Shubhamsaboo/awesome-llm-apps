#!/usr/bin/env python3
"""Score a SKILL.md against the golden set once. No mutation, no loop.

Use it to sanity-check a skill in CI, or to confirm an optimizer run's gain is
real before you commit the new SKILL.md.

    python scripts/score_routing.py
    python scripts/score_routing.py --skill /tmp/candidate.md --model gpt-4o
    python scripts/score_routing.py --json > report.json

Exit code is 1 when accuracy is below --min-accuracy, so it gates a merge, and 2
when any model reply could not be parsed, because that score is partly noise.
"""

import argparse
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "optimizer"))
import skill_paths  # noqa: E402
import telemetry  # noqa: E402
from routing_scorer import RoutingScorer  # noqa: E402
from skill_optimizer import SkillOptimizer  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description="Score a triage SKILL.md on routing accuracy.")
    p.add_argument("--skill", default=skill_paths.SKILL_MD)
    p.add_argument("--golden", default=skill_paths.ROUTING_GOLDEN)
    p.add_argument("--model", default=os.environ.get("TRIAGE_MODEL", "gpt-4o-mini"))
    p.add_argument("--api-key", default=None, help="Defaults to the provider's env var.")
    p.add_argument("--concurrency", type=int, default=4)
    p.add_argument("--min-accuracy", type=float, default=0.0,
                   help="Exit 1 below this. Set it in CI to gate regressions.")
    p.add_argument("--json", action="store_true", help="Emit JSON instead of a table.")
    args = p.parse_args()

    with open(args.skill) as f:
        skill_md = f.read()
    with open(args.golden) as f:
        golden = json.load(f)

    opt = SkillOptimizer(model=args.model, api_key=args.api_key, concurrency=args.concurrency)
    scorer = RoutingScorer(golden["teams"], golden["evals"])
    # One trace per CLI run, so its calls appear as one session in the app.
    with telemetry.span("cli.score_routing",
                        **{"triage.model": opt.model, "triage.backend": opt.backend}):
        result = asyncio.run(opt.score(skill_md, scorer, golden["scenarios"]))

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        _report(result, args)

    if result["parse_errors"]:
        return 2  # the number is partly unparseable model output: do not gate on it
    return 1 if result["pass_rate"] < args.min_accuracy else 0


def _report(result: dict, args) -> None:
    print(f"\n  skill  {os.path.relpath(args.skill)}")
    print(f"  model  {args.model}")
    print(f"\n  Routing accuracy  {result['pass_rate']}%  "
          f"({result['passed']}/{result['total']} scenarios fully correct)\n")
    if result["parse_errors"]:
        print(f"  ⚠  {result['parse_errors']} model reply(ies) could not be parsed and "
              "were scored as failures. Exit 2: rerun before gating on this.\n")

    for e in result["per_eval"]:
        bar = "█" * round(e["pass_rate"] / 5) + "·" * (20 - round(e["pass_rate"] / 5))
        print(f"    {e['name']:<20} {bar} {e['pass_rate']:>5}%  ({e['passed']}/{e['total']})")

    if result["confusion"]:
        print("\n  Mis-routes")
        for c in result["confusion"]:
            print(f"    {c['scenario']:<38} {c['expected']} → {c['predicted']}")

    if result["failures"]:
        print("\n  Failure detail")
        for f in result["failures"]:
            print(f"\n    [{f['scenario_id']}] {f['name']}")
            print(f"      expected  {f['expected_team']} / {f['expected_severity']}")
            print(f"      got       {f['predicted_team']} / {f['predicted_severity']}")
            print(f"      because   {f['agent_reasoning'][:160]}")
    else:
        print("\n  No failures.")
    print()


if __name__ == "__main__":
    sys.exit(main())
