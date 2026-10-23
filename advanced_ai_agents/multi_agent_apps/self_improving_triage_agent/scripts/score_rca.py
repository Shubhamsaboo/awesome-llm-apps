#!/usr/bin/env python3
"""Score an RCA against the binary-check rubric.

Three numbers, never averaged together:

  CORRECTNESS  did the RCA find the documented root cause?   (needs ground truth)
  QUALITY      weighted pass rate over the rubric's checks    (always available)
  GROUNDING    is it tied to the log links and code it was given?  (when attached)

A polished RCA with the wrong conclusion scores high on quality and fails
correctness. Folding them into one number hides exactly the failure you care
about most. Grounding is likewise separate: an RCA can be right and well argued
while citing a code line that does not exist, and that must not be averaged away.
A fabricated link or code line is a hard fail that blocks handoff.

    python scripts/score_rca.py --rca incident.md --evidence bundle.json
    python scripts/score_rca.py --rca incident.md --profile returning-owner
    python scripts/score_rca.py --calibrate            # judge vs human labels
"""

import argparse
import asyncio
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "optimizer"))
import grounding  # noqa: E402
import log_links  # noqa: E402
import telemetry  # noqa: E402
from triage_optimizer import TriageOptimizer  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
REFS = os.path.join(ROOT, "references")

JUDGE_SYSTEM = (
    "You audit RCA documents against binary checks. For each check answer true "
    "only if it is unambiguously satisfied by the document as written — not by "
    "what the author probably meant, and not by what you would have written. "
    "Answer \"na\" only when the check's own precondition is absent, and only "
    "where its wording offers na as an option. Quote the span of the RCA that "
    "decides each answer. Return valid JSON only."
)

GATE_SYSTEM = (
    "You compare an RCA's conclusion against a documented root cause. Judge "
    "substance over wording: an equivalent mechanism described in different "
    "words is correct. Listing the true cause as one possibility among several "
    "is partially_correct, not correct. Return valid JSON only."
)


SESSION_LINE = re.compile(r"^\s*-\s*\*\*Session:\*\*.*$\n?", re.MULTILINE)


def strip_session(rca: str) -> str:
    """Drop the replay link: the judge cannot open it, and evidence that exists
    only in the replay must not satisfy an evidence check."""
    return SESSION_LINE.sub("", rca)


def _verdict(raw):
    """Coerce a judge answer to True, False, or the string "na"."""
    if isinstance(raw, str):
        word = raw.strip().lower()
        if word in {"na", "n/a", "not_applicable"}:
            return "na"
        # bool("false") is True; an unrecognised word fails closed.
        return word in {"true", "yes", "pass", "passed"}
    return raw is True or (isinstance(raw, int) and raw == 1)


def render_evidence(bundle, max_entries: int = 40) -> str:
    """Compact the bundle for a prompt without losing what checks depend on."""
    if not bundle:
        return "(no evidence bundle supplied)"
    w = bundle.get("symptom_window") or {}
    head = [
        f"vendor: {bundle.get('vendor')}",
        f"symptom: {bundle.get('symptom') or '(unstated)'}",
        f"window: {w.get('start')} -> {w.get('end')}",
        f"services: {', '.join(bundle.get('services') or []) or '(none)'}",
        f"trace_ids: {', '.join(bundle.get('trace_ids') or []) or '(none)'}",
        f"severity_counts: {bundle.get('severity_counts')}",
    ]
    if bundle.get("query"):
        head.append(f"query: {bundle['query']}")
    if bundle.get("deploys"):
        head.append(f"deploys: {json.dumps(bundle['deploys'])}")

    entries = bundle.get("entries") or []
    # Errors first: a truncated tail of INFO lines would strand the checks that
    # ask whether the RCA cited the actual failure.
    ranked = sorted(
        entries,
        key=lambda e: ({"CRITICAL": 0, "ERROR": 1, "WARN": 2, "INFO": 3, "DEBUG": 4}
                       .get(e.get("severity"), 5), e.get("ts") or ""),
    )[:max_entries]
    lines = [
        f"  [{e.get('ts')}] {e.get('severity')} {e.get('service') or '-'} "
        f"trace={e.get('trace_id') or '-'} :: {(e.get('message') or '')[:200]}"
        + (f"  attrs={json.dumps(e['attributes'])[:200]}" if e.get("attributes") else "")
        for e in ranked
    ]
    omitted = len(entries) - len(ranked)
    if omitted > 0:
        lines.append(f"  ... {omitted} lower-severity entries omitted")
    return ("\n".join(head) + "\n\nentries (most severe first):\n" + "\n".join(lines)
            + _render_attachments(bundle))


