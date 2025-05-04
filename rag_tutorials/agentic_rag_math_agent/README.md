# 🧠 Math Tutor Agent – Agentic RAG with Feedback Loop

This project implements an **Agentic-RAG architecture** to simulate a math professor that solves **JEE-level math questions** with step-by-step explanations. The system smartly routes queries between a vector database and web search, applies input/output guardrails, and incorporates human feedback for continuous learning.

## 📌 Features

- ✅ **Input Guardrails** (DSPy): Accepts only academic math questions.
- 📚 **Knowledge Base Search**: Uses **Qdrant Vector DB** with OpenAI Embeddings to match known questions.
- 🌐 **Web Fallback**: Integrates **Tavily API** when no good match is found.
- ✍️ **GPT-4.1 Explanations**: Generates step-by-step math solutions.
- 🛡️ **Output Guardrails**: Filters for correctness and safety.
- 👍 **Human-in-the-Loop Feedback**: Users rate answers (Yes/No), logged for future learning.
- 📊 **Benchmarking**: Evaluated on **JEEBench** dataset with adjustable question limits.
- 💻 **Streamlit UI**: Interactive dashboard with multiple tabs.

## 🚀 Architecture Flow
<img width="465" alt="Screenshot 2025-05-04 at 3 45 58 PM" src="https://github.com/user-attachments/assets/c0a9e612-2ef0-413c-b779-c99fe9f48619" />


## 📚 Knowledge Base

- **Dataset:** [JEEBench (HuggingFace)](https://huggingface.co/datasets/daman1209arora/jeebench)
- **Vector DB:** Qdrant (with OpenAI Embeddings)
- **Storage:** Built with `llama-index` to persist embeddings and perform top-1 similarity search

## 🌐 Web Search

- Uses **Tavily API** for fallback search when the KB doesn't contain a good match
- Fetched content is piped into **GPT-4o** for clean explanation


## 🔐 Guardrails

- **Input Guardrail (DSPy):** Accepts only math-related academic questions
- **Output Guardrail (DSPy):** Blocks hallucinated or off-topic content


## 👨‍🏫 Human-in-the-Loop Feedback

- Streamlit UI allows students to give 👍 / 👎 after seeing the answer
- Feedback is logged to a local JSON file for future improvement

## 📊 Benchmarking

- Evaluated on **50 random JEEBench Math Questions**
- **Current Accuracy:** 66%
- Benchmark results saved to: `benchmark/results.csv`


## 🚀 Demo 

To run the app with Streamlit:

```bash
streamlit run app/streamlit.py




