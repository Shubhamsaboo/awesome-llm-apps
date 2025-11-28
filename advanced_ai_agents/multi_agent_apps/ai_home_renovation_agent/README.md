# 🏚️ 🍌 AI Home Renovation Planner Agent 

### 🎓 FREE Step-by-Step Tutorial 
**👉 [Click here to follow our complete step-by-step tutorial](https://www.theunwindai.com/p/build-an-ai-home-renovation-planner-agent-using-nano-banana) and learn how to build this from scratch with detailed code walkthroughs, explanations, and best practices.**

A multi-agent system built with Google ADK that analyzes photos of your space, creates personalized renovation plans, and generates photorealistic renderings using Gemini 2.5 Flash's multimodal capabilities.

## Features

- **🔍 Smart Image Analysis**: Upload room photos and inspiration images - agent automatically detects and analyzes them
- **🎨 Photorealistic Rendering**: Generates professional-quality images of your renovated space using Gemini 2.5 Flash
- **💰 Budget-Aware Planning**: Tailors recommendations to your budget constraints
- **📊 Complete Roadmap**: Provides timeline, budget breakdown, contractor list, and action checklist
- **🤖 Multi-Agent Orchestration**: Demonstrates Coordinator/Dispatcher + Sequential Pipeline patterns
- **✏️ Iterative Refinement**: Edit generated renderings based on feedback

## How It Works

The system uses a **Coordinator/Dispatcher pattern** with three specialized agents:

1. **Visual Assessor** 📸
   - Analyzes uploaded room photos (layout, condition, dimensions)
   - Extracts style from inspiration images
   - Estimates costs and identifies improvement opportunities

2. **Design Planner** 🎨
   - Creates budget-appropriate design plans
   - Specifies exact materials, colors, and fixtures
   - Prioritizes high-impact changes

3. **Project Coordinator** 🏗️
   - Generates comprehensive renovation roadmap
   - Creates photorealistic rendering of renovated space
   - Provides budget breakdown, timeline, and action steps

## Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd awesome-llm-apps/advanced_ai_agents/multi_agent_apps/ai_home_renovation_agent
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your API key**
   ```bash
   export GOOGLE_API_KEY="your_gemini_api_key"
   ```
   Or create a `.env` file:
   ```
   GOOGLE_API_KEY=your_gemini_api_key
   ```

4. **Launch ADK Web** 
   ```bash
   cd multi_agent_apps
   adk web
   ```

5. **Open browser** and select "ai_home_renovation_agent"

## Usage Examples

### Scenario 1: Current Room + Budget
```
[Upload photo of your kitchen]
"What can I improve here with a $5k budget?"
```
→ Agent analyzes your space, suggests budget-friendly improvements, generates rendering

### Scenario 2: Room + Inspiration
```
[Upload photo 1: your kitchen]
[Upload photo 2: Pinterest inspiration]
"Transform my kitchen to look like this. What's the cost?"
```
→ Agent extracts style from inspiration, applies to your room, provides budget + rendering

### Scenario 3: Text Only
```
"Renovate my 10x12 kitchen with oak cabinets and laminate counters. 
Want modern farmhouse style with white shaker cabinets. Budget: $30k"
```
→ Agent creates design plan and generates rendering from description

### Scenario 4: Iterative Refinement
```
[After initial rendering]
"Make the cabinets cream instead of white"
"Add pendant lights over the island"
"Change flooring to lighter oak"
```
→ Agent refines the rendering with your feedback

## Sample Prompts
- "I want to renovate my small galley kitchen. It's 8x12 feet, has oak cabinets from the 90s. I love modern farmhouse style. Budget: $25k"
- "My master bathroom is tiny (5x8) with a cramped tub. I want a spa-like retreat with walk-in shower. Budget: $15k"
- "Transform my boring bedroom into a cozy retreat. Thinking accent wall, new flooring. Budget: $12k"

## Tools & Capabilities

- **google_search**: Finds renovation costs, materials, and trends
- **estimate_renovation_cost**: Calculates costs by room type and scope
- **calculate_timeline**: Estimates project duration
- **generate_renovation_rendering**: Creates photorealistic renderings
- **edit_renovation_rendering**: Refines renderings based on feedback
- **Versioned artifacts**: Automatic version tracking for all renderings

## Multi-Agent Pattern

Demonstrates **Coordinator/Dispatcher + Sequential Pipeline**:

```
Coordinator (Root Agent)
    ├── Info Agent (quick Q&A)
    └── Planning Pipeline (Sequential)
          ├── Visual Assessor (image analysis)
          ├── Design Planner (specifications)
          └── Project Coordinator (rendering + roadmap)
```

**Why this pattern?**
- Efficient: Only runs workflows that are needed
- Modular: Each agent has clear responsibilities
- Scalable: Easy to add new features
- Production-ready: Real-world agentic system pattern