def _render_attachments(bundle, max_code_lines: int = 80) -> str:
    """Attached log links and code, so a judge (and the skill under test) sees what
    the RCA is allowed to cite. Code carries line numbers: a citation is only
    checkable against numbered lines."""
    out = []
    for item in bundle.get("links") or []:
        parsed = log_links.parse_link(item.get("url", ""))
        label = f" ({item['label']})" if item.get("label") else ""
        out.append(f"  - {item.get('url')}{label}\n      shows: "
                   + (log_links.describe(parsed) if parsed else "unrecognised link"))
    text = ("\n\nattached log links (an RCA may cite only these):\n" + "\n".join(out)) if out else ""

    blocks, budget = [], max_code_lines
    for s in grounding.snippets(bundle):
        shown = s["lines"][:max(budget, 0)]
        budget -= len(shown)
        ref = f" @ {s['ref']}" if s["ref"] else ""
        blocks.append(f"  {s['path']}{ref}, lines {s['start']}-{s['end']}:\n"
                      + "\n".join(f"    {s['start'] + i:>4} | {ln}" for i, ln in enumerate(shown))
                      + ("\n    ... truncated" if len(shown) < len(s["lines"]) else ""))
    if blocks:
        text += "\n\nattached code (an RCA may cite only these lines):\n" + "\n".join(blocks)
    return text


def all_checks(rubric) -> list:
    return [{**c, "dimension": d["id"]} for d in rubric["dimensions"] for c in d["checks"]]


async def judge_once(opt, rca, evidence_text, checks, role="judge"):
    return await opt._ask_json(
        JUDGE_SYSTEM,
        (
            f"# Evidence bundle\n{evidence_text}\n\n"
            f"# RCA under review\n{rca}\n\n"
            f"# Checks\n{json.dumps([{k: c[k] for k in ('id', 'question')} for c in checks], indent=2)}\n\n"
            f'Return JSON: {{"results": [{{"id": "ev_quotes_log", '
            f'"passed": true | false | "na", '
            f'"quote": "the deciding span of the RCA, or empty if none"}}]}}'
        ),
        fallback={"results": []},
        temperature=0.0,
        role=role,
    )


async def judge_gate(opt, rca, true_root_cause, gate):
    return await opt._ask_json(
        GATE_SYSTEM,
        (
            f"# Documented root cause\n{true_root_cause}\n\n"
            f"# RCA conclusion under review\n{rca}\n\n"
            f"# Question\n{gate['question']}\n\n"
            f'Return JSON: {{"verdict": "{"|".join(gate["bands"])}", '
            f'"reason": "one sentence"}}'
        ),
        fallback={"verdict": "wrong", "reason": "judge failed to parse"},
        temperature=0.0,
        role="judge.gate",
    )


def _majority(passes, ids):
    """Majority vote per check rather than a median of composites: variance shows
    up on individual judgments, so that is where it should be suppressed."""
    votes: dict = {cid: [] for cid in ids}
    quotes: dict = {}
    for p in passes:
        for r in (p.get("results") or []):
            cid = r.get("id")
            if cid in votes:
                votes[cid].append(_verdict(r.get("passed")))
                if r.get("quote") and cid not in quotes:
                    quotes[cid] = r["quote"]

    verdicts, unstable = {}, []
    for cid, vs in votes.items():
        if not vs:
            verdicts[cid] = False  # No judge output is a failure, not a pass.
            continue
        winner, count = Counter(vs).most_common(1)[0]
        verdicts[cid] = winner
        if count < len(vs):
            unstable.append(cid)
    return verdicts, quotes, unstable


async def score_grounding(opt, rca, bundle, rubric, evidence_text, runs=3):
    """Third score: deterministic checks in code, the rest by the judge.

    Returns None when the rubric has no grounding block. Judged checks run only
    when their inputs (links or code) are attached; otherwise they are n/a.
    """
    spec = rubric.get("grounding")
    if not spec:
        return None
    det = grounding.run_deterministic(rca, bundle, spec)
    to_judge = grounding.applicable_judged(bundle, spec)
    judged = []
    if to_judge:
        passes = await asyncio.gather(*[
            judge_once(opt, rca, evidence_text, to_judge, role="judge.grounding")
            for _ in range(runs)])
        verdicts, quotes, unstable = _majority(passes, [c["id"] for c in to_judge])
        judged = [{"id": cid, "passed": verdicts[cid], "quote": quotes.get(cid, "")}
                  for cid in verdicts]
    else:
        unstable = []
    result = grounding.summarize(det, judged, spec)
    result["unstable_checks"] = unstable
    return result


