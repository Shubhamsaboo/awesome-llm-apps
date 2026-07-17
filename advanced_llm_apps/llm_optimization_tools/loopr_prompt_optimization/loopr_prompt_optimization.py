"""Loopr — a self-improving prompt-optimization loop, implemented from scratch.

Give it a task (a description, an under-specified seed prompt, a scorer, and a few
eval cases). It runs the prompt, scores the outputs, reflects on the failures in
plain language, rewrites the prompt, and repeats — until the outputs pass.

    seed prompt ─▶ RUN on each case ─▶ SCORE (deterministic) ─▶ best? keep it
        ▲                                     │
        │                                     ▼
        └──── REWRITE prompt ◀── REFLECT on the failures (LLM) ◀──┘

    stop when: score hits target (converged) · no improvement for N iters (plateau) · budget spent

The key idea (a lightweight take on GEPA, arXiv:2507.19457): the LLM only (a) runs
the candidate prompt and (b) phrases the reflection. Scoring, best-tracking, and the
stop decision are pure Python — so a run is reproducible for a fixed model, and a bad
reflection can never silently corrupt the state.

Zero third-party dependencies — standard library only. Backend is local-first:

    Local (recommended, free):  ollama serve  &&  ollama pull qwen2.5:14b
    Cloud fallback:             export LOOPR_PROVIDER=openai OPENAI_API_KEY=sk-...

Run:
    python loopr_prompt_optimization.py
"""
from __future__ import annotations

import json
import os
import re
import urllib.request
from dataclasses import dataclass, field
from typing import Callable

# --------------------------------------------------------------------------- #
# 1. LLM backend — Ollama (local) or OpenAI, both over the standard library.
# --------------------------------------------------------------------------- #

PROVIDER = os.environ.get("LOOPR_PROVIDER", "ollama").lower()
MODEL = os.environ.get("LOOPR_MODEL", "qwen2.5:14b" if PROVIDER == "ollama" else "gpt-4o-mini")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")


def _post(url: str, payload: dict, headers: dict | None = None, timeout: int = 120) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # ponytail: no retry/backoff; add if a flaky remote needs it
        return json.loads(resp.read().decode())


def call_llm(prompt: str, system: str = "", temperature: float = 0.2) -> str:
    """Send one prompt to the configured backend and return the text response."""
    if PROVIDER == "openai":
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("LOOPR_PROVIDER=openai but OPENAI_API_KEY is not set.")
        base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        messages = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
        out = _post(f"{base}/chat/completions",
                    {"model": MODEL, "messages": messages, "temperature": temperature},
                    headers={"Authorization": f"Bearer {key}"})
        return out["choices"][0]["message"]["content"].strip()

    # default: Ollama
    out = _post(f"{OLLAMA_HOST}/api/generate",
                {"model": MODEL, "prompt": prompt, "system": system,
                 "stream": False, "options": {"temperature": temperature}})
    return out.get("response", "").strip()


# --------------------------------------------------------------------------- #
# 2. Scorers — deterministic, return a score in [0, 1]. This is why the loop is
#    reproducible: the pass/fail signal never depends on the LLM's mood.
# --------------------------------------------------------------------------- #

def _json_field(output: str, expected: str, field_name: str) -> float:
    """Parse the first JSON object in `output` and compare `field_name` to `expected`."""
    match = re.search(r"\{.*\}", output, re.DOTALL)
    if not match:
        return 0.0
    try:
        obj = json.loads(match.group(0))
    except json.JSONDecodeError:
        return 0.0
    return 1.0 if str(obj.get(field_name, "")).strip().lower() == expected.strip().lower() else 0.0


