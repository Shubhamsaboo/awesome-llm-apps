"""
Tests for memory schema Pydantic models.
"""

import pytest
from datetime import datetime
from memory_schema import (
    ExecutionOutcome,
    ConstraintDiscovered,
    StrategyAdaptation,
    OutcomeStatus,
    AgentSession,
)


class TestExecutionOutcome:
    """Test ExecutionOutcome model."""
    
    def test_outcome_creation_success(self):
        """Test creating a successful outcome."""
        outcome = ExecutionOutcome(
            task="Refactor to OOP",
            attempt_number=1,
            approach="procedural_to_oop",
            code_input="def process(data): pass",
            code_output="class Processor: pass",
            status=OutcomeStatus.SUCCESS,
            tags=["python", "oop"],
        )
        
        assert outcome.status == OutcomeStatus.SUCCESS
        assert outcome.task == "Refactor to OOP"
        assert outcome.id is not None
        assert outcome.timestamp is not None
    
    def test_outcome_creation_failed(self):
        """Test creating a failed outcome."""
        outcome = ExecutionOutcome(
            task="Dataclass migration",
            attempt_number=2,
            approach="dataclass_migration",
            code_input="class User: pass",
            code_output="",
            status=OutcomeStatus.FAILED,
            error_message="TypeError: missing field",
            root_cause="Field ordering issue",
            tags=["python", "dataclass"],
        )
        
        assert outcome.status == OutcomeStatus.FAILED
        assert outcome.error_message is not None
        assert outcome.root_cause is not None
    
    def test_outcome_tags_default(self):
        """Test that tags default to empty list."""
        outcome = ExecutionOutcome(
            task="test",
            attempt_number=1,
            approach="test",
            code_input="",
            code_output="",
            status=OutcomeStatus.SUCCESS,
        )
        
        assert outcome.tags == []
    
    def test_outcome_uuid_generation(self):
        """Test that IDs are unique."""
        outcome1 = ExecutionOutcome(
            task="test1",
            attempt_number=1,
            approach="test",
            code_input="",
            code_output="",
            status=OutcomeStatus.SUCCESS,
        )
        
        outcome2 = ExecutionOutcome(
            task="test2",
            attempt_number=1,
            approach="test",
            code_input="",
            code_output="",
            status=OutcomeStatus.SUCCESS,
        )
        
        assert outcome1.id != outcome2.id


class TestConstraintDiscovered:
    """Test ConstraintDiscovered model."""
    
    def test_constraint_creation(self):
        """Test creating a constraint."""
        constraint = ConstraintDiscovered(
            discovered_from_outcome_id="uuid-123",
            constraint="NEVER rename functions without updating all imports",
            explanation="Function rename breaks all call sites if not updated",
            severity="high",
            context="Renamed User.init() to User.constructor(), broke 12 imports",
            tags=["refactoring", "imports"],
            applies_to=["rename_function"],
        )
        
        assert constraint.constraint is not None
        assert constraint.severity == "high"
        assert constraint.times_violated == 0
        assert constraint.times_helpful == 0
    
    def test_constraint_severity_levels(self):
        """Test different severity levels."""
        for severity in ["high", "medium", "low"]:
            constraint = ConstraintDiscovered(
                discovered_from_outcome_id="uuid",
                constraint="test",
                explanation="test",
                severity=severity,
                context="test",
            )
            assert constraint.severity == severity


class TestStrategyAdaptation:
    """Test StrategyAdaptation model."""
    
    def test_adaptation_creation(self):
        """Test creating a strategy adaptation."""
        adaptation = StrategyAdaptation(
            triggered_condition="Failed 3 times on dataclass migration",
            related_task_type="dataclass_migration",
            old_strategy="Try refactoring directly, debug on failure",
            new_strategy="Write tests first, then refactor",
            reason="Proactive testing catches edge cases early",
            failed_attempts_count=3,
        )
        
        assert adaptation.triggered_condition is not None
        assert adaptation.applied_count == 0
        assert adaptation.success_rate_after is None
    
    def test_adaptation_success_tracking(self):
        """Test tracking success after adaptation."""
        adaptation = StrategyAdaptation(
            triggered_condition="test",
            related_task_type="test",
            old_strategy="old",
            new_strategy="new",
            reason="reason",
            applied_count=5,
            success_rate_after=85.0,
        )
        
        assert adaptation.applied_count == 5
        assert adaptation.success_rate_after == 85.0


class TestAgentSession:
    """Test AgentSession model."""
    
    def test_session_creation(self):
        """Test creating an agent session."""
        session = AgentSession(session_name="Refactoring Session 1")
        
        assert session.id is not None
        assert session.total_tasks == 0
        assert session.success_rate == 0.0
    
    def test_session_with_outcomes(self):
        """Test session tracking outcomes."""
        outcome1 = ExecutionOutcome(
            task="test1",
            attempt_number=1,
            approach="test",
            code_input="",
            code_output="",
            status=OutcomeStatus.SUCCESS,
        )
        
        outcome2 = ExecutionOutcome(
            task="test2",
            attempt_number=1,
            approach="test",
            code_input="",
            code_output="",
            status=OutcomeStatus.FAILED,
            error_message="test error",
        )
        
        session = AgentSession(
            session_name="Test Session",
            outcomes=[outcome1, outcome2],
            total_tasks=2,
            successful_tasks=1,
            failed_tasks=1,
        )
        
        assert session.total_tasks == 2
        assert session.successful_tasks == 1
        assert session.success_rate == 50.0
    
    def test_session_success_rate_calculation(self):
        """Test success rate is calculated correctly."""
        session = AgentSession(
            total_tasks=4,
            successful_tasks=3,
            failed_tasks=1,
        )
        
        assert session.success_rate == 75.0


class TestOutcomeStatus:
    """Test OutcomeStatus enum."""
    
    def test_status_values(self):
        """Test all status values exist."""
        statuses = [
            OutcomeStatus.SUCCESS,
            OutcomeStatus.FAILED,
            OutcomeStatus.PARTIAL,
            OutcomeStatus.BLOCKED,
        ]
        
        assert len(statuses) == 4
        assert all(isinstance(s, OutcomeStatus) for s in statuses)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
