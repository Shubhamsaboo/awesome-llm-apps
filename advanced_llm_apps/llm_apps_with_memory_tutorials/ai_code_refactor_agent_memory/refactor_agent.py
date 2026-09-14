<<<<<<< HEAD
"""
AI Code Refactor Agent with Structured Experience Memory.
Learns from refactoring failures and adapts strategy.
"""

import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import ollama
from memory_schema import (
    ExecutionOutcome,
    ConstraintDiscovered,
    StrategyAdaptation,
    OutcomeStatus,
    MemoryQuery,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CodeRefactorAgent:
    """
    Agent that refactors Python code and learns from failures.
    
    Key features:
    - Executes refactoring tasks using local Ollama
    - Stores execution outcomes (success/failure)
    - Discovers constraints from repeated failures
    - Adapts strategy based on learning
    - Retrieves relevant past experiences for new tasks
    """
    
    # Available refactoring strategies
    STRATEGIES = {
        "procedural_to_oop": "Convert procedural code to OOP (classes, inheritance)",
        "add_type_hints": "Add comprehensive type hints and docstrings",
        "async_conversion": "Convert sync functions to async/await",
        "dataclass_migration": "Migrate classes to dataclasses",
        "pattern_extraction": "Extract common patterns into utility functions",
        "test_driven": "Write tests first, then refactor",
        "simplify_logic": "Simplify complex logic with better patterns",
    }
    
    def __init__(self, model: str = "mistral", ollama_host: str = "http://localhost:11435"):
        """
        Initialize the agent.
        
        Args:
            model: Ollama model name (default: mistral)
            ollama_host: Ollama server URL
        """
        self.model = model
        self.ollama_host = ollama_host
        
        # Memory for this session
        self.session_outcomes: List[ExecutionOutcome] = []
        self.discovered_constraints: List[ConstraintDiscovered] = []
        self.adaptations: List[StrategyAdaptation] = []
        
        # Track attempt counts by task type
        self.attempt_counts: Dict[str, int] = {}
        
        # Current strategy preferences (may adapt)
        self.current_strategies: Dict[str, str] = self.STRATEGIES.copy()
        
        logger.info(f"Agent initialized with model: {model}")
    
    def _call_ollama(self, prompt: str, max_tokens: int = 2000) -> str:
        """
        Call Ollama API to generate a response.
        
        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens in response
            
        Returns:
            Generated text from the model
        """
        try:
            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                stream=False,
            )
            return response.get("response", "").strip()
        except Exception as e:
            logger.error(f"Ollama call failed: {e}")
            raise
    
    def get_relevant_constraints(
        self, task: str, technology: str = "python"
    ) -> List[ConstraintDiscovered]:
        """
        Retrieve constraints relevant to current task.
        
        In production, this would query Mem0 with semantic search.
        For now, returns constraints with matching tags.
        
        Args:
            task: Description of the task
            technology: Programming language/tech
            
        Returns:
            List of relevant constraints
        """
        relevant = []
        for constraint in self.discovered_constraints:
            if technology in constraint.tags or any(
                tag in task.lower() for tag in constraint.tags
            ):
                relevant.append(constraint)
        return relevant
    
    def analyze_failure(self, outcome: ExecutionOutcome) -> ConstraintDiscovered:
        """
        Analyze a failed outcome and extract a constraint.
        
        Uses Ollama to reason about the failure.
        """
        prompt = f"""
Analyze this failed refactoring attempt and extract a key constraint/lesson:

Task: {outcome.task}
Approach: {outcome.approach}
Error: {outcome.error_message}
Code that failed:
```python
{outcome.code_output[:500]}
```

Generate a concise constraint (one sentence) that prevents this error.
Format: Start with "NEVER" or "ALWAYS" followed by the rule.
Example: "NEVER rename a function without updating all imports first"
"""
        constraint_text = self._call_ollama(prompt, max_tokens=100)
        
        constraint = ConstraintDiscovered(
            discovered_from_outcome_id=outcome.id,
            constraint=constraint_text,
            explanation=outcome.root_cause or "Extracted from failure",
            severity="high" if outcome.error_message else "medium",
            context=outcome.task,
            tags=outcome.tags,
            applies_to=[outcome.approach],
        )
        
        self.discovered_constraints.append(constraint)
        logger.info(f"Discovered constraint: {constraint.constraint}")
        
        return constraint
    
    def detect_adaptation_need(self) -> Optional[StrategyAdaptation]:
        """
        Check if agent should adapt strategy based on repeated failures.
        
        Returns adaptation if:
        - Same task type failed 3+ times
        - Success rate < 30%
        """
        # Count failures by task type
        task_failures: Dict[str, int] = {}
        
        for outcome in self.session_outcomes:
            if outcome.status == OutcomeStatus.FAILED:
                task_key = outcome.task[:30]  # First 30 chars as key
                task_failures[task_key] = task_failures.get(task_key, 0) + 1
        
        # Check if we should adapt
        for task_key, failure_count in task_failures.items():
            if failure_count >= 3:
                # Get details about these failures
                related_outcomes = [
                    o for o in self.session_outcomes if o.task.startswith(task_key)
                ]
                
                failed_tags = []
                for outcome in related_outcomes:
                    if outcome.status == OutcomeStatus.FAILED:
                        failed_tags.extend(outcome.tags)
                
                # Create adaptation
                adaptation = StrategyAdaptation(
                    triggered_condition=f"Failed {failure_count} times on similar tasks",
                    related_task_type=task_key,
                    old_strategy="Attempt refactoring directly and debug on failure",
                    new_strategy="Write tests FIRST, understand edge cases, then refactor, validate",
                    reason="Proactive validation reduces failure rate significantly",
                    failed_attempts_count=failure_count,
                    failure_tags=list(set(failed_tags)),
                )
                
                self.adaptations.append(adaptation)
                logger.info(f"Strategy adapted: {adaptation.new_strategy}")
                
                return adaptation
        
        return None
    
    def refactor_code(
        self,
        code: str,
        task: str,
        refactoring_type: str = "simplify_logic",
        use_learned_constraints: bool = True,
    ) -> ExecutionOutcome:
        """
        Refactor code and track the outcome.
        
        Args:
            code: Python code to refactor
            task: Description of what to refactor
            refactoring_type: Type of refactoring to perform
            use_learned_constraints: Use memory to avoid past mistakes
            
        Returns:
            ExecutionOutcome with results
        """
        # Track attempt number
        task_key = refactoring_type
        attempt_num = self.attempt_counts.get(task_key, 0) + 1
        self.attempt_counts[task_key] = attempt_num
        
        # Retrieve relevant constraints
        relevant_constraints = self.get_relevant_constraints(task)
        
        # Build prompt
        constraints_hint = ""
        if use_learned_constraints and relevant_constraints:
            constraints_hint = "\n\nIMPORTANT - Avoid these mistakes from past failures:\n"
            for constraint in relevant_constraints[:3]:  # Top 3
                constraints_hint += f"- {constraint.constraint}\n"
        
        prompt = f"""Refactor this Python code.

Task: {task}
Refactoring type: {refactoring_type} - {self.STRATEGIES.get(refactoring_type, '')}

Original code:
```python
{code}
```

Requirements:
1. Preserve all functionality
2. Include comprehensive docstrings
3. Add type hints
4. Explain your changes clearly
5. Warn about any edge cases{constraints_hint}

Provide ONLY the refactored code in a markdown code block, then explain changes.
"""
        
        try:
            response = self._call_ollama(prompt, max_tokens=2000)
            
            # Extract code from response
            # Simple extraction: look for ```python ... ```
            code_start = response.find("```python")
            code_end = response.find("```", code_start + 9)
            
            if code_start >= 0 and code_end > code_start:
                refactored_code = response[code_start + 9 : code_end].strip()
            else:
                refactored_code = response[:500]  # Fallback
            
            # Assume success if we got code (in real app, would run tests)
            outcome = ExecutionOutcome(
                task=task,
                attempt_number=attempt_num,
                approach=refactoring_type,
                code_input=code[:1000],
                code_output=refactored_code[:1000],
                status=OutcomeStatus.SUCCESS,
                key_insight=response[code_end:].strip()[:500] if code_end else None,
                tags=[refactoring_type, "python"],
                test_result="Not executed (mock mode)",
            )
            
            self.session_outcomes.append(outcome)
            logger.info(f"✓ Refactoring succeeded: {task}")
            
            return outcome
            
        except Exception as e:
            logger.error(f"Refactoring failed: {e}")
            
            # Record failure
            outcome = ExecutionOutcome(
                task=task,
                attempt_number=attempt_num,
                approach=refactoring_type,
                code_input=code[:1000],
                code_output="",
                status=OutcomeStatus.FAILED,
                error_message=str(e),
                root_cause="Model or parsing error",
                tags=[refactoring_type, "python", "error"],
            )
            
            self.session_outcomes.append(outcome)
            
            # Analyze and extract constraint
            self.analyze_failure(outcome)
            
            # Check if we should adapt
            self.detect_adaptation_need()
            
            return outcome
    
    def get_session_summary(self) -> Dict[str, Any]:
        """
        Return summary of all learning in this session.
        """
        total = len(self.session_outcomes)
        successful = sum(
            1 for o in self.session_outcomes if o.status == OutcomeStatus.SUCCESS
        )
        
        return {
            "total_refactorings": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": f"{(successful/total*100):.1f}%" if total > 0 else "N/A",
            "constraints_discovered": len(self.discovered_constraints),
            "strategy_adaptations": len(self.adaptations),
            "top_issues": [c.constraint for c in self.discovered_constraints[:5]],
            "adaptations_made": [a.new_strategy for a in self.adaptations],
        }