SCORERS: dict[str, Callable[[str, str, dict], float]] = {
    "exact":    lambda out, exp, cfg: 1.0 if out.strip().lower() == exp.strip().lower() else 0.0,
    "contains": lambda out, exp, cfg: 1.0 if exp.strip().lower() in out.lower() else 0.0,
    "regex":    lambda out, exp, cfg: 1.0 if re.search(exp, out) else 0.0,
    "json_field": lambda out, exp, cfg: _json_field(out, exp, cfg.get("field", "value")),
}


# --------------------------------------------------------------------------- #
# 3. Task, results, and the reflection (prompt-rewrite) step.
# --------------------------------------------------------------------------- #

@dataclass
class Task:
    name: str
    description: str
    seed_prompt: str                 # must contain the {input} placeholder
    scorer: str                      # a key of SCORERS
    cases: list[dict]                # [{"input": ..., "expected": ...}, ...]
    system: str = ""
    scorer_config: dict = field(default_factory=dict)
    budget: int = 5                  # max iterations
    patience: int = 2                # stop after N iters with no improvement
    target_score: float = 1.0        # stop once mean score reaches this


@dataclass
class CaseResult:
    input: str
    expected: str
    output: str
    score: float


@dataclass
class Iteration:
    n: int
    prompt: str
    mean_score: float
    results: list[CaseResult]
    is_best: bool


@dataclass
class OptimizeResult:
    task_name: str
    seed_prompt: str
    best_prompt: str
    seed_score: float
    best_score: float
    stop_reason: str
    iterations: list[Iteration]


REFLECT_SYSTEM = (
    "You are a prompt-optimization engine. You improve an instruction prompt so a "
    "language model gets more eval cases right. Reason about WHY the current prompt "
    "failed, then rewrite it. Keep the {input} placeholder. Do NOT solve or hard-code "
    "the individual cases — improve the general instruction."
)
_PROMPT_RE = re.compile(r"<prompt>\s*(.*?)\s*</prompt>", re.DOTALL | re.IGNORECASE)


def reflect_and_rewrite(task: Task, current_prompt: str, failures: list[CaseResult]) -> str:
    """Ask the model to diagnose the failures and propose a better prompt.

    Returns the new prompt, or the current one unchanged if the reply can't be parsed
    (the loop then scores that as a no-improvement step — a safe no-op).
    """
    shown = "\n".join(
        f"{i}. INPUT: {r.input}\n   EXPECTED: {r.expected}\n   GOT: {(r.output or '')[:200]}"
        for i, r in enumerate(failures[:8], 1)
    )
    reflection_prompt = (
        f"TASK GOAL: {task.description or task.name}\n\n"
        f'CURRENT PROMPT:\n"""\n{current_prompt}\n"""\n\n'
        f"THIS PROMPT FAILED ON THESE CASES:\n{shown}\n\n"
        "Step 1 — Diagnose: in 1-3 sentences, what about the prompt caused these failures "
        "(ambiguity, missing format constraint, wrong label set, ...)?\n"
        "Step 2 — Rewrite: produce an improved prompt that fixes the diagnosis. It must keep "
        "the {input} placeholder and must generalize — never name or answer the cases above.\n\n"
        "Return ONLY the rewritten prompt wrapped exactly like this:\n<prompt>\n...\n</prompt>"
    )
    raw = call_llm(reflection_prompt, REFLECT_SYSTEM)
    match = _PROMPT_RE.search(raw)
    proposed = match.group(1).strip() if match else ""
    if not proposed or "{input}" not in proposed:
        return current_prompt          # unparseable → keep current (no-op step)
    return proposed


# --------------------------------------------------------------------------- #
# 4. The loop: evaluate → track best → stop-check → reflect → repeat.
# --------------------------------------------------------------------------- #

def evaluate(task: Task, prompt: str) -> tuple[float, list[CaseResult]]:
    scorer = SCORERS[task.scorer]
    results = []
    for case in task.cases:
        rendered = prompt.replace("{input}", str(case["input"]))
        output = call_llm(rendered, task.system)
        results.append(CaseResult(case["input"], case["expected"], output,
                                  scorer(output, case["expected"], task.scorer_config)))
    mean = sum(r.score for r in results) / len(results) if results else 0.0
    return mean, results


