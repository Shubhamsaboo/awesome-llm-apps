"""Self-improving RCA writer: the same hill-climb, scored on RCA quality.

Reuses TriageOptimizer's loop (rounds, patience, mutation log, events) and
replaces only the scorer. Per case the Executor writes an RCA from a normalized
evidence bundle, then the judge grades it against the binary-check rubric.

Two numbers come back, never averaged:
  correctness — did the RCA reach the documented root cause?
  quality     — weighted pass rate over the rubric's checks

The optimized objective is `0.6 * correctness + 0.4 * quality`, because a skill
that writes beautiful RCAs with wrong conclusions is a worse skill.
"""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))

from triage_optimizer import TriageOptimizer  # noqa: E402
from score_rca import render_evidence, score_rca as score_rca_doc  # noqa: E402

CORRECTNESS_WEIGHT = 0.6

# Fallback when the rubric carries no credit matrix. Keyed [expected][actual].
_DEFAULT_CREDIT = {
    "correct": {"correct": 1.0, "partially_correct": 0.5,
                "insufficient_evidence": 0.25, "wrong": 0.0},
    "insufficient_evidence": {"correct": 0.3, "partially_correct": 0.3,
                              "insufficient_evidence": 1.0, "wrong": 0.0},
}


def correctness_credit(expected, actual, rubric=None):
    """Credit the verdict against what the case SHOULD have produced.

    Scoring against a fixed "correct" target would mark a ticket-only case wrong
    for correctly declining to conclude, and reward it for guessing.
    """
    matrix = ((rubric or {}).get("gate", {}).get("credit")) or _DEFAULT_CREDIT
    row = matrix.get(expected or "correct")
    if not isinstance(row, dict):
        row = _DEFAULT_CREDIT.get(expected or "correct", _DEFAULT_CREDIT["correct"])
    return float(row.get(actual, 0.0))

RCA_ANALYST_SYSTEM = (
    "You diagnose why a triage skill produces weak or wrong RCAs. Given the "
    "checks that failed and the conclusions that missed the documented root "
    "cause, find the single root cause that explains the most failures, then "
    "pick one mutation_strategy from: add_evidence_rule, add_citation_rule, "
    "add_causal_rule, add_falsification_rule, add_template_section, "
    "add_worked_example, restructure.\n\n"
    "Citing a log link or code line that was never attached is as serious as a "
    "wrong conclusion: the reader copies it into a fix.\n\n"
    "A wrong conclusion outranks a missing checkbox: if the skill reaches the "
    "wrong root cause, fix the reasoning, not the formatting. Prefer a rule "
    "that generalizes across cases over one that memorizes a single incident. "
    "Return valid JSON only."
)


