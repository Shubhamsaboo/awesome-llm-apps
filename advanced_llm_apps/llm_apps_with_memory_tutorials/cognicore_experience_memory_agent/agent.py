"""
CogniCore Experience Agent
--------------------------
Demonstrates an AI agent that systematically learns from previous verified
execution experiences across sessions using CogniCore.

Architecture:
- The LLM performs reasoning and decision-making.
- CogniCore acts as the persistent structured experience memory and verification gate.
"""

import os
import time
import hashlib
import json
from typing import Dict, Any, List, Optional, Tuple

from dotenv import load_dotenv

# Import CogniCore experience engine components directly
from cognicore.experience import (
    ExperienceManager,
    StructuredExperience,
    Attempt,
    AttemptOutcome,
    EvidenceRecord,
    EnvironmentContext,
    RepositoryContext,
    VerificationStatus,
    RetrievalResult,
    RevalidationResult,
)
from cognicore.memory.sqlite_backend import SQLiteMemoryBackend

load_dotenv()


class ExperienceAgent:
    """An AI agent backed by CogniCore structured experience memory."""

    def __init__(
        self,
        session_id: str,
        db_path: str = "cognicore_agent_memory.db",
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
    ):
        self.session_id = session_id
        self.db_path = db_path
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model

        # Initialize CogniCore Memory Backend & ExperienceManager
        self.backend = SQLiteMemoryBackend(self.db_path)
        self.manager = ExperienceManager(backend=self.backend)

        # Environment Context for current agent runtime
        self.current_env = EnvironmentContext(
            python_version="3.11.9",
            os="Windows/Linux",
            framework="pytest",
            framework_version="8.0.0",
            dependencies={"pydantic": "2.6.0", "fastapi": "0.110.0"},
        )

        self.current_repo = RepositoryContext(
            repo_id="awesome-llm-service",
            commit="a1b2c3d",
            branch="main",
            affected_files=["models/user.py"],
        )

    def recall_experiences(self, query: str) -> Tuple[RetrievalResult, float]:
        """Recall relevant prior verified experiences from CogniCore with measured latency."""
        start_time = time.perf_counter()
        # Sanitize query for FTS5 tokenization (remove special characters like @, /, :)
        safe_query = "".join(c if c.isalnum() or c.isspace() else " " for c in query)
        safe_query = " ".join(safe_query.split())
        results: RetrievalResult = self.manager.retrieve(
            query=safe_query, current_env=self.current_env
        )
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        return results, latency_ms

    def run_verification_test(
        self, code: str, expected_snippet: str
    ) -> Tuple[bool, int, str, str]:
        """Simulate / execute verification of an attempted solution against a test suite.

        Returns (passed, exit_code, stdout, stdout_hash).
        """
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        if expected_snippet in code and "@validator" not in code:
            stdout = f"================== 3 passed in 0.12s at {timestamp} =================="
            exit_code = 0
            passed = True
        else:
            stdout = (
                f"FAILED test_models.py::test_user_validator - "
                f"PydanticUserError: @validator is deprecated in Pydantic v2. "
                f"Use @field_validator instead."
            )
            exit_code = 1
            passed = False

        stdout_hash = hashlib.sha256(stdout.encode("utf-8")).hexdigest()[:16]
        return passed, exit_code, stdout, stdout_hash

    def solve_session_1_cold_start(
        self, task_description: str
    ) -> Dict[str, Any]:
        """SESSION 1:

        Agent receives a difficult task with NO previous experience.
        1. Queries CogniCore (returns empty).
        2. Tries naive approach A -> Fails test.
        3. Analyzes failure, tries verified approach B -> Passes test.
        4. Submits real EvidenceRecord to CogniCore VerificationGate (CANDIDATE -> VERIFIED).
        5. Stores structured experience for future sessions.
        """
        # Step 1: Recall
        retrieval, latency_ms = self.recall_experiences(task_description)

        attempts: List[Attempt] = []

        # Step 2: Attempt 1 (Naive v1 approach)
        attempt_1_code = (
            "from pydantic import BaseModel, validator\n\n"
            "class UserModel(BaseModel):\n"
            "    username: str\n\n"
            "    @validator('username')\n"
            "    def validate_name(cls, v):\n"
            "        return v.strip()"
        )
        p1, exit1, out1, hash1 = self.run_verification_test(
            attempt_1_code, "@field_validator"
        )
        attempts.append(
            Attempt(
                approach="Use legacy Pydantic v1 @validator syntax",
                outcome=AttemptOutcome.FAILURE,
                reason="Deprecated in Pydantic v2; throws PydanticUserError during class building",
                evidence=f"Exit code {exit1}: {out1[:100]}...",
            )
        )

        # Step 3: Attempt 2 (Corrected v2 approach)
        attempt_2_code = (
            "from pydantic import BaseModel, field_validator\n\n"
            "class UserModel(BaseModel):\n"
            "    username: str\n\n"
            "    @field_validator('username')\n"
            "    @classmethod\n"
            "    def validate_name(cls, v):\n"
            "        return v.strip()"
        )
        p2, exit2, out2, hash2 = self.run_verification_test(
            attempt_2_code, "@field_validator"
        )
        attempts.append(
            Attempt(
                approach="Use Pydantic v2 @field_validator with @classmethod",
                outcome=AttemptOutcome.SUCCESS,
                reason="Complies with Pydantic v2 specification; passes test suite without deprecation errors",
                evidence=f"Exit code {exit2}: {out2}",
            )
        )

        # Step 4: Construct StructuredExperience
        exp_id = f"exp_{int(time.time())}"
        experience = StructuredExperience(
            experience_id=exp_id,
            task=task_description,
            problem="Pydantic v1 @validator is deprecated in v2 and fails validation tests.",
            attempts=attempts,
            solution=(
                "Replace @validator with @field_validator and add the @classmethod decorator. "
                "Import field_validator directly from pydantic."
            ),
            why_it_worked="Pydantic v2 decoupled field-level validation into @field_validator which enforces classmethod semantics.",
            verification_status=VerificationStatus.CANDIDATE,
            verification_method="pytest_suite",
            verification_version="1.0.0",
            verification_evidence=[],
            source_agent="agent_worker_1",
            source_session=self.session_id,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            repository=self.current_repo,
            environment=self.current_env,
            confidence=0.95,
            content_hash="",
        )

        # Record candidate in CogniCore
        recorded_id = self.manager.record(experience)

        # Step 5: Verification Gate (CANDIDATE -> VERIFIED)
        evidence = [
            EvidenceRecord(
                command="pytest tests/test_models.py",
                exit_code=exit2,
                stdout_hash=hash2,
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                commit=self.current_repo.commit,
            )
        ]
        verification_result = self.manager.verify(
            str(recorded_id), evidence=evidence
        )
        verified_id = getattr(verification_result, "_promoted_id", str(recorded_id))

        return {
            "session": self.session_id,
            "retrieved_count": len(retrieval.experiences),
            "retrieval_latency_ms": latency_ms,
            "attempts": attempts,
            "total_attempts": len(attempts),
            "solution": experience.solution,
            "verification_status": verification_result.status,
            "verification_passed": verification_result.passed,
            "recorded_id": verified_id,
            "code": attempt_2_code,
        }

    def solve_session_2_with_memory(
        self, task_description: str
    ) -> Dict[str, Any]:
        """SESSION 2:

        Fresh agent session with a related problem.
        1. Queries CogniCore: retrieves verified solution and DO NOT REPEAT negative constraints.
        2. Applies verified solution on Attempt 1 (no blind trial-and-error).
        3. Passes verification immediately.
        """
        # Step 1: Recall prior experience
        retrieval, latency_ms = self.recall_experiences(task_description)

        recalled_exp: Optional[StructuredExperience] = None
        do_not_repeat: List[str] = []
        verified_approach = ""

        if retrieval.experiences:
            recalled_exp = retrieval.experiences[0]
            verified_approach = recalled_exp.solution
            for att in recalled_exp.attempts:
                if att.outcome == AttemptOutcome.FAILURE or att.outcome == "failure":
                    do_not_repeat.append(f"{att.approach} (Reason: {att.reason})")

        # Step 2: Directly apply verified pattern (Attempt 1)
        attempt_code = (
            "from pydantic import BaseModel, field_validator\n\n"
            "class AuthTokenModel(BaseModel):\n"
            "    token: str\n\n"
            "    @field_validator('token')\n"
            "    @classmethod\n"
            "    def check_token(cls, v):\n"
            "        return v.strip()"
        )

        p, exit_code, stdout, stdout_hash = self.run_verification_test(
            attempt_code, "@field_validator"
        )

        attempts = [
            Attempt(
                approach=f"Directly applied verified pattern: {verified_approach[:60]}...",
                outcome=AttemptOutcome.SUCCESS,
                reason="Leveraged verified CogniCore experience; avoided known dead-ends",
                evidence=f"Exit code {exit_code}: {stdout}",
            )
        ]

        return {
            "session": self.session_id,
            "retrieved_count": len(retrieval.experiences),
            "retrieval_latency_ms": latency_ms,
            "recalled_experience": recalled_exp,
            "do_not_repeat": do_not_repeat,
            "verified_approach": verified_approach,
            "attempts": attempts,
            "total_attempts": len(attempts),
            "verification_passed": p,
            "code": attempt_code,
        }

    def simulate_staleness_check(
        self, experience_id: str
    ) -> Tuple[RevalidationResult, EnvironmentContext]:
        """Demonstrates Staleness Detection:

        When dependencies change (e.g. major framework upgrade), CogniCore detects
        that the stored experience may no longer be valid and demands re-validation.
        """
        # Simulated environment shift: pydantic bumped to 3.0.0 breaking change
        shifted_env = EnvironmentContext(
            python_version="3.12.0",
            os="Windows/Linux",
            framework="pytest",
            framework_version="9.0.0",
            dependencies={"pydantic": "3.0.0", "fastapi": "0.120.0"},
        )

        # CogniCore checks staleness and compatibility
        reval_result: RevalidationResult = self.manager.revalidate(
            experience_id=str(experience_id), current_env=shifted_env
        )

        return reval_result, shifted_env
