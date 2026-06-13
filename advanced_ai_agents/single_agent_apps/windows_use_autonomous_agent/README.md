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

## 🔒 Security / Safe Mode

This agent ships with a **Shell Tool** that can run PowerShell on your machine, and a
**Scrape Tool** that pulls arbitrary web pages into the model's context. Together these
create a real **prompt-injection → remote-code-execution** path: a malicious web page the
agent reads could try to talk the model into running destructive PowerShell as your user.

To contain this, shell execution is **safe-by-default**:

- **Off by default.** The Shell Tool refuses to run unless you set `WINDOWS_USE_ENABLE_SHELL=1`.
  When off, the agent still works — it falls back to GUI automation (Launch/Click/Type/Shortcut).
- **Destructive-command deny-list (always on).** Even when enabled, commands matching known
  destructive/persistence/exfil patterns (disk format, recursive delete, shadow-copy
  deletion, `iex`+web-download droppers, Defender tampering, scheduled-task persistence,
  account creation, etc.) are blocked and never executed.
- **Per-command confirmation.** Each command is shown to you for an interactive `y/N`
  approval (default **No**). Set `WINDOWS_USE_SHELL_AUTO_APPROVE=1` to skip the prompt for
  unattended runs — the deny-list still applies, but **only do this in a throwaway VM**.
- **Audit log (optional).** Set `WINDOWS_USE_SHELL_LOG=<path>` to append every decision
  (`RUN` / `BLOCKED` / `DECLINED`) with a timestamp.

> **Honest caveat:** a deny-list can never catch every dangerous command — PowerShell has
> too many ways to express the same action. The deny-list is defense-in-depth for the
> auto-approve case. The genuine protections are **off-by-default** and **per-command
> confirmation**. Treat enabling shell on an autonomous agent as inherently risky and run it
> in a disposable VM or a throwaway, non-admin account.

See `.env-example` for all switches. The safety logic lives in
`windows_use/desktop/shell_policy.py` (pure-stdlib, unit-tested in `tests/test_shell_policy.py`).

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

Agent interacts directly with your Windows OS at GUI layer to perform actions. While the agent is designed to act intelligently and safely, it can make mistakes that might bring undesired system behaviour or cause unintended changes. Try to run the agent in a sandbox envirnoment. If you enable the Shell Tool (`WINDOWS_USE_ENABLE_SHELL=1`), also read the [Security / Safe Mode](#-security--safe-mode) section above — running LLM-generated PowerShell on a real machine is inherently risky.

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
