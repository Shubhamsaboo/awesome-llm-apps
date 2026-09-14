# AI Code Refactor Agent - Architecture & Design

## System Overview

This document explains the architectural decisions, memory schema design, and adaptation mechanisms of the AI Code Refactor Agent.

```
┌─────────────────────────────────────────────────────────────────┐
│                        User (Streamlit)                         │
│  Paste Code → Describe Task → Select Refactoring Type           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CodeRefactorAgent                            │
│                                                                 │
│  1. Query Memory (Mem0 + Qdrant)                               │
│     ↓ Get relevant constraints from past failures              │
│                                                                 │
│  2. Generate Refactoring Prompt                                │
│     ↓ Include constraints hint to avoid past mistakes          │
│                                                                 │
│  3. Call Ollama                                                │
│     ↓ Local LLM generates refactored code                      │
│                                                                 │
│  4. Execute & Track Outcome                                    │
│     ↓ Store ExecutionOutcome (success/failure)                │
│                                                                 │
│  5. If Failed:                                                 │
│     a) Analyze root cause (ask Ollama)                        │
│     b) Extract constraint (what to avoid)                      │
│     c) Store ConstraintDiscovered                             │
│     d) Detect adaptation need (3+ similar failures?)          │
│        ↓ If yes: Generate StrategyAdaptation                  │
│        ↓ Record new strategy for future attempts              │
│                                                                 │
│  6. Return Results & Summary                                   │
│     ↓ Show refactored code + learned constraints              │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│            Memory Layer (Mem0 + Qdrant)                        │
│                                                                 │
│  ExecutionOutcome[]    → All refactoring attempts             │
│  Constraint[]          → Learned rules to avoid                │
│  StrategyAdaptation[]  → When agent changes approach          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Memory Schema Design

### 1. ExecutionOutcome
**Purpose:** Record what happened during a refactoring attempt.

```python
ExecutionOutcome {
    id: str              # UUID for this outcome
    timestamp: datetime  # When did this happen?
    
    task: str           # What user asked for
    attempt_number: int # First, second, third attempt?
    approach: str       # Which refactoring strategy? (OOP, async, etc)
    
    code_input: str     # Original code
    code_output: str    # Refactored result
    
    status: SUCCESS|FAILED|PARTIAL|BLOCKED
    error_message: str  # If failed, what error?
    root_cause: str     # Why did it fail?
    solution: str       # How to fix it?
    key_insight: str    # What did we learn?
    
    tags: List[str]     # [python, oop, dataclass, inheritance...]
    technology: str     # Language being refactored (python)
    test_result: str    # Did tests pass?
}
```

**Example:**
```json
{
    "id": "a1b2c3d4",
    "task": "Convert procedural to OOP",
    "attempt_number": 1,
    "approach": "procedural_to_oop",
    "status": "failed",
    "error_message": "AttributeError: 'NoneType' object has no attribute 'name'",
    "root_cause": "Forgot to call super().__init__() in child class",
    "solution": "Always call super().__init__() as first line in __init__",
    "tags": ["python", "oop", "inheritance", "initialization"],
}
```

### 2. ConstraintDiscovered
**Purpose:** Extract a rule from failure to prevent future mistakes.

```python
ConstraintDiscovered {
    id: str                      # UUID
    discovered_from_outcome_id: str  # Which failure led to this?
    timestamp: datetime
    
    constraint: str              # The rule (e.g., "NEVER rename without checking imports")
    explanation: str             # Why is this rule important?
    severity: high|medium|low    # How critical?
    
    context: str                 # What situation caused this learning?
    tags: List[str]              # Related to: [refactoring, imports, dataclass]
    applies_to: List[str]        # Which refactoring types? [rename, refactor]
    exceptions: str              # When might this NOT apply?
    
    times_violated: int          # How many times have we ignored this rule?
    times_helpful: int           # How many times did following this help?
}
```

**Example:**
```json
{
    "constraint": "NEVER rename a function without grep-searching for all call sites",
    "severity": "high",
    "context": "Renamed User.__init__ to User.constructor(), broke 12 import statements",
    "applies_to": ["rename_function", "refactor"],
    "tags": ["refactoring", "imports", "debugging"],
    "times_violated": 2,
    "times_helpful": 5
}
```

### 3. StrategyAdaptation
**Purpose:** Track when agent changes its approach based on repeated failures.

```python
StrategyAdaptation {
    id: str                     # UUID
    timestamp: datetime
    
    triggered_condition: str    # What triggered this? "Failed 3 times on dataclasses"
    related_task_type: str      # What task type? "dataclass_migration"
    
    old_strategy: str           # How agent used to approach this
    new_strategy: str           # New approach after learning
    reason: str                 # Why is this better?
    
    failed_attempts_count: int  # How many failures triggered this?
    failure_tags: List[str]     # Common themes in failures
    
    applied_count: int          # How many times used?
    success_rate_after: float   # Success rate with new strategy (%)
}
```

**Example:**
```json
{
    "triggered_condition": "Failed 3 times on dataclass migration",
    "old_strategy": "Direct refactoring → test on failure",
    "new_strategy": "Write tests FIRST → understand edge cases → refactor → validate",
    "reason": "Proactive validation catches initialization bugs and edge cases early",
    "failed_attempts_count": 3,
    "failure_tags": ["dataclass", "initialization", "default_values"],
    "applied_count": 7,
    "success_rate_after": 85.5
}
```

---

## Key Design Decisions

### 1. Why Structured Memory Over Generic LLM History?

**❌ Wrong Approach:**
```
Store all conversations in memory
→ Retrieve with semantic search
→ LLM reads old chat and tries to learn
```

**Why it fails:**
- LLM reads chat but might still make same mistake
- No explicit tracking of root causes
- Hard to verify if constraint actually helps
- Memory grows unbounded

**✅ Our Approach:**
```
Store structured outcomes (task, approach, error, root_cause, solution)
→ Extract explicit constraints (NEVER do X)
→ Track constraint effectiveness (times_helpful vs times_violated)
→ Verify before applying constraint
```

**Benefits:**
- Explicit rules are verifiable
- Can track which constraints actually work
- Clear cause-effect relationship
- Agent can reason about constraints
- Memory is focused, not noisy

### 2. Why Track Attempt Numbers?

When agent fails, knowing *which attempt* is critical:

```python
Attempt 1: Direct refactoring → FAILED
Attempt 2: Same approach → FAILED
Attempt 3: Same approach → FAILED
  → Trigger: Strategy Adaptation

