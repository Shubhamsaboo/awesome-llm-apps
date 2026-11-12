"""Multi-Agent Skill Optimizer using Google ADK.

3 ADK agents work together to improve agent skills:
  Executor: runs the skill against test scenarios, scores outputs, analyzes skills
  Analyst: diagnoses why evals failed, picks a mutation strategy
  Mutator: makes one targeted fix per round
"""

import inspect
import json
import math
import os
import random
import re
from typing import Any, Callable, List, Optional, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


# The Gemini model the agents run on when a request names none. Change it
# without editing code: set GEMINI_MODEL on the server, or pick a model in
# the UI, which sends it with each request (see app.py).
DEFAULT_MODEL = "gemini-3.8-flash"

PARSE_ERROR = "_parse_error"

_FENCED_JSON_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def _reject_invalid_constant(value: str):
    raise ValueError(f"Invalid JSON constant: {value}")


def parse_json(text: str) -> Any:
    """Parse JSON directly, from fenced code blocks, or via raw_decode."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Empty or non-string JSON input")

    try:
        return json.loads(text, parse_constant=_reject_invalid_constant)
    except ValueError:
        pass

    for match in _FENCED_JSON_RE.finditer(text):
        block = match.group(1).strip()
        if not block:
            continue
        try:
            return json.loads(block, parse_constant=_reject_invalid_constant)
        except ValueError:
            pass

    decoder = json.JSONDecoder(parse_constant=_reject_invalid_constant)
    starts = [i for i, ch in enumerate(text) if ch in "{["]
    for idx in starts:
        try:
            result, _ = decoder.raw_decode(text, idx)
            return result
        except ValueError:
            continue

    raise ValueError(f"Could not parse JSON from text: {text[:200]!r}")


def is_parse_error(value: Any) -> bool:
    """Return True when a parsed fallback dict carries the parse-error sentinel."""
    return isinstance(value, dict) and value.get(PARSE_ERROR) is True


def _is_valid_eval_id(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, str))


def split_holdout(scenarios: list, holdout_fraction: float, seed: int = 0) -> tuple:
    """Deterministically split scenarios into (train, holdout) preserving order."""
    if (
        not math.isfinite(holdout_fraction)
        or not (0.0 <= holdout_fraction < 1.0)
    ):
        raise ValueError("holdout_fraction must be in [0.0, 1.0)")
    if holdout_fraction == 0 or len(scenarios) < 2:
        return (list(scenarios), [])
    n = min(len(scenarios) - 1, max(1, round(len(scenarios) * holdout_fraction)))
    rng = random.Random(seed)
    holdout_indices = set(rng.sample(range(len(scenarios)), n))
    train = [s for i, s in enumerate(scenarios) if i not in holdout_indices]
    holdout = [s for i, s in enumerate(scenarios) if i in holdout_indices]
    return (train, holdout)


def _normalize_score_result(result: dict) -> dict:
    """Ensure every scorer dict exposes standard keys while preserving extras."""
    if not isinstance(result, dict):
        raise TypeError(f"Scorer must return a dict, got {type(result).__name__}")

    has_pass_rate = result.get("pass_rate") is not None
    has_passed = result.get("passed") is not None
    has_total = result.get("total") is not None

    details = list(result["details"]) if isinstance(result.get("details"), list) else []
    if isinstance(result.get("failures"), list):
        failures = list(result["failures"])
    else:
        failures = [d for d in details if isinstance(d, dict) and not d.get("passed")]

    if has_passed and not has_pass_rate and not has_total and not details:
        raise ValueError("total is required when passed is provided without pass_rate")

    if has_total:
        total = int(result["total"])
    elif details:
        total = len(details)
    else:
        total = 0
    if total < 0:
        raise ValueError("total must be >= 0")

    if has_pass_rate:
        pass_rate = float(result["pass_rate"])
        if not math.isfinite(pass_rate) or not (0.0 <= pass_rate <= 100.0):
            raise ValueError("pass_rate must be between 0 and 100")
    if has_passed:
        passed = int(result["passed"])
    elif details:
        passed = sum(1 for d in details if isinstance(d, dict) and d.get("passed") is True)
    elif has_pass_rate and total > 0:
        passed = round(pass_rate * total / 100.0)
    else:
        passed = 0

    if has_passed and has_total and (passed < 0 or passed > total):
        raise ValueError("passed must be between 0 and total")

    if not has_pass_rate:
        pass_rate = round(100 * passed / max(total, 1), 1)

    per_eval = list(result["per_eval"]) if isinstance(result.get("per_eval"), list) else []
    parse_errors = int(result["parse_errors"]) if result.get("parse_errors") is not None else 0

    return {
        **result,
        "pass_rate": pass_rate,
        "passed": passed,
        "total": total,
        "per_eval": per_eval,
        "details": details,
        "failures": failures,
        "parse_errors": parse_errors,
    }


# -- Pluggable Scorers -------------------------------------------------------


@runtime_checkable
class Scorer(Protocol):
    kind: str

    async def score(
        self,
        optimizer: "SkillOptimizer",
        skill_md: str,
        scenarios: list,
        evals: list,
    ) -> dict: ...

    async def diagnose(
        self,
        optimizer: "SkillOptimizer",
        skill_md: str,
        scenarios: list,
        evals: list,
        result: dict,
        mutation_log: list,
    ) -> dict: ...

    def mutation_context(self) -> str: ...

    def improves(self, candidate: dict, best: dict, min_gain: float = 0.0) -> bool: ...

    def converged(self, best: dict) -> bool: ...

    def extra_results(self, best: dict) -> dict: ...


class BaseScorer:
    kind = "skill"

    async def score(
        self,
        optimizer: "SkillOptimizer",
        skill_md: str,
        scenarios: list,
        evals: list,
    ) -> dict:
        raise NotImplementedError

    async def diagnose(
        self,
        optimizer: "SkillOptimizer",
        skill_md: str,
        scenarios: list,
        evals: list,
        result: dict,
        mutation_log: list,
    ) -> dict:
        return await optimizer._analyze_failures(
            skill_md,
            scenarios,
            evals,
            result.get("details") or result.get("failures") or [],
            mutation_log=mutation_log,
            result=result,
        )

    def mutation_context(self) -> str:
        return ""

    def improves(self, candidate: dict, best: dict, min_gain: float = 0.0) -> bool:
        gain = round(candidate["pass_rate"] - best["pass_rate"], 9)
        return gain > 0 and gain >= min_gain

    def converged(self, best: dict) -> bool:
        return (
            best.get("pass_rate", 0.0) >= 100.0
            and best.get("parse_errors", 0) == 0
        )

    def extra_results(self, best: dict) -> dict:
        return {}

    @staticmethod
    def tried_block(mutation_log: list) -> str:
        if not mutation_log:
            return ""
        relevant = [m for m in mutation_log if m.get("outcome") != "skipped"][-6:]
        if not relevant:
            return ""
        lines = ["Previously tried mutations (avoid repeating discarded ideas):"]
        for m in relevant:
            outcome = m.get("outcome") or ("kept" if m.get("kept") else "discarded")
            strategy = m.get("strategy_type", "unknown")
            desc = m.get("description") or m.get("diagnosis") or ""
            before = m.get("score_before", "?")
            after = m.get("score_after", "?")
            lines.append(
                f"- Round {m.get('round', '?')} [{outcome}] ({strategy}, {before}% -> {after}%): {desc}"
            )
        return "\n".join(lines)


class ExecutorScorer(BaseScorer):
    kind = "skill"

    async def score(
        self,
        optimizer: "SkillOptimizer",
        skill_md: str,
        scenarios: list,
        evals: list,
    ) -> dict:
        evals = evals or []
        all_results = []
        total_passed = 0
        total_checks = 0
        parse_errors = 0
        valid_evals = []
        invalid_eval_ids = False
        for ev in evals:
            if not isinstance(ev, dict) or not _is_valid_eval_id(ev.get("id")):
                invalid_eval_ids = True
                continue
            valid_evals.append(ev)
        per_eval = {e["id"]: {"passed": 0, "total": 0} for e in valid_evals}

        for sc in scenarios:
            output = await optimizer._ask(
                optimizer.executor,
                f"Execute this skill:\n\n{skill_md}\n\nUser request:\n{sc['input']}",
            )
            scoring = await optimizer._ask_json(
                optimizer.executor,
                (
                    f"Evaluate this output against the criteria.\n\n"
                    f"Input: {sc['input']}\n\n"
                    f"Output: {output}\n\n"
                    f"Criteria:\n{json.dumps(evals, indent=2)}\n\n"
                    f"Return JSON: {{\"results\": [{{\"eval_id\": 1, \"passed\": true, \"reason\": \"...\"}}]}}"
                ),
                fallback={"results": []},
            )
            scenario_parse_error = is_parse_error(scoring) or invalid_eval_ids
            raw_results = scoring.get("results") if isinstance(scoring, dict) else None
            if not isinstance(raw_results, list):
                scenario_parse_error = True
                raw_results = []

            by_eval = {}
            for item in raw_results:
                if not isinstance(item, dict) or not isinstance(item.get("passed"), bool):
                    scenario_parse_error = True
                    continue
                eid = item.get("eval_id")
                if _is_valid_eval_id(eid) and eid in per_eval:
                    by_eval[eid] = item
                else:
                    scenario_parse_error = True

            for ev in valid_evals:
                eid = ev["id"]
                entry = by_eval.get(eid)
                if entry is None:
                    scenario_parse_error = True
                    passed = False
                    record = {
                        "eval_id": eid,
                        "passed": False,
                        "reason": "no verdict returned",
                        "scenario_id": sc["id"],
                        "parse_error": True,
                    }
                else:
                    passed = entry.get("passed") is True
                    record = {
                        **entry,
                        "eval_id": eid,
                        "passed": passed,
                        "reason": entry.get("reason", ""),
                        "scenario_id": sc["id"],
                    }
                total_checks += 1
                per_eval[eid]["total"] += 1
                if passed:
                    total_passed += 1
                    per_eval[eid]["passed"] += 1
                all_results.append(record)

            parse_errors += int(scenario_parse_error)

        return {
            "pass_rate": round(100 * total_passed / max(total_checks, 1), 1),
            "passed": total_passed,
            "total": total_checks,
            "per_eval": [
                {
                    "eval_id": k,
                    **v,
                    "pass_rate": round(v["passed"] / max(v["total"], 1) * 100, 1),
                }
                for k, v in per_eval.items()
            ],
            "details": all_results,
            "failures": [r for r in all_results if not r["passed"]],
            "parse_errors": parse_errors,
        }


class CallableScorer(BaseScorer):
    def __init__(self, fn: Callable):
        if not callable(fn):
            raise TypeError(f"Expected a callable scorer, got {type(fn).__name__}")
        self.fn = fn
        if hasattr(fn, "kind"):
            self.kind = fn.kind

    async def score(
        self,
        optimizer: "SkillOptimizer",
        skill_md: str,
        scenarios: list,
        evals: list,
    ) -> dict:
        res = self.fn(skill_md, scenarios, evals)
        if inspect.isawaitable(res):
            res = await res
        return _normalize_score_result(res)


def _coerce_scorer(scorer: Any) -> Scorer:
    if scorer is None:
        return ExecutorScorer()
    if isinstance(scorer, (BaseScorer, Scorer)) and not isinstance(scorer, type):
        return scorer
    if callable(scorer):
        return CallableScorer(scorer)
    raise TypeError(f"Unsupported scorer: {scorer!r}")


# -- Pydantic schemas for structured agent output ----------------------------


class FailureAnalysis(BaseModel):
    diagnosis: str = Field(description="Root cause of failures")
    mutation_strategy: str = Field(
        description="One of: add_example, add_constraint, restructure, add_edge_case"
    )
    target_section: str = Field(description="Which part of the skill to change")
    suggested_change: str = Field(description="What specific change to make")


class SkillMutation(BaseModel):
    description: str = Field(description="Short description of the change made")
    reasoning: str = Field(description="Why this change should help")
    new_skill_md: str = Field(description="The full updated SKILL.md content")


# -- Optimizer ---------------------------------------------------------------


class SkillOptimizer:
    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        scorer: Optional["Scorer"] = None,
    ):
        # ADK agents authenticate via this env var
        os.environ["GOOGLE_API_KEY"] = api_key
        self.model = model
        self.scorer = _coerce_scorer(scorer)
        self._session_service = InMemorySessionService()
        self._call_id = 0

        self.executor = Agent(
            name="executor",
            model=model,
            instruction=(
                "You are a versatile skill execution agent. You have three modes:\n\n"
                "1. EXECUTE MODE: Given a skill's instructions and a user request, "
                "produce the output that skill would generate. Follow the instructions "
                "exactly. No meta-commentary.\n\n"
                "2. ANALYZE MODE: Given a skill definition, generate test scenarios "
                "and evaluation criteria. Return valid JSON.\n\n"
                "3. SCORE MODE: Given an output and evaluation criteria, score the "
                "output against each criterion. Return valid JSON."
            ),
        )
        self.analyst = Agent(
            name="analyst",
            model=model,
            instruction=(
                "You diagnose why agent skill evaluations fail. "
                "Given failed eval results, identify the root cause and suggest "
                "a specific fix. Pick one mutation_strategy from: "
                "add_example, add_constraint, restructure, or add_edge_case."
            ),
            output_schema=FailureAnalysis,
        )
        self.mutator = Agent(
            name="mutator",
            model=model,
            instruction=(
                "You edit agent skill files. Given a SKILL.md and a diagnosis, "
                "make exactly ONE targeted change. Keep the YAML frontmatter and "
                "overall structure intact. Return the complete updated SKILL.md."
            ),
            output_schema=SkillMutation,
        )

    # -- Agent runner helpers ------------------------------------------------

    async def _ask(self, agent: Agent, prompt: str) -> str:
        """Run an ADK agent with a prompt, return text response."""
        self._call_id += 1
        uid = f"u{self._call_id}"
        runner = Runner(
            agent=agent, app_name="skill_opt", session_service=self._session_service
        )
        session = await self._session_service.create_session(
            app_name="skill_opt", user_id=uid
        )
        text = ""
        async for event in runner.run_async(
            user_id=uid,
            session_id=session.id,
            new_message=types.Content(parts=[types.Part(text=prompt)]),
        ):
            if hasattr(event, "content") and event.content:
                for part in event.content.parts or []:
                    if hasattr(part, "text") and part.text:
                        text += part.text
        return text

    async def _ask_json(self, agent: Agent, prompt: str, fallback=None):
        """Run an ADK agent and parse the JSON response."""
        text = await self._ask(agent, prompt)
        try:
            parsed = parse_json(text)
        except ValueError:
            if fallback is None:
                raise
            if isinstance(fallback, dict):
                return {**fallback, PARSE_ERROR: True}
            return fallback
        if isinstance(fallback, dict) and not isinstance(parsed, dict):
            return {**fallback, PARSE_ERROR: True}
        return parsed

    # -- Public API -----------------------------------------------------------

    async def analyze_skill(self, skill_files: dict) -> dict:
        """Generate test scenarios and eval criteria from skill files."""
        skill_md = next(
            (v for k, v in skill_files.items() if k.endswith("SKILL.md")), ""
        )
        refs = {k: v for k, v in skill_files.items() if "references/" in k}
        ref_text = ""
        if refs:
            ref_text = "\n\nReference files:\n" + "\n---\n".join(
                f"## {k}\n{v}" for k, v in refs.items()
            )

        prompt = (
            f"Analyze this agent skill and generate test scenarios "
            f"with evaluation criteria.\n\n"
            f"# SKILL.md\n{skill_md}\n{ref_text}\n\n"
            f"Generate:\n"
            f"1. 3-4 diverse test scenarios (realistic user inputs)\n"
            f"2. 4-6 binary yes/no evaluation criteria\n\n"
            f"Return JSON:\n"
            f'{{"scenarios": [{{"id": 1, "name": "short name", "description": "short name", '
            f'"input": "the user request to test"}}], '
            f'"evals": [{{"id": 1, "name": "what to check", "criterion": "what to check", '
            f'"question": "yes/no question about the output", '
            f'"pass_condition": "what yes looks like", "fail_condition": "what no looks like"}}]}}'
        )
        return await self._ask_json(self.executor, prompt)

    async def score(
        self,
        skill_md: str,
        scenarios: list,
        evals: Optional[list] = None,
        scorer: Optional[Scorer] = None,
    ) -> dict:
        """Score a skill against scenarios using the active or supplied scorer."""
        active_scorer = _coerce_scorer(scorer) if scorer is not None else self.scorer
        evals_list = list(evals) if evals is not None else []
        raw = await active_scorer.score(self, skill_md, scenarios, evals_list)
        return _normalize_score_result(raw)

    async def optimize(
        self,
        skill_files: dict,
        scenarios: list,
        evals: Optional[list] = None,
        max_rounds: int = 5,
        callback: Optional[Callable] = None,
        min_gain: float = 0.0,
        holdout: Optional[list] = None,
        holdout_fraction: float = 0.0,
        scorer: Optional[Scorer] = None,
    ) -> dict:
        """Run the optimization loop with ADK agents and pluggable scorer."""
        if not math.isfinite(min_gain) or min_gain < 0:
            raise ValueError("min_gain must be >= 0")
        if holdout is not None and holdout_fraction > 0:
            raise ValueError("Cannot specify both holdout and holdout_fraction > 0")
        if (
            not math.isfinite(holdout_fraction)
            or not (0.0 <= holdout_fraction < 1.0)
        ):
            raise ValueError("holdout_fraction must be in [0.0, 1.0)")

        async def emit(event):
            if callback:
                res = callback(event)
                if inspect.isawaitable(res):
                    await res

        active_scorer = _coerce_scorer(scorer) if scorer is not None else self.scorer
        evals_list = list(evals) if evals is not None else []

        if holdout is not None:
            train_scenarios = list(scenarios)
            holdout_scenarios = list(holdout)
        elif holdout_fraction > 0:
            train_scenarios, holdout_scenarios = split_holdout(
                scenarios, holdout_fraction
            )
        else:
            train_scenarios = list(scenarios)
            holdout_scenarios = []

        skill_md = next(
            (v for k, v in skill_files.items() if k.endswith("SKILL.md")), ""
        )
        current_md = skill_md
        score_history = []
        mutation_log = []

        async def record_round(
            round_no: int,
            *,
            analysis: Optional[dict],
            description: str,
            kept: bool,
            outcome: str,
            parse_errors: int,
            score_after: float,
            event_score: float,
            event_per_eval: list,
        ) -> None:
            mutation_log.append({
                "round": round_no,
                "strategy_type": analysis.get("mutation_strategy", "unknown")
                if isinstance(analysis, dict)
                else "unknown",
                "diagnosis": analysis.get("diagnosis", "")
                if isinstance(analysis, dict)
                else "",
                "description": description,
                "score_before": baseline_pct,
                "score_after": score_after,
                "kept": kept,
                "outcome": outcome,
                "parse_errors": parse_errors,
            })
            score_history.append(score_after if kept else baseline_pct)
            await emit({
                "type": "experiment_result",
                "data": {
                    "round": round_no,
                    "score": event_score,
                    "kept": kept,
                    "status": "kept" if kept else outcome,
                    "outcome": outcome,
                    "parse_errors": parse_errors,
                    "description": description,
                    "strategy": analysis.get("mutation_strategy", "")
                    if isinstance(analysis, dict)
                    else "",
                    "per_eval": event_per_eval,
                },
            })

        # -- Baseline ---------------------------------------------------------
        baseline = await self.score(
            current_md, train_scenarios, evals_list, scorer=active_scorer
        )
        baseline_pct = baseline["pass_rate"]
        score_history.append(baseline_pct)

        await emit({
            "type": "baseline",
            "data": {
                "score": baseline_pct,
                "passed": baseline["passed"],
                "total": baseline["total"],
                "per_eval": baseline["per_eval"],
                "parse_errors": baseline.get("parse_errors", 0),
            },
        })

        holdout_start = None
        if holdout_scenarios:
            holdout_start = await self.score(
                skill_md, holdout_scenarios, evals_list, scorer=active_scorer
            )

        # -- Rounds -----------------------------------------------------------
        for rnd in range(1, max_rounds + 1):
            if active_scorer.converged(baseline):
                await emit({"type": "converged", "data": {"round": rnd}})
                break

            await emit({"type": "experiment_start", "data": {"round": rnd}})

            baseline_details = (
                baseline.get("details") if isinstance(baseline.get("details"), list) else []
            )
            misses = [d for d in baseline_details if isinstance(d, dict) and not d.get("passed")]
            real_failures = [d for d in misses if not d.get("parse_error")]
            if (
                baseline.get("parse_errors", 0) > 0
                and misses
                and not real_failures
                and not active_scorer.converged(baseline)
            ):
                await record_round(
                    rnd,
                    analysis=None,
                    description="Scoring replies could not be parsed",
                    kept=False,
                    outcome="skipped",
                    parse_errors=baseline.get("parse_errors", 1),
                    score_after=baseline_pct,
                    event_score=baseline_pct,
                    event_per_eval=baseline.get("per_eval", []),
                )
                continue

            # Analyst diagnoses failures
            analysis = await active_scorer.diagnose(
                self,
                current_md,
                train_scenarios,
                evals_list,
                baseline,
                mutation_log,
            )
            if is_parse_error(analysis):
                await record_round(
                    rnd,
                    analysis=analysis if isinstance(analysis, dict) else None,
                    description="Analyst reply could not be parsed",
                    kept=False,
                    outcome="skipped",
                    parse_errors=1,
                    score_after=baseline_pct,
                    event_score=baseline_pct,
                    event_per_eval=baseline["per_eval"],
                )
                continue

            # Mutator applies fix
            mutation = await self._mutate_skill(
                current_md, analysis, context=active_scorer.mutation_context()
            )
            if is_parse_error(mutation):
                await record_round(
                    rnd,
                    analysis=analysis,
                    description="Mutator reply could not be parsed",
                    kept=False,
                    outcome="skipped",
                    parse_errors=1,
                    score_after=baseline_pct,
                    event_score=baseline_pct,
                    event_per_eval=baseline["per_eval"],
                )
                continue

            new_md = (
                mutation.get("new_skill_md", current_md)
                if isinstance(mutation, dict)
                else current_md
            )
            if not isinstance(new_md, str):
                new_md = current_md

            if new_md.strip() == current_md.strip():
                await record_round(
                    rnd,
                    analysis=analysis,
                    description=mutation.get("description", ""),
                    kept=False,
                    outcome="unchanged",
                    parse_errors=0,
                    score_after=baseline_pct,
                    event_score=baseline_pct,
                    event_per_eval=baseline["per_eval"],
                )
                continue

            # Re-score candidate on training scenarios
            result = await self.score(
                new_md, train_scenarios, evals_list, scorer=active_scorer
            )
            new_pct = result["pass_rate"]
            cand_parse_errors = result.get("parse_errors", 0)

            if cand_parse_errors > baseline.get("parse_errors", 0):
                kept = False
                outcome = "inconclusive"
            else:
                kept = bool(active_scorer.improves(result, baseline, min_gain))
                outcome = "kept" if kept else "discarded"

            await record_round(
                rnd,
                analysis=analysis,
                description=mutation.get("description", ""),
                kept=kept,
                outcome=outcome,
                parse_errors=cand_parse_errors,
                score_after=new_pct,
                event_score=new_pct,
                event_per_eval=result["per_eval"],
            )

            if kept:
                current_md = new_md
                baseline = result
                baseline_pct = new_pct

        # -- Holdout ----------------------------------------------------------
        holdout_summary = None
        if holdout_scenarios:
            if current_md == skill_md:
                holdout_end = holdout_start
            else:
                holdout_end = await self.score(
                    current_md, holdout_scenarios, evals_list, scorer=active_scorer
                )
            holdout_summary = {
                "baseline": holdout_start["pass_rate"],
                "final": holdout_end["pass_rate"],
                "total": len(holdout_scenarios),
                "regressed": holdout_end["pass_rate"] < holdout_start["pass_rate"],
                "parse_errors": holdout_end.get("parse_errors", 0),
            }
            await emit({"type": "holdout", "data": holdout_summary})

        # -- Done -------------------------------------------------------------
        final_pct = baseline_pct
        strategy_stats = self._strategy_stats(mutation_log)
        extra = active_scorer.extra_results(baseline) or {}
        summary = {
            "baseline_score": score_history[0],
            "final_score": final_pct,
            "improved_skill_md": current_md,
            "score_history": score_history,
            "mutation_log": mutation_log,
            "strategy_stats": strategy_stats,
            "min_gain": min_gain,
            "parse_errors": baseline.get("parse_errors", 0),
            "holdout": holdout_summary,
            **extra,
        }

        await emit({"type": "complete", "data": dict(summary)})
        return summary

    # -- Internal helpers -----------------------------------------------------

    async def _score_skill(self, skill_md, scenarios, evals):
        """Executor runs all scenarios, then scores outputs."""
        return await ExecutorScorer().score(self, skill_md, scenarios, evals)

    async def _analyze_failures(
        self,
        skill_md,
        scenarios,
        evals,
        details,
        mutation_log: Optional[list] = None,
        result: Optional[dict] = None,
    ):
        """Analyst agent diagnoses the worst failures."""
        result = result or {}
        failed = [
            d
            for d in details
            if isinstance(d, dict) and not d.get("passed") and not d.get("parse_error")
        ]
        if result.get("pass_rate", 0.0) >= 100.0 and result.get("parse_errors", 0) == 0:
            return {
                "diagnosis": "All passed",
                "mutation_strategy": "add_constraint",
                "target_section": "N/A",
                "suggested_change": "none",
            }

        tried = BaseScorer.tried_block(mutation_log or [])
        tried_section = f"\n\n{tried}" if tried else ""
        aggregate = {
            "pass_rate": result.get("pass_rate", 0.0),
            "passed": result.get("passed", 0),
            "total": result.get("total", 0),
            "parse_errors": result.get("parse_errors", 0),
        }
        failed_block = (
            json.dumps(failed[:5], indent=2)
            if failed
            else "No per-check failures were provided by the scorer."
        )

        return await self._ask_json(
            self.analyst,
            (
                f"Diagnose these failures and suggest ONE fix.\n\n"
                f"Skill:\n{skill_md[:2000]}\n\n"
                f"Scenarios (sample):\n{json.dumps((scenarios or [])[:3], indent=2)}\n\n"
                f"Evals:\n{json.dumps(evals or [], indent=2)}\n\n"
                f"Aggregate score summary:\n{json.dumps(aggregate, indent=2)}\n\n"
                f"Failed evals:\n{failed_block}"
                f"{tried_section}"
            ),
            fallback={
                "diagnosis": "Unable to diagnose",
                "mutation_strategy": "add_constraint",
                "target_section": "unknown",
                "suggested_change": "unclear",
            },
        )

    async def _mutate_skill(self, skill_md, analysis, context: str = ""):
        """Mutator agent makes one targeted change."""
        extra = f"\n\n{context}" if context else ""
        return await self._ask_json(
            self.mutator,
            (
                f"Apply this fix to the skill. Make ONE change only.\n\n"
                f"SKILL.md:\n{skill_md}\n\n"
                f"Diagnosis: {analysis.get('diagnosis')}\n"
                f"Strategy: {analysis.get('mutation_strategy')}\n"
                f"Target: {analysis.get('target_section')}\n"
                f"Change: {analysis.get('suggested_change')}"
                f"{extra}"
            ),
            fallback={
                "description": "Failed to parse mutation",
                "reasoning": "",
                "new_skill_md": skill_md,
            },
        )

    @staticmethod
    def _strategy_stats(mutation_log):
        stats = {}
        for m in mutation_log:
            if m.get("outcome") == "skipped":
                continue
            s = m.get("strategy_type", "unknown")
            if s not in stats:
                stats[s] = {"total": 0, "kept": 0}
            stats[s]["total"] += 1
            if m.get("kept"):
                stats[s]["kept"] += 1
        return stats