def optimize(task: Task, on_iteration: Callable[[Iteration], None] | None = None) -> OptimizeResult:
    current = task.seed_prompt
    best_prompt, best_score = current, -1.0
    seed_score, no_improve, stop_reason = 0.0, 0, "budget"
    iterations: list[Iteration] = []

    for n in range(max(1, task.budget)):
        mean, results = evaluate(task, current)
        if n == 0:
            seed_score = mean

        is_best = mean > best_score
        if is_best:
            best_prompt, best_score, no_improve = current, mean, 0
        else:
            no_improve += 1

        it = Iteration(n, current, mean, results, is_best)
        iterations.append(it)
        if on_iteration:
            on_iteration(it)

        # deterministic stop checks
        if mean >= task.target_score:
            stop_reason = "converged"; break
        if no_improve >= task.patience:
            stop_reason = "plateau"; break
        if n == task.budget - 1:
            stop_reason = "budget"; break

        # reflect on the failing cases and propose the next candidate
        current = reflect_and_rewrite(task, current, [r for r in results if r.score < 1.0])

    return OptimizeResult(task.name, task.seed_prompt, best_prompt,
                          seed_score, best_score, stop_reason, iterations)


# --------------------------------------------------------------------------- #
# 5. Offline self-check + a live demo.
# --------------------------------------------------------------------------- #

def _self_check() -> None:
    """No network — proves the deterministic pieces work."""
    assert SCORERS["exact"]("Yes", "yes", {}) == 1.0
    assert SCORERS["exact"]("maybe", "yes", {}) == 0.0
    assert SCORERS["contains"]("the answer is no", "no", {}) == 1.0
    assert SCORERS["json_field"]('here: {"role": "Backend Engineer"}', "backend engineer", {"field": "role"}) == 1.0
    assert SCORERS["json_field"]("not json", "x", {"field": "role"}) == 0.0
    assert _PROMPT_RE.search("junk <prompt>Answer {input}</prompt> more").group(1) == "Answer {input}"
    print("self-check: scorers + parser OK")


DEMO_TASK = Task(
    name="extract_role",
    description="From a short bio, return a JSON object {\"role\": <job title, lowercase>}.",
    seed_prompt="Extract info from this bio: {input}",          # under-specified on purpose
    scorer="json_field",
    scorer_config={"field": "role"},
    cases=[
        {"input": "Priya is a backend engineer at a fintech startup.", "expected": "backend engineer"},
        {"input": "Sam works as a product manager in Berlin.",         "expected": "product manager"},
        {"input": "Dr. Lee is a data scientist focused on NLP.",       "expected": "data scientist"},
    ],
    budget=5,
    patience=2,
)


def main() -> None:
    _self_check()
    print(f"\nbackend: {PROVIDER} · model: {MODEL}")
    print(f"seed prompt: {DEMO_TASK.seed_prompt!r}\n")
    try:
        result = optimize(DEMO_TASK, on_iteration=lambda it: print(
            f"  iter {it.n}: {it.mean_score:.0%}  ({sum(r.score >= 1 for r in it.results)}/{len(it.results)} cases)"
            + ("  *best*" if it.is_best else "")))
    except Exception as e:  # noqa: BLE001 — a missing backend shouldn't look like a code bug
        print(f"\n[!] Could not reach the '{PROVIDER}' backend: {e}\n"
              f"    Start Ollama (`ollama serve` + `ollama pull {MODEL}`) or set LOOPR_PROVIDER=openai.")
        return
    print(f"\nstop: {result.stop_reason} | seed {result.seed_score:.0%} → best {result.best_score:.0%}")
    print("\nbest prompt Loopr wrote:\n" + result.best_prompt)


if __name__ == "__main__":
    main()
