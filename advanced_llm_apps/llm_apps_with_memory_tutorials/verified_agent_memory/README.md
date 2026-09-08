# 🧠 Verified Agent Memory: Cross-Session Learning with Real Test Execution

A production-grade, standalone tutorial demonstrating how an autonomous AI coding agent learns across independent sessions by coupling **real LLM reasoning** with **isolated subprocess test verification** and **structured persistent experience memory**.

---

## 📌 Problem: Why Conversation History Fails for Agent Memory

Most LLM agents rely on raw chat history (context windows) to "remember" past actions. For coding and software engineering agents, this approach breaks down quickly:

1. **Context Window Exhaustion**: Long debugging sessions with stack traces, test logs, and compiler errors rapidly consume the context window, driving up token costs and causing degradation in reasoning quality.
2. **Noise and Dead Ends**: A 20-message transcript contains mostly failed hypotheses, syntax bugs, and exploratory chatter. Passing this noisy history to a new session pollutes the prompt with irrelevant tokens.
3. **Session Amnesia**: Chat transcripts are ephemeral. When an agent restarts, a CLI tool terminates, or a new PR is opened, all prior hard-earned debugging insights vanish.
4. **Lack of Trust / Hallucinated Memory**: Simply saving raw LLM text into a vector database often indexes unverified code snippets or hallucinated explanations. If an agent retrieves an unverified solution, it risks repeating errors.

### The Solution: Verified Experience Memory
Instead of storing conversational transcripts, this application stores **structured, verified experiences**:
- Code solutions are promoted to `VERIFIED` **only** when an isolated subprocess executes tests and returns **exit code 0**.
- Failed attempts are not discarded; they are distilled into explicit **negative constraints ("DO NOT REPEAT")** to steer future agents away from proven dead ends.
- Subsequent sessions start with a **clean context window** (zero prior chat messages) and inject only concise, verified patterns and guardrails.

---

## 🏗️ Architecture & Verification Loop

```
                     ┌────────────────────────────────┐
                     │          Coding Task           │
                     └───────────────┬────────────────┘
                                     │
                     ┌───────────────▼────────────────┐
                     │          Real LLM              │
                     │ (gpt-4o-mini via OpenAI SDK)   │
                     └───────────────┬────────────────┘
                                     │ Generates Solution
                                     ▼
                     ┌────────────────────────────────┐
                     │    Execution Verifier          │
                     │  (Isolated Subprocess Pytest)  │
                     └───────┬────────────────┬───────┘
                             │                │
            Exit Code != 0   │                │   Exit Code == 0
       (Test Assertion Fail) │                │  (All Tests Pass)
                             ▼                ▼
     ┌─────────────────────────────┐    ┌─────────────────────────────┐
     │ Capture Failed Attempt      │    │ Promote to VERIFIED         │
     │ - Approach summary          │    │ - Working code pattern      │
     │ - Exact pytest diagnostic   │    │ - Execution evidence record │
     │ - "DO NOT REPEAT" constraint│    │ - Key lessons learned       │
     └───────────────┬─────────────┘    └──────────────┬──────────────┘
                     │                                 │
                     └───────────────┬─────────────────┘
                                     ▼
                     ┌────────────────────────────────┐
                     │ Durable SQLite Experience Store│
                     │        (experiences.db)        │
                     └───────────────┬────────────────┘
                                     │
                 Fresh Session Starts (Zero Chat History)
                                     │
                     ┌───────────────▼────────────────┐
                     │  Retrieve Relevant Experience  │
                     │   - Injects verified patterns  │
                     │   - Injects DO NOT REPEAT rules│
                     └────────────────────────────────┘
```

---

## 🔄 Two-Session Lifecycle Walkthrough

This demo orchestrates two logically separated sessions to demonstrate cross-session transfer:

### 1. Session 1: The Learning Loop (Cold Start)
- The agent is assigned a coding task (`SlidingWindowRateLimiter`) with zero prior memory.
- The LLM generates an initial solution attempt.
- The **Execution Verifier** runs the real pytest suite in a sandboxed subprocess.
- If edge cases fail (e.g., fixed-interval counters allowing burst overflows at window boundaries), the agent inspects the test failure diagnostic, logs the failed approach into persistent memory under **DO NOT REPEAT**, and iterates.
- Once all unit tests pass (`exit_code == 0`), the solution is promoted to **`VERIFIED`** status along with duration, test counts, and timestamp evidence.

### 2. Session 2: Experience Transfer (Fresh Agent)
- The Session 1 agent instance and all scratchpad variables are deleted from memory.
- A **brand-new `CodingAgent`** instance is initialized with **zero conversational memory**.
- The agent queries the persistent SQLite database for the task.
- Memory returns the verified pattern and explicit negative constraints (`DO NOT REPEAT: Fixed window division allowed boundary bursts`).
- The LLM leverages these constraints to generate a correct, robust solution on **Attempt 1**.
- Subprocess tests confirm verification (`exit code 0`).

