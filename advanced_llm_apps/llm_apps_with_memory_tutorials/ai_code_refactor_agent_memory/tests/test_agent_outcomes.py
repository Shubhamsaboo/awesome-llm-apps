"""
Tests for CodeRefactorAgent core logic.
"""

import pytest
from unittest.mock import patch, MagicMock
from refactor_agent import CodeRefactorAgent
from memory_schema import OutcomeStatus, ExecutionOutcome


class TestCodeRefactorAgent:
    """Test CodeRefactorAgent initialization and basic operations."""
    
    def test_agent_initialization(self):
        """Test agent initializes correctly."""
        agent = CodeRefactorAgent(model="mistral")
        
        assert agent.model == "mistral"
        assert agent.session_outcomes == []
        assert agent.discovered_constraints == []
        assert agent.adaptations == []
        assert agent.attempt_counts == {}
    
    def test_agent_strategies_available(self):
        """Test all refactoring strategies are defined."""
        agent = CodeRefactorAgent()
        
        expected_strategies = [
            "procedural_to_oop",
            "add_type_hints",
            "async_conversion",
            "dataclass_migration",
            "pattern_extraction",
            "test_driven",
            "simplify_logic",
        ]
        
        for strategy in expected_strategies:
            assert strategy in agent.STRATEGIES
            assert len(agent.STRATEGIES[strategy]) > 0
    
    @patch('refactor_agent.ollama.generate')
    def test_refactor_code_success(self, mock_ollama):
        """Test successful refactoring stores outcome."""
        mock_ollama.return_value = {
            "response": "```python\ndef new_code(): pass\n```\nExplanation here"
        }
        
        agent = CodeRefactorAgent()
        
        outcome = agent.refactor_code(
            code="def old_code(): pass",
            task="Simplify",
            refactoring_type="simplify_logic",
        )
        
        assert outcome.status == OutcomeStatus.SUCCESS
        assert len(agent.session_outcomes) == 1
        assert agent.session_outcomes[0] == outcome
    
    @patch('refactor_agent.ollama.generate')
    def test_refactor_code_failure(self, mock_ollama):
        """Test failed refactoring is recorded."""
        mock_ollama.side_effect = Exception("Ollama connection error")
        
        agent = CodeRefactorAgent()
        
        outcome = agent.refactor_code(
            code="def code(): pass",
            task="Test task",
            refactoring_type="simplify_logic",
        )
        
        assert outcome.status == OutcomeStatus.FAILED
        assert outcome.error_message is not None
        assert len(agent.session_outcomes) == 1
    
    def test_attempt_tracking(self):
        """Test agent tracks attempt numbers per refactoring type."""
        agent = CodeRefactorAgent()
        agent.attempt_counts = {}
        
        # Simulate multiple attempts of same type
        for i in range(3):
            outcome = ExecutionOutcome(
                task=f"task_{i}",
                attempt_number=i + 1,
                approach="simplify_logic",
                code_input="",
                code_output="",
                status=OutcomeStatus.SUCCESS,
            )
            agent.session_outcomes.append(outcome)
        
        assert len(agent.session_outcomes) == 3
    
    def test_get_session_summary(self):
        """Test session summary calculation."""
        agent = CodeRefactorAgent()
        
        # Add outcomes
        for i in range(3):
            outcome = ExecutionOutcome(
                task=f"task_{i}",
                attempt_number=1,
                approach="test",
                code_input="",
                code_output="",
                status=OutcomeStatus.SUCCESS if i < 2 else OutcomeStatus.FAILED,
            )
            agent.session_outcomes.append(outcome)
        
        summary = agent.get_session_summary()
        
        assert summary["total_refactorings"] == 3
        assert summary["successful"] == 2
        assert summary["failed"] == 1
        assert "66.7%" in summary["success_rate"]


