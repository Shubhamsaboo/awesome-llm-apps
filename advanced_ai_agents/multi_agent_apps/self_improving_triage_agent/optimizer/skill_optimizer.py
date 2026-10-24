"""Self-improving skill loop: measure -> diagnose -> mutate -> re-measure.

`SkillOptimizer` owns everything that does not depend on the skill: the model
client (LiteLLM or Claude Code), tracing, and the hill-climb that keeps an edit
only when it measurably helps. What "helps" means comes from a `Scorer`:

  RoutingScorer       did the issue reach the owning team?        routing_scorer.py
  RcaScorer           is the RCA correct, complete and grounded?  rca_scorer.py
  ExpectationsScorer  does the output meet skill-creator evals?   expectations_scorer.py

A new kind of skill needs only a new Scorer; the loop, backends, tracing and UI
are reused unchanged.

Provider-agnostic via LiteLLM: pass any model string it understands
("gpt-4o-mini", "anthropic/claude-sonnet-5", "gemini/gemini-2.0-flash", ...).
Or pass "claude_code/<alias>" to use a local Claude Code login instead of a key.
"""

import asyncio
import importlib
import json
import logging
import os
import re
import tempfile
from typing import Callable, Optional, Protocol

import telemetry


def _import_litellm():
    """Import LiteLLM without the first-import deadlock.

    LiteLLM attaches a secret-redaction filter to loggers such as `asyncio` early in
    its (slow) import. If another thread logs on one of them before the import
    finishes — Streamlit's server thread does — the filter lazily imports a module the
    importing thread is holding, and Python raises `_DeadlockError` on
    `litellm.types.secret_managers.main`. So: drop log records while importing, and
    run the filter once so its lazy imports are already loaded. Redaction stays on.

    The guard is process-wide: for the few seconds of the first import, records
    from every thread are dropped. The warm-up uses a private LiteLLM attribute and
    is skipped if a version lacks it; the guard alone prevents the race.
    """
    previous = logging.root.manager.disable
    logging.disable(logging.CRITICAL)
    try:
        module = importlib.import_module("litellm")
        secret_filter = getattr(getattr(module, "_logging", None), "_secret_filter", None)
        if secret_filter is not None:
            record = logging.LogRecord("asyncio", logging.ERROR, __file__, 0, "warm-up", None, None)
            secret_filter.filter(record)
    finally:
        logging.disable(previous)
    return module


litellm = _import_litellm()

litellm.suppress_debug_info = True
# Newer models reject sampling params (e.g. Claude accepts only temperature=1).
# Drop them rather than fail; the temperatures below are hints, not contracts.
litellm.drop_params = True

# "claude_code/<alias>" runs on the user's own Claude Code login (no API key).
CLAUDE_CODE_PREFIX = "claude_code/"
CLAUDE_CODE_TIMEOUT_S = 300
_workdir: Optional[str] = None

# Marker added to a fallback when a model reply could not be parsed. Must equal
# score_rca.PARSE_ERROR in the triage-issue skill (a test pins this).
PARSE_ERROR = "_parse_error"


def _claude_code_workdir() -> str:
    """An empty directory, so Claude Code finds no project CLAUDE.md or memory."""
    global _workdir
    if _workdir is None or not os.path.isdir(_workdir):
        _workdir = tempfile.mkdtemp(prefix="triage-claude-code-")
    return _workdir


