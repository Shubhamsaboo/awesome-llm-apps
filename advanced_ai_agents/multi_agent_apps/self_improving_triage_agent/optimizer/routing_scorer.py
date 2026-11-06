"""Routing scorer: did each issue reach the team that owns it?

`team_correct` is decided in code by exact match; any other eval is judged by
the model. The objective is the share of scenarios that pass every eval.
"""

import asyncio
import json

import telemetry
from skill_optimizer import BaseScorer, SkillOptimizer, is_parse_error

MUTATION_STRATEGIES = (
    "add_routing_rule",
    "add_team_definition",
    "add_disambiguation_example",
    "add_severity_rule",
    "restructure",
)

EXECUTOR_SYSTEM = (
    "You are a triage execution agent with two modes.\n\n"
    "ROUTE MODE: given a skill's instructions and an issue, produce the routing "
    "decision that skill would produce. Follow the instructions exactly — do not "
    "apply knowledge the skill does not contain. No meta-commentary.\n\n"
    "SCORE MODE: given a routing decision and criteria, score it. A team is "
    "correct only on an exact match.\n\n"
    "Return valid JSON only in both modes."
)

ANALYST_SYSTEM = (
    "You diagnose why a triage skill mis-routes issues. Given failed cases, find "
    "the single root cause that explains the most failures, then pick one "
    f"mutation_strategy from: {', '.join(MUTATION_STRATEGIES)}.\n\n"
    "Prefer a rule that generalizes over one that memorizes a single case. "
    "Return valid JSON only."
)


class RoutingScorer(BaseScorer):
    kind = "routing"
    objective_label = "routing accuracy %"

    def __init__(self, teams: list, evals: list):
        self.teams = list(teams)
        self.evals = list(evals)

    def mutation_context(self) -> str:
        return f"# Teams\n{json.dumps(self.teams)}"

    async def score(self, client: SkillOptimizer, skill_md: str, cases: list) -> dict:
        results = await asyncio.gather(*[
            self._score_one(client, skill_md, sc) for sc in cases
        ])

        per_eval = {e["id"]: {"name": e.get("name", str(e["id"])), "passed": 0, "total": 0}
                    for e in self.evals}
        failures, confusion = [], []
        passed_scenarios = parse_errors = 0

        for sc, decision, checks, errors in results:
            parse_errors += errors
            all_passed = True
            for c in checks:
                eid = c.get("eval_id")
                ok = bool(c.get("passed"))
                if eid in per_eval:
                    per_eval[eid]["total"] += 1
                    per_eval[eid]["passed"] += int(ok)
                if not ok:
                    all_passed = False
            if all_passed and checks:
                passed_scenarios += 1
            else:
                failures.append({
                    "scenario_id": sc["id"],
                    "name": sc.get("name", ""),
                    "input": sc["input"],
                    "expected_team": sc.get("expected_team"),
                    "predicted_team": decision.get("team"),
                    "expected_severity": sc.get("expected_severity"),
                    "predicted_severity": decision.get("severity"),
                    "agent_reasoning": decision.get("reasoning", ""),
                    "failed_checks": [c for c in checks if not c.get("passed")],
                    "parse_errors": errors,
                })
            if decision.get("team") != sc.get("expected_team"):
                confusion.append({
                    "expected": sc.get("expected_team"),
                    "predicted": decision.get("team"),
                    "scenario": sc.get("name", sc["id"]),
                })

        total = len(cases) or 1
        return {
            "pass_rate": round(100 * passed_scenarios / total, 1),
            "passed": passed_scenarios,
            "total": len(cases),
            "per_eval": [
                {"eval_id": k, **v,
                 "pass_rate": round(100 * v["passed"] / max(v["total"], 1), 1)}
                for k, v in per_eval.items()
            ],
            "failures": failures,
            "confusion": confusion,
            "parse_errors": parse_errors,
        }

    async def _score_one(self, client, skill_md, sc):
        decision = await client._ask_json(
            EXECUTOR_SYSTEM,
            (
                f"ROUTE MODE.\n\n"
                f"# Skill\n{skill_md}\n\n"
                f"# Allowed teams (pick exactly one)\n{json.dumps(self.teams)}\n\n"
                f"# Issue\nEnvironment: {sc.get('environment', 'non-prod')}\n"
                f"Source: {sc.get('source', 'unknown')}\n\n{sc['input']}\n\n"
                f'Return JSON: {{"team": "...", "severity": "P2", '
                f'"reasoning": "which signal drove it", "confidence": 0.0}}'
            ),
            fallback={"team": "unknown", "severity": "unknown",
                      "reasoning": "executor returned unparseable output",
                      "confidence": 0.0},
            temperature=0.0,
            role="executor.route",
        )
        errors = int(is_parse_error(decision))

        # team_correct is decided in code, not by the judge — a string match is
        # not a judgment call, and letting the judge make it adds variance.
        deterministic, to_judge = [], []
        for e in self.evals:
            if e.get("name") == "team_correct":
                ok = decision.get("team") == sc.get("expected_team")
                deterministic.append({
                    "eval_id": e["id"], "passed": ok,
                    "reason": f"predicted {decision.get('team')!r}, "
                              f"expected {sc.get('expected_team')!r}",
                })
            else:
                to_judge.append(e)

        judged = []
        if to_judge:
            scoring = await client._ask_json(
                EXECUTOR_SYSTEM,
                (
                    f"SCORE MODE.\n\n"
                    f"Issue: {sc['input']}\n"
                    f"Environment: {sc.get('environment', 'non-prod')}\n"
                    f"Expected severity: {sc.get('expected_severity')}\n\n"
                    f"Decision: {json.dumps({k: v for k, v in decision.items() if not k.startswith('_')})}\n\n"
                    f"Criteria:\n{json.dumps(to_judge, indent=2)}\n\n"
                    f'Return JSON: {{"results": [{{"eval_id": 1, "passed": true, '
                    f'"reason": "..."}}]}}'
                ),
                fallback={"results": [{"eval_id": e["id"], "passed": False,
                                       "reason": "judge failed to parse"}
                                      for e in to_judge]},
                temperature=0.0,
                role="executor.score",
            )
            errors += int(is_parse_error(scoring))
            judged = scoring.get("results", []) if isinstance(scoring, dict) else []

        return sc, decision, deterministic + judged, errors

    async def diagnose(self, client, skill_md, failures, mutation_log) -> dict:
        if not failures:
            return {"diagnosis": "All scenarios passed", "mutation_strategy": "restructure",
                    "target_section": "N/A", "suggested_change": "none"}
        return await client._ask_json(
            ANALYST_SYSTEM,
            (
                f"Diagnose these mis-routes and propose ONE generalizing fix.\n\n"
                f"# Current skill\n{skill_md}\n\n"
                f"# Failed cases\n{json.dumps(failures[:6], indent=2)}"
                f"{self.tried_block(mutation_log, unit='%')}\n\n"
                f'Return JSON: {{"diagnosis": "the one root cause", '
                f'"mutation_strategy": "{"|".join(MUTATION_STRATEGIES)}", '
                f'"target_section": "heading to edit", '
                f'"suggested_change": "the specific edit"}}'
            ),
            fallback={"diagnosis": "Unable to diagnose",
                      "mutation_strategy": "add_routing_rule",
                      "target_section": "Workflow",
                      "suggested_change": "clarify routing precedence"},
            role="analyst",
        )