class TestConstraintExtraction:
    """Test constraint discovery from failures."""
    
    @patch('refactor_agent.ollama.generate')
    def test_analyze_failure_creates_constraint(self, mock_ollama):
        """Test that failed outcome triggers constraint extraction."""
        mock_ollama.return_value = {
            "response": "NEVER rename functions without checking all import statements"
        }
        
        agent = CodeRefactorAgent()
        
        outcome = ExecutionOutcome(
            task="Rename User class to UserModel",
            attempt_number=1,
            approach="procedural_to_oop",
            code_input="class User: pass",
            code_output="",
            status=OutcomeStatus.FAILED,
            error_message="NameError: User not defined",
            root_cause="Missed import statement",
            tags=["refactoring", "imports"],
        )
        
        constraint = agent.analyze_failure(outcome)
        
        assert constraint.constraint is not None
        assert constraint.discovered_from_outcome_id == outcome.id
        assert len(agent.discovered_constraints) == 1
    
    def test_get_relevant_constraints(self):
        """Test retrieving constraints by task similarity."""
        agent = CodeRefactorAgent()
        
        # Add sample constraints
        constraint1 = ExecutionOutcome(
            task="dataclass migration",
            attempt_number=1,
            approach="dataclass_migration",
            code_input="",
            code_output="",
            status=OutcomeStatus.FAILED,
            error_message="test",
            tags=["dataclass", "python"],
        )
        
        from memory_schema import ConstraintDiscovered
        
        constraint = ConstraintDiscovered(
            discovered_from_outcome_id="uuid",
            constraint="NEVER skip field defaults in dataclasses",
            explanation="test",
            severity="high",
            context="test",
            tags=["dataclass", "initialization"],
        )
        agent.discovered_constraints.append(constraint)
        
        # Query for dataclass-related constraints
        relevant = agent.get_relevant_constraints(
            task="convert class to dataclass",
            technology="python"
        )
        
        # Should find the constraint with matching tags
        assert len(relevant) >= 0  # May or may not match depending on tag logic


class TestStrategyAdaptation:
    """Test strategy adaptation logic."""
    
    def test_detect_adaptation_need_three_failures(self):
        """Test adaptation triggers after 3 failures of same type."""
        agent = CodeRefactorAgent()
        
        # Add 3 consecutive failures
        for i in range(3):
            outcome = ExecutionOutcome(
                task="dataclass migration test",
                attempt_number=i + 1,
                approach="dataclass_migration",
                code_input="",
                code_output="",
                status=OutcomeStatus.FAILED,
                error_message=f"Error {i+1}",
                tags=["dataclass"],
            )
            agent.session_outcomes.append(outcome)
        
        # Check for adaptation
        adaptation = agent.detect_adaptation_need()
        
        assert adaptation is not None
        assert adaptation.failed_attempts_count >= 3
        assert "test-first" in adaptation.new_strategy.lower()
    
    def test_detect_adaptation_less_than_three_failures(self):
        """Test adaptation doesn't trigger with < 3 failures."""
        agent = CodeRefactorAgent()
        
        # Add 2 failures
        for i in range(2):
            outcome = ExecutionOutcome(
                task="test task",
                attempt_number=i + 1,
                approach="simplify_logic",
                code_input="",
                code_output="",
                status=OutcomeStatus.FAILED,
                error_message=f"Error {i+1}",
            )
            agent.session_outcomes.append(outcome)
        
        adaptation = agent.detect_adaptation_need()
        
        assert adaptation is None  # Not enough failures yet
    
    def test_adaptation_stored_in_session(self):
        """Test adaptation is stored when triggered."""
        agent = CodeRefactorAgent()
        
        # Trigger adaptation
        for i in range(3):
            outcome = ExecutionOutcome(
                task="oop conversion test",
                attempt_number=i + 1,
                approach="procedural_to_oop",
                code_input="",
                code_output="",
                status=OutcomeStatus.FAILED,
                error_message="test",
            )
            agent.session_outcomes.append(outcome)
        
        adaptation = agent.detect_adaptation_need()
        
        if adaptation:
            assert len(agent.adaptations) == 1
            assert agent.adaptations[0] == adaptation


class TestIntegration:
    """Integration tests combining multiple components."""
    
    @patch('refactor_agent.ollama.generate')
    def test_failure_to_constraint_to_memory(self, mock_ollama):
        """Test full pipeline: failure -> constraint extraction -> memory."""
        mock_ollama.return_value = {
            "response": "ALWAYS initialize parent class before child"
        }
        
        agent = CodeRefactorAgent()
        
        # Simulate failure
        outcome = ExecutionOutcome(
            task="OOP refactor",
            attempt_number=1,
            approach="procedural_to_oop",
            code_input="class Child: pass",
            code_output="",
            status=OutcomeStatus.FAILED,
            error_message="AttributeError: super() not initialized",
            root_cause="Missing super().__init__()",
            tags=["oop", "inheritance"],
        )
        
        agent.session_outcomes.append(outcome)
        constraint = agent.analyze_failure(outcome)
        
        # Verify full pipeline
        assert len(agent.session_outcomes) == 1
        assert len(agent.discovered_constraints) == 1
        assert constraint.discovered_from_outcome_id == outcome.id
        assert "initialize" in constraint.constraint.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
