# 🛡️ Self-Healing / Anti-Loop LangGraph Agent (Powered by Groq)

A production-ready **Loop-Detection Middleware Pattern** built with LangGraph and Groq (`llama-3.3-70b-versatile`) to prevent AI agents from getting stuck in infinite tool-calling loops and draining API credits.

## 🚨 The Problem
In production environments, autonomous agents often get trapped in "silent loops"—repeatedly calling the exact same failing tool with identical arguments.

## 💡 The Solution
This project implements a lightweight **Loop-Detection Node** using LangGraph's `StateGraph` and dynamic `interrupt()` mechanism:
1. **State Tracking:** Monitors the last 3 tool calls in the graph state.
2. **Automatic Circuit Breaker:** If the last 3 actions are identical, the graph triggers `interrupt()` to halt execution immediately.
3. **Human-in-the-Loop Recovery:** Prompts the user for new instructions and resumes execution seamlessly using `Command(resume=...)`.

## 🚀 How to Run
1. `pip install -r requirements.txt`
2. `export GROQ_API_KEY="your-groq-api-key"`
3. `python self_healing_agent.py`
