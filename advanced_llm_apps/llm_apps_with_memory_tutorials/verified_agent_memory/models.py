"""Data models for Verified Agent Memory.

Defines schemas for verification evidence, failed attempts, structured experiences,
and lifecycle statuses.
"""

from __future__ import annotations

from enum import Enum
import platform
import sys
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ExperienceStatus(str, Enum):
    """Lifecycle state of an experience in memory."""
    CANDIDATE = "candidate"     # Recorded proposal; not yet verified by execution
    VERIFIED = "verified"       # Formally proven through test execution (exit code 0)
    REJECTED = "rejected"       # Failed verification criteria
    SUPERSEDED = "superseded"   # Replaced by a more comprehensive or recent solution
    STALE = "stale"             # Environment mismatch or invalid dependencies


class VerificationEvidence(BaseModel):
    """Concrete, verifiable evidence gathered from actual test/process execution."""
    command: str
    exit_code: int
    passed: bool
    stdout: str
    stderr: str
    duration_seconds: float
    timestamp: str
    tests_passed: int = 0
    tests_failed: int = 0


class FailedAttempt(BaseModel):
    """Negative constraint data capturing failed approaches ("DO NOT REPEAT")."""
    attempt_number: int
    approach_summary: str
    error_message: str
    failure_reason: str
    code_snippet: Optional[str] = None


class EnvironmentMetadata(BaseModel):
    """Execution environment details to detect configuration drift and staleness."""
    python_version: str = Field(default_factory=lambda: sys.version.split()[0])
    os_platform: str = Field(default_factory=lambda: f"{platform.system()} {platform.release()}")
    arch: str = Field(default_factory=lambda: platform.machine())


class StructuredExperience(BaseModel):
    """A durable, verified experience record linking a task to tested solutions and failure guardrails."""
    id: str
    task_id: str
    task_description: str
    status: ExperienceStatus = ExperienceStatus.CANDIDATE
    verified_solution: Optional[str] = None
    failed_approaches: List[FailedAttempt] = Field(default_factory=list)
    verification_evidence: Optional[VerificationEvidence] = None
    environment: EnvironmentMetadata = Field(default_factory=EnvironmentMetadata)
    lessons_learned: List[str] = Field(default_factory=list)
    created_at: str
    updated_at: str

    def is_verified(self) -> bool:
        """Check if this experience has been verified with exit code 0."""
        return (
            self.status == ExperienceStatus.VERIFIED
            and self.verification_evidence is not None
            and self.verification_evidence.exit_code == 0
            and self.verification_evidence.passed
        )
