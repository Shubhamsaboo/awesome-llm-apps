# 🚀 ShipSite Deploy Agent

A Streamlit application that lets you describe a website in natural language and have an AI agent build and deploy it live — using [ShipSite](https://shipsite.sh) through the Model Context Protocol (MCP).

## Features

- **Natural Language to Live Site**: Describe what you want and get a deployed URL
- **One-Step Deploy**: The agent generates HTML/CSS/JS and deploys in a single flow
- **MCP Integration**: Uses the `@shipsite/mcp` server to deploy static sites via API
- **Site Management**: List, update, and delete your deployed sites through conversation
- **Instant Results**: Sites go live on a global CDN in under a second

## How It Works

[ShipSite](https://shipsite.sh) is a static site hosting API built for LLM agents. Instead of git repos, build steps, and dashboards, your agent POSTs files as JSON and gets back a live URL. The MCP server exposes this as tools (`deploy_site`, `list_sites`, `delete_site`, etc.) that any MCP-compatible agent can call natively.

## Setup

### Requirements

- Python 3.8+
- Node.js and npm (for the ShipSite MCP server)
  - Download and install from [nodejs.org](https://nodejs.org/)
- OpenAI API Key
- ShipSite API Key (get one at [shipsite.sh](https://shipsite.sh))

### Getting a ShipSite API Key

1. Your agent can create an account by calling `POST https://api.shipsite.sh/v1/accounts` with your email
2. You'll get back an API key and a Stripe checkout link
3. Open the checkout link to activate your account ($0.05/site/day, usage-based)
4. Your API key is now active

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd mcp_ai_agents/shipsite_deploy_agent
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

### Running the App

1. Start the Streamlit app:
   ```bash
   streamlit run shipsite_agent.py
   ```

2. In the app interface:
   - Enter your OpenAI API key
   - Enter your ShipSite API key
   - Describe the site you want to build
   - Click "Deploy"

### Example Prompts

#### Simple Sites
- "Create a personal portfolio page with a dark theme, my name is Alex Chen, and I'm a software engineer"
- "Build a countdown timer page for New Year's Eve 2027"
- "Make a simple landing page for my dog walking business called PawSteps"

#### More Complex
- "Build a recipe page for chocolate chip cookies with ingredients, steps, and a photo placeholder"
- "Create a team directory page with 4 cards showing name, role, and a short bio"
- "Deploy a changelog page for my app with 3 release entries"

#### Site Management
- "List all my deployed sites"
- "Delete the site with ID site_abc123"

## Architecture

The application uses:
- **Streamlit** for the user interface
- **MCP** (Model Context Protocol) to connect the LLM with ShipSite's deploy tools
- **@shipsite/mcp** as the MCP server (runs via npx)
- **OpenAI** to interpret prompts and generate site code
- **ShipSite API** to host and serve the deployed sites on a global edge CDN
