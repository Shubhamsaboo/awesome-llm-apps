"""Unit tests for ExecutionVerifier subprocess execution and pytest parsing."""

from pathlib import Path
import sys
import tempfile
import pytest

from verifier import ExecutionVerifier


def test_verifier_successful_command():
    verifier = ExecutionVerifier(timeout=5)
    evidence = verifier.run_command([sys.executable, "-c", "print('Antigravity Verifier OK')"])

    assert evidence.exit_code == 0
    assert evidence.passed is True
    assert "Antigravity Verifier OK" in evidence.stdout
    assert evidence.duration_seconds >= 0.0


def test_verifier_failing_command():
    verifier = ExecutionVerifier(timeout=5)
    evidence = verifier.run_command([sys.executable, "-c", "import sys; sys.exit(42)"])

    assert evidence.exit_code == 42
    assert evidence.passed is False


def test_verifier_timeout():
    verifier = ExecutionVerifier(timeout=1)
    evidence = verifier.run_command([sys.executable, "-c", "import time; time.sleep(3)"])

    assert evidence.exit_code == -1
    assert evidence.passed is False
    assert "timed out" in evidence.stderr


def test_verify_solution_with_pytest():
    verifier = ExecutionVerifier(timeout=10)

    with tempfile.TemporaryDirectory() as td:
        work_dir = Path(td)
        target_file = work_dir / "math_lib.py"
        test_file = work_dir / "test_math_lib.py"

        test_file.write_text(
            "from math_lib import multiply\n"
            "def test_multiply():\n"
            "    assert multiply(3, 4) == 12\n",
            encoding="utf-8",
        )

        # 1. Test failing solution
        failing_code = "def multiply(a, b):\n    return a + b\n"
        fail_ev = verifier.verify_solution(
            solution_code=failing_code,
            target_file=target_file,
            test_file=test_file,
            work_dir=work_dir,
        )
        assert fail_ev.passed is False
        assert fail_ev.exit_code != 0

        # 2. Test passing solution
        passing_code = "def multiply(a, b):\n    return a * b\n"
        pass_ev = verifier.verify_solution(
            solution_code=passing_code,
            target_file=target_file,
            test_file=test_file,
            work_dir=work_dir,
        )
        assert pass_ev.passed is True
        assert pass_ev.exit_code == 0
        assert pass_ev.tests_passed >= 1