Adapt: "Try test-first approach"

Attempt 4: Write tests first → SUCCESS
```

This signals: "This type of task needs a different strategy, not just a retry."

### 3. Why Detect Adaptation After 3 Failures?

**Why not 1?** Too noisy, could be a one-time error
**Why not 5?** Waste of tokens, user gets frustrated
**Why 3?** Sweet spot:
- Proves pattern (not coincidence)
- Agent learns quickly
- User sees improvement (attempt 4 succeeds)
- Aligns with psychological learning curve

### 4. Why Separate Constraints from Outcomes?

Could store constraint directly in outcome:
```python
outcome.constraint = "NEVER rename without checking imports"
```

But this creates problems:
- What if same constraint applies to 10 different failures?
- How do you track if constraint is actually helpful?
- Can't search constraints independently

**Better:** Separate tables with relationship:
```
outcome.id → constraint.discovered_from_outcome_id
constraint.times_helpful ← tracks effectiveness
```

---

## Memory Retrieval Strategy

### How Agent Finds Relevant Knowledge

**Step 1: Semantic Search (Mem0)**
```python
Query: "Refactor class to dataclass"
↓
Mem0 searches embeddings: "dataclass", "class", "migration"
↓
Returns: Similar past queries & outcomes
```

**Step 2: Filter by Tags**
```python
from_memory = [
    constraints with tags: dataclass, initialization, field
]
↓
Sort by severity
↓
Sort by times_helpful
↓
Show top 3 constraints
```

**Step 3: Suggest in Prompt**
```python
prompt = f"""
Refactor this class to dataclass.

IMPORTANT - Avoid these mistakes from past failures:
- NEVER skip field defaults in dataclasses
- ALWAYS check if field has default before setting it
- REMEMBER: Dataclass field order matters (no-default before default)

Original code:
{code}
"""
```

---

## Adaptation Mechanism

### Trigger Detection

```python
def detect_adaptation_need():
    # Count failures by task type
    task_failures = {
        "dataclass_migration": 3,
        "procedural_to_oop": 2,
        "simplify_logic": 1,
    }
    
    # If 3+ failures of same type
    if task_failures["dataclass_migration"] >= 3:
        
        # Get details of failures
        failures = [o for o in outcomes if o.approach == "dataclass_migration"]
        
        # Extract common error patterns
        common_errors = ["field initialization", "default values", "inheritance"]
        
        # Create adaptation
        adaptation = StrategyAdaptation(
            old_strategy="Try refactoring, debug on error",
            new_strategy="Write tests first to catch edge cases",
            failed_attempts_count=3,
            failure_tags=common_errors,
        )
        
        return adaptation
```

### Strategy Application

**Before Adaptation:**
```
User: "Refactor to dataclass"
Agent: "Let me refactor..." → FAILED