---

## 📂 Project Structure

```
verified_agent_memory/
├── app.py                     # Main runnable demo (Session 1 -> Session 2)
├── agent.py                   # CodingAgent using official OpenAI SDK
├── memory.py                  # SQLite-backed Structured Experience engine
├── verifier.py                # Safe subprocess test runner & evidence collector
├── models.py                  # Pydantic schemas for evidence & experiences
├── benchmark.py               # Empirical benchmarking harness
├── tasks/
│   └── rate_limiter/          # Real task with sliding window edge cases
│       ├── problem.py         # Starter template
│       ├── test_rate_limiter.py # Comprehensive pytest test suite
│       └── README.md          # Task specification
├── tests/
│   ├── conftest.py            # Test path configuration
│   ├── test_agent.py          # Unit tests for reasoning & mock iteration
│   ├── test_memory.py         # Unit tests for CRUD & status transitions
│   └── test_verifier.py       # Unit tests for subprocess execution & parsing
├── requirements.txt           # Minimal, standard dependencies
├── .env.example               # Template for environment variables
└── README.md                  # Documentation & tutorial
```

---

## 🚀 Quick Start

### 1. Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/advanced_llm_apps/llm_apps_with_memory_tutorials/verified_agent_memory
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy `.env.example` to `.env` and set your OpenAI API key:

```bash
cp .env.example .env
```

Edit `.env`:
```env
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
# Optional: Use any OpenAI-compatible provider (e.g., Ollama, vLLM, OpenRouter)
# OPENAI_BASE_URL=https://api.openai.com/v1
```

> **Note**: If `OPENAI_API_KEY` is not set, the application exits cleanly with setup instructions rather than falling back to fake responses.

### 3. Run the Demonstration

Run the complete cross-session learning loop (Session 1 + Session 2):

```bash
python app.py
```

#### Running across separate Python processes:
You can also run Session 1 and Session 2 in completely distinct process executions to verify memory survival across process boundaries:

```bash
# Step 1: Run Session 1 in its own process
python app.py --session 1

# Step 2: Inspect persistent SQLite storage from the CLI
python app.py --inspect

# Step 3: Run Session 2 in a fresh process (loads from SQLite, zero prior chat state)
python app.py --session 2
```

Optional CLI flags:
```bash
# Clean previous SQLite memory before running
python app.py --clean-db

# Specify custom SQLite database path
python app.py --db-path my_experiences.db
```

---

## 🧪 Running Unit Tests

All internal mechanics (subprocess execution, timeout handling, memory lifecycle, prompt formatting, and error iteration) are covered by automated unit tests that run offline without an API key:

```bash
pytest tests/ -v
```

Output:
```
tests/test_agent.py::test_missing_api_key_raises_error PASSED
tests/test_agent.py::test_extract_code_from_markdown PASSED
tests/test_agent.py::test_agent_run_session_iteration_and_learning_loop PASSED
tests/test_memory.py::test_record_candidate_and_retrieval PASSED
tests/test_memory.py::test_promote_to_verified_requires_passing_evidence PASSED
tests/test_memory.py::test_failed_approaches_retained_as_negative_constraints PASSED
tests/test_memory.py::test_environment_staleness_detection PASSED
tests/test_memory.py::test_retrieval_ranking PASSED
tests/test_verifier.py::test_verifier_successful_command PASSED
tests/test_verifier.py::test_verifier_failing_command PASSED
tests/test_verifier.py::test_verifier_timeout PASSED
tests/test_verifier.py::test_verify_solution_with_pytest PASSED

============================= 12 passed in 11.66s =============================
```

---

## 📊 Measured Execution Trace

Below is an actual, unscripted execution trace from running the application:

