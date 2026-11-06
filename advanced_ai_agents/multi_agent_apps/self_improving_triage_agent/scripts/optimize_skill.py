#!/usr/bin/env python3
"""Score or optimize ANY agent_skills/ skill against its evals.json.

Uses the same loop, backends and tracing as the triage optimizer, with the
skill-creator expectations every skill in this repo already ships:

    python scripts/optimize_skill.py ../../../agent_skills/scope-creep-detector
    python scripts/optimize_skill.py <skill-dir> --optimize --rounds 5 --min-gain 5 \\
        --holdout 0.3 --out /tmp/SKILL.md --model claude_code/sonnet

Scoring is the default. `--optimize` writes the improved SKILL.md to --out and
never overwrites the skill in place. Exit 2 if any model reply was unparseable.
"""

import argparse
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "optimizer"))
import telemetry  # noqa: E402
from expectations_scorer import ExpectationsScorer, evals_path, load_cases  # noqa: E402
from skill_optimizer import SkillOptimizer, split_holdout  # noqa: E402


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Score or optimize a skill against its evals.json.")
    p.add_argument("skill_dir", help="A skill folder containing SKILL.md.")
    p.add_argument("--evals", help="Defaults to agent_skills/evals/<skill>/evals.json.")
    p.add_argument("--model", default=os.environ.get("TRIAGE_MODEL", "gpt-4o-mini"))
    p.add_argument("--api-key", default=None)
    p.add_argument("--concurrency", type=int, default=4)
    p.add_argument("--optimize", action="store_true")
    p.add_argument("--rounds", type=int, default=5)
    p.add_argument("--patience", type=int, default=3)
    p.add_argument("--min-gain", type=float, default=5.0,
                   help="Objective points an edit must add to be kept.")
    p.add_argument("--holdout", type=float, default=0.0,
                   help="Fraction of evals held out from optimization, reported only.")
    p.add_argument("--out", help="Where --optimize writes the improved SKILL.md.")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    if args.optimize and not args.out:
        p.error("--optimize needs --out; the skill is never edited in place")
    with open(os.path.join(args.skill_dir, "SKILL.md")) as f:
        skill_md = f.read()
    cases = load_cases(args.evals or evals_path(args.skill_dir))
    opt = SkillOptimizer(model=args.model, api_key=args.api_key, concurrency=args.concurrency)
    scorer = ExpectationsScorer()
    attrs = {"triage.model": opt.model, "triage.backend": opt.backend}

    if not args.optimize:
        with telemetry.span("cli.score_skill", **attrs):
            result = asyncio.run(opt.score(skill_md, scorer, cases))
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"\n  {os.path.basename(os.path.normpath(args.skill_dir))}: "
                  f"{result['pass_rate']}% of expectations met "
                  f"({result['passed']}/{result['total']} evals fully met)")
            for f in result["failures"]:
                print(f"\n  [{f['case_id']}] {f['prompt'][:90]}")
                for u in f["unmet"]:
                    print(f"    ✗ {u['expectation'][:90]}\n      {u['reason'][:110]}")
            print()
        return 2 if result["parse_errors"] else 0

    train, held = split_holdout(cases, args.holdout)
    result = asyncio.run(opt.optimize(skill_md, scorer, train, holdout=held,
                                      max_rounds=args.rounds, patience=args.patience,
                                      min_gain=args.min_gain))
    with open(args.out, "w") as f:
        f.write(result["improved_skill_md"])
    if args.json:
        print(json.dumps({k: v for k, v in result.items()
                          if k not in ("improved_skill_md", "original_skill_md")}, indent=2))
    else:
        print(f"\n  {result['baseline_score']}% -> {result['final_score']}% on {len(train)} evals")
        if result["holdout"]:
            h = result["holdout"]
            print(f"  held out ({h['total']}): {h['baseline']}% -> {h['final']}%"
                  + ("  ⚠ regressed: likely overfit" if h["regressed"] else ""))
        print(f"  improved SKILL.md written to {args.out}\n")
    return 2 if result["parse_errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