def parse_json(text: str):
    """Parse a model's JSON reply, tolerating code fences and surrounding prose."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    fenced = re.search(r"```(?:json)?\s*(.+?)```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else text
    starts = [i for i in (candidate.find("{"), candidate.find("[")) if i != -1]
    if starts:
        try:
            return json.JSONDecoder().raw_decode(candidate, min(starts))[0]
        except json.JSONDecodeError:
            pass
    raise ValueError(f"Could not parse JSON from model response: {text[:300]}")


def is_parse_error(value) -> bool:
    return isinstance(value, dict) and value.get(PARSE_ERROR) is True


MUTATOR_SYSTEM = (
    "You edit agent SKILL.md files. Given a skill and a diagnosis, make exactly "
    "ONE targeted change. Preserve the YAML frontmatter and the overall section "
    "structure. Never delete existing rules unless the diagnosis says they are "
    "the cause. Return the complete updated file as valid JSON only."
)


class Scorer(Protocol):
    """What a skill is measured on. Implement this to optimize a new kind of skill.

    `score()` returns a dict with at least:
      pass_rate     the objective the loop climbs, 0-100
      passed/total  cases fully correct, and cases scored
      per_eval      [{"eval_id", "name", "passed", "total", "pass_rate"}]
      failures      what the analyst sees; any JSON-serializable dicts
      parse_errors  model replies that could not be parsed while scoring
    """

    kind: str
    objective_label: str

    async def score(self, client: "SkillOptimizer", skill_md: str, cases: list) -> dict: ...

    async def diagnose(self, client: "SkillOptimizer", skill_md: str, failures: list,
                       mutation_log: list) -> dict: ...

    def mutation_context(self) -> str: ...

    def improves(self, candidate: dict, best: dict, min_gain: float = 0.0) -> bool: ...

    def converged(self, best: dict) -> bool: ...

    def extra_results(self, best: dict) -> dict: ...


class BaseScorer:
    """Defaults for the parts of `Scorer` most skills share."""

    kind = "skill"
    objective_label = "score %"

    def mutation_context(self) -> str:
        return ""

    def improves(self, candidate: dict, best: dict, min_gain: float = 0.0) -> bool:
        """Keep an edit only if it beats the best by more than noise.

        `min_gain` is in objective points. With 8 cases one flipped case moves the
        score 12.5 points, so a non-zero threshold stops a lucky run being kept.
        """
        gain = candidate["pass_rate"] - best["pass_rate"]
        return gain > 0 and gain >= min_gain

    def converged(self, best: dict) -> bool:
        return best["pass_rate"] >= 100.0

    def extra_results(self, best: dict) -> dict:
        return {}

    @staticmethod
    def tried_block(mutation_log: list, unit: str = "") -> str:
        """Recent measured edits, so the analyst stops re-proposing discarded ones."""
        tried = [
            f"- [{m['strategy_type']}] {m['description']} "
            f"({m['score_before']}{unit} -> {m['score_after']}{unit}, "
            f"{'kept' if m['kept'] else m.get('outcome', 'discarded').upper()})"
            for m in mutation_log if m.get("outcome") != "skipped"
        ][-6:]
        if not tried:
            return ""
        return "\n\n# Already attempted (do not repeat a discarded one)\n" + "\n".join(tried)


class SkillOptimizer:
    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        concurrency: int = 4,
    ):
        self.model = model
        # Kept on the instance and passed per call. Writing it to os.environ would
        # let one Streamlit session's calls go out on another session's key.
        self.api_key = api_key if api_key and not model.startswith(CLAUDE_CODE_PREFIX) else None
        self._sem = asyncio.Semaphore(concurrency)

    # -- LLM plumbing --------------------------------------------------------

    @property
    def backend(self) -> str:
        if self.model.startswith(CLAUDE_CODE_PREFIX):
            return "claude_code"
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
                        **({"api_key": self.api_key} if self.api_key else {}),
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

        No API key needed. Isolation matters here: the executor must use only the
        skill under test, so nothing from the user's own Claude Code setup may leak
        in. Flags: no tools, no skills/slash-commands, no MCP, no saved session, no
        settings files (hooks), an empty working directory (no CLAUDE.md), and our
        own system prompt. `--bare` would be tidier but it accepts only an API key,
        which is exactly what this backend avoids. Sampling params cannot be set
        from the CLI, so `temperature` is not applied.
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
        """Ask for JSON. An unparseable reply returns `fallback` marked with
        PARSE_ERROR, so callers can count it instead of scoring it as real output."""
        text = await self._ask(system, user, **kw)
        try:
            return parse_json(text)
        except ValueError:
            if fallback is None:
                raise
            return {**fallback, PARSE_ERROR: True}

    # -- Public API ----------------------------------------------------------

    async def score(self, skill_md: str, scorer: Scorer, cases: list) -> dict:
        """Score once. No mutation, no loop."""
        return await scorer.score(self, skill_md, cases)

    async def optimize(
        self,
        skill_md: str,
        scorer: Scorer,
        cases: list,
        holdout: Optional[list] = None,
        max_rounds: int = 10,
        patience: int = 4,
        min_gain: float = 0.0,
        callback: Optional[Callable] = None,
    ) -> dict:
        """Hill-climb the SKILL.md on `cases`. Only edits that pass `scorer.improves`
        survive.

        `holdout` cases are scored only for the starting and final skill and never
        influence which edits are kept, so a gain that does not carry over to them
        shows up as overfitting rather than progress.

        The whole run is one trace (see telemetry.py): session > baseline/round > calls.
        """
        with telemetry.span(
            "optimizer.session",
            **{"triage.model": self.model, "triage.backend": self.backend,
               "triage.kind": scorer.kind, "triage.max_rounds": max_rounds,
               "triage.min_gain": min_gain, "triage.scenarios": len(cases),
               "triage.holdout": len(holdout or [])},
        ) as sp:
            payload = await self._optimize(
                skill_md, scorer, cases, holdout or [], max_rounds, patience, min_gain, callback)
            sp.set_attribute("triage.baseline_score", payload["baseline_score"])
            sp.set_attribute("triage.final_score", payload["final_score"])
            sp.set_attribute("triage.rounds", len(payload["score_history"]) - 1)
            if payload["holdout"]:
                sp.set_attribute("triage.holdout_baseline", payload["holdout"]["baseline"])
                sp.set_attribute("triage.holdout_final", payload["holdout"]["final"])
            return payload

    async def _optimize(self, skill_md, scorer, cases, holdout, max_rounds, patience,
                        min_gain, callback) -> dict:

        async def emit(event):
            if callback:
                await callback(event)

        best_md = skill_md
        with telemetry.span("optimizer.baseline") as bsp:
            best = await scorer.score(self, best_md, cases)
            bsp.set_attribute("triage.score", best["pass_rate"])
        best_pct = best["pass_rate"]
        score_history = [best_pct]
        mutation_log = []

        holdout_start = None
        if holdout:
            with telemetry.span("optimizer.holdout", **{"triage.phase": "baseline"}):
                holdout_start = await scorer.score(self, skill_md, holdout)

        await emit({"type": "baseline", "data": {"score": best_pct, **_summary(best)}})

        stale = 0
        for rnd in range(1, max_rounds + 1):
            with telemetry.span("optimizer.round", **{"triage.round": rnd}) as rsp:
                if scorer.converged(best):
                    await emit({"type": "converged", "data": {"round": rnd}})
                    break
                if stale >= patience:
                    await emit({"type": "plateau", "data": {"round": rnd, "stale": stale}})
                    break

                await emit({"type": "round_start", "data": {"round": rnd}})

                analysis = await scorer.diagnose(self, best_md, best["failures"], mutation_log)
                mutation = (await self._mutate(best_md, analysis, scorer)
                            if not is_parse_error(analysis) else None)
                strategy = analysis.get("mutation_strategy", "unknown")
                rsp.set_attribute("triage.strategy", strategy)

                # A reply that could not be parsed carries no diagnosis or edit.
                # Acting on the fallback would mutate the skill on a guess.
                skip = ("Analyst reply could not be parsed" if mutation is None else
                        "Mutator reply could not be parsed" if is_parse_error(mutation) else None)
                if skip:
                    rsp.set_attribute("triage.kept", False)
                    rsp.set_attribute("triage.outcome", "skipped")
                    stale += 1
                    score_history.append(best_pct)
                    mutation_log.append(_log_entry(rnd, analysis, {"description": skip},
                                                   best_pct, best_pct, "skipped", 0))
                    await emit({"type": "round_result", "data": {
                        "round": rnd, "score": best_pct, "kept": False, "outcome": "skipped",
                        "description": skip, "strategy": strategy,
                        "per_eval": best["per_eval"]}})
                    continue

                candidate_md = mutation.get("new_skill_md") or best_md
                rsp.set_attribute("triage.description", mutation.get("description", ""))
                rsp.set_attribute("triage.score_before", best_pct)

                if candidate_md.strip() == best_md.strip():
                    rsp.set_attribute("triage.kept", False)
                    rsp.set_attribute("triage.unchanged", True)
                    stale += 1
                    score_history.append(best_pct)
                    await emit({"type": "round_result", "data": {
                        "round": rnd, "score": best_pct, "kept": False, "outcome": "unchanged",
                        "description": "Mutator returned an unchanged skill",
                        "strategy": strategy, "per_eval": best["per_eval"]}})
                    continue

                result = await scorer.score(self, candidate_md, cases)
                # More unparseable replies than the best had means the score is
                # partly judge noise: neither keep nor learn from it.
                if result.get("parse_errors", 0) > best.get("parse_errors", 0):
                    kept, outcome = False, "inconclusive"
                else:
                    kept = scorer.improves(result, best, min_gain)
                    outcome = "kept" if kept else "discarded"
                rsp.set_attribute("triage.kept", kept)
                rsp.set_attribute("triage.outcome", outcome)
                rsp.set_attribute("triage.score_after", result["pass_rate"])

                mutation_log.append(_log_entry(rnd, analysis, mutation, best_pct,
                                               result["pass_rate"], outcome,
                                               result.get("parse_errors", 0)))

                if kept:
                    best_md, best, best_pct, stale = candidate_md, result, result["pass_rate"], 0
                else:
                    stale += 1

                score_history.append(best_pct)
                await emit({"type": "round_result", "data": {
                    "round": rnd, "score": result["pass_rate"], "kept": kept,
                    "outcome": outcome, "description": mutation.get("description", ""),
                    "strategy": strategy, "per_eval": result["per_eval"]}})

        holdout_summary = None
        if holdout:
            if best_md == skill_md:
                holdout_end = holdout_start
            else:
                with telemetry.span("optimizer.holdout", **{"triage.phase": "final"}):
                    holdout_end = await scorer.score(self, best_md, holdout)
            holdout_summary = {
                "baseline": holdout_start["pass_rate"],
                "final": holdout_end["pass_rate"],
                "total": len(holdout),
                "regressed": holdout_end["pass_rate"] < holdout_start["pass_rate"],
                "parse_errors": holdout_end.get("parse_errors", 0),
            }
            await emit({"type": "holdout", "data": holdout_summary})

        payload = {
            "kind": scorer.kind,
            "baseline_score": score_history[0],
            "final_score": best_pct,
            "improved_skill_md": best_md,
            "original_skill_md": skill_md,
            "score_history": score_history,
            "mutation_log": mutation_log,
            "strategy_stats": _strategy_stats(mutation_log),
            "remaining_failures": best["failures"],
            "confusion": best.get("confusion", []),
            "parse_errors": best.get("parse_errors", 0),
            "min_gain": min_gain,
            "holdout": holdout_summary,
            **scorer.extra_results(best),
        }
        await emit({"type": "complete", "data": payload})
        return payload

    async def _mutate(self, skill_md: str, analysis: dict, scorer: Scorer) -> dict:
        context = scorer.mutation_context()
        return await self._ask_json(
            MUTATOR_SYSTEM,
            (
                f"Apply this fix. ONE change only.\n\n"
                f"# SKILL.md\n{skill_md}\n\n"
                f"# Diagnosis\n{analysis.get('diagnosis')}\n"
                f"# Strategy\n{analysis.get('mutation_strategy')}\n"
                f"# Target section\n{analysis.get('target_section')}\n"
                f"# Change\n{analysis.get('suggested_change')}\n"
                + (f"{context}\n" if context else "")
                + '\nReturn JSON: {"description": "one line", '
                  '"reasoning": "why this generalizes", '
                  '"new_skill_md": "the complete updated file"}'
            ),
            fallback={"description": "Mutation failed to parse",
                      "reasoning": "", "new_skill_md": skill_md},
            temperature=0.4,
            role="mutator",
        )


def _log_entry(rnd, analysis, mutation, before, after, outcome, parse_errors) -> dict:
    return {
        "round": rnd,
        "strategy_type": analysis.get("mutation_strategy", "unknown"),
        "diagnosis": analysis.get("diagnosis", ""),
        "target_section": analysis.get("target_section", ""),
        "description": mutation.get("description", ""),
        "reasoning": mutation.get("reasoning", ""),
        "score_before": before,
        "score_after": after,
        "kept": outcome == "kept",
        "outcome": outcome,
        "parse_errors": parse_errors,
    }


def _summary(result: dict) -> dict:
    return {k: result[k] for k in ("passed", "total", "per_eval")}


def _strategy_stats(mutation_log: list) -> dict:
    stats: dict = {}
    for m in mutation_log:
        if m.get("outcome") == "skipped":
            continue
        s = stats.setdefault(m.get("strategy_type", "unknown"), {"total": 0, "kept": 0})
        s["total"] += 1
        s["kept"] += int(bool(m.get("kept")))
    return stats


def split_holdout(cases: list, holdout_fraction: float, seed: int = 0) -> tuple:
    """Deterministically split cases into (train, holdout).

    At least one case always stays in train. A fraction of 0 returns no holdout.
    """
    if holdout_fraction <= 0 or len(cases) < 2:
        return list(cases), []
    import random

    order = list(range(len(cases)))
    random.Random(seed).shuffle(order)
    n = min(len(cases) - 1, max(1, round(len(cases) * holdout_fraction)))
    held = set(order[:n])
    return ([c for i, c in enumerate(cases) if i not in held],
            [c for i, c in enumerate(cases) if i in held])
