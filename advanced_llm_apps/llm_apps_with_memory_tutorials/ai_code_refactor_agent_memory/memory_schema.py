<<<<<<< HEAD
"""
Memory schema for AI Code Refactor Agent.
Defines structured models for storing and retrieving execution experiences.
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field
import uuid


class OutcomeStatus(str, Enum):
    """Status of a refactoring outcome."""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    BLOCKED = "blocked"


class ExecutionOutcome(BaseModel):
    """Stores the result of a refactoring attempt."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Task description
    task: str = Field(..., description="What was the user trying to refactor?")
    attempt_number: int = Field(default=1, description="Which attempt is this? (1, 2, 3...)")
    
    # What the agent tried
    approach: str = Field(..., description="What strategy/approach was used?")
    code_input: str = Field(..., description="Original code that was refactored")
    code_output: str = Field(..., description="Result of refactoring attempt")
    
    # Outcome
    status: OutcomeStatus = Field(...)
    error_message: Optional[str] = Field(default=None, description="If FAILED, what was the error?")
    root_cause: Optional[str] = Field(default=None, description="Analysis of why it failed")
    
    # Solution/Learning
    solution: Optional[str] = Field(default=None, description="How to fix the issue")
    key_insight: Optional[str] = Field(default=None, description="What was learned from this")
    
    # Categorization
    tags: List[str] = Field(default_factory=list, description="Tags: python, oop, refactoring, etc")
    technology: str = Field(default="python", description="Language/tech being refactored")
    
    # Memory index
    test_result: Optional[str] = Field(default=None, description="Did tests pass after refactoring?")
    
    class Config:
        use_enum_values = True


class ConstraintDiscovered(BaseModel):
    """A rule learned from failure to avoid future mistakes."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    discovered_from_outcome_id: str = Field(..., description="Which outcome led to this constraint?")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # The constraint
    constraint: str = Field(..., description="What NOT to do? (e.g., 'NEVER rename a function without updating imports')")
    explanation: str = Field(..., description="Why is this important?")
    severity: str = Field(default="medium", description="high, medium, low")
    
    # Context
    context: str = Field(..., description="What situation caused this learning?")
    tags: List[str] = Field(default_factory=list, description="Associated tags")
    
    # Applicability
    applies_to: List[str] = Field(default_factory=list, description="What refactoring types does this apply to?")
    exceptions: Optional[str] = Field(default=None, description="When might this constraint NOT apply?")
    
    # Tracking
    times_violated: int = Field(default=0, description="How many times has this been violated?")
    times_helpful: int = Field(default=0, description="How many times did following this help?")


class StrategyAdaptation(BaseModel):
    """Tracks when the agent changes its approach based on learning."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Trigger
    triggered_condition: str = Field(..., description="What condition triggered adaptation? (e.g., 'failed 3 times')")
    related_task_type: str = Field(..., description="What type of refactoring triggered this?")
    
    # The change
    old_strategy: str = Field(..., description="How agent used to approach similar tasks")
    new_strategy: str = Field(..., description="New approach after learning")
    reason: str = Field(..., description="Why is this new approach better?")
    
    # Evidence
    failed_attempts_count: int = Field(default=0, description="How many failures led to this?")
    failure_tags: List[str] = Field(default_factory=list, description="Common tags in failures")
    
    # Tracking
    applied_count: int = Field(default=0, description="How many times has this adaptation been used?")
    success_rate_after: Optional[float] = Field(default=None, description="Success rate after applying new strategy")
    
    class Config:
        use_enum_values = True


class AgentSession(BaseModel):
    """Tracks a single session with all outcomes."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = Field(default=None)
    
    session_name: str = Field(default="Refactoring Session")
    outcomes: List[ExecutionOutcome] = Field(default_factory=list)
    constraints_discovered: List[ConstraintDiscovered] = Field(default_factory=list)
    adaptations: List[StrategyAdaptation] = Field(default_factory=list)
    
    # Summary
    total_tasks: int = Field(default=0)
    successful_tasks: int = Field(default=0)
    failed_tasks: int = Field(default=0)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate of this session."""
        if self.total_tasks == 0:
            return 0.0
        return (self.successful_tasks / self.total_tasks) * 100


class MemoryQuery(BaseModel):
    """Query structure for retrieving memories."""
    
    query_text: str = Field(..., description="Semantic query (e.g., 'dataclass refactoring failures')")
    tags: List[str] = Field(default_factory=list, description="Optional tags to filter")
    limit: int = Field(default=5, description="Max results to return")
    filter_status: Optional[str] = Field(default=None, description="Filter by status (success, failed, etc)")
=======
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional
import uuid


@dataclass
class ConstraintRecord:
    constraint: str
    source_error: str = ""
    severity: str = "medium"
    frequency: int = 1
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class OutcomeRecord:
    task: str
    status: str
    error_message: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class SessionMemory:
    constraints: List[ConstraintRecord] = field(default_factory=list)
    outcomes: List[OutcomeRecord] = field(default_factory=list)

    def record_constraint(self, constraint: str, source_error: str = "", severity: str = "medium") -> ConstraintRecord:
        existing = next((c for c in self.constraints if c.constraint == constraint), None)
        if existing is not None:
            existing.frequency += 1
            return existing

        record = ConstraintRecord(
            constraint=constraint,
            source_error=source_error,
            severity=severity,
            frequency=1,
        )
        self.constraints.append(record)
        return record

    def record_outcome(self, task: str, status: str, error_message: str = "") -> OutcomeRecord:
        outcome = OutcomeRecord(task=task, status=status, error_message=error_message)
        self.outcomes.append(outcome)
        return outcome

    def get_relevant_constraints(self, query: str, limit: int = 5) -> List[ConstraintRecord]:
        query_text = (query or "").lower()
        if not query_text:
            return self.constraints[:limit]

        matches = [
            item for item in self.constraints
            if query_text in item.constraint.lower() or query_text in item.source_error.lower()
        ]
        return matches[:limit]
>>>>>>> 88c344b (feat: add local AI code refactor agent memory demo)
