## 🔄 Loopy Agent Orchestrator

A kanban-style multi-agent workflow that uses three specialized agents (Researcher, Builder, Supervisor) to take a product idea from concept to implementation plan.

### Features

- **Kanban-style orchestration**: Three agents work in sequence — Researcher, Builder, Supervisor
- **Context-aware handoffs**: Each agent receives the output of the previous stage
- **Dark-themed dashboard**: Professional Streamlit UI with real-time progress tracking
- **Model flexibility**: Supports any OpenAI-compatible model (gpt-4o, gpt-4o-mini, etc.)
- **Execution metrics**: Tracks agent count, execution time, and output statistics

### How to get started?

1. **Clone the repo**
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd awesome-llm-apps/starter_ai_agents/loopy_agent_orchestrator
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Get your OpenAI API Key**
   - Sign up at [OpenAI Platform](https://platform.openai.com/)
   - Create a new API key from the dashboard

4. **Run the app**
   ```bash
   streamlit run agent_orchestrator.py
   ```

### How it works?

1. **Supervisor** receives your product idea and delegates to specialized agents
2. **Researcher** analyzes the idea — market context, technical approach, key considerations
3. **Builder** creates an implementation plan — architecture, steps, code snippets
4. **Supervisor** synthesizes everything into an executive summary with feasibility assessment

### Example use case

Enter an idea like: *"A mobile app that uses computer vision to identify plants from photos and provides care instructions"* — the agents will research similar products, design the architecture, and produce a build-ready plan.

### Configuration

- **OpenAI API Key**: Enter in the sidebar or set `OPENAI_API_KEY` environment variable
- **Model selection**: Choose from available OpenAI models in the sidebar dropdown
