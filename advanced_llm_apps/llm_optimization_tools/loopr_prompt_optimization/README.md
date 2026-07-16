# 🔁 Loopr — Self-Improving Prompt Optimization

**Stop hand-tuning prompts.** Give Loopr a task prompt and a handful of eval cases. It runs the prompt, scores the outputs, reflects on the failures in plain language, rewrites the prompt, and repeats — until it converges on the best-performing version. It answers the question every LLM developer keeps asking by hand — *"which prompt actually works best for this task?"* — automatically, as a loop.

Loopr is **local-first**: one `pip install`, runs offline on [Ollama](https://ollama.com) at zero per-token cost, with a cloud key as an optional fallback. No account, no dashboard, no hosted infra.

---

## 📋 Overview

Prompt/agent **evaluation** is one of the fastest-growing developer-tool categories, and the technique that wins is **reflective evolution**, not gradient methods. Loopr is the lightweight, local version of that idea — a drop-in self-improving prompt loop instead of a platform you have to adopt.

```
        ┌──────────────────────────── the loop ────────────────────────────┐
        │                                                                    │
  seed prompt ─▶ RUN on each case ─▶ SCORE (deterministic) ─▶ best? keep it  │
        ▲                                     │                              │
        │                                     ▼                              │
        └──── REWRITE prompt ◀── REFLECT on the failures (LLM, GEPA-lite) ◀──┘

  stop when: score hits target (converged) · no improvement for N iters (plateau) · budget spent
```

### Key Benefits

- ✅ **Deterministic & reproducible** — scoring and the stop decision are eval-gated; the LLM only runs the task and phrases the reflection.
- ✅ **Local-first, zero cost** — runs on Ollama offline; cloud (OpenAI / Anthropic) is an optional fallback.
- ✅ **No platform to adopt** — a `pip install` and a dict/YAML file, not an eval SaaS account.
- ✅ **Reflective evolution** — improves prompts by reading their own failures, the GEPA-style approach that beats RL.

---

## 🚀 Features

- **11 built-in scorers** — `exact`, `contains`, `regex`, `json_field`, `field`, `pattern`, `sentiment`, `llm_judge`, `rubric`, and more.
- **Pluggable backends** — Ollama (default), OpenAI, or Anthropic, auto-detected.
- **CLI + Python API + web UI** — `loopr run task.yaml`, `from loopr import optimize`, or `loopr serve` to watch it converge live in the browser.
- **Tasks as data** — define a task in a dict or a YAML file (`name`, `seed_prompt`, `scorer`, `cases`).
- **Traceable** — every run writes the best prompt and a full JSON trace to `loopr-out/`.

---

## 📦 Installation

1. Install the tool (pulls the `loopr` package and its only runtime dependency, `pyyaml`):

   ```bash
   cd loopr_prompt_optimization/
   pip install -r requirements.txt
   ```

2. Pick a backend — Loopr is local-first, so choose **one**:

   ```bash
   # Local, zero-cost (recommended)
   ollama serve
   ollama pull qwen2.5:14b

   # ...or a cloud fallback
   export OPENAI_API_KEY='your-key'      # or ANTHROPIC_API_KEY
   ```

---

## 💻 Usage

Run the included demo:

```bash
python loopr_demo.py
```

### Basic Example

```python
from loopr import Task, optimize

task = Task.from_dict({
    "name": "yesno",
    "description": "Answer with exactly 'yes' or 'no', lowercase.",
    "seed_prompt": "Question: {input}",   # under-specified on purpose
    "scorer": "exact",
    "config": {"budget": 5, "patience": 2},
    "cases": [
        {"input": "Is the sky blue on a clear day?", "expected": "yes"},
        {"input": "Is 7 an even number?", "expected": "no"},
    ],
})

result = optimize(task, on_iteration=lambda it: print(f"iter {it.n}: {it.mean_score:.0%}"))
print(result.best_prompt)
```

### A real converge run

```
🔁 loopr · optimizing 'extract_contact' (scorer=json_field, budget=5, cases=4)

  iter 0: ························    0%  (0/4 cases) *best*
  iter 1: ████████████████████████  100%  (4/4 cases) *best*

✅ stop: converged  |  seed 0% → best 100% (+100%, iter 1)
```

The seed prompt — *"Extract info from this bio."* — produced no parseable JSON (0%). Loopr read the failures, diagnosed the missing format constraint, and rewrote the prompt itself to include a schema and a worked example — hitting 100% in one iteration. (Local `qwen2.5:14b` via Ollama.)

---

## 📊 Why Reflective Optimization Wins

[**GEPA**](https://arxiv.org/abs/2507.19457) (DSPy's reflective prompt optimizer) is the technique Loopr follows in miniature. Its published results:

| Metric | Result |
|---|---|
| vs. RL (GRPO) | **+20%** with **35× fewer rollouts** |
| MATH accuracy (instruction refinement only) | **67% → 93%** |
| Fine-tuning required | **None** |
| Few-shot examples required | **None** |

Loopr brings that reflect-and-rewrite loop to a single local `pip install`.

---

## 🎯 Best Use Cases

- 📤 Extraction prompts (JSON / structured output) that keep drifting off-format.
- 🏷️ Classification / intent / sentiment prompts you tune by trial and error.
- ✅ Any task with a **checkable** answer (exact match, regex, a JSON field, a rubric).
- 🔒 Offline / private workloads where sending prompts to a SaaS eval platform is a non-starter.

---

## 🔗 Resources

- **Repository:** https://github.com/rohitguta2432/loopr
- **Homepage:** https://rohitraj.tech/agents
- **GEPA paper:** https://arxiv.org/abs/2507.19457

---

## 🤝 Contributing

Issues and PRs welcome on the [Loopr repo](https://github.com/rohitguta2432/loopr). New scorers and backends are the easiest first contributions.

---

## 📄 License

MIT — see the [Loopr repository](https://github.com/rohitguta2432/loopr).

---

## 🙏 Credits

Built by [Rohit Raj](https://rohitraj.tech). Reflective-evolution approach inspired by [GEPA](https://arxiv.org/abs/2507.19457) (DSPy).
