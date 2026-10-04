"""Self-improving triage agent: 3 agents that raise routing accuracy.

  Executor — routes an issue using the current SKILL.md, then scores the result
  Analyst  — diagnoses the mis-routes and picks one mutation strategy
  Mutator  — applies exactly one targeted edit to the SKILL.md

Provider-agnostic via LiteLLM: pass any model string it understands
("gpt-4o-mini", "anthropic/claude-sonnet-5", "gemini/gemini-2.0-flash",
"github_copilot/<model-id>", ...). Copilot models need no API key — run
scripts/copilot_login.py once instead.
"""

import asyncio
import json
import os
import re
import tempfile
from typing import Callable, Optional

import litellm # pyright: ignore[reportMissingImports]
from pydantic import BaseModel, Field

import telemetry

litellm.suppress_debug_info = True
# Newer models reject sampling params (e.g. Claude accepts only temperature=1).
# Drop them rather than fail; the temperatures below are hints, not contracts.
litellm.drop_params = True

# "claude_code/<alias>" runs on the user's own Claude Code login (no API key).
CLAUDE_CODE_PREFIX = "claude_code/"
CLAUDE_CODE_TIMEOUT_S = 300
_workdir: Optional[str] = None


def _claude_code_workdir() -> str:
    """An empty directory, so Claude Code finds no project CLAUDE.md or memory."""
    global _workdir
    if _workdir is None or not os.path.isdir(_workdir):
        _workdir = tempfile.mkdtemp(prefix="triage-claude-code-")
    return _workdir

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

MUTATOR_SYSTEM = (
    "You edit triage SKILL.md files. Given a skill and a diagnosis, make exactly "
    "ONE targeted change. Preserve the YAML frontmatter and the overall section "
    "structure. Never delete existing routing rules unless the diagnosis says "
    "they are the cause. Return the complete updated file as valid JSON only."
)


class RoutingDecision(BaseModel):
    team: str = Field(description="Exactly one team from the roster")
    severity: str = Field(description="P0 | P1 | P2 | P3 | P4")
    reasoning: str = Field(description="Which signal drove the routing")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class FailureAnalysis(BaseModel):
    diagnosis: str
    mutation_strategy: str
    target_section: str
    suggested_change: str


class SkillMutation(BaseModel):
    description: str
    reasoning: str
    new_skill_md: str


_KEY_ENV = (
    (("gpt", "o1", "o3", "openai"), "OPENAI_API_KEY"),
    (("claude", "anthropic"), "ANTHROPIC_API_KEY"),
    (("gemini", "google"), "GEMINI_API_KEY"),
)