class RcaOptimizer(TriageOptimizer):
    """`context` expects {"rubric": <parsed rca-rubric.json>, "profile": str}."""

    async def _score(self, skill_md, scenarios, evals, context) -> dict:
        rubric = context["rubric"]
        profile = context.get("profile", rubric.get("default_profile", "balanced"))
        runs = context.get("judge_runs", 1)
        results = await asyncio.gather(*[
            self._score_one(skill_md, c, rubric, profile, runs) for c in scenarios
        ])

        dim_totals = {d["id"]: {"passed": 0, "total": 0} for d in rubric["dimensions"]}
        failures, scored, correctness_points = [], 0.0, 0.0
        overconfident = []
        grounding_scores, fabricated_cases = [], []

        for case, rca, detail in results:
            for d in detail["per_dimension"]:
                dim_totals[d["dimension"]]["passed"] += d["passed"]
                dim_totals[d["dimension"]]["total"] += d["total"]
            expected = case.get("expected_correctness", "correct")
            verdict = detail.get("correctness", "wrong")
            credit = correctness_credit(expected, verdict, rubric)
            correctness_points += credit
            g = detail.get("grounding") or {}
            if g.get("score") is not None:
                grounding_scores.append(g["score"])
            if g.get("hard_fail"):
                fabricated_cases.append({"case_id": case["id"], "checks": g["fabricated"]})
            scored += detail["quality"]

            # Concluding anything on a case that should have declined is the
            # failure mode worth naming on its own, not just docking points for.
            if expected == "insufficient_evidence" and verdict != "insufficient_evidence":
                overconfident.append({"case_id": case["id"], "concluded": verdict})

            grounding_failed = [
                {"id": c["id"], "question": c["question"], "detail": c["detail"],
                 "hard_fail": c.get("hard_fail", False)}
                for c in g.get("checks", []) if c["passed"] is False
            ]
            if credit < 1.0 or detail["quality"] < 100 or grounding_failed:
                failures.append({
                    "case_id": case["id"],
                    "vendor": case.get("vendor"),
                    "expected_correctness": expected,
                    "correctness": verdict,
                    "credit": credit,
                    "correctness_reason": detail.get("correctness_reason", ""),
                    "true_root_cause": (case.get("true_root_cause") or "")[:400],
                    "quality": detail["quality"],
                    "failed_checks": [
                        {"id": c["id"], "question": c["question"]}
                        for c in detail["checks"]
                        if c["passed"] is not True and c["passed"] != "na"
                    ],
                    "grounding": g.get("score"),
                    "grounding_failed": grounding_failed,
                    "rca_excerpt": (rca or "")[:700],
                })

        n = len(scenarios) or 1
        correctness_pct = round(100 * correctness_points / n, 1)
        quality_pct = round(scored / n, 1)
        objective = round(
            CORRECTNESS_WEIGHT * correctness_pct
            + (1 - CORRECTNESS_WEIGHT) * quality_pct, 1
        )

        return {
            # The base loop hill-climbs on pass_rate, so the blended objective
            # goes here; the components stay visible alongside it.
            "pass_rate": objective,
            "correctness_pct": correctness_pct,
            "quality_pct": quality_pct,
            "passed": sum(
                1 for c, _, d in results
                if d.get("correctness") == c.get("expected_correctness", "correct")
            ),
            "total": len(scenarios),
            "overconfident": overconfident,
            # Third score: reported, and guarded in _improves, never blended in.
            "grounding_pct": (round(sum(grounding_scores) / len(grounding_scores), 1)
                              if grounding_scores else None),
            "fabricated": fabricated_cases,
            "per_eval": [
                {"eval_id": k, "name": k, **v,
                 "pass_rate": round(100 * v["passed"] / max(v["total"], 1), 1)}
                for k, v in dim_totals.items()
            ],
            "failures": failures,
            "confusion": [],
        }

    @staticmethod
    def _fabrications(result: dict) -> set:
        return {(f["case_id"], check) for f in result.get("fabricated") or []
                for check in (f.get("checks") or ["?"])}

    def _improves(self, candidate: dict, best: dict) -> bool:
        """Grounding is a constraint, not a term in the objective.

        - Any fabrication the best did not have vetoes the edit, even if it fixes
          a different one: swapping case A's invented line for case B's is not progress.
        - Lower grounding vetoes the edit.
        - Otherwise a higher objective is kept, as in the base loop, and so is an
          equal objective that strictly removes fabrications. Without that, the
          analyst's top-priority fix could never survive unless it also happened to
          raise correctness or quality.
        """
        cand_f, best_f = self._fabrications(candidate), self._fabrications(best)
        if cand_f - best_f:
            return False
        cg, bg = candidate.get("grounding_pct"), best.get("grounding_pct")
        if cg is not None and bg is not None and cg < bg:
            return False
        if super()._improves(candidate, best):
            return True
        return candidate["pass_rate"] == best["pass_rate"] and cand_f < best_f

    def _converged(self, best: dict) -> bool:
        # A perfect objective with an invented citation still has work to do.
        return super()._converged(best) and not best.get("fabricated")

    def _extra_results(self, best: dict) -> dict:
        return {"grounding_pct": best.get("grounding_pct"),
                "fabricated": best.get("fabricated") or []}

    async def _score_one(self, skill_md, case, rubric, profile, runs):
        bundle = case.get("evidence")
        ticket = case.get("ticket")
        if bundle:
            source = (f"# Evidence bundle ({case.get('vendor', 'unknown')} / "
                      f"{case.get('environment', 'non-prod')})\n{render_evidence(bundle)}")
        else:
            # No telemetry: the skill should reach insufficient_evidence. Saying so
            # here would hand it the answer, so the prompt stays neutral.
            source = (f"# Ticket ({case.get('environment', 'non-prod')})\n"
                      f"{ticket or '(no telemetry and no ticket supplied)'}")

        # The intake stands in for the answers a live user would give. Without it
        # the user_input_handling checks could never pass, and the sycophancy
        # cases would measure nothing.
        intake = case.get("intake")
        intake_block = ""
        if intake:
            intake_block = (
                "\n\n# Intake (the answers the user gave)\n"
                + "\n".join(
                    f"- **{k.replace('_', ' ')}:** "
                    f"{', '.join(v) if isinstance(v, list) else v}"
                    for k, v in intake.items() if v
                )
            )

        rca = await self._ask(
            "You are an RCA execution agent. Follow the supplied skill exactly. "
            "Use only facts present in the material given — never invent a log line, "
            "service, identifier, or number. Output the document only, no preamble.",
            f"# Skill\n{skill_md}\n\n{source}{intake_block}\n\n"
            f"Produce the output the skill calls for.",
            temperature=0.0,
            role="executor.rca",
        )

        # Same scorer the CLI uses, so an optimizer gain reproduces under
        # scripts/score_rca.py instead of being an artifact of a second code path.
        detail = await score_rca_doc(self, rca, bundle, rubric, profile, runs,
                                     case.get("true_root_cause"))
        return case, rca, detail

    async def _analyze(self, skill_md, failures, mutation_log) -> dict:
        if not failures:
            return {"diagnosis": "All cases correct and complete",
                    "mutation_strategy": "restructure",
                    "target_section": "N/A", "suggested_change": "none"}

        overconfident = [f for f in failures
                         if f.get("expected_correctness") == "insufficient_evidence"
                         and f.get("correctness") != "insufficient_evidence"]
        wrong = [f for f in failures
                 if f.get("credit", 0) == 0.0 and f not in overconfident]
        # Which checks count as invention comes from the rubric (grounding.hard_fail),
        # carried on each failed check, not from a list copied here.
        invented = [
            {"case_id": f["case_id"],
             "invented": [g for g in f.get("grounding_failed", []) if g.get("hard_fail")]}
            for f in failures
            if any(g.get("hard_fail") for g in f.get("grounding_failed", []))
        ]
        tried = [
            f"- [{m['strategy_type']}] {m['description']} "
            f"({m['score_before']} -> {m['score_after']}, "
            f"{'kept' if m['kept'] else 'DISCARDED'})"
            for m in mutation_log[-6:]
        ]
        # Priority order: concluding without evidence, then concluding wrongly,
        # then everything else. Formatting gaps are last.
        priority = ""
        if overconfident:
            priority += (
                f"\n\n# HIGHEST PRIORITY — concluded without evidence\n"
                f"These cases had no telemetry and should have returned "
                f"insufficient_evidence with an evidence request. The skill "
                f"produced a conclusion instead. Fix the guard that decides "
                f"whether there is enough evidence to conclude at all.\n"
                f"{json.dumps(overconfident[:3], indent=2)}"
            )
        if invented:
            priority += (
                f"\n\n# HIGH PRIORITY — cited evidence that was never attached\n"
                f"These RCAs cite a log link, a code line, or a verbatim quote that is "
                f"not in the attached links and code. Make the skill cite only what "
                f"it was given, quote code verbatim, and say so when the code it "
                f"needs is not attached.\n"
                f"{json.dumps(invented[:3], indent=2)}"
            )
        if wrong:
            priority += (
                f"\n\n# Wrong conclusions — fix these before any formatting gap\n"
                f"{json.dumps(wrong[:3], indent=2)}"
            )
        return await self._ask_json(
            RCA_ANALYST_SYSTEM,
            (
                f"Diagnose these RCA failures and propose ONE generalizing fix.\n\n"
                f"# Current skill\n{skill_md}\n\n"
                f"# Failing cases\n{json.dumps(failures[:4], indent=2)}"
                f"{priority}"
                + (f"\n\n# Already attempted (do not repeat a discarded one)\n"
                   + "\n".join(tried) if tried else "")
                + "\n\nReturn JSON: {\"diagnosis\": \"the one root cause\", "
                  "\"mutation_strategy\": \"add_evidence_rule|add_citation_rule|"
                  "add_causal_rule|add_falsification_rule|add_template_section|"
                  "add_worked_example|restructure\", \"target_section\": \"heading to edit\", "
                  "\"suggested_change\": \"the specific edit\"}"
            ),
            fallback={"diagnosis": "Unable to diagnose",
                      "mutation_strategy": "add_causal_rule",
                      "target_section": "Workflow",
                      "suggested_change": "require an explicit mechanism in the causal chain"},
            role="analyst",
        )
