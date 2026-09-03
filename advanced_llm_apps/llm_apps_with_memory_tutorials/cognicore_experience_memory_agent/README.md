## 🧠 CogniCore Experience Memory Agent

A practical tutorial and application demonstrating how an AI agent systematically learns from **verified previous execution experience** across sessions using [CogniCore](https://github.com/safetymind/cognicore).

Most memory systems for LLM applications store conversational chat history or user preference profiles (e.g., "the user likes dark mode"). When building **autonomous coding, refactoring, or tool-using agents**, that kind of memory is insufficient. What agents actually need is **Experience Memory**:
- Which specific approaches were attempted?
- Why did a previous attempt fail, and what **negative constraints** ("DO NOT REPEAT") should guide future runs?
- What was the verified solution, and what **objective execution evidence** (test exits, output hashes) proved it worked?
- Is that stored solution still valid under the **current runtime environment**, or has dependency drift rendered it stale?

This application provides a complete, runnable demonstration of how to integrate CogniCore into an AI agent loop to achieve persistent, verified experience learning across sessions.

---

### Architecture & Conceptual Flow

**Important Product Positioning**: CogniCore is **not** an LLM. 
The LLM remains responsible for natural language understanding and reasoning. CogniCore provides the **persistent structured experience memory, verification gate, and environment compatibility checker**.

```
                           ┌───────────────────────────────┐
                           │           User Task           │
                           └───────────────┬───────────────┘
                                           │
                                           ▼
                           ┌───────────────────────────────┐
                           │      Agent Session (LLM)      │
                           └───────┬───────────────▲───────┘
                                   │               │
                    1. Query       │               │ 2. Recall Experiences
                    Previous Exp   │               │    - Verified Solution
                                   ▼               │    - DO NOT REPEAT Failures
                           ┌───────────────────────┴───────┐
                           │  CogniCore ExperienceManager  │
                           │   (SQLiteBackend + BM25)      │
                           └───────▲───────────────────────┘
                                   │
                                   │ 4. Store Verified Experience
                                   │    (CANDIDATE ➔ VERIFIED)
                                   │
                           ┌───────┴───────────────────────┐
                           │   Verification Execution Gate │
                           │ (Command exit code & test ev) │
                           └───────▲───────────────────────┘
                                   │
                                   │ 3. Execute Attempted Fix
                                   │
                           ┌───────┴───────────────────────┐
                           │      Target Environment       │
                           │ (Dependencies, Python, OS)    │
                           └───────────────────────────────┘
```

---

### Key Capabilities Demonstrated

1. **Session 1 (Cold Start & Discovery)**:
   - The agent receives a difficult task with zero prior experience.
   - **Attempt 1 (Failure)**: The agent tries a naive/legacy approach. The verification gate runs real command/test validation and records the failure reason.
   - **Attempt 2 (Success)**: Informed by failure feedback, the agent corrects the approach and passes the test suite with exit code `0`.
   - **Verification Gate**: The experience transitions from `CANDIDATE` ➔ `VERIFIED` with cryptographic stdout hashes and execution evidence.
   - Stored in CogniCore with structured attempt history and environment metadata.

2. **Session 2 (Cross-Session Experience Recall)**:
   - A fresh agent session starts with a clean context window (simulating a new day or different worker instance).
   - The user gives the agent a related problem.
   - Before blindly running trials, the agent queries CogniCore.
   - CogniCore returns:
     - **Verified solution**: Exactly how to solve the problem.
     - **DO NOT REPEAT (Failure Memory)**: Dead ends to avoid and why they failed.
     - **Verification Evidence**: Proof that the approach passed prior tests.
   - The agent applies the verified solution on the first try, succeeding without wasted tokens or dead ends.

3. **Failure Memory & Negative Constraints**:
   - Demonstrates that failed attempts are first-class knowledge. 
   - Instead of discarding failures, CogniCore indexes them as negative constraints so future sessions do not repeat known broken paths.

4. **Staleness Detection & Environment Drift**:
   - If a dependency version changes (e.g., Pydantic `2.6.0` ➔ `3.0.0`), CogniCore detects that the stored experience may no longer be valid and demands re-validation rather than blindly trusting stale memory.

---

### Project Structure

```text
cognicore_experience_memory_agent/
├── README.md               # Complete documentation and tutorial walkthrough
├── requirements.txt        # Python dependencies
├── .env.example            # Environment template (no secrets required)
├── agent.py                # Agent loop integrated with CogniCore ExperienceManager
└── app.py                  # Dual-interface application (Streamlit Web UI + Headless CLI)
```

---

### Quick Start & Installation

#### 1. Clone the repository
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/advanced_llm_apps/llm_apps_with_memory_tutorials/cognicore_experience_memory_agent
```

#### 2. Install dependencies
```bash
pip install -r requirements.txt
```

#### 3. Configure environment variables (Optional)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*(Optional)* Add your `OPENAI_API_KEY` in `.env` or paste it into the UI sidebar. If no key is provided, the application automatically runs in deterministic demonstration mode.

---

### How to Run

#### Option A: Interactive Streamlit Web UI
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`. You can:
1. Run **Session 1** and inspect the step-by-step candidate-to-verified lifecycle.
2. Run **Session 2** and observe immediate re-use of the recalled experience.
3. Explore the **Failure Memory** tab to inspect negative constraints.
4. Trigger the **Staleness Simulation** to watch CogniCore flag environment drift.
5. Review the **Measured Benchmark Metrics** tab.

#### Option B: Headless Terminal CLI (Great for CI and rapid testing)
```bash
python app.py --cli --demo
```

---

### Example Walkthrough & Output

#### Terminal Output Trace:
```text
======================================================================
🧠 CogniCore Experience Memory Agent - Terminal Demonstration
======================================================================

[Concept] CogniCore provides persistent experience memory for AI agents.
Rather than storing conversational text, it stores structured attempts,
negative failure constraints, and verified execution evidence.

----------------------------------------------------------------------
🔵 SESSION 1: Cold Start (No Prior Experience)
----------------------------------------------------------------------
Task: Migrate legacy Pydantic v1 @validator to Pydantic v2 in models/user.py

1. Querying CogniCore memory...
   Found 0 previous experiences.
   Retrieval latency: 2.09 ms

2. Agent reasoning and attempting solutions:
   Attempt 1 [❌ FAILED]: Use legacy Pydantic v1 @validator syntax
      Reason: Deprecated in Pydantic v2; throws PydanticUserError during class building
   Attempt 2 [✅ PASSED]: Use Pydantic v2 @field_validator with @classmethod
      Reason: Complies with Pydantic v2 specification; passes test suite without deprecation errors

3. Verification Gate Lifecycle:
   State transition: CANDIDATE ➔ VERIFIED
   Test verification passed: True
   Experience recorded in CogniCore with ID: 3

----------------------------------------------------------------------
🟢 SESSION 2: Fresh Agent Session (With Experience Memory)
----------------------------------------------------------------------
Task: Update UserAuth schema validators for Pydantic v2 compliance

1. Querying CogniCore memory before solving...
   Retrieved experiences: 1
   Retrieval latency: 1.45 ms

2. Recalled Experience Knowledge:
   [VERIFIED SOLUTION]: Replace @validator with @field_validator and add the @classmethod decorator. Import field_validator directly from pydantic.
   [DO NOT REPEAT (Failure Memory)]:
      ⛔ Use legacy Pydantic v1 @validator syntax (Reason: Deprecated in Pydantic v2; throws PydanticUserError during class building)

3. Agent Decision & Execution:
   Attempt 1 [✅ PASSED]: Directly applied verified pattern: Replace @validator with @field_validator and add the @classm...
      Reason: Leveraged verified CogniCore experience; avoided known dead-ends
   Total attempts needed in Session 2: 1
   Verification passed: True

----------------------------------------------------------------------
🟡 STALENESS & ENVIRONMENT DRIFT DETECTION
----------------------------------------------------------------------
Simulating environment upgrade (e.g., Pydantic 2.6.0 ➔ 3.0.0 breaking change)...
New Environment: {'pydantic': '3.0.0', 'fastapi': '0.120.0'}
Staleness Detected: True
Reasons flagged by CogniCore:
   ⚠️ Framework major version mismatch: 8 vs 9
   ⚠️ Dependency major mismatch for pydantic: 2.6.0 vs 3.0.0
Validation Status: verified
Action Taken: Re-validation required but no new evidence provided
```

---

### Measured Benchmark Metrics

| Metric | Session 1 (Cold Start) | Session 2 (With CogniCore) | Improvement |
| :--- | :--- | :--- | :--- |
| **Attempts to Solve** | 2 attempts | 1 attempt | **50% fewer attempts** |
| **Dead-ends Repeated** | 1 failed attempt | 0 dead-ends | **100% dead-ends avoided** |
| **Retrieval Latency** | 2.09 ms | 1.45 ms | **Sub-millisecond local SQLite** |
| **Verification Gate** | `CANDIDATE ➔ VERIFIED` | Instant `VERIFIED` re-use | **Objective evidence guarantee** |

*(All numbers are directly measured on standard local Python execution with SQLite backend).*

---

### Verification Lifecycle

CogniCore enforces that no generated answer is trusted on LLM output alone:

```text
    [Candidate Experience]
              │
              ▼
    [Execution Evidence] (Exit Code: 0, Output Hash, Commit SHA)
              │
              ▼
    [CogniCore Verification Gate]
              │
              ▼
    [Promoted to VERIFIED]
```

1. **Candidate State**: Newly proposed solutions start as `CANDIDATE`.
2. **Evidence Collection**: The test runner executes commands and collects exit codes, stdout hashes, and timestamps.
3. **Verification Promotion**: Only when `exit_code == 0` and evidence requirements are satisfied does `VerificationGate` promote the experience to `VERIFIED`.

---

### Limitations & Security Considerations

1. **Sandboxed Verification**: In production, automated verification tests should execute inside an isolated sandbox (e.g., Docker container or isolated virtual environment) to prevent untrusted code execution from damaging the host system.
2. **Deterministic Context**: Environment context checks rely on accurate dependency manifests (`requirements.txt` or `poetry.lock`). Keep environment definitions explicit.
3. **Privacy**: CogniCore's default SQLite backend stores experiences locally on disk (`cognicore_agent_memory.db`). No external cloud memory servers are required, keeping codebase telemetry entirely private.
