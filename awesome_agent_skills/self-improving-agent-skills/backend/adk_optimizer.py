"""Multi-Agent Skill Optimizer using Google ADK.

3 ADK agents work together to improve agent skills:
  Executor: runs the skill against test scenarios
  Analyst: diagnoses why evals failed, picks a mutation strategy
  Mutator: makes one targeted fix per round
"""

import json
import re
import uuid
from typing import Callable, Optional

from google.adk import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google import genai
from google.genai import types


class SkillOptimizer:
    def __init__(self, api_key: str, model: str = "gemini-3-flash-preview"):
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self._session_service = InMemorySessionService()
        self._call_id = 0

        self.executor = Agent(
            name="executor",
            model=model,
            instruction=(
                "You execute agent skills faithfully. Given a skill's instructions "
                "and a user request, produce the output that skill would generate. "
                "Follow the instructions exactly. No meta-commentary."
            ),
        )
        self.analyst = Agent(
            name="analyst",
            model=model,
            instruction=(
                "You diagnose why agent skill evaluations fail. "
                "Given failed eval results, identify the root cause and suggest "
                "a specific fix. Return valid JSON with keys: "
                "diagnosis, mutation_strategy (add_example|add_constraint|restructure|add_edge_case), "
                "target_section, suggested_change."
            ),
        )
        self.mutator = Agent(
            name="mutator",
            model=model,
            instruction=(
                "You edit agent skill files. Given a SKILL.md and a diagnosis, "
                "make exactly ONE targeted change. Keep structure and frontmatter intact. "
                "Return valid JSON with keys: description, reasoning, new_skill_md."
            ),
        )

    # -- Agent runner helper --------------------------------------------------

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

    # -- Gemini direct call (for structured JSON) -----------------------------

    async def _gen_json(self, prompt: str):
        """Call Gemini directly for structured JSON output."""
        resp = await self.client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            ),
        )
        return json.loads(resp.text)

    # -- Parse JSON from agent text (agents don't guarantee pure JSON) --------

    def _parse_json(self, text: str, fallback: dict) -> dict:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group(0))
                except json.JSONDecodeError:
                    pass
        return fallback

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

        prompt = f"""Analyze this agent skill and generate test scenarios with evaluation criteria.

# SKILL.md
{skill_md}
{ref_text}

Generate:
1. 3-4 diverse test scenarios (realistic user inputs that test different aspects)
2. 4-6 binary yes/no evaluation criteria

Return JSON:
{{
  "scenarios": [
    {{"id": 1, "name": "short name", "description": "short name", "input": "the user request to test"}}
  ],
  "evals": [
    {{"id": 1, "name": "what to check", "criterion": "what to check", "question": "yes/no question about the output", "pass_condition": "what yes looks like", "fail_condition": "what no looks like"}}
  ]
}}"""
        return await self._gen_json(prompt)

    async def optimize(
        self,
        skill_files: dict,
        scenarios: list,
        evals: list,
        max_rounds: int = 5,
        callback: Optional[Callable] = None,
    ) -> dict:
        """Run the optimization loop with 3 ADK agents."""

        async def emit(event):
            if callback:
                await callback(event)

        skill_md = next(
            (v for k, v in skill_files.items() if k.endswith("SKILL.md")), ""
        )
        current_md = skill_md
        score_history = []
        mutation_log = []

        # -- Baseline ---------------------------------------------------------
        baseline = await self._score_skill(current_md, scenarios, evals)
        baseline_pct = round(100 * baseline["passed"] / max(baseline["total"], 1), 1)
        score_history.append(baseline_pct)

        await emit({
            "type": "baseline",
            "data": {
                "score": baseline_pct,
                "passed": baseline["passed"],
                "total": baseline["total"],
                "per_eval": baseline["per_eval"],
            },
        })

        # -- Rounds -----------------------------------------------------------
        for rnd in range(1, max_rounds + 1):
            await emit({"type": "experiment_start", "data": {"round": rnd}})

            # Analyst diagnoses worst failure
            analysis = await self._analyze_failures(
                current_md, scenarios, evals, baseline["details"]
            )

            # Mutator applies fix
            mutation = await self._mutate_skill(current_md, analysis)
            new_md = mutation.get("new_skill_md", current_md)

            # Re-score
            result = await self._score_skill(new_md, scenarios, evals)
            new_pct = round(100 * result["passed"] / max(result["total"], 1), 1)

            kept = new_pct > baseline_pct
            entry = {
                "round": rnd,
                "strategy_type": analysis.get("mutation_strategy", "unknown"),
                "diagnosis": analysis.get("diagnosis", ""),
                "description": mutation.get("description", ""),
                "score_before": baseline_pct,
                "score_after": new_pct,
                "kept": kept,
            }
            mutation_log.append(entry)

            if kept:
                current_md = new_md
                baseline = result
                baseline_pct = new_pct

            score_history.append(baseline_pct)

            await emit({
                "type": "experiment_result",
                "data": {
                    "round": rnd,
                    "score": new_pct,
                    "kept": kept,
                    "status": "kept" if kept else "discarded",
                    "description": mutation.get("description", ""),
                    "strategy": analysis.get("mutation_strategy", ""),
                    "per_eval": result["per_eval"],
                },
            })

        # -- Done -------------------------------------------------------------
        final_pct = baseline_pct
        await emit({
            "type": "complete",
            "data": {
                "baseline_score": score_history[0],
                "final_score": final_pct,
                "improved_skill_md": current_md,
                "score_history": score_history,
                "mutation_log": mutation_log,
                "strategy_stats": self._strategy_stats(mutation_log),
            },
        })

        return {
            "baseline_score": score_history[0],
            "final_score": final_pct,
            "improved_skill_md": current_md,
            "score_history": score_history,
            "mutation_log": mutation_log,
        }

    # -- Internal helpers -----------------------------------------------------

    async def _score_skill(self, skill_md, scenarios, evals):
        """Run Executor on all scenarios, then score with Gemini."""
        all_results = []
        total_passed = 0
        total_checks = 0
        per_eval = {e["id"]: {"passed": 0, "total": 0} for e in evals}

        for sc in scenarios:
            # Executor runs the skill
            output = await self._ask(
                self.executor,
                f"Execute this skill:\n\n{skill_md}\n\nUser request:\n{sc['input']}",
            )
            # Score with Gemini (structured JSON, not an agent)
            scores = await self._gen_json(
                f"""Evaluate this output against criteria. Return JSON array.

Input: {sc['input']}
Output: {output}

Criteria:
{json.dumps(evals, indent=2)}

Return: [{{"eval_id": 1, "passed": true, "reason": "..."}}]"""
            )
            if not isinstance(scores, list):
                scores = scores.get("results", scores.get("evaluations", []))

            for s in scores:
                eid = s.get("eval_id")
                passed = s.get("passed", False)
                if passed:
                    total_passed += 1
                total_checks += 1
                if eid in per_eval:
                    per_eval[eid]["total"] += 1
                    if passed:
                        per_eval[eid]["passed"] += 1
                all_results.append({**s, "scenario_id": sc["id"]})

        return {
            "passed": total_passed,
            "total": total_checks,
            "per_eval": [
                {"eval_id": k, **v, "pass_rate": round(v["passed"] / max(v["total"], 1) * 100, 1)}
                for k, v in per_eval.items()
            ],
            "details": all_results,
        }

    async def _analyze_failures(self, skill_md, scenarios, evals, details):
        """Analyst agent diagnoses the worst failures."""
        failed = [d for d in details if not d.get("passed")]
        if not failed:
            return {"diagnosis": "All passed", "mutation_strategy": "add_constraint",
                    "target_section": "N/A", "suggested_change": "none"}

        prompt = (
            f"Diagnose these failures and suggest ONE fix.\n\n"
            f"Skill:\n{skill_md[:2000]}\n\n"
            f"Failed evals:\n{json.dumps(failed[:5], indent=2)}\n\n"
            f"Return JSON: {{diagnosis, mutation_strategy, target_section, suggested_change}}"
        )
        text = await self._ask(self.analyst, prompt)
        return self._parse_json(text, {
            "diagnosis": text[:200],
            "mutation_strategy": "add_constraint",
            "target_section": "unknown",
            "suggested_change": "unclear",
        })

    async def _mutate_skill(self, skill_md, analysis):
        """Mutator agent makes one targeted change."""
        prompt = (
            f"Apply this fix to the skill. Make ONE change only.\n\n"
            f"SKILL.md:\n{skill_md}\n\n"
            f"Diagnosis: {analysis.get('diagnosis')}\n"
            f"Strategy: {analysis.get('mutation_strategy')}\n"
            f"Target: {analysis.get('target_section')}\n"
            f"Change: {analysis.get('suggested_change')}\n\n"
            f"Return JSON: {{description, reasoning, new_skill_md}}"
        )
        text = await self._ask(self.mutator, prompt)
        return self._parse_json(text, {
            "description": "Failed to parse mutation",
            "reasoning": "",
            "new_skill_md": skill_md,
        })

    @staticmethod
    def _strategy_stats(mutation_log):
        stats = {}
        for m in mutation_log:
            s = m.get("strategy_type", "unknown")
            if s not in stats:
                stats[s] = {"total": 0, "kept": 0}
            stats[s]["total"] += 1
            if m.get("kept"):
                stats[s]["kept"] += 1
        return stats
