<div align="center">

  <h1>🪟 Windows Use Autonomous Agent</h1>

  <a href="https://github.com/CursorTouch/windows-use/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  </a>
  <img src="https://img.shields.io/badge/python-3.12%2B-blue" alt="Python">
  <img src="https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-blue" alt="Platform">
  <br>

  <a href="https://x.com/CursorTouch">
    <img src="https://img.shields.io/badge/follow-%40CursorTouch-1DA1F2?logo=twitter&style=flat" alt="Follow on Twitter">
  </a>
  <a href="https://discord.com/invite/Aue9Yj2VzS">
    <img src="https://img.shields.io/badge/Join%20on-Discord-5865F2?logo=discord&logoColor=white&style=flat" alt="Join us on Discord">
  </a>

</div>

<br>

**Windows-Use** is a powerful automation agent that interact directly with the Windows at GUI layer. It bridges the gap between AI Agents and the Windows OS to perform tasks such as opening apps, clicking buttons, typing, executing shell commands, and capturing UI state all without relying on traditional computer vision models. Enabling any LLM to perform computer automation instead of relying on specific models for it.

## 🛠️Installation Guide

### **Prerequisites**

- Python 3.12 or higher
- [UV](https://github.com/astral-sh/uv) (or `pip`)
- Windows 10 or 11

### **Installation Steps**

**Install using `uv`:**

```bash
uv pip install windows-use
````

Or with pip:

```bash
pip install windows-use
```

## ⚙️Basic Usage

```python
# main.py
from langchain_google_genai import ChatGoogleGenerativeAI
from windows_use.agent import Agent
from dotenv import load_dotenv

load_dotenv()

llm=ChatGoogleGenerativeAI(model='gemini-2.0-flash')
agent = Agent(llm=llm,use_vision=True)
query=input("Enter your query: ")
agent_result=agent.invoke(query=query)
print(agent_result.content)
```

## 🤖 Run Agent

You can use the following to run from a script:

```bash
python main.py
Enter your query: <YOUR TASK>
```

---

## 🎥 Demos

**PROMPT:** Write a short note about LLMs and save to the desktop

<https://github.com/user-attachments/assets/0faa5179-73c1-4547-b9e6-2875496b12a0>

**PROMPT:** Change from Dark mode to Light mode

<https://github.com/user-attachments/assets/47bdd166-1261-4155-8890-1b2189c0a3fd>

## Vision

Talk to your computer. Watch it get things done.

## Roadmap

### 🤖 Agent Intelligence

* [ ] **Integrate memory** : allow the agent to remember past interactions made by the user.
* [ ] **Optimize token usage** : implement strategies like Ally Tree compression and prompt engineering to reduce overhead.
* [ ] **Simulate advanced human-like input** : enable accurate and naturalistic mouse & keyboard interactions across apps.
* [ ] **Support for local LLMs** : local models with near-parity performance to cloud-based APIs (e.g., Mistral, LLaMA, etc.).
* [ ] **Improve reasoning and planning** : enhance the agent's ability to break down and sequence complex tasks.

### 🌳 Ally Tree Optimization

* [ ] **Improve UI element detection** : automatically identify and prioritize essential, interactive components on screen.
* [ ] **Compress Ally Tree intelligently** : reduce complexity by pruning irrelevant branches.
* [ ] **Context-aware prioritization** : rank UI elements based on relevance to the task at hand.

### 💡 User Experience

* [ ] **Reduce latency** : optimize to improve response time between GUI interaction.
* [ ] **Polish command interface** : make it easier to write, speak, or type commands through a simplified UX layer.
* [ ] **Better error handling & recovery** : ensure graceful handling of edge cases and unclear instructions.

### 🧪 Evaluation

* [ ] **LLM evaluation benchmarks** — track performance across different models and benchmarks.

## ⚠️ Caution

Agent interacts directly with your Windows OS at GUI layer to perform actions. While the agent is designed to act intelligently and safely, it can make mistakes that might bring undesired system behaviour or cause unintended changes. Try to run the agent in a sandbox envirnoment.

## 🪪 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please check the [CONTRIBUTING](CONTRIBUTING) file for setup and development workflow.

Made with ❤️ by [Jeomon George](https://github.com/Jeomon)

---

## Citation

```bibtex
@software{
  author       = {George, Jeomon},
  title        = {Windows-Use: Enable AI to control Windows OS},
  year         = {2025},
  publisher    = {GitHub},
  url={https://github.com/CursorTouch/Windows-Use}
}
```
