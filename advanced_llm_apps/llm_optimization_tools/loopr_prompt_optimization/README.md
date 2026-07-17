# 🔁 Loopr — Self-Improving Prompt Optimization

**Stop hand-tuning prompts.** Give Loopr a task, an under-specified seed prompt, and a
handful of eval cases. It runs the prompt, scores the outputs, **reflects on the failures
in plain language, rewrites the prompt, and repeats** — until the outputs pass. It answers
the question every LLM developer asks by hand — *"which prompt actually works best for this
task?"* — automatically, as a loop.

The entire optimizer is **one self-contained file** ([`loopr_prompt_optimization.py`](loopr_prompt_optimization.py))
with **zero third-party dependencies** — read it top to bottom in a few minutes. It's
**local-first**: runs offline on [Ollama](https://ollama.com) at zero per-token cost, with
an OpenAI fallback.

---

## 📋 How it works

```
        ┌──────────────────────────── the loop ────────────────────────────┐
        │                                                                    │
  seed prompt ─▶ RUN on each case ─▶ SCORE (deterministic) ─▶ best? keep it  │
        ▲                                     │                              │
        │                                     ▼                              │
        └──── REWRITE prompt ◀── REFLECT on the failures (LLM) ◀─────────────┘

  stop when: score hits target (converged) · no improvement for N iters (plateau) · budget spent
```

The key idea (a lightweight take on [GEPA](https://arxiv.org/abs/2507.19457), ICLR 2026):
the LLM only (a) runs the candidate prompt and (b) phrases the reflection. **Scoring,
best-tracking, and the stop decision are pure Python** — so a run is reproducible for a
fixed model, and a bad reflection can never silently corrupt the state (an unparseable
rewrite is scored as a no-op step and discarded).

---

## 🚀 Features

- ✅ **Self-contained** — the whole reflect-and-rewrite loop is in one readable file, stdlib only.
- ✅ **Deterministic & reproducible** — 4 built-in scorers (`exact`, `contains`, `regex`, `json_field`); the pass/fail signal never depends on the LLM's mood.
- ✅ **Local-first** — runs on Ollama offline; set `LOOPR_PROVIDER=openai` for a cloud fallback (also dependency-free, via `urllib`).
- ✅ **Tasks as data** — a `Task` is just a description, a seed prompt, a scorer, and a list of `{input, expected}` cases.

---

## 📦 Installation

No dependencies to install — Python 3.10+ standard library only. Just pick a backend:

```bash
# Local, zero-cost (recommended)
ollama serve
ollama pull qwen2.5:14b

# ...or a cloud fallback
export LOOPR_PROVIDER=openai
export OPENAI_API_KEY='your-key'
```

---

## 💻 Usage

Run the included demo (extraction task — turns a vague seed prompt into a strict JSON extractor):

```bash
python loopr_prompt_optimization.py
```

**Real output** (local `qwen2.5:14b` via Ollama):

```
self-check: scorers + parser OK

backend: ollama · model: qwen2.5:14b
seed prompt: 'Extract info from this bio: {input}'

  iter 0: 0%    (0/3 cases)  *best*
  iter 1: 100%  (3/3 cases)  *best*

stop: converged | seed 0% → best 100%

best prompt Loopr wrote:
Given a short bio, extract only the job title in lowercase and return it as a
JSON object {"role": <job title>}. Do not include any additional information
such as location or industry.
{input}
```

The seed prompt produced no parseable JSON (0%). Loopr read the failures, diagnosed the
missing format constraint, and **rewrote the prompt itself** — hitting 100% in one iteration.

### Optimize your own task

```python
from loopr_prompt_optimization import Task, optimize

task = Task(
    name="yesno",
    description="Answer with exactly 'yes' or 'no', lowercase.",
    seed_prompt="Question: {input}",          # under-specified on purpose
    scorer="exact",
    cases=[
        {"input": "Is the sky blue on a clear day?", "expected": "yes"},
        {"input": "Is 7 an even number?",            "expected": "no"},
    ],
)

result = optimize(task, on_iteration=lambda it: print(f"iter {it.n}: {it.mean_score:.0%}"))
print(result.best_prompt)      # the prompt Loopr rewrote for you
```

---

## 🧩 Code tour

The single file is organized in five short sections:

| Section | What it does |
|---|---|
| **1. LLM backend** | `call_llm()` — one function, hits Ollama or OpenAI over `urllib` |
| **2. Scorers** | `SCORERS` — deterministic pass/fail in `[0,1]` (this is what makes runs reproducible) |
| **3. Task & reflection** | `Task` dataclass + `reflect_and_rewrite()` — the GEPA-style diagnose-then-rewrite step |
| **4. The loop** | `evaluate()` + `optimize()` — score, track best, stop-check, reflect, repeat |
| **5. Demo + self-check** | `_self_check()` (offline assertions) and a runnable `main()` |

---

## 📊 Why reflective optimization

[**GEPA**](https://arxiv.org/abs/2507.19457) (ICLR 2026) is the technique this tutorial follows in miniature. Its published results:

| Metric | Result |
|---|---|
| vs. RL (GRPO) | **+20%** with **35× fewer rollouts** |
| MATH accuracy (instruction refinement only) | **67% → 93%** |
| Fine-tuning / few-shot examples required | **None** |

---

## 🎯 Best use cases

- 📤 Extraction prompts (JSON / structured output) that keep drifting off-format.
- 🏷️ Classification / intent / sentiment prompts you tune by trial and error.
- ✅ Any task with a **checkable** answer (exact match, regex, a JSON field).

---

## 🔗 Resources

- [GEPA paper (arXiv:2507.19457)](https://arxiv.org/abs/2507.19457) — the reflective-evolution method this follows.
- A fuller version of this idea (CLI, web UI, YAML tasks, more scorers) lives at [github.com/rohitguta2432/loopr](https://github.com/rohitguta2432/loopr).

---

## 📄 License

MIT.
