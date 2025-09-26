# Multi-Agent Web Research System (YAML-based)

A sophisticated multi-agent system built with Google ADK that uses Firecrawl MCP tools for web scraping and coordinates between specialized research and summary agents.

## Architecture

This system consists of:

1. **Main Coordinator Agent** (`root_agent.yaml`) - Orchestrates the entire workflow
2. **Research Agent** (`research_agent.yaml`) - Uses Firecrawl MCP tools for web scraping and content analysis
3. **Summary Agent** (`summary_agent.yaml`) - Creates comprehensive reports and summaries
4. **Firecrawl MCP Integration** - Advanced web scraping with proper sub-agent configuration

## Features

- 🔍 **Advanced Web Scraping**: Uses Firecrawl MCP tools for reliable content extraction
- 🔬 **Intelligent Content Analysis**: Research agent extracts insights, patterns, and key data
- 📝 **Comprehensive Report Generation**: Summary agent creates structured reports and recommendations
- 🤖 **Multi-Agent Coordination**: Main agent orchestrates the entire workflow seamlessly
- 🔐 **Secure API Management**: Firecrawl API key managed via environment variables
- ⚡ **Sub-Agent MCP Support**: Properly configured MCP tools in sub-agents

## Setup

### Prerequisites

1. Install Google ADK:
   ```bash
   pip install google-adk
   ```

2. Get Firecrawl API key from [firecrawl.dev](https://firecrawl.dev)

3. Set environment variables in `.env` file:

   **Option A: Google AI Studio (Recommended for development)**
   ```bash
   GOOGLE_GENAI_USE_VERTEXAI=0
   GOOGLE_API_KEY=<your-google-gemini-api-key>
   FIRECRAWL_API_KEY=<your-firecrawl-api-key>
   ```
   
   **Option B: Vertex AI (Recommended for production)**
   ```bash
   GOOGLE_GENAI_USE_VERTEXAI=1
   GOOGLE_CLOUD_PROJECT=<your-gcp-project-id>
   GOOGLE_CLOUD_LOCATION=us-central1
   FIRECRAWL_API_KEY=<your-firecrawl-api-key>
   ```
   
   **Getting API Keys:**
   - **Google AI Studio**: Get your API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
   - **Vertex AI**: Set up authentication using [Google Cloud Authentication](https://cloud.google.com/vertex-ai/generative-ai/docs/start/api-keys)
   - **Firecrawl**: Get your API key from [Firecrawl](https://firecrawl.dev/app/api-keys)

### Installation

1. Navigate to the agent directory:
   ```bash
   cd ai_agent_framework_crash_course/google_adk_crash_course/adk_yaml_examples/multi_agent_web_research_team/multi_agent_web_researcher
   ```

2. Verify ADK installation:
   ```bash
   adk --version
   ```

## Usage

### Running the Agent

Choose one of these methods to run your agent:

1. **Web Interface** (Recommended for testing):
   ```bash
   adk web
   ```

2. **Command Line**:
   ```bash
   adk run
   ```

3. **API Server** (For integration):
   ```bash
   adk api_server
   ```

## Agent Configuration

### Main Agent (`root_agent.yaml`)

The coordinator agent that:
- Delegates tasks to specialized sub-agents
- Coordinates between research and summary agents
- Synthesizes final comprehensive reports
- Provides clear instructions to sub-agents

### Research Agent (`research_agent.yaml`)

Specialized for web scraping and content analysis:
- **Firecrawl MCP Tools**: Uses `firecrawl_scrape` and `firecrawl_search`
- **Content Analysis**: Extracts key findings and insights
- **Pattern Recognition**: Identifies trends and relationships
- **Data Extraction**: Highlights important quotes and data points
- **Research Suggestions**: Suggests areas for further investigation

**Available Firecrawl Tools:**
- `firecrawl_scrape`: Scrape content from single URLs
- `firecrawl_search`: Search the web for relevant content
- `firecrawl_batch_scrape`: Scrape multiple URLs efficiently
- `firecrawl_map`: Discover URLs on websites
- `firecrawl_crawl`: Comprehensive website crawling

### Summary Agent (`summary_agent.yaml`)

Specialized for report generation:
- Creates executive summaries
- Organizes information by topic
- Generates key takeaways
- Provides actionable recommendations

## Workflow

1. **Input**: User provides URL or research topic
2. **Delegation**: Main agent passes clear instructions to research_agent
3. **Web Scraping**: Research agent uses Firecrawl MCP tools to extract content
4. **Analysis**: Research agent analyzes scraped content for insights
5. **Summarization**: Summary agent creates comprehensive report
6. **Synthesis**: Main agent combines findings into final report

## Environment Variables

### Google AI Studio Configuration
| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_GENAI_USE_VERTEXAI` | Set to 0 for Google AI Studio | Yes |
| `GOOGLE_API_KEY` | Google Gemini API key from AI Studio | Yes |
| `FIRECRAWL_API_KEY` | Firecrawl API key for web scraping | Yes |

### Vertex AI Configuration
| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_GENAI_USE_VERTEXAI` | Set to 1 for Vertex AI | Yes |
| `GOOGLE_CLOUD_PROJECT` | Your Google Cloud Project ID | Yes |
| `GOOGLE_CLOUD_LOCATION` | GCP region (e.g., us-central1) | Yes |
| `FIRECRAWL_API_KEY` | Firecrawl API key for web scraping | Yes |

### Authentication Methods

**Google AI Studio:**
- Simple API key authentication
- Best for development and testing
- No Google Cloud setup required

**Vertex AI:**
- Enterprise-grade authentication
- Best for production deployments
- Requires Google Cloud Project setup
- Supports advanced features like grounding and safety settings


## Example Usage

### Web Interface
1. Run `adk web`
2. Open browser to the provided URL
3. Enter a URL or research topic (e.g., "Scrape and analyze https://example.com" or "Research AI trends")
4. Watch the multi-agent system process your request

### Command Line
```bash
adk run
# Enter your research query when prompted
```

## Troubleshooting

### Common Issues

1. **API Key Errors**: Ensure all required API keys are set in `.env`
2. **ADK Not Found**: Make sure ADK is installed and Python environment is activated
3. **Firecrawl Errors**: Verify your Firecrawl API key is valid and has sufficient credits
4. **MCP Connection Issues**: Check that Node.js and npm are properly installed
5. **Authentication Issues**: 
   - **Google AI Studio**: Verify your API key is valid and has proper permissions
   - **Vertex AI**: Ensure Google Cloud authentication is set up correctly (`gcloud auth application-default login`)
   - **Project ID**: Verify your Google Cloud Project ID is correct for Vertex AI


## References

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [Agent Config Reference](https://google.github.io/adk-docs/agents/config/#build-an-agent)
- [Firecrawl Documentation](https://docs.firecrawl.dev/)
- [MCP Tools](https://modelcontextprotocol.io/)
