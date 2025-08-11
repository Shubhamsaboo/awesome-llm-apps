# 🎯 Tutorial 9.1: Sequential Agents - Business Implementation Plan Generator

## 🎯 What You'll Learn

- **Sequential Agent Composition**: How to orchestrate multiple specialized agents in sequence
- **AgentTool Integration**: Wrapping agents as tools for enhanced capabilities
- **Web Search Integration**: Real-time market intelligence through search agents
- **Business Analysis Pipeline**: From market research to implementation planning
- **Streamlit Web Interface**: User-friendly application for business planning

## 🧠 Core Concept: Sequential Agent with Search Capabilities

According to the [ADK workflow agents documentation](https://google.github.io/adk-docs/agents/workflow-agents/), **Sequential Agents** execute sub-agents one after another, in sequence. This tutorial demonstrates a **Business Implementation Plan Generator** that combines web search capabilities with sequential analysis:

```
Business Topic → SequentialAgent → 4 Sub-agents (Sequential Execution)
                ↓
        [Market Research + Web Search] → [SWOT Analysis] → [Strategy] → [Implementation]
                ↓
        Complete Business Implementation Plan
```

**Key Innovation**: The Market Research Agent uses a specialized Search Agent (wrapped as AgentTool) to access real-time web search capabilities for current market intelligence.

## 📁 Project Structure

```
9_1_sequential_agent/
├── agent.py              # Business implementation plan generator with search capabilities
├── app.py                # Streamlit web interface for business planning
├── requirements.txt      # Python dependencies
└── README.md            # This documentation
```

## 🚀 Getting Started

### 1. Install Dependencies
```bash
cd 9_1_sequential_agent
pip install -r requirements.txt
```

### 2. Set Up Environment
Create a `.env` file with your Google API key:
```bash
echo "GOOGLE_API_KEY=your_ai_studio_key_here" > .env
```

**Important**: Get your API key from [Google AI Studio](https://aistudio.google.com/)

### 3. Run the Streamlit App
```bash
streamlit run app.py
```

This will launch the **Business Implementation Plan Generator Agent** web interface!

## 🧪 How It Works

### **Business Implementation Plan Generation Pipeline**

The agent processes business opportunities through a sophisticated 4-step sequential workflow:

1. **🔍 Market Analysis** - Uses web search for current market information and competitive research
2. **📊 SWOT Analysis** - Strategic assessment of strengths, weaknesses, opportunities, and threats
3. **🎯 Strategy Development** - Strategic objectives and action plans
4. **📋 Implementation Planning** - Detailed execution roadmap and resource requirements

**Key Innovation**: The Market Analysis Agent has access to a specialized Search Agent (wrapped as AgentTool) that can perform real-time web searches using the `google_search` tool. This provides current market intelligence that feeds into the sequential analysis pipeline.

The `SequentialAgent` ensures each step builds upon the previous step's output, creating a comprehensive business implementation plan ready for execution.

**Result**: A complete business implementation plan with market research, strategic analysis, and execution roadmap.

## 🔧 ADK Concepts Demonstrated

### **1. SequentialAgent Pattern**
The core workflow orchestrator that executes sub-agents in sequence, ensuring each step builds upon the previous step's output.

### **2. AgentTool Integration**
Advanced pattern where one agent (Search Agent) is wrapped as a tool and used by another agent (Market Researcher) to enhance capabilities.

### **3. Web Search Capabilities**
Real-time market intelligence through integrated search functionality, providing current data rather than relying on training data.

### **4. Sub-agent Specialization**
Each sub-agent specializes in a specific business analysis phase, creating a modular and maintainable system.

### **5. Session Management**
Maintains conversation state across the entire analysis pipeline, ensuring context flows between agents.

### **6. Runner Execution**
Processes the complete business implementation workflow with proper error handling and response management.

## 🧪 Sample Topics to Try

- **Electric vehicle charging stations** in urban areas
- **AI-powered healthcare diagnostics** and patient care
- **Sustainable food delivery** services and packaging
- **Remote work collaboration** tools and platforms
- **Renewable energy storage** solutions

## 📊 Expected Output

The sequential agent will provide:
1. **Market Research**: Competitive analysis and market trends
2. **SWOT Analysis**: Strategic assessment with actionable insights
3. **Strategy Plan**: Clear objectives and implementation steps
4. **Implementation Roadmap**: Practical execution guidance

## 🎯 Learning Objectives

- ✅ Understand how `SequentialAgent` orchestrates sub-agents
- ✅ Learn to execute sequential agents with Runner and Session management
- ✅ See how sub-agents can build upon each other's output
- ✅ Experience a working, executable sequential workflow
- ✅ Understand AgentTool integration for enhanced capabilities

## 🚀 Next Steps

- Try different business topics to see the sequential workflow in action
- Experiment with reordering the sub-agents
- Add more specialized agents to the pipeline
- Explore other ADK workflow patterns (Parallel, Branching)

## 🔧 Troubleshooting

**Common Issues:**
- **API Key Error**: Ensure `GOOGLE_API_KEY` is set in `.env`
- **Import Errors**: Make sure you're in the correct directory
- **Search Tool Errors**: Verify your API key has access to search capabilities

**Pro Tips:**
- Start with simple topics to understand the flow
- Use the Streamlit app for easy testing and visualization
- The sequential pattern is great for predictable, step-by-step processes
- Web search integration provides real-time market intelligence

## 📚 Key Takeaways

- **SequentialAgent** is perfect for workflows that must happen in order
- **AgentTool integration** allows agents to enhance each other's capabilities
- **Web search capabilities** provide current market intelligence
- **Sub-agents** can be simple `LlmAgent` instances or complex tool-enabled agents
- **Clean, readable code** makes it easy to understand and modify
- **Streamlit interface** provides user-friendly access to complex agent workflows
