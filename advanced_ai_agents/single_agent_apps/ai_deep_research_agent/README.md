# Deep Research Agent with OpenAI Agents SDK and Firecrawl

### 🎓 FREE Step-by-Step Tutorial 
**👉 [Click here to follow our complete step-by-step tutorial](https://www.theunwindai.com/p/build-a-deep-research-agent-with-openai-agents-sdk-and-firecrawl) and learn how to build this from scratch with detailed code walkthroughs, explanations, and best practices.**

A powerful research assistant that leverages OpenAI's Agents SDK and Firecrawl's deep research capabilities to perform comprehensive web research on any topic and any question.

## Features

- **Deep Web Research**: Automatically searches the web, extracts content, and synthesizes findings
- **Enhanced Analysis**: Uses OpenAI's Agents SDK to elaborate on research findings with additional context and insights
- **Interactive UI**: Clean Streamlit interface for easy interaction
- **Downloadable Reports**: Export research findings as markdown files

## How It Works

1. **Input Phase**: User provides a research topic and API credentials
2. **Research Phase**: The tool uses Firecrawl to search the web and extract relevant information
3. **Analysis Phase**: An initial research report is generated based on the findings
4. **Enhancement Phase**: A second agent elaborates on the initial report, adding depth and context
5. **Output Phase**: The enhanced report is presented to the user and available for download

## Requirements

- Python 3.8+
- OpenAI API key
- Firecrawl API key
- Required Python packages (see `requirements.txt`)

## Installation

1. Clone this repository:
   ```bash
   git clone  https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd advanced_ai_agents/single_agent_apps/ai_deep_research_agent
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the Streamlit app:
   ```bash
   streamlit run deep_research_openai.py
   ```

2. Enter your API keys in the sidebar:
   - OpenAI API key
   - Firecrawl API key

3. Enter your research topic in the main input field

4. Click "Start Research" and wait for the process to complete

5. View and download your enhanced research report

## Example Research Topics

- "Latest developments in quantum computing"
- "Impact of climate change on marine ecosystems"
- "Advancements in renewable energy storage"
- "Ethical considerations in artificial intelligence"
- "Emerging trends in remote work technologies"

## Technical Details

The application uses two specialized agents:

1. **Research Agent**: Utilizes Firecrawl's deep research endpoint to gather comprehensive information from multiple web sources.

2. **Elaboration Agent**: Enhances the initial research by adding detailed explanations, examples, case studies, and practical implications.

The Firecrawl deep research tool performs multiple iterations of web searches, content extraction, and analysis to provide thorough coverage of the topic.

