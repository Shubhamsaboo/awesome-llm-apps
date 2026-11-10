#!/usr/bin/env python3
"""
Minimal entry point: train and evaluate NeuroMAS on one benchmark.

Progressive growth is built in: requesting --size 7 trains NeuroMAS-3, grows it
to NeuroMAS-5, then to NeuroMAS-7, and reports the accuracy of every stage.

Examples
--------
  # Fast smoke test (tiny budgets, just verifies the pipeline end to end)
  SMOKE=1 python run.py --task navigate --size 3

  # Train NeuroMAS-3 on ARC-Challenge
  python run.py --task arc --size 3

  # Full progressive growth (3 -> 5 -> 7) on Algebra
  python run.py --task algebra --size 7

Results accumulate in results/results.json across runs.
"""
import os, sys, json, argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Smoke mode: shrink every budget BEFORE importing config-dependent modules.
if os.environ.get("SMOKE"):
    os.environ.setdefault("STEPS_NM_P1", "6")
    os.environ.setdefault("STEPS_NM_P2", "4")
    os.environ.setdefault("STEPS_NM_P3", "4")
    os.environ.setdefault("EVAL_SIZE", "8")
    os.environ.setdefault("TRAIN_SIZE", "16")
    os.environ.setdefault("DEV_SIZE", "4")
    os.environ.setdefault("DEV_EVAL_N", "4")
    os.environ.setdefault("CKPT_EVERY", "4")
    os.environ.setdefault("TOK_MCQ_INNER", "48")
    os.environ.setdefault("TOK_MCQ_OUTER", "24")
    os.environ.setdefault("TOK_CODE_INNER", "64")
    os.environ.setdefault("TOK_CODE_OUTER", "96")

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
RESULTS_PATH = os.path.join(RESULTS_DIR, "results.json")

TASK_CHOICES = ["arc", "navigate", "algebra", "physics", "medicine", "humaneval"]


def load_results():
    if os.path.exists(RESULTS_PATH):
        with open(RESULTS_PATH) as f:
            return json.load(f)
    return {}


def save_results(res):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        json.dump(res, f, indent=2)


def main():
    ap = argparse.ArgumentParser(description="Train and evaluate NeuroMAS on one benchmark.")
    ap.add_argument("--task", required=True, choices=TASK_CHOICES,
                    help="benchmark to train and evaluate on")
    ap.add_argument("--size", type=int, default=7, choices=[3, 5, 7],
                    help="largest NeuroMAS stage to grow to (LLM calls per query)")
    args = ap.parse_args()

    # Heavy imports are deferred so --help works without the GPU stack installed.
    import config
    from tasks import TASKS
    from engine import run_neuromas

    task = TASKS[args.task]
    device = config.device()
    print(f"Task: {args.task} | up to NeuroMAS-{args.size} | device: {device}"
          f"{' | SMOKE' if os.environ.get('SMOKE') else ''}")

    out = run_neuromas(task, device, up_to=args.size)

    res = load_results()
    for stage, acc in out.items():                     # neuromas3 / neuromas5 / neuromas7
        res.setdefault(stage, {})[args.task] = acc
    save_results(res)

    print("\nResults:")
    for stage, acc in out.items():
        print(f"  {stage:10s} {args.task}: {acc * 100:.1f}%")
    print(f"\nSaved to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