```text
######################################################################
🧠 VERIFIED AGENT MEMORY: CROSS-SESSION DEMONSTRATION
   Architecture: Real LLM + Subprocess Pytest Verification + Durable Memory
######################################################################

----------------------------------------------------------------------
▶️  SESSION 1: Solving Task from Scratch (Cold Start)
    - Memory Retrieval: DISABLED (No prior knowledge)
    - Goal: Discover solution, observe test feedback, capture failed attempts
----------------------------------------------------------------------
ℹ️  Running with zero prior experience context (cold start).
🔄 Attempt 1/3: Querying real LLM...
🧪 Attempt 1/3: Executing pytest in isolated subprocess...
   Result: Exit Code 1 | Passed: 4 | Failed: 1 | Duration: 0.42s
❌ Attempt 1 FAILED verification.
   Failure Diagnostic:
   E   assert limiter.allow_request("api_client", current_time=1.1) is False
   E   AssertionError: boundary burst allowed by naive bucket division
📝 Captured failed approach into memory under 'DO NOT REPEAT' constraints.

🔄 Attempt 2/3: Querying real LLM...
🧪 Attempt 2/3: Executing pytest in isolated subprocess...
   Result: Exit Code 0 | Passed: 5 | Failed: 0 | Duration: 0.38s
✅ Attempt 2 PASSED all verification tests!
💾 Promoted experience `exp_b48a1` to status: VERIFIED in persistent storage.

----------------------------------------------------------------------
🔄 DESTROYING SESSION 1 AGENT INSTANCE...
   Session 1 context, scratch variables, and conversation transcripts purged.
----------------------------------------------------------------------

▶️  SESSION 2: Fresh Agent Session with Memory Retrieval
    - Memory Retrieval: ENABLED (Structured Prior Lessons & Negative Constraints)
    - Conversation Transcript: NONE (Zero chat memory carried over)
    - Goal: Utilize verified pattern and avoid previously failed dead ends
----------------------------------------------------------------------
📦 Retrieved 1 verified experience(s) from persistent memory.
🔄 Attempt 1/3: Querying real LLM...
🧪 Attempt 1/3: Executing pytest in isolated subprocess...
   Result: Exit Code 0 | Passed: 5 | Failed: 0 | Duration: 0.37s
✅ Attempt 1 PASSED all verification tests!
💾 Promoted experience `exp_b48a1` to status: VERIFIED in persistent storage.

======================================================================
📊 EXECUTION TRACE & RUNTIME COMPARISON (MEASURED RUN)
======================================================================
Metric                              | Session 1 (Cold Start) | Session 2 (With Memory)
---------------------------------------------------------------------------------
Task Solved                         | YES                    | YES
Total Attempts to Verification      | 2                      | 1
Total Wall-Clock Time               | 12.45s                 | 4.10s
Memory Retrieval Used               | None                   | Retrieved Prior Exp
Negative Constraints Injected       | None                   | 1 DO NOT REPEAT rule
======================================================================
```

This example demonstrates how verified structured experience can be transferred between independent agent sessions.

---

## 🔬 Reproducible Benchmark Harness

To evaluate agent performance empirically across multiple runs rather than relying on claims, a benchmark harness is provided in `benchmark.py`.

> **Important**: `benchmark.py` requires an active `OPENAI_API_KEY` and performs live OpenAI API calls and real subprocess test executions for every trial. It does not contain predetermined or hardcoded metrics.

Run the benchmark:
```bash
python benchmark.py --task rate_limiter --trials 3 --output benchmark_results.json
```

The script records trial-by-trial outcomes (attempts, wall-clock time, pass/fail status) into the specified JSON file:
```json
{
  "task": "rate_limiter",
  "model": "gpt-4o-mini",
  "trials_requested": "<integer>",
  "timestamp": "<ISO-8601>",
  "cold_start_runs": [ ... ],
  "memory_assisted_runs": [ ... ],
  "summary": {
    "cold_start_avg_attempts": "<computed>",
    "memory_assisted_avg_attempts": "<computed>",
    "cold_start_avg_duration_s": "<computed>",
    "memory_assisted_avg_duration_s": "<computed>"
  }
}
```

---

## ⚖️ Realistic Limitations & Trade-offs

1. **Verification Requires Concrete Test Suites**: This architecture requires executable tests or verification criteria (e.g., unit tests, type checkers, linters). For open-ended creative tasks without objective verification gates, experience memory cannot formally prove correctness.
2. **Environment Drift**: A solution verified on Python 3.11 with `pydantic v2` may fail on Python 3.9 or `pydantic v1`. The built-in `check_environment_staleness()` detects version drift and marks experiences `STALE`, but domain-specific library shifts still require re-verification.
3. **Prompt Injection Overhead**: Injecting extensive verified code patterns into the prompt consumes context tokens. For large codebases, experiences should store architectural summaries and diffs rather than full multi-file listings.
4. **Does Not Eliminate All Hallucinations**: An LLM may still occasionally misinterpret a constraint; verification gates ensure such errors are caught immediately before being committed to memory.

---

## 🔌 Optional Enterprise Integration: CogniCore

This project implements a self-contained, standalone SQLite experience engine. For enterprise deployments requiring distributed multi-agent memory or hybrid vector search, the storage layer can be swapped to [CogniCore](https://github.com/CogniCore/cognicore):

```python
# Optional: Point memory backend to CogniCore SQLite or Remote Memory Engine
# from cognicore.memory.backends.sqlite import SQLiteMemoryBackend
# memory = ExperienceMemory(backend=SQLiteMemoryBackend(...))
```

---

## 📜 License

This tutorial is distributed under the MIT License, following the conventions of the [awesome-llm-apps](https://github.com/Shubhamsaboo/awesome-llm-apps) repository.
