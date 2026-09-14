"""Main demonstration runner for Verified Agent Memory.

Demonstrates cross-session learning using real OpenAI LLM calls and real subprocess test runs:
- Session 1: Solves task from scratch, iterates on real test failures, stores verified solution + "DO NOT REPEAT" constraints.
- Session 2: Completely fresh agent (zero conversation history) retrieves structured memory and succeeds directly.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
import time

from dotenv import load_dotenv

# Load .env file if available
load_dotenv()

from agent import CodingAgent
from memory import ExperienceMemory
from verifier import ExecutionVerifier


def check_api_key_or_exit() -> None:
    """Validate that OPENAI_API_KEY is configured; exit with clear instructions if missing."""
    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL")
    if not api_key:
        print("\n" + "=" * 70, file=sys.stderr)
        print("❌ Error: OPENAI_API_KEY environment variable is not set.", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        print("\nThis application requires a real LLM for code generation and verification.", file=sys.stderr)
        print("To run the application, configure your environment:\n", file=sys.stderr)
        print("  1. Copy the example configuration:", file=sys.stderr)
        print("     cp .env.example .env\n", file=sys.stderr)
        print("  2. Edit .env and enter your OpenAI API key:", file=sys.stderr)
        print("     OPENAI_API_KEY=sk-...\n", file=sys.stderr)
        print("  3. (Optional) Select a model (default: gpt-4o-mini):", file=sys.stderr)
        print("     OPENAI_MODEL=gpt-4o-mini\n", file=sys.stderr)
        print("  4. (Optional) For OpenAI-compatible local/custom providers:", file=sys.stderr)
        print("     OPENAI_BASE_URL=https://your-custom-endpoint/v1\n", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Verified Agent Memory: Cross-Session Learning Demo")
    parser.add_argument(
        "--db-path",
        type=str,
        default="agent_experiences.db",
        help="Path to persistent SQLite database file (default: agent_experiences.db)",
    )
    parser.add_argument(
        "--task",
        type=str,
        default="rate_limiter",
        help="Task directory inside tasks/ to execute (default: rate_limiter)",
    )
    parser.add_argument(
        "--session",
        choices=["1", "2", "all"],
        default="all",
        help="Run Session 1 (cold start learning), Session 2 (fresh agent + memory), or all (default: all)",
    )
    parser.add_argument(
        "--inspect",
        action="store_true",
        help="Inspect existing stored experiences in the SQLite database and exit",
    )
    parser.add_argument(
        "--clean-db",
        action="store_true",
        help="Remove existing memory database before running demo",
    )
    args = parser.parse_args()

    db_file = Path(args.db_path)

    # If user requests inspection only, read DB and exit
    if args.inspect:
        if not db_file.exists():
            print(f"No database found at {db_file}")
            sys.exit(0)
        mem = ExperienceMemory(db_path=db_file)
        exp = mem.get_experience_by_task(args.task)
        if not exp:
            print(f"No experience found for task: {args.task}")
            sys.exit(0)
        print("\n" + "=" * 60)
        print(f"📦 INSPECTING PERSISTENT MEMORY (Task: {exp.task_id})")
        print("=" * 60)
        print(f"ID: {exp.id}")
        print(f"Status: {exp.status.value.upper()} (is_verified={exp.is_verified()})")
        print(f"Lessons Learned: {exp.lessons_learned}")
        print(f"Failed Approaches Retained: {len(exp.failed_approaches)}")
        for fa in exp.failed_approaches:
            print(f"  - Attempt #{fa.attempt_number}: {fa.approach_summary}")
            print(f"    Diagnostic: {fa.error_message}")
        if exp.verification_evidence:
            print(f"Verification Evidence:")
            print(f"  Command: {exp.verification_evidence.command}")
            print(f"  Exit Code: {exp.verification_evidence.exit_code}")
            print(f"  Passed: {exp.verification_evidence.passed}")
            print(f"  Tests: {exp.verification_evidence.tests_passed} passed, {exp.verification_evidence.tests_failed} failed")
        print("=" * 60)
        sys.exit(0)

    # Validate API key for agent execution
    check_api_key_or_exit()

    db_file = Path(args.db_path)
    if args.clean_db and db_file.exists():
        db_file.unlink()
        print(f"🧹 Cleaned existing database: {db_file}")

    memory = ExperienceMemory(db_path=db_file)
    verifier = ExecutionVerifier(timeout=30)

    task_dir = Path(__file__).parent / "tasks" / args.task
    if not task_dir.exists():
        print(f"❌ Error: Task directory not found at {task_dir}", file=sys.stderr)
        sys.exit(1)

    print("\n" + "#" * 70)
    print("🧠 VERIFIED AGENT MEMORY: CROSS-SESSION DEMONSTRATION")
    print("   Architecture: Real LLM + Subprocess Pytest Verification + Durable Memory")
    print("#" * 70)

    # -------------------------------------------------------------------------
    # SESSION 1: Learning Loop from Scratch (Cold Start)
    # -------------------------------------------------------------------------
    session1_result = None
    session1_duration = 0.0

    if args.session in ["1", "all"]:
        print("\n" + "-" * 70)
        print("▶️  SESSION 1: Solving Task from Scratch (Cold Start)")
        print("    - Memory Retrieval: DISABLED (No prior knowledge)")
        print("    - Goal: Discover solution, observe test feedback, capture failed attempts")
        print("-" * 70)

        session1_agent = CodingAgent(
            memory=memory,
            verifier=verifier,
        )

        t0 = time.perf_counter()
        session1_result = session1_agent.run_session(
            task_id=args.task,
            task_dir=task_dir,
            problem_filename="problem.py",
            test_filename="test_rate_limiter.py",
            use_memory=False,
            max_attempts=3,
            session_label="Session 1 (Cold Start)",
        )
        session1_duration = time.perf_counter() - t0

        print("\n" + "=" * 70)
        print("🏁 SESSION 1 COMPLETED")
        print(f"   Success: {session1_result['solved']}")
        print(f"   Attempts Required: {session1_result['attempts_count']}")
        print(f"   Total Duration: {session1_duration:.2f}s")
        print("=" * 70)

        # Inter-session inspection
        print("\n" + "." * 70)
        print("🔍 Inspecting Persistent SQLite Memory after Session 1:")
        stored_exp = memory.get_experience_by_task(args.task)
        if stored_exp:
            print(f"   Experience ID: {stored_exp.id}")
            print(f"   Status: {stored_exp.status.value.upper()}")
            print(f"   Failed attempts retained ('DO NOT REPEAT'): {len(stored_exp.failed_approaches)}")
            for fa in stored_exp.failed_approaches:
                print(f"     - Attempt #{fa.attempt_number}: {fa.error_message}")
            if stored_exp.verification_evidence:
                print(f"   Verification command: {stored_exp.verification_evidence.command}")
                print(f"   Verification exit code: {stored_exp.verification_evidence.exit_code}")
        print("." * 70)

        print("\n" + "-" * 70)
        print("🔄 DESTROYING SESSION 1 AGENT INSTANCE...")
        del session1_agent
        print("   Session 1 context, scratch variables, and conversation transcripts purged.")
        print("-" * 70)

    # -------------------------------------------------------------------------
    # SESSION 2: Experience Transfer with Fresh Agent Session
    # -------------------------------------------------------------------------
    session2_result = None
    session2_duration = 0.0

    if args.session in ["2", "all"]:
        print("\n" + "-" * 70)
        print("▶️  SESSION 2: Fresh Agent Session with Memory Retrieval")
        print("    - Memory Retrieval: ENABLED (Structured Prior Lessons & Negative Constraints)")
        print("    - Conversation Transcript: NONE (Zero chat memory carried over)")
        print("    - Goal: Utilize verified pattern and avoid previously failed dead ends")
        print("-" * 70)

        # Initialize brand-new agent instance with NO conversation state
        session2_agent = CodingAgent(
            memory=memory,
            verifier=verifier,
        )

        t1 = time.perf_counter()
        session2_result = session2_agent.run_session(
            task_id=args.task,
            task_dir=task_dir,
            problem_filename="problem.py",
            test_filename="test_rate_limiter.py",
            use_memory=True,
            max_attempts=3,
            session_label="Session 2 (With Experience Memory)",
        )
        session2_duration = time.perf_counter() - t1

    # -------------------------------------------------------------------------
    # FINAL COMPARATIVE TRACE (ACTUAL MEASURED EXECUTION)
    # -------------------------------------------------------------------------
    if session1_result and session2_result:
        print("\n" + "=" * 70)
        print("📊 EXECUTION TRACE & RUNTIME COMPARISON (MEASURED RUN)")
        print("=" * 70)
        print(f"{'Metric':<35} | {'Session 1 (Cold Start)':<20} | {'Session 2 (With Memory)':<20}")
        print("-" * 81)
        print(
            f"{'Task Solved':<35} | "
            f"{'YES' if session1_result['solved'] else 'NO':<20} | "
            f"{'YES' if session2_result['solved'] else 'NO':<20}"
        )
        print(
            f"{'Total Attempts to Verification':<35} | "
            f"{session1_result['attempts_count']:<20} | "
            f"{session2_result['attempts_count']:<20}"
        )
        print(
            f"{'Total Wall-Clock Time':<35} | "
            f"{session1_duration:<20.2f}s | "
            f"{session2_duration:<20.2f}s"
        )
        stored_exp = memory.get_experience_by_task(args.task)
        print(
            f"{'Memory Retrieval Used':<35} | "
            f"{'None':<20} | "
            f"{'Retrieved Prior Experience':<20}"
        )
        print(
            f"{'Negative Constraints Injected':<35} | "
            f"{'None':<20} | "
            f"{f'{len(stored_exp.failed_approaches)} DO NOT REPEAT rules' if stored_exp else '0':<20}"
        )
        print("=" * 70)
    print("✅ Done.\n")


if __name__ == "__main__":
    main()
