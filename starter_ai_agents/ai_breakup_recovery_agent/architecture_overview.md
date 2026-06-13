# 🏗️ Breakup Recovery Squad: Code Architecture

The **Breakup Recovery Squad** is designed as a multi-agent application using **Streamlit** for the frontend interface and the **Agno (formerly Phidata)** framework for agent orchestration, powered by **OpenAI's GPT-4o** model.

Below is a detailed breakdown of the application layers, components, and data flow.

---

## 🗺️ Architecture Overview Diagram

```mermaid
graph TD
    %% User Inputs
    User([User]) -->|Inputs Feelings / Chats| StreamlitUI[Streamlit Frontend UI]
    User -->|Provides API Key| Sidebar[Streamlit Sidebar]

    %% Configuration & Initialization
    Sidebar -->|API Key| InitAgents[initialize_agents Function]

    %% Image Processing
    StreamlitUI -->|Uploads Screenshots| TempFiles[Tempfile Handler]
    TempFiles -->|Agno Image Files| Team[Relationship Recovery Coordinator Team]

    %% Team & Agents
    subgraph "Agno Team (GPT-4o)"
        InitAgents --> Team
        Team -->|Members| Therapist[Therapist Agent]
        Team -->|Members| Closure[Closure Agent]
        Team -->|Members| Routine[Routine Planner Agent]
        Team -->|Members| Honesty[Brutal Honesty Agent]
    end

    %% Tools
    Honesty -->|Searches Web| DDG[DuckDuckGo Search Tool]

    %% Execution & Synthesis
    Therapist -->|Empathetic Support| Team
    Closure -->|Closure Rituals| Team
    Routine -->|7-Day Routine| Team
    Honesty -->|Objective Feedback| Team

    Team -->|Synthesized Roadmap| RenderRoadmap[Render Roadmap]
    RenderRoadmap --> StreamlitUI
```

---

## 📂 Core Architectural Layers

### 1. Frontend & Presentation Layer ([Streamlit](file:///Users/xili/Documents/codes/github/awesome-llm-apps/starter_ai_agents/ai_breakup_recovery_agent/ai_breakup_recovery_agent.py#L83-150))
*   **Sidebar Config**: Securely takes the OpenAI API key, checks environment variables via `os.environ.get("OPENAI_API_KEY", "")` to auto-populate, and stores it in `st.session_state`.
*   **User Input Panel**: Collects a narrative of the breakup (text field) and optional chat screenshots (multi-file uploader).
*   **Response Renderer**: Groups outputs from individual agents into distinct sections using Markdown for structured formatting.

### 2. Multi-Agent Orchestration Layer ([Agno Framework](file:///Users/xili/Documents/codes/github/awesome-llm-apps/starter_ai_agents/ai_breakup_recovery_agent/ai_breakup_recovery_agent.py#L16-91))
Agno's Team class orchestrates a group of specialist agents sharing a model configuration ([OpenAIChat](file:///Users/xili/Documents/codes/github/awesome-llm-apps/starter_ai_agents/ai_breakup_recovery_agent/ai_breakup_recovery_agent.py#L19)):
*   **Relationship Recovery Coordinator (Team)**: An Agno `Team` instance that manages four specialist agents as `members=`. Routes user input to specialists, collects responses, and synthesizes results into a cohesive recovery roadmap.
*   **Therapist Agent**: Empathetic counselor validating user feelings. Handles visual information (chat screenshot analysis).
*   **Closure Agent**: Focuses on releasing emotions, suggesting closure exercises, and drafting unsent releases.
*   **Routine Planner Agent**: Structured recovery architect proposing self-care steps, social rules, and playlists.
*   **Brutal Honesty Agent**: Objective reality check analyzing errors/opportunities. Uses a search tool to check relationship dynamics or common recovery strategies online.

### 3. Tool & External Services Layer ([DuckDuckGo Search](file:///Users/xili/Documents/codes/github/awesome-llm-apps/starter_ai_agents/ai_breakup_recovery_agent/ai_breakup_recovery_agent.py#L66))
*   Provides web search capability to the Brutal Honesty Agent via `DuckDuckGoTools()` and the underlying python `ddgs` package.

---

## 🔄 Execution & Data Flow