if __name__ == "__main__":
    # Quick test
    agent = CodeRefactorAgent(model="mistral")
    
    sample_code = """
def process_data(data):
    result = []
    for i in range(len(data)):
        if data[i] > 10:
            result.append(data[i] * 2)
    return result
"""
    
    outcome = agent.refactor_code(
        code=sample_code,
        task="Refactor to use list comprehension and be more pythonic",
        refactoring_type="simplify_logic",
    )
    
    print(f"\nOutcome: {outcome.status}")
    print(f"Session summary: {agent.get_session_summary()}")
=======
from __future__ import annotations

from typing import List

from memory_schema import ConstraintRecord, SessionMemory


class RefactorAgent:
    def __init__(self) -> None:
        self.memory = SessionMemory()

    def learn_from_outcome(self, task: str, outcome: str, error_message: str = "") -> None:
        self.memory.record_outcome(task=task, status=outcome, error_message=error_message)

        if outcome == "failure" and error_message:
            self.memory.record_constraint(
                constraint=self._infer_constraint(error_message),
                source_error=error_message,
                severity="high" if "AttributeError" in error_message or "NameError" in error_message else "medium",
            )

    def _infer_constraint(self, error_message: str) -> str:
        msg = error_message.lower()
        if "nameerror" in msg:
            return "Do not reference undefined symbols without checking the current scope."
        if "attributeerror" in msg:
            return "Check object attributes before using them during refactoring."
        if "importerror" in msg:
            return "Verify imports and module dependencies before changing symbols."
        return "Validate the refactor against the actual runtime error before applying the change."

    def get_relevant_constraints(self, task: str) -> List[ConstraintRecord]:
        return self.memory.get_relevant_constraints(task)

    def summarize_memory(self) -> str:
        if not self.memory.outcomes:
            return "No refactor outcomes recorded yet."

        success_count = sum(1 for outcome in self.memory.outcomes if outcome.status == "success")
        failure_count = sum(1 for outcome in self.memory.outcomes if outcome.status == "failure")
        return (
            f"Recorded {len(self.memory.outcomes)} outcomes: "
            f"{success_count} success, {failure_count} failure. "
            f"{len(self.memory.constraints)} learned constraints available."
        )
>>>>>>> 88c344b (feat: add local AI code refactor agent memory demo)
