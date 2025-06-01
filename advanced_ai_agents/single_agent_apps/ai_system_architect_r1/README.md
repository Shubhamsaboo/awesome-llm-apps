# 🤖 AI System Architect Advisor with R1

An Agno agentic system that provides expert software architecture analysis and recommendations using a dual-model approach combining DeepSeek R1's Reasoning and Claude. The system provides detailed technical analysis, implementation roadmaps, and architectural decisions for complex software systems.

## Features

- **Dual AI Model Architecture**
  - **DeepSeek Reasoner**: Provides initial technical analysis and structured reasoning about architecture patterns, tools, and implementation strategies
  - **Claude-3.5**: Generates detailed explanations, implementation roadmaps, and technical specifications based on DeepSeek's analysis

- **Comprehensive Analysis Components**
  - Architecture Pattern Selection
  - Infrastructure Resource Planning
  - Security Measures and Compliance
  - Database Architecture
  - Performance Requirements
  - Cost Estimation
  - Risk Assessment

- **Analysis Types**
  - Real-time Event Processing Systems
  - Healthcare Data Platforms
  - Financial Trading Platforms
  - Multi-tenant SaaS Solutions
  - Digital Content Delivery Networks
  - Supply Chain Management Systems

## How to Run

1. **Setup Environment**
   ```bash
   # Clone the repository
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd advanced_ai_agents/single_agent_apps/ai_system_architect_r1
   
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Configure API Keys**
   - Get DeepSeek API key from DeepSeek platform
   - Get Anthropic API key from [Anthropic Platform](https://www.anthropic.com)

3. **Run the Application**
   ```bash
   streamlit run ai_system_architect_r1.py
   ```

4. **Use the Interface**
   - Enter API credentials in sidebar
   - Structure your prompt with:
     - Project Context
     - Requirements
     - Constraints
     - Scale
     - Security/Compliance needs
   - View detailed analysis results

## Example Test Prompts:

### 1. Financial Trading Platform
"We need to build a high-frequency trading platform that processes market data streams, executes trades with sub-millisecond latency, maintains audit trails, and handles complex risk calculations. The system needs to be globally distributed, handle 100,000 transactions per second, and have robust disaster recovery capabilities."
### 2. Multi-tenant SaaS Platform
"Design a multi-tenant SaaS platform for enterprise resource planning that needs to support customization per tenant, handle different data residency requirements, support offline capabilities, and maintain performance isolation between tenants. The system should scale to 10,000 concurrent users and support custom integrations."

## Notes

- Requires both DeepSeek and Anthropic API keys
- Provides real-time analysis with detailed explanations
- Supports chat-based interaction
- Includes clear reasoning for all architectural decisions
- API usage costs apply


