# 🤝 AI Consultant Agent with Google ADK 

### 🎓 FREE Step-by-Step Tutorial 
**👉 [Click here to follow our complete step-by-step tutorial](https://www.theunwindai.com/p/build-an-ai-consultant-agent-with-gemini-2-5-flash) and learn how to build this from scratch with detailed code walkthroughs, explanations, and best practices.**

A powerful business consultant powered by Google's Agent Development Kit that provides comprehensive market analysis, strategic planning, and actionable business recommendations with real-time web research.


## Features

- **Real-time Web Research**: Uses Perplexity AI search for current market data, trends, and competitor intelligence
- **Market Analysis**: Leverages web search and AI insights to analyze market conditions and opportunities
- **Strategic Recommendations**: Generates actionable business strategies with timelines and implementation plans
- **Risk Assessment**: Identifies potential risks and provides mitigation strategies
- **Interactive UI**: Clean Google ADK web interface for easy consultation
- **Evaluation System**: Built-in evaluation and debugging capabilities with session tracking

## How It Works

1. **Input Phase**: User provides business questions or consultation requests through the ADK web interface
2. **Research Phase**: The agent conducts real-time web research using Perplexity AI to gather current market data
3. **Analysis Phase**: The agent uses market analysis tools to process the query and generate insights
4. **Strategy Phase**: Strategic recommendations are generated based on the analysis and web research
5. **Synthesis Phase**: The agent combines findings into a comprehensive consultation report with citations
6. **Output Phase**: Actionable recommendations with timelines and implementation steps are presented

## Requirements

- Python 3.8+
- Google API key (for Gemini model)
- Perplexity API key (for real-time web search)
- Required Python packages (see `requirements.txt`)

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd advanced_ai_agents/single_agent_apps
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Set your API keys:
   ```bash
   export GOOGLE_API_KEY=your-google-api-key
   export PERPLEXITY_API_KEY=your-perplexity-api-key
   ```

2. Start the Google ADK web interface:
   ```bash
   adk web 
   ```

3. Open your browser and navigate to `http://localhost:8000`

4. Select "AI Business Consultant" from the available agents

5. Enter your business questions or consultation requests

6. Review the comprehensive analysis and strategic recommendations with real-time web data and citations

7. Use the Eval tab to save and evaluate consultation sessions

## Example Consultation Topics

- "I want to launch a SaaS startup for small businesses"
- "Should I expand my retail business to e-commerce?"
- "What are the market opportunities in healthcare technology?"
- "How should I position my new fintech product?"
- "What are the risks of entering the renewable energy market?"

## Technical Details

The application uses specialized analysis tools:

1. **Perplexity Search Tool**: Conducts real-time web research using Perplexity AI's "sonar" model to gather current market data, competitor information, and industry trends with citations.

2. **Market Analysis Tool**: Processes business queries and generates market insights, competitive analysis, and opportunity identification.

3. **Strategic Recommendations Tool**: Creates actionable business strategies with priority levels, timelines, and implementation roadmaps.

The agent is built on Google ADK's LlmAgent framework using the Gemini 2.5 Flash model, providing fast and accurate business consultation capabilities backed by real-time web research.

## Evaluation and Testing

The agent includes built-in evaluation features:

- **Session Management**: Track consultation history and progress
- **Test Case Creation**: Save successful consultations as evaluation cases
- **Performance Metrics**: Monitor tool usage and response quality
- **Custom Evaluation**: Configure metrics for specific business requirements 