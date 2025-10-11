# 🎨 🍌 Multimodal UI/UX Feedback Agent Team with Nano Banana

A sophisticated multi-agent system built with Google ADK that analyzes landing page designs, provides expert UI/UX feedback, and automatically generates improved versions using Gemini 2.5 Flash's multimodal capabilities.

## Features

- **👁️ Visual AI Analysis**: Upload landing page screenshots - agents automatically analyze layout, typography, colors, and UX patterns
- **🎯 Expert Feedback**: Comprehensive critique covering visual hierarchy, accessibility, conversion optimization, and design best practices
- **✨ Automatic Improvements**: Generates improved landing page designs incorporating all recommendations
- **📊 Detailed Reports**: Creates comprehensive reports summarizing issues and improvements made
- **🤖 Multi-Agent Orchestration**: Demonstrates Coordinator/Dispatcher + Sequential Pipeline patterns
- **♻️ Iterative Refinement**: Edit and refine generated designs based on additional feedback
- **♿ Accessibility Focus**: WCAG compliance checks and recommendations

## How It Works

The system uses a **Coordinator/Dispatcher pattern** with three specialized agents working in sequence:

### The Team

1. **UI Critic Agent** 🎨
   - Analyzes landing page design using Gemini 2.5 Flash's vision capabilities
   - Can see and analyze uploaded images directly (no manual tool calls needed)
   - Evaluates layout, visual hierarchy, typography, color scheme, and CTA effectiveness
   - Identifies critical issues and improvement opportunities
   - Provides detailed scores across multiple dimensions
   - References specific elements and provides actionable feedback

2. **Design Strategist Agent** 📐
   - Creates comprehensive improvement plan based on analysis
   - Specifies exact colors (with hex codes), typography, and spacing
   - Prioritizes changes for maximum impact
   - Ensures accessibility compliance (WCAG AA)
   - Considers mobile responsiveness

3. **Visual Implementer Agent** 🚀
   - Generates improved landing page design using Gemini 2.5 Flash
   - Implements all recommendations from the analysis
   - Creates high-quality, professional designs
   - Generates comprehensive improvement report
   - Maintains version history

## Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/advanced_ai_agents/multi_agent_apps/agent_teams/multimodal_uiux_feedback_agent_team
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up your API key
```bash
export GOOGLE_API_KEY="your_gemini_api_key"
```

Or create a `.env` file:
```
GOOGLE_API_KEY=your_gemini_api_key
```

### 4. Launch ADK Web
```bash
cd advanced_ai_agents/multi_agent_apps/agent_teams
adk web
```

### 5. Open browser
Navigate to the ADK Web interface and select **multimodal_uiux_feedback_agent_team**

## Tools & Capabilities

### Core Tools
- **Direct Vision Analysis**: Agents can see and analyze uploaded images automatically (no tool needed)
- **edit_landing_page_image**: Refine existing designs based on feedback
- **generate_improved_landing_page**: Create new improved designs from scratch
- **google_search**: Research UI/UX trends and best practices

### Features
- **Native Vision Capabilities**: Agents automatically see uploaded images in conversations
- **Versioned artifacts**: Automatic version tracking for all designs
- **State management**: Maintains context across the conversation
- **Detailed prompts**: Generates ultra-specific prompts for high-quality results
- **Sequential Processing**: Each agent builds on previous agent's analysis

## Multi-Agent Architecture

```
Coordinator (Root Agent)
    ├── Info Agent (general Q&A)
    ├── Design Editor (iterative refinements)
    └── Analysis Pipeline (Sequential)
          ├── UI Critic (visual analysis & feedback)
          ├── Design Strategist (improvement planning)
          └── Visual Implementer (generate improved design + report)
```


## Best Practices for Users

### Getting Better Results

1. **Use High-Quality Screenshots**
   - Full-page captures preferred
   - Minimum 1920x1080 resolution
   - Clear, uncompressed images

2. **Provide Context**
   - Mention target audience (B2B, B2C, enterprise, consumer)
   - Share goals (conversions, awareness, engagement)
   - Specify any constraints or requirements

3. **Be Specific with Refinements**
   - "Make the CTA button 20% larger with vibrant orange color"
   - vs "Make the button better"

4. **Iterate Gradually**
   - Make one category of changes at a time
   - Review each version before requesting more changes

### Common Use Cases

- **Landing Page Audits**: Comprehensive analysis of existing pages
- **Pre-Launch Review**: Get feedback before going live
- **A/B Testing Ideas**: Generate alternative designs to test
- **Competitive Analysis**: Compare your design to competitors
- **Accessibility Audit**: Check WCAG compliance
- **Mobile Optimization**: Review mobile responsiveness
- **Conversion Optimization**: Improve CTA and user flow

## Limitations

- Image generation has inherent variability (run multiple times for options)
- Complex interactions and animations cannot be fully captured
- Best suited for static landing page screenshots
- Real code implementation requires manual development
- Analysis focuses on visual design, not content quality or copy
