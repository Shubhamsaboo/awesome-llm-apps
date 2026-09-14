"""AI Coding Agent with Experience Memory and Subprocess Verification.

Drives code generation, test execution, iteration on failures, and memory persistence
using the official OpenAI SDK and real subprocess verification.
"""

from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any, Dict, List, Optional, Tuple

from memory import ExperienceMemory
from models import (
    ExperienceStatus,
    FailedAttempt,
    StructuredExperience,
    VerificationEvidence,
)
from verifier import ExecutionVerifier


class CodingAgent:
    """Agent that solves coding tasks, runs real tests, and persists verified experiences."""

    def __init__(
        self,
        client: Optional[Any] = None,
        model: Optional[str] = None,
        memory: Optional[ExperienceMemory] = None,
        verifier: Optional[ExecutionVerifier] = None,
    ):
        self.model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        self.memory = memory or ExperienceMemory()
        self.verifier = verifier or ExecutionVerifier()

        if client is not None:
            self.client = client
        else:
            api_key = os.environ.get("OPENAI_API_KEY")
            base_url = os.environ.get("OPENAI_BASE_URL")
            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY environment variable is not set.\n\n"
                    "Setup Instructions:\n"
                    "  1. Copy .env.example to .env: cp .env.example .env\n"
                    "  2. Add your key: OPENAI_API_KEY=sk-...\n"
                    "  3. (Optional) Set OPENAI_MODEL=gpt-4o-mini\n"
                )
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key, base_url=base_url)

    def extract_code(self, response_text: str) -> str:
        """Extract clean Python code from markdown fences or raw output."""
        pattern = r"```(?:python)?\s*\n(.*?)\n```"
        matches = re.findall(pattern, response_text, re.DOTALL | re.IGNORECASE)
        if matches:
            # Pick the largest python block (usually the complete implementation)
            return max(matches, key=len).strip()
        return response_text.strip()

    def generate_solution(
        self,
        task_description: str,
        starter_code: str,
        test_code: str,
        experience_context: Optional[str] = None,
        failure_feedback: Optional[str] = None,
    ) -> str:
        """Query LLM to generate a complete Python solution satisfying tests."""
        system_prompt = (
            "You are a principal software engineer and expert Python programmer. "
            "Your task is to write clean, complete, fully working Python code that passes "
            "all provided unit tests. Return ONLY valid, executable Python code enclosed "
            "in ```python ... ``` fences. Do not use ellipsis (...) or leave placeholder code."
        )

        user_content_blocks = [
            f"### TASK SPECIFICATION\n{task_description}\n",
            f"### STARTER / INTERFACE TEMPLATE\n```python\n{starter_code}\n```\n",
            f"### UNIT TESTS THAT MUST PASS\n```python\n{test_code}\n```\n",
        ]

        if experience_context:
            user_content_blocks.append(
                f"### RETRIEVED CROSS-SESSION EXPERIENCE & CONSTRAINTS\n"
                f"{experience_context}\n"
                f"CRITICAL: Follow the verified patterns above and STRICTLY AVOID the failed approaches listed under DO NOT REPEAT.\n"
            )

        if failure_feedback:
            user_content_blocks.append(
                f"### PREVIOUS ATTEMPT FAILED THE TEST RUN\n"
                f"The test runner returned the following failure output:\n"
                f"```\n{failure_feedback}\n```\n"
                f"Diagnose the error, fix the root cause, and provide the updated complete solution."
            )

        user_prompt = "\n".join(user_content_blocks)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )

        raw_content = response.choices[0].message.content or ""
        return self.extract_code(raw_content)

    def run_session(
        self,
        task_id: str,
        task_dir: Path,
        problem_filename: str = "problem.py",
        test_filename: str = "test_rate_limiter.py",
        use_memory: bool = False,
        max_attempts: int = 3,
        session_label: str = "Session",
    ) -> Dict[str, Any]:
        """Execute a complete agent session with real LLM generation and real test verification."""
        print(f"\n{'='*60}")
        print(f"🚀 Starting {session_label} for Task: {task_id}")
        print(f"   Memory Retrieval Enabled: {use_memory}")
        print(f"   Model: {self.model}")
        print(f"{'='*60}\n")

        task_desc_file = task_dir / "README.md"
        task_desc = task_desc_file.read_text(encoding="utf-8") if task_desc_file.exists() else f"Task: {task_id}"
        starter_file = task_dir / problem_filename
        starter_code = starter_file.read_text(encoding="utf-8")
        test_file = task_dir / test_filename
        test_code = test_file.read_text(encoding="utf-8")

        # Step 1: Memory Retrieval (if enabled)
        exp_context = ""
        retrieved_experiences: List[StructuredExperience] = []
        if use_memory and self.memory:
            retrieved_experiences = self.memory.retrieve_relevant(query=task_id)
            if retrieved_experiences:
                print(f"📦 Retrieved {len(retrieved_experiences)} verified experience(s) from persistent memory.")
                exp_context = self.memory.format_experience_context(retrieved_experiences)
                # Check for environment drift
                drift, msg = self.memory.check_environment_staleness(retrieved_experiences[0])
                if drift:
                    print(f"⚠️  Environment advisory: {msg}")
            else:
                print("ℹ️  No prior verified experiences found in memory.")
        else:
            print("ℹ️  Running with zero prior experience context (cold start).")

        # Prepare isolated sandbox directory for test execution
        sandbox_dir = Path(tempfile.mkdtemp(prefix=f"agent_{task_id}_"))
        sandbox_target = sandbox_dir / problem_filename
        sandbox_test = sandbox_dir / test_filename
        shutil.copy2(test_file, sandbox_test)

        evidences: List[VerificationEvidence] = []
        current_feedback: Optional[str] = None
        solved = False
        final_solution = ""

        try:
            for attempt in range(1, max_attempts + 1):
                print(f"🔄 Attempt {attempt}/{max_attempts}: Querying real LLM...")
                solution_code = self.generate_solution(
                    task_description=task_desc,
                    starter_code=starter_code,
                    test_code=test_code,
                    experience_context=exp_context,
                    failure_feedback=current_feedback,
                )

                print(f"🧪 Attempt {attempt}/{max_attempts}: Executing pytest in isolated subprocess...")
                evidence = self.verifier.verify_solution(
                    solution_code=solution_code,
                    target_file=sandbox_target,
                    test_file=sandbox_test,
                    work_dir=sandbox_dir,
                )
                evidences.append(evidence)

                print(
                    f"   Result: Exit Code {evidence.exit_code} | "
                    f"Passed: {evidence.tests_passed} | Failed: {evidence.tests_failed} | "
                    f"Duration: {evidence.duration_seconds}s"
                )

                if evidence.passed:
                    print(f"✅ Attempt {attempt} PASSED all verification tests!")
                    solved = True
                    final_solution = solution_code

                    # Record verified experience into memory
                    if self.memory:
                        lessons = [
                            f"Verified against tests in {test_filename}",
                            "Used sliding window queue pruning to prevent boundary burst overflows.",
                        ]
                        saved_exp = self.memory.promote_to_verified(
                            task_id=task_id,
                            solution=solution_code,
                            evidence=evidence,
                            lessons_learned=lessons,
                        )
                        print(f"💾 Promoted experience `{saved_exp.id}` to status: VERIFIED in persistent storage.")
                    break
                else:
                    print(f"❌ Attempt {attempt} FAILED verification.")
                    # Extract concise failure diagnostic
                    fail_summary = self._extract_failure_summary(evidence)
                    print(f"   Failure Diagnostic:\n   {fail_summary}")

                    # Retain failed attempt as negative constraint ("DO NOT REPEAT")
                    if self.memory:
                        self.memory.record_failed_attempt(
                            task_id=task_id,
                            attempt=FailedAttempt(
                                attempt_number=attempt,
                                approach_summary=f"Approach generated in attempt {attempt}",
                                error_message=fail_summary,
                                failure_reason="Pytest assertion failed during boundary or capacity check",
                                code_snippet=solution_code[:300] + "...",
                            ),
                        )
                        print("📝 Captured failed approach into memory under 'DO NOT REPEAT' constraints.")

                    current_feedback = (
                        f"Exit code: {evidence.exit_code}\n"
                        f"Stdout summary:\n{evidence.stdout[-600:] if evidence.stdout else 'None'}\n"
                        f"Stderr:\n{evidence.stderr[-300:] if evidence.stderr else 'None'}"
                    )

            return {
                "task_id": task_id,
                "session_label": session_label,
                "solved": solved,
                "attempts_count": len(evidences),
                "evidences": evidences,
                "memory_used": use_memory,
                "final_solution": final_solution,
            }

        finally:
            shutil.rmtree(sandbox_dir, ignore_errors=True)

    @staticmethod
    def _extract_failure_summary(evidence: VerificationEvidence) -> str:
        """Extract the most relevant assertion failure line from pytest output."""
        output = evidence.stdout + "\n" + evidence.stderr
        failures = []
        for line in output.splitlines():
            line_s = line.strip()
            if line_s.startswith("E   ") or "AssertionError" in line_s or "FAILED" in line_s:
                failures.append(line_s)
        if failures:
            return "\n   ".join(failures[:4])
        return output[-300:].strip() if output else "Unknown failure"