User: "Try again"
Agent: "Let me refactor..." → FAILED

User: "Try again"
Agent: "Let me refactor..." → FAILED
```

**After Adaptation:**
```
Agent: "Detected pattern: failing on dataclasses"
Agent: "Shifting to test-first approach"
Agent: "First, let me write tests for this class"
Agent: "Now refactor to dataclass, tests guide the implementation"
Agent: "Tests pass!" → SUCCESS
```

---

## Technology Stack Rationale

### Ollama (Not OpenAI/Cloud)
✅ **Pros:**
- Local = privacy, no data leaves machine
- Deterministic = reproducible test results
- Fast for development
- Free, no API costs

❌ **Cons:**
- Requires 4-8GB VRAM
- Slower than cloud models

**Why chosen:** Privacy + reproducibility > speed for learning agents

### Mem0 + Qdrant (Not Just Vector Store)
✅ **Mem0 abstracts:**
- Memory chunking
- Semantic search
- Metadata filtering
- Multi-user support

✅ **Qdrant provides:**
- Vector search (semantic similarity)
- Filtering by metadata
- Scalable storage
- Embedded mode (no Docker)

### Streamlit (Not FastAPI + React)
✅ **Why:**
- Rapid iteration
- Live code updates
- Built-in components (sidebar, expanders, metrics)
- Matches repo pattern (all memory apps use Streamlit)

---

## Testing Strategy

### Unit Tests (memory_schema.py)
- Validate Pydantic models
- Test enum values
- Verify default behaviors
- Test UUID generation

### Integration Tests (agent_outcomes.py)
- Test agent outcome recording
- Mock Ollama calls
- Verify constraint extraction
- Test strategy adaptation detection
- End-to-end pipelines

### What We DON'T Test (Yet)
- Actual Ollama quality (would need semantic testing)
- Mem0 persistence (would need actual DB)
- UI interactions (would need Selenium)

---

## Future Enhancements

### Phase 2: Production Memory
```python
# Currently: In-memory lists (resets per session)
agent.discovered_constraints = []

# Phase 2: Persistent storage via Mem0
memory.add(
    constraint_object,
    user_id="user_123",
    category="refactoring"
)
```

### Phase 3: Multi-User Memory
```python
# Agent learns from all users' experiences
memory.search(
    "dataclass initialization bug",
    user_id="*",  # Across all users
    limit=10,
)
```

### Phase 4: Behavioral Cloning
```python
# Store not just outcomes, but agent's reasoning
# Could train a smaller model to predict good strategies
# Faster than querying Ollama every time
```

### Phase 5: Hierarchy of Memory
```python
short_term = []  # Current session only
medium_term = []  # Last 7 days of sessions
long_term = []  # Permanent learnings (constraints)

# Forget noisy short-term, keep proven long-term
```

---

## Performance Considerations

### Memory Query Time
```
Semantic search (Mem0):    ~500ms
Tag filtering:             ~10ms
Constraint ranking:        ~50ms
Total:                     ~560ms
```

### Agent Total Time per Refactor
```
Query memory:              560ms
Build prompt:              50ms
Ollama generation:         30-60s (depends on model)
Parse response:            100ms
Store outcome:             50ms
Detect adaptation:         100ms
Total:                     31-61s
```

**Optimization opportunities:**
- Cache frequent queries
- Batch memory searches
- Use faster model (e.g., neural-chat vs mistral)
- Parallel constraint extraction

---

## Monitoring & Debugging

### Key Metrics to Track

```python
# Session health
total_refactorings: int
success_rate: float  # Should improve over time
constraints_per_task: float  # Should stabilize

# Learning progress
adaptations_triggered: int  # Should decrease (learning stabilizes)
constraints_violations: int  # Should decrease
constraint_helpfulness: Dict[str, float]  # Track effectiveness

# Agent health
average_attempt_count: float  # Should decrease as agent learns
error_variety: int  # Different error types encountered
recovery_rate: float  # After failure, does next attempt succeed?
```

### Debug Mode

```python
agent = CodeRefactorAgent(debug=True)
# Logs:
# - Memory queries and results
# - Prompt construction
# - Ollama response
# - Constraint extraction reasoning
# - Adaptation triggering conditions
```

---

## References

- **Mem0 Framework:** https://mem0.ai
- **Qdrant Database:** https://qdrant.tech  
- **Ollama Models:** https://ollama.ai
- **Pydantic Documentation:** https://docs.pydantic.dev
- **Self-Improving Agent Skills:** Self-Improving Agent Skills (Agent Skills repo)

---

**Last Updated:** 2026-09-06  
**Author:** AI Code Refactor Agent Contributors  
**Status:** Active Development
