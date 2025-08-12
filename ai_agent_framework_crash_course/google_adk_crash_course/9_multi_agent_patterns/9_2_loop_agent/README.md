# 🔁 Tutorial 9.2: Loop Agents - Iterative Plan Refiner

## 🎯 What You'll Learn

- **Loop Agent Composition**: Execute sub-agents sequentially in a loop
- **Stateful Iterations**: Persist counters and flags across iterations
- **Termination Conditions**: Stop by reaching a max or when a sub-agent escalates
- **Streamlit Web Interface**: Interactive UI to run iterative refinements

## 🧠 Core Concept: LoopAgent with Condition

According to the ADK workflow agents documentation, **LoopAgent** repeats a set of sub-agents while sharing the same context/state across iterations. This tutorial demonstrates an **Iterative Plan Refiner** that improves a plan over multiple iterations and stops when a condition is met.

```
Topic → LoopAgent → [Refine Plan] → [Increment Iteration] → [Check Completion]
        ↑                                                        │
        └──────────────────────────── Repeat until stop ─────────┘
```

**Termination**: The loop stops if the optional `max_iterations` is reached, or if any sub-agent returns an `Event` with `escalate=True` in its `EventActions`.

**Context & State**: The same `InvocationContext` and `session.state` are used across iterations, allowing values like `iteration`, `target_iterations`, and `accepted` to persist and control the loop.

## 📁 Project Structure

```
9_2_loop agent/
├── agent.py              # LoopAgent with 3 sub-agents and session-state control
├── app.py                # Streamlit UI to run the loop refinement
└── README.md             # This documentation
```

## 🚀 Getting Started

### 1. Install Dependencies
```bash
cd "9_2_loop agent"
pip install -r ../9_1_sequential_agent/requirements.txt
```

### 2. Set Up Environment
Create a `.env` file with your Google API key (or reuse from the sequential example):
```bash
echo "GOOGLE_API_KEY=your_ai_studio_key_here" > .env
```

### 3. Run the Streamlit App
```bash
streamlit run app.py
```

## 🧪 How It Works

- **plan_refiner (LlmAgent)**: Produces a concise, improved plan each iteration.
- **increment_iteration (BaseAgent)**: Increments `session.state['iteration']`.
- **check_completion (BaseAgent)**: Escalates (to stop) if `accepted=True` or `iteration >= target_iterations`.

The `LoopAgent` sequences these sub-agents on every iteration, persisting and updating state until a stop condition is met.

### Session State Keys
- **topic**: The subject being refined.
- **iteration**: Current iteration counter.
- **target_iterations**: Loop budget before stopping.
- **accepted**: When set to `True`, the loop stops immediately.

## 🧪 Try It
- Enter a topic (e.g., "AI-powered customer support platform launch plan").
- Set `Target iterations` to 3–5.
- Run and observe the final refined plan and run metadata.

## 🔧 ADK Concepts Demonstrated
- **LoopAgent pattern** with sequential sub-agents.
- **Session state persistence** across iterations.
- **Escalation-based termination** with `EventActions(escalate=True)`.
- **Runner + SessionService** execution pattern.

## 🔎 Troubleshooting
- Ensure `GOOGLE_API_KEY` is set in `.env`.
- Run from the directory containing `app.py`.
- If you previously ran the app, the same session id is reused; changing the topic or target updates state accordingly.

## 📚 Key Takeaways
- **LoopAgent** enables iterative refinement workflows.
- **Shared state** allows complex control signals to accumulate across iterations.
- **Clean, modular sub-agents** keep the loop logic clear and maintainable.


