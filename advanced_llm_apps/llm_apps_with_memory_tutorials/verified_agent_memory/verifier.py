"""Execution Verifier for AI Coding Agent.

Runs real tests and commands using isolated subprocesses, parses exit codes
and test results, and builds formal VerificationEvidence.
"""

from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import List, Optional, Tuple

from models import VerificationEvidence


class ExecutionVerifier:
    """Safely executes code and tests in subprocesses to collect real verification evidence."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def run_command(
        self,
        command: List[str],
        cwd: Optional[Path] = None,
        env: Optional[dict] = None,
    ) -> VerificationEvidence:
        """Run an arbitrary command list safely via subprocess and extract evidence."""
        start_time = time.perf_counter()
        timestamp = datetime.now(timezone.utc).isoformat()
        cmd_str = " ".join(command)

        run_env = os.environ.copy()
        if env:
            run_env.update(env)
        # Ensure python path includes cwd so imports work seamlessly
        if cwd:
            existing_pp = run_env.get("PYTHONPATH", "")
            run_env["PYTHONPATH"] = f"{cwd}{os.pathsep}{existing_pp}" if existing_pp else str(cwd)

        try:
            result = subprocess.run(
                command,
                cwd=str(cwd) if cwd else None,
                env=run_env,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            duration = time.perf_counter() - start_time
            exit_code = result.returncode
            stdout = result.stdout or ""
            stderr = result.stderr or ""
        except subprocess.TimeoutExpired as err:
            duration = time.perf_counter() - start_time
            exit_code = -1
            stdout = (err.stdout.decode() if isinstance(err.stdout, bytes) else str(err.stdout)) if err.stdout else ""
            stderr = f"Execution timed out after {self.timeout} seconds."
        except Exception as err:
            duration = time.perf_counter() - start_time
            exit_code = -2
            stdout = ""
            stderr = f"Execution failed to launch: {str(err)}"

        passed = (exit_code == 0)
        tests_passed, tests_failed = self._parse_pytest_counts(stdout + "\n" + stderr)

        return VerificationEvidence(
            command=cmd_str,
            exit_code=exit_code,
            passed=passed,
            stdout=stdout,
            stderr=stderr,
            duration_seconds=round(duration, 3),
            timestamp=timestamp,
            tests_passed=tests_passed,
            tests_failed=tests_failed,
        )

    def run_pytest(
        self,
        test_file: Path,
        cwd: Optional[Path] = None,
        extra_args: Optional[List[str]] = None,
    ) -> VerificationEvidence:
        """Run pytest against a specified test file."""
        cmd = [sys.executable, "-m", "pytest", str(test_file), "-v"]
        if extra_args:
            cmd.extend(extra_args)
        return self.run_command(cmd, cwd=cwd or test_file.parent)

    def verify_solution(
        self,
        solution_code: str,
        target_file: Path,
        test_file: Path,
        work_dir: Optional[Path] = None,
    ) -> VerificationEvidence:
        """Write proposed solution code to target file and execute pytest."""
        effective_work_dir = work_dir or target_file.parent
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(solution_code, encoding="utf-8")

        return self.run_pytest(test_file=test_file, cwd=effective_work_dir)

    @staticmethod
    def _parse_pytest_counts(output: str) -> Tuple[int, int]:
        """Extract passed and failed test counts from pytest stdout."""
        passed = 0
        failed = 0

        # Look for standard pytest summary: e.g. "4 passed, 1 failed in 0.12s"
        pass_match = re.search(r"(\d+)\s+passed", output)
        if pass_match:
            passed = int(pass_match.group(1))

        fail_match = re.search(r"(\d+)\s+failed", output)
        if fail_match:
            failed = int(fail_match.group(1))

        return passed, failed
