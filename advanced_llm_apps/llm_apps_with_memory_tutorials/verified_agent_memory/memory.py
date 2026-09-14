"""Structured Experience Memory Engine.

Provides durable SQLite-backed storage for agent experiences, enforcing the rule that
only solutions backed by exit-code-0 verification evidence become VERIFIED knowledge,
while failed attempts are preserved as negative constraints ("DO NOT REPEAT").
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import sys
from typing import Any, Dict, List, Optional, Tuple
import uuid

from models import (
    EnvironmentMetadata,
    ExperienceStatus,
    FailedAttempt,
    StructuredExperience,
    VerificationEvidence,
)


class ExperienceMemory:
    """Persistent experience storage and retrieval engine with verification enforcement."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path("experiences.db")
        self._init_db()

    @contextmanager
    def _get_conn(self):
        """Context manager that guarantees SQLite connection closure to prevent file locks."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Initialize database schema for structured experiences."""
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS experiences (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    task_description TEXT NOT NULL,
                    status TEXT NOT NULL,
                    verified_solution TEXT,
                    failed_approaches_json TEXT NOT NULL DEFAULT '[]',
                    verification_evidence_json TEXT,
                    environment_json TEXT NOT NULL,
                    lessons_learned_json TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_task_id ON experiences(task_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON experiences(status)")
            conn.commit()

    def get_experience_by_task(self, task_id: str) -> Optional[StructuredExperience]:
        """Fetch experience record for a given task_id if it exists."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM experiences WHERE task_id = ? ORDER BY updated_at DESC LIMIT 1",
                (task_id,),
            ).fetchone()
            if row:
                return self._row_to_model(row)
        return None

    def get_experience_by_id(self, exp_id: str) -> Optional[StructuredExperience]:
        """Fetch experience by primary key ID."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM experiences WHERE id = ?",
                (exp_id,),
            ).fetchone()
            if row:
                return self._row_to_model(row)
        return None

    def record_candidate(
        self,
        task_id: str,
        task_description: str,
        environment: Optional[EnvironmentMetadata] = None,
    ) -> StructuredExperience:
        """Create or initialize a candidate experience record."""
        existing = self.get_experience_by_task(task_id)
        now = datetime.now(timezone.utc).isoformat()

        if existing:
            return existing

        exp = StructuredExperience(
            id=f"exp_{uuid.uuid4().hex[:10]}",
            task_id=task_id,
            task_description=task_description,
            status=ExperienceStatus.CANDIDATE,
            environment=environment or EnvironmentMetadata(),
            created_at=now,
            updated_at=now,
        )
        self._save(exp)
        return exp

    def record_failed_attempt(
        self,
        task_id: str,
        attempt: FailedAttempt,
    ) -> StructuredExperience:
        """Record a failed attempt into negative constraints ("DO NOT REPEAT")."""
        exp = self.get_experience_by_task(task_id)
        if not exp:
            exp = self.record_candidate(task_id=task_id, task_description=f"Task: {task_id}")

        # Check if already present to avoid duplication
        if not any(f.attempt_number == attempt.attempt_number for f in exp.failed_approaches):
            exp.failed_approaches.append(attempt)

        exp.updated_at = datetime.now(timezone.utc).isoformat()
        self._save(exp)
        return exp

    def promote_to_verified(
        self,
        task_id: str,
        solution: str,
        evidence: VerificationEvidence,
        lessons_learned: Optional[List[str]] = None,
    ) -> StructuredExperience:
        """Promote an experience to VERIFIED status only if verification evidence passes."""
        if not evidence.passed or evidence.exit_code != 0:
            raise ValueError(
                f"Cannot promote to VERIFIED: Execution evidence failed with exit code {evidence.exit_code}."
            )

        exp = self.get_experience_by_task(task_id)
        if not exp:
            exp = self.record_candidate(task_id=task_id, task_description=f"Task: {task_id}")

        exp.status = ExperienceStatus.VERIFIED
        exp.verified_solution = solution
        exp.verification_evidence = evidence
        if lessons_learned:
            exp.lessons_learned.extend([l for l in lessons_learned if l not in exp.lessons_learned])
        exp.updated_at = datetime.now(timezone.utc).isoformat()

        self._save(exp)
        return exp

    def mark_stale(self, task_id: str, reason: str) -> Optional[StructuredExperience]:
        """Mark an experience as STALE due to environment drift or API deprecation."""
        exp = self.get_experience_by_task(task_id)
        if exp:
            exp.status = ExperienceStatus.STALE
            exp.lessons_learned.append(f"Stale flag: {reason}")
            exp.updated_at = datetime.now(timezone.utc).isoformat()
            self._save(exp)
        return exp

    def retrieve_relevant(
        self,
        query: str,
        status_filter: Optional[ExperienceStatus] = ExperienceStatus.VERIFIED,
        limit: int = 5,
    ) -> List[StructuredExperience]:
        """Retrieve relevant experiences based on keyword overlap with task_id or description."""
        query_words = set(w.lower() for w in query.replace("_", " ").replace("-", " ").split() if len(w) > 2)

        with self._get_conn() as conn:
            if status_filter:
                rows = conn.execute(
                    "SELECT * FROM experiences WHERE status = ? ORDER BY updated_at DESC",
                    (status_filter.value,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM experiences ORDER BY updated_at DESC"
                ).fetchall()

        results = []
        for row in rows:
            exp = self._row_to_model(row)
            text_corpus = f"{exp.task_id} {exp.task_description} {' '.join(exp.lessons_learned)}".lower()
            # Simple keyword score
            score = sum(1 for word in query_words if word in text_corpus)
            if score > 0 or not query_words:
                results.append((score, exp))

        results.sort(key=lambda item: item[0], reverse=True)
        return [exp for _, exp in results[:limit]]

    def format_experience_context(self, experiences: List[StructuredExperience]) -> str:
        """Format retrieved experiences into clean prompt context for an LLM."""
        if not experiences:
            return ""

        sections = [
            "### RELEVANT VERIFIED EXPERIENCE & CONSTRAINTS FROM PREVIOUS RUNS",
            "The following solutions were formally tested and verified with exit code 0. "
            "Critically, pay attention to the failed approaches to avoid repeating known dead ends:\n",
        ]

        for idx, exp in enumerate(experiences, start=1):
            sections.append(f"#### Experience {idx}: Task `{exp.task_id}`")
            sections.append(f"- **Status:** {exp.status.value.upper()}")

            if exp.verification_evidence:
                sections.append(
                    f"- **Verification Evidence:** Passed `{exp.verification_evidence.command}` "
                    f"(exit code: {exp.verification_evidence.exit_code}, {exp.verification_evidence.tests_passed} tests passed)"
                )

            if exp.lessons_learned:
                sections.append("- **Verified Insights & Key Patterns:**")
                for lesson in exp.lessons_learned:
                    sections.append(f"  * {lesson}")

            if exp.failed_approaches:
                sections.append("- **DO NOT REPEAT (Previously Failed Approaches):**")
                for fa in exp.failed_approaches:
                    sections.append(
                        f"  * Attempt #{fa.attempt_number}: {fa.approach_summary} -> "
                        f"Failed with: {fa.error_message}"
                    )

            if exp.verified_solution:
                sections.append("- **Working Reference Pattern:**")
                sections.append(f"```python\n{exp.verified_solution}\n```\n")

        return "\n".join(sections)

    def check_environment_staleness(self, experience: StructuredExperience) -> Tuple[bool, str]:
        """Check whether execution environment has drifted from when experience was verified."""
        current_py = sys.version.split()[0].split(".")[:2]  # e.g. ["3", "11"]
        exp_py = experience.environment.python_version.split(".")[:2]

        if current_py != exp_py:
            return (
                True,
                f"Python version mismatch: Verified on {experience.environment.python_version}, "
                f"current runtime is {sys.version.split()[0]}.",
            )
        return False, "Environment matches."

    def _save(self, exp: StructuredExperience) -> None:
        """Upsert experience model into database."""
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO experiences (
                    id, task_id, task_description, status, verified_solution,
                    failed_approaches_json, verification_evidence_json,
                    environment_json, lessons_learned_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status=excluded.status,
                    verified_solution=excluded.verified_solution,
                    failed_approaches_json=excluded.failed_approaches_json,
                    verification_evidence_json=excluded.verification_evidence_json,
                    environment_json=excluded.environment_json,
                    lessons_learned_json=excluded.lessons_learned_json,
                    updated_at=excluded.updated_at
                """,
                (
                    exp.id,
                    exp.task_id,
                    exp.task_description,
                    exp.status.value,
                    exp.verified_solution,
                    json.dumps([f.model_dump() for f in exp.failed_approaches]),
                    json.dumps(exp.verification_evidence.model_dump()) if exp.verification_evidence else None,
                    json.dumps(exp.environment.model_dump()),
                    json.dumps(exp.lessons_learned),
                    exp.created_at,
                    exp.updated_at,
                ),
            )
            conn.commit()

    @staticmethod
    def _row_to_model(row: sqlite3.Row) -> StructuredExperience:
        """Convert SQLite row to StructuredExperience model."""
        failed_approaches = [
            FailedAttempt(**item) for item in json.loads(row["failed_approaches_json"])
        ]
        evidence = (
            VerificationEvidence(**json.loads(row["verification_evidence_json"]))
            if row["verification_evidence_json"]
            else None
        )
        environment = EnvironmentMetadata(**json.loads(row["environment_json"]))
        lessons = json.loads(row["lessons_learned_json"])

        return StructuredExperience(
            id=row["id"],
            task_id=row["task_id"],
            task_description=row["task_description"],
            status=ExperienceStatus(row["status"]),
            verified_solution=row["verified_solution"],
            failed_approaches=failed_approaches,
            verification_evidence=evidence,
            environment=environment,
            lessons_learned=lessons,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
