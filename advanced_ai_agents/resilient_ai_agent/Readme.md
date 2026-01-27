# Resilient AI Agent

This advanced AI agent demonstrates **production-grade patterns** for building reliable AI agents.

## Features
- Task planning
- Short-term and long-term memory
- Output evaluation
- Retry & failure handling
- Modular architecture

## Architecture
User → Planner → LLM Tool → Evaluator → Memory → Output


## How to Run
```bash
pip install -r requirements.txt
set OPENAI_API_KEY=your_key_here   # Windows
python agent.py
