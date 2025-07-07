# AI Services Agency 👨‍💼

An AI application that simulates a full-service digital agency using multiple AI agents to analyze and plan software projects. Each agent represents a different role in the project lifecycle, from strategic planning to technical implementation.

## Demo: 

https://github.com/user-attachments/assets/a0befa3a-f4c3-400d-9790-4b9e37254405

## Features

### Five specialized AI agents 

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

- **Client Success Agent**: Marketing strategy leader
  - Develops go-to-market strategies
  - Plans customer acquisition approaches
  - Coordinates with product team

### Custom Tools

The agency uses specialized tools built with OpenAI Schema for structured analysis:
- **Analysis Tools**: AnalyzeProjectRequirements for market evaluation and analysis of startup idea
- **Technical Tools**: CreateTechnicalSpecification for technical assessment

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
   cd advanced_ai_agents/multi_agent_apps/agent_teams/ai_services_agency
   ```

2. **Install the dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Run the Streamlit app**:
    ```bash
    streamlit run agency.py
    ```

4. **Enter your OpenAI API Key** in the sidebar when prompted and start analyzing your startup idea!