async def score_rca(opt, rca, bundle, rubric, profile="balanced", runs=3,
                    true_root_cause=None):
    rca = strip_session(rca)
    checks = all_checks(rubric)
    evidence_text = render_evidence(bundle)

    passes = await asyncio.gather(
        *[judge_once(opt, rca, evidence_text, checks) for _ in range(runs)]
    )

    verdicts, quotes, unstable = _majority(passes, [c["id"] for c in checks])

    weights = rubric["profiles"][profile]["weights"]
    per_dimension, weighted, applicable_weight = [], 0.0, 0.0
    for d in rubric["dimensions"]:
        ids = [c["id"] for c in d["checks"]]
        applicable = [i for i in ids if verdicts.get(i) != "na"]
        passed = sum(1 for i in applicable if verdicts.get(i) is True)
        w = weights.get(d["id"], 0.0)
        if applicable:
            rate = passed / len(applicable)
            weighted += rate * w
            applicable_weight += w
        else:
            rate = None  # Whole dimension inapplicable; weight redistributes below.
        per_dimension.append({
            "dimension": d["id"], "weight": w, "passed": passed,
            "total": len(applicable), "na": len(ids) - len(applicable),
            "rate": None if rate is None else round(100 * rate, 1),
            "failed": [i for i in applicable if verdicts.get(i) is not True],
        })

    # Redistribute the weight of dropped dimensions across those that applied, so
    # a case the user gave no hypothesis for is not capped below 100 for it.
    composite = weighted / applicable_weight if applicable_weight else 0.0

    result = {
        "profile": profile,
        "quality": round(100 * composite, 1),
        "per_dimension": per_dimension,
        "dropped_dimensions": [d["dimension"] for d in per_dimension if d["rate"] is None],
        "applicable_weight": round(applicable_weight, 4),
        "checks": [
            {"id": c["id"], "dimension": c["dimension"],
             "passed": verdicts.get(c["id"], False),
             "quote": quotes.get(c["id"], ""), "question": c["question"]}
            for c in checks
        ],
        "unstable_checks": unstable,
        "runs": runs,
    }

    grounded = await score_grounding(opt, rca, bundle, rubric, evidence_text, runs)
    if grounded is not None:
        result["grounding"] = grounded

    if true_root_cause:
        gate = await judge_gate(opt, rca, true_root_cause, rubric["gate"])
        result["correctness"] = gate.get("verdict", "wrong")
        result["correctness_reason"] = gate.get("reason", "")
    return result


# -- Reporting ---------------------------------------------------------------


def report(r, rca_path):
    band = ("HAND OFF" if r["quality"] > 80 else
            "CONDITIONAL" if r["quality"] >= 60 else "SEND BACK")
    print(f"\n  {os.path.basename(rca_path)}   profile={r['profile']}  runs={r['runs']}")
    if "correctness" in r:
        mark = {"correct": "PASS", "partially_correct": "PARTIAL", "wrong": "FAIL"}
        print(f"\n  CORRECTNESS  {mark.get(r['correctness'], '?')}  ({r['correctness']})")
        if r.get("correctness_reason"):
            print(f"               {r['correctness_reason'][:100]}")
    print(f"  QUALITY      {r['quality']}/100  ->  {band}")
    g = r.get("grounding")
    if g:
        if g["hard_fail"]:
            print(f"  GROUNDING    FAIL  cites something that was never attached "
                  f"({', '.join(g['fabricated'])}) -> blocks handoff")
        elif g["score"] is None:
            print("  GROUNDING    n/a   (no log links or code attached)")
        else:
            print(f"  GROUNDING    {g['score']}/100  ({g['passed']}/{g['total']} checks)")
    print()

    for d in r["per_dimension"]:
        if d["rate"] is None:
            print(f"    {d['dimension']:<22} {'—' * 20}    n/a  0/0  "
                  f"w={d['weight']:.2f}   (not applicable, weight redistributed)")
            continue
        filled = round(d["rate"] / 5)
        bar = "█" * filled + "·" * (20 - filled)
        notes = []
        if not d["weight"]:
            notes.append("unweighted in this profile")
        if d["na"]:
            notes.append(f"{d['na']} n/a")
        suffix = f"   ({', '.join(notes)})" if notes else ""
        print(f"    {d['dimension']:<22} {bar} {d['rate']:>5}%  "
              f"{d['passed']}/{d['total']}  w={d['weight']:.2f}{suffix}")

    if r.get("dropped_dimensions"):
        print(f"\n  Weight rescaled over {r['applicable_weight']:.2f} of the profile "
              f"(dropped: {', '.join(r['dropped_dimensions'])})")

    failed = [c for c in r["checks"] if c["passed"] is not True and c["passed"] != "na"]
    if failed:
        print("\n  Failed checks")
        for c in failed:
            print(f"    ✗ {c['id']:<22} {c['question'][:92]}")
    na = [c["id"] for c in r["checks"] if c["passed"] == "na"]
    if na:
        print(f"\n  Not applicable: {', '.join(na)}")
    if g and g["total"]:
        print("\n  Grounding checks")
        for c in g["checks"]:
            if c["passed"] == "na":
                continue
            mark = "✓" if c["passed"] is True else ("✗✗" if c["hard_fail"] else "✗")
            kind = "code " if c["kind"] == "deterministic" else "judge"
            print(f"    {mark:<2} {c['id']:<27} [{kind}] {str(c['detail'])[:80]}")
    unstable = r["unstable_checks"] + ((g or {}).get("unstable_checks") or [])
    if unstable:
        print(f"\n  ⚠  Split votes across runs: {', '.join(unstable)}")
        print("     Those checks are ambiguous for this RCA — reword them or raise --runs.")
    print()


