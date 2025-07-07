# 🌐 Browser MCP Agent

![Area](https://github.com/user-attachments/assets/285a6a02-c1a9-4581-b32b-b244f665f648)

A Streamlit application that allows you to browse and interact with websites using natural language commands through the Model Context Protocol (MCP) and [MCP-Agent](https://github.com/lastmile-ai/mcp-agent) with Puppeteer integration.

## Features

- **Natural Language Interface**: Control a browser with simple English commands
- **Full Browser Navigation**: Visit websites and navigate through pages
- **Interactive Elements**: Click buttons, fill forms, and scroll through content
- **Visual Feedback**: Take screenshots of webpage elements
- **Information Extraction**: Extract and summarize content from webpages
- **Multi-step Tasks**: Complete complex browsing sequences through conversation

## Setup

### Requirements

- Python 3.8+
- Node.js and npm (for Puppeteer)
  - This is a critical requirement! The app uses Puppeteer to control a headless browser
  - Download and install from [nodejs.org](https://nodejs.org/)
- OpenAI or Anthropic API Key

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd mcp_ai_agents/browser_mcp_agent
   ```

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Verify Node.js and npm are installed:
   ```bash
   node --version
   npm --version
   ```
   Both commands should return version numbers. If they don't, please install Node.js.

4. Set up your API keys:
   - Set OpenAI API Key as an environment variable:
     ```bash
     export OPENAI_API_KEY=your-openai-api-key
     ```


### Running the App

1. Start the Streamlit app:
   ```bash
   streamlit run main.py
   ```

2. In the app interface:
   - Enter your browsing command
   - Click "Run Command"
   - View the results and screenshots

### Example Commands

#### Basic Navigation
- "Go to www.lastmileai.dev"
- "Go back to the previous page"

#### Interaction
- "Click on the login button"
- "Scroll down to see more content"

#### Content Extraction
- "Summarize the main content of this page"
- "Extract the navigation menu items"
- "Take a screenshot of the hero section"

#### Multi-step Tasks
- "Go to the blog, find the most recent article, and summarize its key points"

## Architecture

The application uses:
- Streamlit for the user interface
- MCP (Model Context Protocol) to connect the LLM with tools
- Puppeteer for browser automation
- [MCP-Agent](https://github.com/lastmile-ai/mcp-agent/) for the Agentic Framework
- OpenAI's models to interpret commands and generate responses