class TriageOptimizer:
    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        concurrency: int = 4,
    ):
        self.model = model
        self._sem = asyncio.Semaphore(concurrency)
        # Copilot and Claude Code authenticate through a login, not a key. Check
        # them first: "github_copilot/claude-…" and "claude_code/…" would otherwise
        # match the "claude" needle.
        if api_key and not model.startswith(("github_copilot/", CLAUDE_CODE_PREFIX)):
            for needles, env_var in _KEY_ENV:
                if any(n in model.lower() for n in needles):
                    os.environ[env_var] = api_key
                    break

    # -- LLM plumbing --------------------------------------------------------

    @property
    def backend(self) -> str:
        if self.model.startswith(CLAUDE_CODE_PREFIX):
            return "claude_code"
        if self.model.startswith("github_copilot/"):
            return "github_copilot"
        return "litellm"

    async def _ask(self, system: str, user: str, temperature: float = 0.2,
                   role: str = "llm") -> str:
        async with self._sem:
            with telemetry.span(
                "llm.call",
                **{
                    "triage.role": role,
                    "triage.backend": self.backend,
                    "gen_ai.system": self.backend,
                    "gen_ai.request.model": self.model,
                    "gen_ai.request.temperature": temperature,
                    "triage.prompt_chars": len(system) + len(user),
                    "triage.system_prompt": telemetry.clip(system) if telemetry.record_content() else None,
                    "triage.user_prompt": telemetry.clip(user) if telemetry.record_content() else None,
                },
            ) as sp:
                if self.backend == "claude_code":
                    text, usage = await self._ask_claude_code(system, user)
                else:
                    resp = await litellm.acompletion(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system},
                            {"role": "user", "content": user},
                        ],
                        temperature=temperature,
                    )
                    text = resp.choices[0].message.content or ""
                    u = getattr(resp, "usage", None)
                    usage = {
                        "input_tokens": getattr(u, "prompt_tokens", None),
                        "output_tokens": getattr(u, "completion_tokens", None),
                    }
                for key, value in {
                    "gen_ai.usage.input_tokens": usage.get("input_tokens"),
                    "gen_ai.usage.output_tokens": usage.get("output_tokens"),
                    "gen_ai.response.model": usage.get("response_model"),
                    "triage.cost_usd": usage.get("cost_usd"),
                    "triage.response_chars": len(text),
                    "triage.response": telemetry.clip(text) if telemetry.record_content() else None,
                }.items():
                    if value is not None:
                        sp.set_attribute(key, value)
        return text

    async def _ask_claude_code(self, system: str, user: str) -> tuple:
        """One call through the user's own Claude Code login via headless `claude -p`.

        No API key needed. Isolation matters here: the executor must route using
        only the skill under test, so nothing from the user's own Claude Code setup
        may leak in. Flags: no tools, no skills/slash-commands, no MCP, no saved
        session, no settings files (hooks), an empty working directory (no
        CLAUDE.md), and our own system prompt. `--bare` would be tidier but it
        accepts only an API key, which is exactly what this backend avoids.
        Sampling params cannot be set from the CLI, so `temperature` is not applied.
        """
        alias = self.model[len(CLAUDE_CODE_PREFIX):] or "sonnet"
        cmd = [
            os.environ.get("TRIAGE_CLAUDE_BIN", "claude"), "-p",
            "--model", alias,
            "--output-format", "json",
            "--tools", "",
            "--disable-slash-commands",
            "--strict-mcp-config",
            "--no-session-persistence",
            "--setting-sources", "",
            "--system-prompt", system,
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd, cwd=_claude_code_workdir(),
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            out, err = await asyncio.wait_for(
                proc.communicate(user.encode()), timeout=CLAUDE_CODE_TIMEOUT_S)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise RuntimeError(f"claude -p timed out after {CLAUDE_CODE_TIMEOUT_S}s")
        raw = out.decode(errors="replace").strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            raise RuntimeError(
                f"claude -p exited {proc.returncode} without JSON: "
                f"{(err.decode(errors='replace') or raw)[:300]}")
        if proc.returncode != 0 or data.get("is_error"):
            raise RuntimeError(f"claude -p failed: {str(data.get('result') or raw)[:300]}")
        u = data.get("usage") or {}
        models = data.get("modelUsage") or {}
        main = max(models, key=lambda m: models[m].get("costUSD", 0), default=None)
        return data.get("result") or "", {
            "input_tokens": (u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
                             + u.get("cache_read_input_tokens", 0)),
            "output_tokens": u.get("output_tokens"),
            "cost_usd": data.get("total_cost_usd"),
            "response_model": main,
        }

    async def _ask_json(self, system: str, user: str, fallback=None, **kw):
        text = await self._ask(system, user, **kw)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        # Models wrap JSON in prose or fences more often than they should.
        fenced = re.search(r"```(?:json)?\s*(.+?)```", text, re.DOTALL)
        candidate = fenced.group(1) if fenced else text
        decoder = json.JSONDecoder()
        start = min(
            (i for i in (candidate.find("{"), candidate.find("[")) if i != -1),
            default=-1,
        )
        if start != -1:
            try:
                return decoder.raw_decode(candidate, start)[0]
            except json.JSONDecodeError:
                pass
        if fallback is not None:
            return fallback
        raise ValueError(f"Could not parse JSON from model response: {text[:300]}")

    # -- Public API ----------------------------------------------------------

    async def analyze_skill(self, skill_md: str, teams: list) -> dict:
        """Generate scenarios + evals when you have no golden set yet.

        Prefer a hand-labeled golden set. Self-generated labels measure the
        model's opinion of correct routing, not your org's.
        """
        with telemetry.span(
            "optimizer.generate",
            **{"triage.model": self.model, "triage.backend": self.backend,
               "triage.teams": len(teams)},
        ):
            return await self._ask_json(
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

    async def optimize(
        self,
        skill_md: str,
        context: dict,
        scenarios: list,
        evals: list,
        max_rounds: int = 10,
        patience: int = 4,
        callback: Optional[Callable] = None,
    ) -> dict:
        """Hill-climb the SKILL.md. Only score-improving mutations survive.

        `context` carries whatever the subclass's scorer needs — `{"teams": [...]}`
        here, `{"rubric": ..., "profile": ...}` for the RCA optimizer.

        The whole run is one trace (see telemetry.py): session > baseline/round > calls.
        """
        with telemetry.span(
            "optimizer.session",
            **{"triage.model": self.model, "triage.backend": self.backend,
               "triage.kind": type(self).__name__, "triage.max_rounds": max_rounds,
               "triage.scenarios": len(scenarios)},
        ) as sp:
            payload = await self._optimize(
                skill_md, context, scenarios, evals, max_rounds, patience, callback)
            sp.set_attribute("triage.baseline_score", payload["baseline_score"])
            sp.set_attribute("triage.final_score", payload["final_score"])
            sp.set_attribute("triage.rounds", len(payload["score_history"]) - 1)
            return payload

    async def _optimize(self, skill_md, context, scenarios, evals, max_rounds,
                        patience, callback) -> dict:

        async def emit(event):
            if callback:
                await callback(event)

        best_md = skill_md
        with telemetry.span("optimizer.baseline") as bsp:
            best = await self._score(best_md, scenarios, evals, context)
            bsp.set_attribute("triage.score", best["pass_rate"])
        best_pct = best["pass_rate"]
        score_history = [best_pct]
        mutation_log = []

        await emit({"type": "baseline", "data": {"score": best_pct, **_summary(best)}})

        stale = 0
        for rnd in range(1, max_rounds + 1):
            with telemetry.span("optimizer.round", **{"triage.round": rnd}) as rsp:
                if best_pct >= 100.0:
                    await emit({"type": "converged", "data": {"round": rnd}})
                    break
                if stale >= patience:
                    await emit({"type": "plateau", "data": {"round": rnd, "stale": stale}})
                    break

                await emit({"type": "round_start", "data": {"round": rnd}})

                analysis = await self._analyze(best_md, best["failures"], mutation_log)
                mutation = await self._mutate(best_md, analysis, context)
                candidate_md = mutation.get("new_skill_md") or best_md
                rsp.set_attribute("triage.strategy", analysis.get("mutation_strategy", ""))
                rsp.set_attribute("triage.description", mutation.get("description", ""))
                rsp.set_attribute("triage.score_before", best_pct)

                if candidate_md.strip() == best_md.strip():
                    rsp.set_attribute("triage.kept", False)
                    rsp.set_attribute("triage.unchanged", True)
                    stale += 1
                    score_history.append(best_pct)
                    await emit({
                        "type": "round_result",
                        "data": {
                            "round": rnd, "score": best_pct, "kept": False,
                            "description": "Mutator returned an unchanged skill",
                            "strategy": analysis.get("mutation_strategy", ""),
                            "per_eval": best["per_eval"],
                        },
                    })
                    continue

                result = await self._score(candidate_md, scenarios, evals, context)
                kept = result["pass_rate"] > best_pct
                rsp.set_attribute("triage.kept", kept)
                rsp.set_attribute("triage.score_after", result["pass_rate"])

                mutation_log.append({
                    "round": rnd,
                    "strategy_type": analysis.get("mutation_strategy", "unknown"),
                    "diagnosis": analysis.get("diagnosis", ""),
                    "target_section": analysis.get("target_section", ""),
                    "description": mutation.get("description", ""),
                    "reasoning": mutation.get("reasoning", ""),
                    "score_before": best_pct,
                    "score_after": result["pass_rate"],
                    "kept": kept,
                })

                if kept:
                    best_md, best, best_pct, stale = candidate_md, result, result["pass_rate"], 0
                else:
                    stale += 1

                score_history.append(best_pct)
                await emit({
                    "type": "round_result",
                    "data": {
                        "round": rnd,
                        "score": result["pass_rate"],
                        "kept": kept,
                        "description": mutation.get("description", ""),
                        "strategy": analysis.get("mutation_strategy", ""),
                        "per_eval": result["per_eval"],
                    },
                })

        payload = {
            "baseline_score": score_history[0],
            "final_score": best_pct,
            "improved_skill_md": best_md,
            "original_skill_md": skill_md,
            "score_history": score_history,
            "mutation_log": mutation_log,
            "strategy_stats": _strategy_stats(mutation_log),
            "remaining_failures": best["failures"],
            "confusion": best["confusion"],
        }
        await emit({"type": "complete", "data": payload})
        return payload

    # -- Scoring -------------------------------------------------------------

    async def _score(self, skill_md, scenarios, evals, context) -> dict:
        results = await asyncio.gather(*[
            self._score_one(skill_md, sc, evals, context) for sc in scenarios
        ])

        per_eval = {e["id"]: {"name": e.get("name", str(e["id"])), "passed": 0, "total": 0}
                    for e in evals}
        failures, confusion = [], []
        passed_scenarios = 0

        for sc, decision, checks in results:
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
                })
            if decision.get("team") != sc.get("expected_team"):
                confusion.append({
                    "expected": sc.get("expected_team"),
                    "predicted": decision.get("team"),
                    "scenario": sc.get("name", sc["id"]),
                })

        total = len(scenarios) or 1
        return {
            "pass_rate": round(100 * passed_scenarios / total, 1),
            "passed": passed_scenarios,
            "total": len(scenarios),
            "per_eval": [
                {"eval_id": k, **v,
                 "pass_rate": round(100 * v["passed"] / max(v["total"], 1), 1)}
                for k, v in per_eval.items()
            ],
            "failures": failures,
            "confusion": confusion,
        }

    async def _score_one(self, skill_md, sc, evals, context):
        teams = context["teams"]
        decision = await self._ask_json(
            EXECUTOR_SYSTEM,
            (
                f"ROUTE MODE.\n\n"
                f"# Skill\n{skill_md}\n\n"
                f"# Allowed teams (pick exactly one)\n{json.dumps(teams)}\n\n"
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

        # team_correct is decided in code, not by the judge — a string match is
        # not a judgment call, and letting the judge make it adds variance.
        deterministic, to_judge = [], []
        for e in evals:
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
            scoring = await self._ask_json(
                EXECUTOR_SYSTEM,
                (
                    f"SCORE MODE.\n\n"
                    f"Issue: {sc['input']}\n"
                    f"Environment: {sc.get('environment', 'non-prod')}\n"
                    f"Expected severity: {sc.get('expected_severity')}\n\n"
                    f"Decision: {json.dumps(decision)}\n\n"
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
            judged = scoring.get("results", []) if isinstance(scoring, dict) else []

        return sc, decision, deterministic + judged

    # -- Analyst / Mutator ---------------------------------------------------

    async def _analyze(self, skill_md, failures, mutation_log) -> dict:
        if not failures:
            return {"diagnosis": "All scenarios passed", "mutation_strategy": "restructure",
                    "target_section": "N/A", "suggested_change": "none"}

        # Show the analyst what has already been tried, so it stops re-proposing
        # a mutation that was measured and discarded.
        tried = [
            f"- [{m['strategy_type']}] {m['description']} "
            f"({m['score_before']}% -> {m['score_after']}%, "
            f"{'kept' if m['kept'] else 'DISCARDED'})"
            for m in mutation_log[-6:]
        ]
        tried_block = ("\n\n# Already attempted (do not repeat a discarded one)\n"
                       + "\n".join(tried)) if tried else ""

        return await self._ask_json(
            ANALYST_SYSTEM,
            (
                f"Diagnose these mis-routes and propose ONE generalizing fix.\n\n"
                f"# Current skill\n{skill_md}\n\n"
                f"# Failed cases\n{json.dumps(failures[:6], indent=2)}"
                f"{tried_block}\n\n"
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

    async def _mutate(self, skill_md, analysis, context) -> dict:
        return await self._ask_json(
            MUTATOR_SYSTEM,
            (
                f"Apply this fix. ONE change only.\n\n"
                f"# SKILL.md\n{skill_md}\n\n"
                f"# Diagnosis\n{analysis.get('diagnosis')}\n"
                f"# Strategy\n{analysis.get('mutation_strategy')}\n"
                f"# Target section\n{analysis.get('target_section')}\n"
                f"# Change\n{analysis.get('suggested_change')}\n"
                f"# Teams\n{json.dumps(context.get('teams', []))}\n\n"
                f'Return JSON: {{"description": "one line", '
                f'"reasoning": "why this generalizes", '
                f'"new_skill_md": "the complete updated file"}}'
            ),
            fallback={"description": "Mutation failed to parse",
                      "reasoning": "", "new_skill_md": skill_md},
            temperature=0.4,
            role="mutator",
        )


def _summary(result: dict) -> dict:
    return {k: result[k] for k in ("passed", "total", "per_eval")}


def _strategy_stats(mutation_log: list) -> dict:
    stats: dict = {}
    for m in mutation_log:
        s = stats.setdefault(m.get("strategy_type", "unknown"), {"total": 0, "kept": 0})
        s["total"] += 1
        s["kept"] += int(bool(m.get("kept")))
    return stats
