<div align="center">

# 🧠 OpenAgents Multi-Agent Research Team

🚀 A production-ready multi-agent collaboration demo built with OpenAgents  
📦 Designed for Awesome-LLM-Apps showcase  
⚡ Uses default `openagents init` network (no custom YAML required)

</div>

---

## ✨ Overview

This project demonstrates a fully automated **multi-agent research workflow** using the OpenAgents framework.

It models a collaborative research team composed of:

- 📋 **Planner** – Breaks down user requests into structured plans  
- 🔎 **Researcher** – Generates detailed research notes  
- 🧠 **Critic** – Reviews and improves the output  
- ✍️ **Writer** – Produces the final Markdown report  

Agents communicate via OpenAgents workspace channels using the official `workspace()` API.

No custom YAML.  
No low-level event hacks.  
Only recommended framework interfaces.

---

## 🏗 Architecture

### Agent Pipeline

```
User (#general)
      ↓
Planner (#ideas)
      ↓
Researcher (#discussion)
      ↓
Critic (#pitch-room)
      ↓
Writer (writes file + posts result)
```

### Channel Flow

```
general → ideas → discussion → pitch-room → discussion
```

---

## 🚀 Quick Start

### 1️⃣ Install

```bash
pip install openagents
```

### 2️⃣ Initialize Network

```bash
openagents init my_first_network
cd my_first_network
```

> Do NOT modify `network.yaml`.

---

### 3️⃣ Set OpenAI API Key

**Windows (PowerShell)**

```powershell
$env:OPENAI_API_KEY="your_key_here"
```

**macOS / Linux**

```bash
export OPENAI_API_KEY="your_key_here"
```

---

### 4️⃣ Start Network

```bash
openagents network start
```

---

### 5️⃣ Start Agents (Recommended: gRPC)

Open four separate terminals:

```bash
python planner_agent.py --url grpc://localhost:8600
python researcher_agent.py --url grpc://localhost:8600
python critic_agent.py --url grpc://localhost:8600
python writer_agent.py --url grpc://localhost:8600
```

---

## 💬 Usage

1. Open the OpenAgents UI  
2. Navigate to **#general**  
3. Send a message, for example:

```
Explain the difference between multi-agent and single-agent systems.
```

The agents will automatically collaborate and generate a structured research report.

---

## 📄 Output

The final report:

- Appears in **#discussion**
- Is saved locally as:

```
report_<run_id>.md
```

Example:

```
report_aba50bd9.md
```

---

## 🔥 Why This Demo Matters

This project demonstrates:

- Multi-agent orchestration using a production-ready framework
- Clean separation of agent responsibilities
- Structured channel-based collaboration
- End-to-end automated content generation
- Official workspace API usage (no internal event hacks)

It serves as a minimal and reproducible template for building multi-agent systems with OpenAgents.

---

## 🧪 Optional: Mock Mode

Run without OpenAI API calls:

```bash
export OPENAGENTS_MOCK=1
```

---

## ⚠️ Troubleshooting

### Agents not responding?

- Ensure you send messages in `#general`
- Verify all agents are running
- Use `grpc://localhost:8600`
- Confirm API key is set in each terminal

### "Agent already registered"?

Stop old processes or restart the network.

---

## 🧩 Built With

- OpenAgents Official Website: https://openagents.org  
- OpenAgents GitHub: https://github.com/openagents-org/openagents  

---

## 📦 Project Structure

```
openagents_research_team/
│
├── planner_agent.py
├── researcher_agent.py
├── critic_agent.py
├── writer_agent.py
├── requirements.txt
└── README.md
```

---