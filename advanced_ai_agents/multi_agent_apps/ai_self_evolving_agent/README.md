# 🧬 Self-Evolving AI Agent

A multi-agent app built on [EvoAgentX](https://github.com/EvoAgentX/EvoAgentX) that turns a
single natural-language goal into a working program. It **automatically generates a
multi-agent workflow**, executes it to produce code, then **verifies and repairs** that code
with a second model — no manual agent wiring required.

The included example takes the goal *"Generate HTML code for a Tetris game that can be played
in the browser"* and writes a ready-to-play `index.html`.

## ✨ What It Demonstrates

- **Automatic workflow generation** — `WorkFlowGenerator` designs the agents and steps from a plain-English goal.
- **Multi-agent execution** — `AgentManager` + `WorkFlow` instantiate and run the generated agents.
- **Cross-model code verification** — generation runs on OpenAI `gpt-4o-mini`; a separate Anthropic Claude pass verifies and fixes the output.
- **Self-evolving by design** — the workflow is built and refined by the system itself rather than hand-coded.

## 🛠️ How to Get Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd awesome-llm-apps/advanced_ai_agents/multi_agent_apps/ai_self_evolving_agent
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install git+https://github.com/EvoAgentX/EvoAgentX.git
   ```

3. **Set your API keys**
   ```bash
   export OPENAI_API_KEY=<your-openai-api-key>
   export ANTHROPIC_API_KEY=<your-anthropic-api-key>
   ```
   (Or place them in a `.env` file in this folder.)

4. **Run the agent**
   ```bash
   python ai_Self-Evolving_agent.py
   ```
   The generated game is written to `examples/output/tetris_game/index.html` — open it in a browser to play.

## 🔧 How It Works

1. **Define a goal** in natural language (e.g. build a Tetris game).
2. **Generate a workflow** — `WorkFlowGenerator` produces a multi-agent graph for the goal.
3. **Run the workflow** — `AgentManager` builds the agents and `WorkFlow` executes them with `gpt-4o-mini`.
4. **Verify the output** — a Claude model (via LiteLLM) reviews and repairs the generated code through `CodeVerification`.
5. **Save the result** — the final code is extracted and written to the output directory.

## 📚 Learn More

This example is powered by the open-source **EvoAgentX** framework. For docs, tutorials, and
additional optimizers (TextGrad, AFlow, MIPRO), see the
[EvoAgentX repository](https://github.com/EvoAgentX/EvoAgentX).
