# 🤝 Mixture-of-Agents LLM App

Ask one question to several LLMs, then have an aggregator model combine their answers into a single, higher-quality response. This is the **Mixture-of-Agents** approach: different models catch different details and make different mistakes, so combining them gives a more complete and balanced answer than any one model alone.

---

## 📁 What's Inside

| File | Runs on | Needs |
|---|---|---|
| `mixture-of-agents.py` | [Together AI](https://www.together.ai/) cloud models (Qwen 72B, Mixtral 8x22B, DBRX) | Together API key |
| `local_mixture_of_agents.py` | Local models with [Ollama](https://ollama.com/) (Llama 3.2, Qwen 2.5, Gemma 2) | No API key, runs fully offline |

**Local version (`local_mixture_of_agents.py`)**

**✅ Pros:**
- Free, no API key
- Private: your questions never leave your machine
- Pick any models you have in Ollama

**❌ Cons:**
- Slower on CPU (models run one after another)
- Small local models are less capable than the 72B cloud models

---

## 🚀 Getting Started

1. **Clone the repository**
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/starter_ai_agents/mixture_of_agents
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Choose a model backend**

**Option A – Together AI** (`mixture-of-agents.py`)
- Sign up at [together.ai](https://www.together.ai/) and create an API key
- Run the app and paste the key when prompted:
```bash
streamlit run mixture-of-agents.py
```

**Option B – Local models with Ollama** (`local_mixture_of_agents.py`)
- Install Ollama from [ollama.com/download](https://ollama.com/download) (Windows, macOS, Linux)
- Make sure the Ollama server is running on `http://localhost:11434`. On Windows and macOS the desktop app starts it automatically; otherwise run `ollama serve`. If you see `bind: Only one usage of each socket address`, the server is already running.
- Pull the recommended models (about 2 GB each). This is optional, because the app downloads any missing model the first time you use it:
```bash
ollama pull llama3.2:latest
ollama pull qwen2.5:3b
ollama pull gemma2:2b
```
- Run the app:
```bash
streamlit run local_mixture_of_agents.py
```

You don't need to `ollama run` any model yourself. The app calls the Ollama server, which loads each model when it's needed.

---

## 🖥️ Using the Local App

**Sidebar**
- **Ollama URL:** change this if Ollama runs on another machine or port
- **Reference models:** the models that each answer your question. They default to `llama3.2:latest`, `qwen2.5:3b` and `gemma2:2b`, three different model families, so the answers genuinely differ. Models marked *(will download)* are pulled automatically on first use, with a progress bar.
- **Aggregator model:** the model that combines the answers (default `llama3.2:latest`)

**Results**
- **1️⃣ What each model says:** each reference model's answer streams into its own card, with how long it took
- **2️⃣ Final answer:** the aggregator's combined answer, streamed into a separate box

Any other chat model you pull with Ollama (for example `mistral` or `phi3.5`) shows up in the sidebar automatically. Embedding-only models such as `nomic-embed-text` are hidden.

---

## 🧪 Example Questions

| Question | What to look for |
|---|---|
| What is the capital of Australia? One sentence. | Quick check that everything works (about 1 minute on CPU) |
| Explain the difference between TCP and UDP with one real-world example each. | How models pick different examples, and how the final answer merges them |
| What are the pros and cons of remote work? | Each model covers different points; the final answer should be the most complete |
| Is a tomato a fruit or a vegetable? | Models may disagree; see how the aggregator resolves it |

---

## 🔧 How It Works

1. Your question is sent to each selected reference model
2. Each model answers independently. Locally, they run one at a time because they share the same CPU/GPU
3. All answers are numbered, labelled with the model name, and passed to the aggregator along with your original question
4. The aggregator critically evaluates them and writes one refined final answer

---

## ⚡ Performance Tips

- On CPU, each 2–3B model takes roughly 10–30 seconds for a short answer. Check whether you're on CPU or GPU with `ollama ps`.
- Ask for short answers ("in 3 bullet points") to speed things up.
- Use fewer reference models, or smaller ones like `llama3.2:1b`, when testing.

---

## 📖 Documentation

- **Mixture-of-Agents paper:** [Mixture-of-Agents Enhances Large Language Model Capabilities](https://arxiv.org/abs/2406.04692)
- **Ollama:** [ollama.com](https://ollama.com/) · [Model library](https://ollama.com/library)
- **Together AI:** [docs.together.ai](https://docs.together.ai/)
