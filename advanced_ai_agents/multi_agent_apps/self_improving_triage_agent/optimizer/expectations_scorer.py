"""Expectations scorer: optimize any agent_skills/ skill against its evals.json.

Every skill in this repo ships `agent_skills/evals/<skill>/evals.json` in
Anthropic skill-creator's schema: a prompt, an expected_output, and a list of
binary `expectations`. This scorer runs the skill on each prompt and has a judge
check each expectation, so the same loop, backends and tracing that improve the
triage skill can improve any skill.

Limitation: the executor has no tools. It answers as the skill would, describing
any script it would run, so expectations about real script output are judged on
the described behavior. Confirm a gain with the skill's deterministic tests
before shipping the edited SKILL.md.
"""

import asyncio
import json
import os

import skill_paths
from skill_optimizer import BaseScorer, SkillOptimizer, is_parse_error

MUTATION_STRATEGIES = ("add_example", "add_constraint", "add_edge_case", "restructure")

EXECUTOR_SYSTEM = (
    "You are an agent that has just loaded the skill below. Follow it exactly for "
    "the user's request. You cannot run tools in this session: where the skill "
    "says to run a script or read a file, state precisely what you would run and "
    "with which arguments, then continue as the skill instructs. Output only your "
    "response to the user."
)

JUDGE_SYSTEM = (
    "You check an agent's response against binary expectations. Mark an "
    "expectation passed only if the response, as written, clearly satisfies it. "
    "Return valid JSON only."
)

ANALYST_SYSTEM = (
    "You diagnose why an agent skill fails its expectations. Given the unmet "
    "expectations, find the single root cause that explains the most failures, "
    f"then pick one mutation_strategy from: {', '.join(MUTATION_STRATEGIES)}. "
    "Prefer a rule that generalizes over one that memorizes a single prompt. "
    "Return valid JSON only."
)


def evals_path(skill_dir: str) -> str:
    """Where a skill's evals.json lives by repo convention."""
    name = os.path.basename(os.path.normpath(skill_dir))
    return os.path.join(skill_paths.SKILLS_ROOT, "evals", name, "evals.json")


def load_cases(path: str) -> list:
    """Read skill-creator evals.json into scorer cases."""
    with open(path) as f:
        data = json.load(f)
    cases = []
    for e in data.get("evals", []):
        if not e.get("prompt") or not e.get("expectations"):
            raise ValueError(f"eval {e.get('id')!r} needs a prompt and expectations")
        cases.append({"id": e["id"], "prompt": e["prompt"],
                      "expected_output": e.get("expected_output", ""),
                      "expectations": list(e["expectations"])})
    if not cases:
        raise ValueError(f"{path} has no evals")
    return cases


class ExpectationsScorer(BaseScorer):
    kind = "expectations"
    objective_label = "expectations met %"

    async def score(self, client: SkillOptimizer, skill_md: str, cases: list) -> dict:
        results = await asyncio.gather(*[self._score_one(client, skill_md, c) for c in cases])
        met = total = passed = parse_errors = 0
        per_eval, failures = [], []
        for case, output, verdicts, errors in results:
            parse_errors += errors
            ok = sum(1 for v in verdicts if v["passed"])
            met, total = met + ok, total + len(verdicts)
            passed += int(ok == len(verdicts))
            per_eval.append({"eval_id": case["id"], "name": case["prompt"][:60],
                             "passed": ok, "total": len(verdicts),
                             "pass_rate": round(100 * ok / max(len(verdicts), 1), 1)})
            unmet = [v for v in verdicts if not v["passed"]]
            if unmet:
                failures.append({"case_id": case["id"], "prompt": case["prompt"],
                                 "expected_output": case["expected_output"],
                                 "unmet": unmet, "output_excerpt": output[:900],
                                 "parse_errors": errors})
        return {
            # Expectations, not cases, so partial progress on a case still counts.
            "pass_rate": round(100 * met / max(total, 1), 1),
            "passed": passed,
            "total": len(cases),
            "per_eval": per_eval,
            "failures": failures,
            "parse_errors": parse_errors,
        }

    async def _score_one(self, client, skill_md, case):
        output = await client._ask(
            EXECUTOR_SYSTEM, f"# Skill\n{skill_md}\n\n# User request\n{case['prompt']}",
            temperature=0.0, role="executor.skill")
        expectations = case["expectations"]
        judged = await client._ask_json(
            JUDGE_SYSTEM,
            (
                f"# User request\n{case['prompt']}\n\n# Agent response\n{output}\n\n"
                f"# Expectations\n"
                + "\n".join(f"{i}. {x}" for i, x in enumerate(expectations))
                + '\n\nReturn JSON: {"results": [{"index": 0, "passed": true, '
                  '"reason": "one sentence"}]}'
            ),
            fallback={"results": []},
            temperature=0.0,
            role="judge.expectations",
        )
        by_index = {}
        for r in judged.get("results") or []:
            if isinstance(r, dict) and isinstance(r.get("index"), int):
                by_index[r["index"]] = r
        # A missing verdict is a failure, never a silent pass.
        verdicts = [{"expectation": x,
                     "passed": by_index.get(i, {}).get("passed") is True,
                     "reason": by_index.get(i, {}).get("reason", "no verdict returned")}
                    for i, x in enumerate(expectations)]
        return case, output, verdicts, int(is_parse_error(judged))

    async def diagnose(self, client, skill_md, failures, mutation_log) -> dict:
        if not failures:
            return {"diagnosis": "All expectations met", "mutation_strategy": "restructure",
                    "target_section": "N/A", "suggested_change": "none"}
        return await client._ask_json(
            ANALYST_SYSTEM,
            (
                f"Diagnose these unmet expectations and propose ONE generalizing fix.\n\n"
                f"# Current skill\n{skill_md}\n\n"
                f"# Failing cases\n{json.dumps(failures[:4], indent=2)}"
                f"{self.tried_block(mutation_log, unit='%')}\n\n"
                f'Return JSON: {{"diagnosis": "the one root cause", '
                f'"mutation_strategy": "{"|".join(MUTATION_STRATEGIES)}", '
                f'"target_section": "heading to edit", '
                f'"suggested_change": "the specific edit"}}'
            ),
            fallback={"diagnosis": "Unable to diagnose", "mutation_strategy": "add_constraint",
                      "target_section": "N/A", "suggested_change": "none"},
            role="analyst",
        )
