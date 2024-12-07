# AI Startup Organization Agency 🚀

An intelligent multi-agent system that provides comprehensive startup analysis and strategic guidance for a startup you'd want to build using Agency Swarm framework and OpenAI's GPT models

## Demo: 

## Features

### 🤖 Agency Swarm Agents

- **CEO Agent**: Strategic leader and final decision maker
  - Analyzes startup ideas using structured evaluation
  - Makes strategic decisions across product, technical, marketing, and financial domains
  - Uses AnalyzeStartupTool and MakeStrategicDecision tools

- **CTO Agent**: Technical architecture and feasibility expert
  - Evaluates technical requirements and feasibility
  - Provides architecture decisions
  - Uses QueryTechnicalRequirements and EvaluateTechnicalFeasibility tools

- **Product Manager Agent**: Product strategy specialist
  - Defines product strategy and roadmap
  - Coordinates between technical and marketing teams
  - Focuses on product-market fit

- **Developer Agent**: Technical implementation expert
  - Provides detailed technical implementation guidance
  - Suggests optimal tech stack and cloud solutions
  - Estimates development costs and timelines

- **Marketing Manager Agent**: Marketing strategy leader
  - Develops go-to-market strategies
  - Plans customer acquisition approaches
  - Coordinates with product team

### 🔄 Asynchronous Communication

The agency operates in async mode, enabling:
- Parallel processing of analyses from different agents
- Efficient multi-agent collaboration
- Real-time communication between agents
- Non-blocking operations for better performance

### 🔗 Agent Communication Flows
- CEO ↔️ All Agents (Strategic Oversight)
- CTO ↔️ Developer (Technical Implementation)
- Product Manager ↔️ Marketing Manager (Go-to-Market Strategy)
- Product Manager ↔️ Developer (Feature Implementation)
- (and more!)
## How to Run

Follow the steps below to set up and run the application:
Before anything else, Please get your OpenAI API Key here: https://platform.openai.com/api-keys

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd ai_agent_tutorials
   ```

2. **Install the dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Run the Streamlit app**:
    ```bash
    streamlit run ai_startup_org_agents/main.py
    ```

4. **Enter your OpenAI API Key** in the sidebar when prompted and start analyzing your startup idea!

## Project Structure

ai_startup_org_agents/
├── main.py              # Main application file with agents and tools
├── requirements.txt     # Project dependencies
└── README.md           # Project documentation
