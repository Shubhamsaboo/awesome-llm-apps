"""Tests for ExperienceMemory storage, retrieval, and lifecycle transitions."""

from pathlib import Path
import pytest
import tempfile

from memory import ExperienceMemory
from models import (
    EnvironmentMetadata,
    ExperienceStatus,
    FailedAttempt,
    StructuredExperience,
    VerificationEvidence,
)


@pytest.fixture
def temp_memory():
    """Provides an isolated ExperienceMemory backed by a temporary SQLite database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = Path(tf.name)
    mem = ExperienceMemory(db_path=db_path)
    yield mem
    if db_path.exists():
        try:
            db_path.unlink()
        except OSError:
            pass


def test_record_candidate_and_retrieval(temp_memory: ExperienceMemory):
    exp = temp_memory.record_candidate(
        task_id="test_rate_limiter",
        task_description="Implement sliding window rate limiter",
    )
    assert exp.status == ExperienceStatus.CANDIDATE
    assert exp.task_id == "test_rate_limiter"

    # Fetch from memory
    fetched = temp_memory.get_experience_by_task("test_rate_limiter")
    assert fetched is not None
    assert fetched.id == exp.id
    assert fetched.status == ExperienceStatus.CANDIDATE


def test_promote_to_verified_requires_passing_evidence(temp_memory: ExperienceMemory):
    temp_memory.record_candidate(task_id="task_calc", task_description="Calculator")

    failing_evidence = VerificationEvidence(
        command="pytest test_calc.py",
        exit_code=1,
        passed=False,
        stdout="AssertionError in test_add",
        stderr="",
        duration_seconds=0.45,
        timestamp="2026-09-07T00:00:00Z",
        tests_passed=1,
        tests_failed=1,
    )

    # Promoting with failing evidence must raise ValueError
    with pytest.raises(ValueError, match="Cannot promote to VERIFIED"):
        temp_memory.promote_to_verified(
            task_id="task_calc",
            solution="def add(a, b): return a - b",
            evidence=failing_evidence,
        )

    # Promoting with passing evidence succeeds
    passing_evidence = VerificationEvidence(
        command="pytest test_calc.py",
        exit_code=0,
        passed=True,
        stdout="2 passed in 0.05s",
        stderr="",
        duration_seconds=0.05,
        timestamp="2026-09-07T00:01:00Z",
        tests_passed=2,
        tests_failed=0,
    )

    promoted = temp_memory.promote_to_verified(
        task_id="task_calc",
        solution="def add(a, b): return a + b",
        evidence=passing_evidence,
        lessons_learned=["Addition must use + operator."],
    )
    assert promoted.status == ExperienceStatus.VERIFIED
    assert promoted.is_verified() is True
    assert promoted.verified_solution == "def add(a, b): return a + b"


def test_failed_approaches_retained_as_negative_constraints(temp_memory: ExperienceMemory):
    temp_memory.record_candidate("task_cache", "LRU Cache")

    attempt_1 = FailedAttempt(
        attempt_number=1,
        approach_summary="Used ordinary dict without re-ordering",
        error_message="KeyError: element not evicted correctly",
        failure_reason="Evicted newest rather than oldest entry",
    )
    temp_memory.record_failed_attempt("task_cache", attempt_1)

    attempt_2 = FailedAttempt(
        attempt_number=2,
        approach_summary="Used list for keys (O(N) lookup)",
        error_message="TimeoutError: exceed 1.0s benchmark",
        failure_reason="O(N) search per get() call",
    )
    temp_memory.record_failed_attempt("task_cache", attempt_2)

    exp = temp_memory.get_experience_by_task("task_cache")
    assert exp is not None
    assert len(exp.failed_approaches) == 2
    assert exp.failed_approaches[0].approach_summary == "Used ordinary dict without re-ordering"
    assert exp.failed_approaches[1].failure_reason == "O(N) search per get() call"

    # Context formatting must include DO NOT REPEAT section
    context = temp_memory.format_experience_context([exp])
    assert "DO NOT REPEAT" in context
    assert "Used ordinary dict without re-ordering" in context
    assert "TimeoutError: exceed 1.0s benchmark" in context


def test_environment_staleness_detection(temp_memory: ExperienceMemory):
    old_env = EnvironmentMetadata(python_version="2.7.18", os_platform="Linux 4.4", arch="x86_64")
    exp = temp_memory.record_candidate("stale_task", "Old task", environment=old_env)

    stale, msg = temp_memory.check_environment_staleness(exp)
    assert stale is True
    assert "Python version mismatch" in msg

    # Marking stale
    marked = temp_memory.mark_stale("stale_task", "Python 2.7 is unsupported")
    assert marked is not None
    assert marked.status == ExperienceStatus.STALE


def test_retrieval_ranking(temp_memory: ExperienceMemory):
    passing_ev = VerificationEvidence(
        command="pytest", exit_code=0, passed=True, stdout="", stderr="",
        duration_seconds=0.1, timestamp="2026-09-07T00:00:00Z",
    )
    temp_memory.promote_to_verified(
        task_id="rate_limiter_token_bucket",
        solution="class TokenBucket: ...",
        evidence=passing_ev,
        lessons_learned=["Token bucket handles bursts well."],
    )
    temp_memory.promote_to_verified(
        task_id="binary_search_tree",
        solution="class BST: ...",
        evidence=passing_ev,
        lessons_learned=["In-order traversal yields sorted order."],
    )

    results = temp_memory.retrieve_relevant("token bucket rate limiter")
    assert len(results) >= 1
    assert results[0].task_id == "rate_limiter_token_bucket"
