"""Loopr — a self-improving prompt-optimization loop (run -> score -> reflect -> rewrite).

This demo hands Loopr a deliberately under-specified seed prompt and 4 eval cases,
then lets it optimize the prompt itself until the outputs pass. Scoring and the
stop decision are deterministic and eval-gated; the LLM only runs the task and
phrases the reflection, so a run is reproducible given a fixed model.

Run:
    pip install -r requirements.txt
    python loopr_demo.py

Backend (Loopr is local-first — pick ONE):
    * Local, zero-cost:  `ollama serve` with a model pulled, e.g. `ollama pull qwen2.5:14b`
    * Cloud fallback:    export OPENAI_API_KEY=...   (or ANTHROPIC_API_KEY=...)
"""

from loopr import Task, optimize

# A task = a description, an under-specified seed prompt, a deterministic scorer,
# and a handful of eval cases. Loopr rewrites the seed prompt until the cases pass.
task = Task.from_dict(
    {
        "name": "yesno",
        "description": "Answer the question with exactly 'yes' or 'no', lowercase.",
        "seed_prompt": "Question: {input}",  # under-specified on purpose — scores poorly
        "scorer": "exact",                    # deterministic: output must equal expected
        "config": {"budget": 5, "patience": 2},
        "cases": [
            {"input": "Is the sky blue on a clear day?", "expected": "yes"},
            {"input": "Is 7 an even number?", "expected": "no"},
            {"input": "Do fish breathe air with lungs?", "expected": "no"},
            {"input": "Is water wet?", "expected": "yes"},
        ],
    }
)

print(f"seed prompt : {task.seed_prompt!r}\n")

result = optimize(
    task,
    on_iteration=lambda it: print(f"  iter {it.n}: {it.mean_score:.0%}"),
)

print(f"\nstop: {result.stop_reason} | seed {result.seed_score:.0%} -> best {result.best_score:.0%}")
print("\nbest prompt Loopr wrote:\n" + result.best_prompt)