1.  **Initialization**: When the user clicks **"Get Recovery Plan 💝"**, [initialize_agents](file:///Users/xili/Documents/codes/github/awesome-llm-apps/starter_ai_agents/ai_breakup_recovery_agent/ai_breakup_recovery_agent.py#L17) builds an Agno `Team` instance with four specialist agents as members, all using `gpt-4o` as the shared LLM model.
2.  **Screenshot Handling**: If screenshots are uploaded, they are written to a temp folder and wrapped as Agno `Image` objects.
3.  **Single Team Run**: The `team_leader.run(prompt, images=all_images)` method is called once. The Team internally routes the user situation and instructions to its member agents, each agent processes the request per its role, and the Team synthesizes all responses.
4.  **Unified Synthesis**: The Team compiles feedback from all specialists into a single, cohesive, beautifully-structured recovery roadmap and returns it as `response.content`, which is then rendered to Streamlit.

---

## 📚 Appendix: LLM Tool Calls & Agent Orchestration

### How Agents Execute Multi-Step Workflows

**LLM Tool Calls** are the foundation of agent orchestration. They allow LLMs to invoke external functions in a structured, controlled manner.

#### Tool Call Mechanism

1. **Tool Registration**:
   - Agent/Team lists available tools in system prompt (as JSON schema)
   - Tools include: sub-agents, Toolkits (like DuckDuckGo), MCPs, functions
   - LLM sees tool definitions during initialization

2. **LLM Decision**:
   - LLM reads user prompt + instructions
   - LLM decides which tools to invoke based on reasoning
   - Generates structured JSON: `{"tool": "therapist_agent", "args": {...}}`

3. **Framework Interception**:
   - Agno framework intercepts tool call
   - Validates tool exists and arguments match schema
   - Executes the tool (calls agent, function, or MCP)

4. **Result Feedback**:
   - Tool returns result (text, JSON, etc.)
   - Framework sends result back to LLM
   - LLM sees result, decides next action (call more tools or synthesize)

5. **Loop Until Done**:
   - Process repeats until LLM generates final response
   - LLM may call multiple tools in sequence or parallel

#### Example: Team Orchestration via Tool Calls

When `team_leader.run("I'm heartbroken...")` executes:

```
System Prompt (auto-generated):
  Available Tools:
    - therapist_agent(situation): Empathetic support
    - closure_agent(situation): Emotional release
    - routine_planner_agent(situation): Recovery schedule
    - brutal_honesty_agent(situation): Reality check [has DuckDuckGo tool]

User Input:
  "I broke up after 3 years..."

LLM Reasoning:
  "I need emotional support, reality check, routine, and closure messaging"

Tool Calls (LLM generates):
  1. therapist_agent(situation="I broke up after 3 years...")
     → Returns: "I hear your pain..."
  
  2. brutal_honesty_agent(situation="I broke up after 3 years...")
     → LLM inside agent thinks: "Should search for breakup statistics"
     → Calls: DuckDuckGo.web_search("relationship breakup patterns")
     → Gets: [search results]
     → Returns: "Statistically, 40% of relationships..."
  
  3. routine_planner_agent(situation="I broke up after 3 years...")
     → Returns: "Day 1: Journaling + exercise..."
  
  4. closure_agent(situation="I broke up after 3 years...")
     → Returns: "Letter template: Dear [name]..."

LLM Synthesis:
  Combines all responses into single roadmap:
  "### Your Recovery Plan
   [therapist output]
   [honesty output with DuckDuckGo data]
   [routine output]
   [closure output]"
```

#### Tools in Agno (Universal Pattern)

All three sources inject tools into system prompt identically:

| Source | Example | Conversion |
|--------|---------|-----------|
| **Sub-agents (Team members)** | `members=[therapist_agent, ...]` | Agent metadata → tool schema → system prompt |
| **Toolkits** | `tools=[DuckDuckGoTools()]` | Toolkit methods (web_search, search_news) → tool schema → system prompt |
| **MCPs** | `mcp=[server]` | MCP resources + tools → wrapped as tools → system prompt |

Each becomes a callable tool. LLM sees unified interface.

#### Why Tool Calls Matter

- **Agentic Capability**: Without tools, LLM only generates text. Tools enable **actions**
- **Composition**: Agents coordinate via tools (no manual orchestration)
- **Safety**: Only whitelisted tools can execute (framework controls boundary)
- **Flexibility**: LLM decides tool sequence dynamically based on reasoning
- **Standard Pattern**: Used by LangChain, OpenAI Assistants, Claude API, CrewAI, AutoGen, etc.

#### System Prompt Generation

Agno automatically generates system prompt combining:

1. **Your instructions** (you provide):
   ```
   "You are the Relationship Recovery Coordinator..."
   ```

2. **Auto-generated tool definitions** (Agno injects):
   ```
   Tool: therapist_agent
   Description: Therapist Agent
   Instructions: You are an empathetic therapist...
   Input: situation (str)
   Output: str
   ```

Result: LLM has both strategic instructions + tactical tool list