async def generate_scenarios(client: SkillOptimizer, skill_md: str, teams: list) -> dict:
    """Generate routing scenarios + evals when there is no golden set yet.

    Prefer a hand-labeled golden set. Self-generated labels measure the model's
    opinion of correct routing, not your org's.
    """
    with telemetry.span(
        "optimizer.generate",
        **{"triage.model": client.model, "triage.backend": client.backend,
           "triage.teams": len(teams)},
    ):
        return await client._ask_json(
            "You generate test scenarios and eval criteria for a triage routing "
            "agent. Return valid JSON only.",
            (
                f"Generate routing test scenarios for this skill.\n\n"
                f"# SKILL.md\n{skill_md}\n\n"
                f"# Teams (the only allowed labels)\n{json.dumps(teams)}\n\n"
                f"Produce 6-8 scenarios as realistic Jira tickets or Teams messages "
                f"about NON-PROD (dev/staging/CI) issues. Include at least two pairs "
                f"that share a surface symptom but belong to different teams.\n\n"
                f"Also produce 2-3 binary evals.\n\n"
                f"Return JSON:\n"
                f'{{"scenarios": [{{"id": 1, "name": "...", "source": "jira|teams", '
                f'"environment": "staging", "input": "the ticket or message text", '
                f'"expected_team": "one of the teams", "expected_severity": "P2"}}], '
                f'"evals": [{{"id": 1, "name": "...", "criterion": "...", '
                f'"question": "...", "pass_condition": "...", "fail_condition": "..."}}]}}'
            ),
            fallback={"scenarios": [], "evals": []},
            role="generate",
        )