async def calibrate(opt, golden, rubric, profile, runs):
    """Compare judge output against human labels in the golden set."""
    cases = [c for c in golden["cases"] if c.get("human_quality") is not None]
    if not cases:
        print("No cases carry a human_quality label. Add some before calibrating.")
        return 1

    print(f"\n  Calibrating {len(cases)} labeled case(s), profile={profile}, runs={runs}\n")
    print(f"    {'case':<26} {'human':>6} {'judge':>6} {'delta':>6}   correctness")
    deltas = []
    for c in cases:
        r = await score_rca(opt, c["rca"], c.get("evidence"), rubric, profile, runs,
                            c.get("true_root_cause"))
        delta = r["quality"] - c["human_quality"]
        deltas.append(delta)
        agree = "" if "correctness" not in r else (
            f"   {r['correctness']} (expected {c.get('expected_correctness', '?')})")
        print(f"    {c['id']:<26} {c['human_quality']:>6} {r['quality']:>6} "
              f"{delta:>+6.1f}{agree}")

    mean = sum(deltas) / len(deltas)
    spread = max(deltas) - min(deltas)
    print(f"\n    mean bias {mean:+.1f} pts   spread {spread:.1f} pts")
    if abs(mean) > 10:
        print("    ⚠  Judge is systematically off. Reword the checks it keeps "
              "misreading before trusting absolute scores.")
    elif spread > 25:
        print("    ⚠  Bias is inconsistent across cases — the rubric is being read "
              "differently per document. Absolute scores are not comparable yet.")
    else:
        print("    Judge tracks the human labels closely enough to compare RCAs.")
    print()
    return 0


def _session_attrs(opt) -> dict:
    return {"triage.model": opt.model, "triage.backend": opt.backend}


def main() -> int:
    p = argparse.ArgumentParser(description="Score an RCA against the binary-check rubric.")
    p.add_argument("--rca", help="Path to the RCA markdown document.")
    p.add_argument("--evidence", help="Normalized evidence bundle from normalize_evidence.py.")
    p.add_argument("--true-root-cause", help="Ground truth, to score correctness.")
    p.add_argument("--rubric", default=os.path.join(REFS, "rca-rubric.json"))
    p.add_argument("--golden", default=os.path.join(REFS, "rca-golden-set.json"))
    p.add_argument("--profile", default=None, help="balanced | returning-owner | curious")
    p.add_argument("--model", default=os.environ.get("TRIAGE_MODEL", "gpt-4o-mini"))
    p.add_argument("--api-key", default=None)
    p.add_argument("--runs", type=int, default=3, help="Judge passes; majority vote per check.")
    p.add_argument("--calibrate", action="store_true", help="Score the labeled golden set.")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    with open(args.rubric) as f:
        rubric = json.load(f)
    profile = args.profile or rubric.get("default_profile", "balanced")
    if profile not in rubric["profiles"]:
        print(f"Unknown profile {profile!r}. Available: {sorted(rubric['profiles'])}",
              file=sys.stderr)
        return 2

    opt = TriageOptimizer(model=args.model, api_key=args.api_key,
                          concurrency=max(args.runs, 4))

    if args.calibrate:
        with open(args.golden) as f:
            golden = json.load(f)
        with telemetry.span("cli.score_rca.calibrate", **_session_attrs(opt)):
            return asyncio.run(calibrate(opt, golden, rubric, profile, args.runs))

    if not args.rca:
        print("Pass --rca, or --calibrate.", file=sys.stderr)
        return 2

    with open(args.rca) as f:
        rca = f.read()
    bundle = None
    if args.evidence:
        with open(args.evidence) as f:
            bundle = json.load(f)

    with telemetry.span("cli.score_rca", **_session_attrs(opt)):
        result = asyncio.run(score_rca(opt, rca, bundle, rubric, profile, args.runs,
                                       args.true_root_cause))
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        report(result, args.rca)

    if result.get("correctness") == "wrong":
        return 2
    if (result.get("grounding") or {}).get("hard_fail"):
        return 2  # cites a link or code line that was never attached
    return 0 if result["quality"] > 80 else 1


if __name__ == "__main__":
    sys.exit(main())
