"""Reproducible Benchmark Harness for Verified Agent Memory.

Runs controlled trials comparing agent performance with and without experience memory.
Executes real LLM calls and real subprocess tests; records actual empirical results.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import time
from typing import Any, Dict, List

from dotenv import load_dotenv

load_dotenv()

from agent import CodingAgent
from memory import ExperienceMemory
from verifier import ExecutionVerifier


def run_benchmark_trials(
    task_name: str,
    trials: int = 3,
    output_file: str = "benchmark_results.json",
) -> Dict[str, Any]:
    """Execute benchmark trials across cold-start and memory-assisted conditions."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY environment variable is required to run benchmarks.", file=sys.stderr)
        sys.exit(1)

    task_dir = Path(__file__).parent / "tasks" / task_name
    if not task_dir.exists():
        raise FileNotFoundError(f"Task directory not found: {task_dir}")

    db_path = Path("benchmark_temp_memory.db")
    if db_path.exists():
        db_path.unlink()

    memory = ExperienceMemory(db_path=db_path)
    verifier = ExecutionVerifier(timeout=30)

    results: Dict[str, Any] = {
        "task": task_name,
        "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        "trials_requested": trials,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "cold_start_runs": [],
        "memory_assisted_runs": [],
    }

    print(f"\n🧪 Starting Benchmark on Task: {task_name} ({trials} trials)")
    print(f"   Model: {results['model']}\n")

    # Phase 1: Cold start trials (No prior memory)
    print("--- Phase 1: Cold Start Trials (No Memory) ---")
    for i in range(1, trials + 1):
        print(f"Trial {i}/{trials} [Cold Start]...")
        agent = CodingAgent(memory=None, verifier=verifier)
        t0 = time.perf_counter()
        res = agent.run_session(
            task_id=task_name,
            task_dir=task_dir,
            problem_filename="problem.py",
            test_filename="test_rate_limiter.py",
            use_memory=False,
            session_label=f"Cold-Start Trial {i}",
        )
        duration = time.perf_counter() - t0
        results["cold_start_runs"].append({
            "trial": i,
            "solved": res["solved"],
            "attempts": res["attempts_count"],
            "duration_seconds": round(duration, 2),
        })

    # Prime memory by running a session that populates memory
    print("\n--- Priming Experience Memory with Verified Solution ---")
    primer_agent = CodingAgent(memory=memory, verifier=verifier)
    primer_agent.run_session(
        task_id=task_name,
        task_dir=task_dir,
        problem_filename="problem.py",
        test_filename="test_rate_limiter.py",
        use_memory=False,
        session_label="Memory Primer",
    )

    # Phase 2: Memory-assisted trials (Fresh agents with memory retrieval)
    print("\n--- Phase 2: Memory-Assisted Trials (Fresh Agents + Memory) ---")
    for i in range(1, trials + 1):
        print(f"Trial {i}/{trials} [With Memory]...")
        agent = CodingAgent(memory=memory, verifier=verifier)
        t0 = time.perf_counter()
        res = agent.run_session(
            task_id=task_name,
            task_dir=task_dir,
            problem_filename="problem.py",
            test_filename="test_rate_limiter.py",
            use_memory=True,
            session_label=f"Memory-Assisted Trial {i}",
        )
        duration = time.perf_counter() - t0
        results["memory_assisted_runs"].append({
            "trial": i,
            "solved": res["solved"],
            "attempts": res["attempts_count"],
            "duration_seconds": round(duration, 2),
        })

    # Summary calculations
    def avg(lst: List[float]) -> float:
        return round(sum(lst) / len(lst), 2) if lst else 0.0

    cold_attempts = [r["attempts"] for r in results["cold_start_runs"]]
    mem_attempts = [r["attempts"] for r in results["memory_assisted_runs"]]
    cold_durations = [r["duration_seconds"] for r in results["cold_start_runs"]]
    mem_durations = [r["duration_seconds"] for r in results["memory_assisted_runs"]]

    results["summary"] = {
        "cold_start_avg_attempts": avg(cold_attempts),
        "memory_assisted_avg_attempts": avg(mem_attempts),
        "cold_start_avg_duration_s": avg(cold_durations),
        "memory_assisted_avg_duration_s": avg(mem_durations),
    }

    out_path = Path(output_file)
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\n📊 Benchmark results written to {out_path.resolve()}")
    print(f"   Cold Start Avg Attempts: {results['summary']['cold_start_avg_attempts']}")
    print(f"   Memory Assisted Avg Attempts: {results['summary']['memory_assisted_avg_attempts']}")

    if db_path.exists():
        db_path.unlink()

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run reproducible agent memory benchmarks.")
    parser.add_argument("--task", type=str, default="rate_limiter", help="Task name")
    parser.add_argument("--trials", type=int, default=2, help="Number of trials per condition")
    parser.add_argument("--output", type=str, default="benchmark_results.json", help="Output JSON path")
    args = parser.parse_args()
    run_benchmark_trials(task_name=args.task, trials=args.trials, output_file=args.output)
