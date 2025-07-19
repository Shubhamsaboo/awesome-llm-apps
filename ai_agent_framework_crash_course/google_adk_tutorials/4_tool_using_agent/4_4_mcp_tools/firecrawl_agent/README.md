# 🔥 Firecrawl Agent - Advanced Web Scraping with MCP

Welcome to the **Firecrawl MCP Agent**! This powerful agent demonstrates how to integrate Firecrawl's advanced web scraping capabilities with Google ADK through the Model Context Protocol (MCP).

## 🌟 What You'll Learn

- **Firecrawl Integration**: Connect to Firecrawl's comprehensive web scraping platform
- **Advanced Web Scraping**: Single page, batch processing, and full website crawling
- **AI-Powered Extraction**: Use LLMs to extract structured data from web content
- **Research Capabilities**: Conduct deep web research with multi-source analysis
- **Real-world Applications**: Practical examples for data extraction and research

## 🚀 Key Features

### 🔧 Comprehensive Toolset
- **Single Page Scraping**: Extract content from individual URLs with advanced options
- **Batch Processing**: Efficiently scrape multiple URLs with parallel processing
- **Website Mapping**: Discover all URLs on a website for exploration
- **Web Search**: Search the web and extract content from results
- **Full Site Crawling**: Perform comprehensive website analysis with depth control
- **Structured Extraction**: Use AI to extract specific data points from pages
- **Deep Research**: Conduct in-depth research with multi-source analysis
- **LLMs.txt Generation**: Create standardized AI interaction guidelines for domains

### 🌍 Advanced Capabilities
- **Automatic Rate Limiting**: Built-in retry logic and backoff strategies
- **Multiple Output Formats**: Support for Markdown, HTML, and JSON
- **Content Filtering**: Advanced options for content selection and exclusion
- **Mobile/Desktop Rendering**: Choose between different rendering modes
- **Authentication Support**: Handle sites requiring login credentials
- **JavaScript Rendering**: Full support for dynamic content

## 📋 Prerequisites

### Required Dependencies
1. **Node.js**: Required for the Firecrawl MCP server
   ```bash
   # Install Node.js if not already installed
   # Visit https://nodejs.org/ for installation instructions
   ```

2. **Firecrawl API Key**: Get your API key from [Firecrawl.dev](https://firecrawl.dev)
   ```bash
   # Set your API key as an environment variable
   export FIRECRAWL_API_KEY=your_api_key_here
   ```

3. **Google ADK Dependencies**: Ensure you have the required packages
   ```bash
   pip install -r ../requirements.txt
   ```

## 🛠️ Setup Instructions

### 1. Environment Configuration
```bash
# Set your Firecrawl API key
export FIRECRAWL_API_KEY=fc-your_api_key_here

# Optional: Configure retry settings
export FIRECRAWL_RETRY_MAX_ATTEMPTS=5
export FIRECRAWL_RETRY_INITIAL_DELAY=2000
```

### 2. Install Dependencies
```bash
# From the tutorials root directory
pip install -r requirements.txt
```

### 3. Run the Agent
```bash
# From the tutorials root directory
adk web
```

Then select `firecrawl_mcp_agent` from the dropdown menu.

## 🎯 Usage Examples

### Basic Web Scraping
```text
User: "Scrape the homepage of https://example.com"
Agent: Uses firecrawl_scrape to extract clean content in Markdown format
```

### Batch URL Processing
```text
User: "Extract content from these three articles: [url1, url2, url3]"
Agent: Uses firecrawl_batch_scrape for efficient parallel processing
```

### Website Discovery
```text
User: "Find all blog post URLs on https://blog.example.com"
Agent: Uses firecrawl_map to discover and list all available URLs
```

### Web Search & Extraction
```text
User: "Search for research papers on AI Agents in the last 4 weeks and extract key information"
Agent: Uses firecrawl_search to find relevant papers and extract summaries
```

### Structured Data Extraction
```text
User: "Extract product details (name, price, description) from this e-commerce page"
Agent: Uses firecrawl_extract with custom schema for structured data
```

### Deep Research
```text
User: "Perform comprehensive research on sustainable energy technologies"
Agent: Uses firecrawl_deep_research for multi-source analysis and synthesis
```

### Website Crawling
```text
User: "Crawl the documentation section of https://docs.example.com"
Agent: Uses firecrawl_crawl with appropriate depth and filtering
```

## 🔧 Available Tools

### Core Scraping Tools
| Tool | Purpose | Best For |
|------|---------|----------|
| `firecrawl_scrape` | Single page extraction | Known URLs, specific pages |
| `firecrawl_batch_scrape` | Multiple URL processing | Lists of URLs, parallel extraction |
| `firecrawl_map` | URL discovery | Exploring site structure |

### Advanced Tools
| Tool | Purpose | Best For |
|------|---------|----------|
| `firecrawl_search` | Web search + extraction | Finding relevant content |
| `firecrawl_crawl` | Full site crawling | Comprehensive site analysis |
| `firecrawl_extract` | Structured data extraction | Specific data points |
| `firecrawl_deep_research` | Multi-source research | Complex research tasks |

### Utility Tools
| Tool | Purpose | Best For |
|------|---------|----------|
| `firecrawl_generate_llmstxt` | LLMs.txt generation | AI interaction guidelines |
| `firecrawl_check_crawl_status` | Monitor crawl progress | Long-running operations |
| `firecrawl_check_batch_status` | Monitor batch progress | Batch operation tracking |

## 💡 Best Practices

### Tool Selection Guide
- **Single URL**: Use `firecrawl_scrape`
- **Multiple known URLs**: Use `firecrawl_batch_scrape`
- **Discover URLs**: Use `firecrawl_map` first
- **Search the web**: Use `firecrawl_search`
- **Structured data**: Use `firecrawl_extract`
- **Deep research**: Use `firecrawl_deep_research`
- **Full site analysis**: Use `firecrawl_crawl` (with limits)

### Performance Optimization
- Use batch operations for multiple URLs instead of individual scrapes
- Set appropriate limits for crawl operations to avoid timeouts
- Monitor long-running operations with status check tools
- Respect rate limits and be considerate of target websites

### Content Quality
- Use `onlyMainContent: true` to extract clean content
- Leverage content filtering options for better results
- Choose appropriate output formats (Markdown for text, JSON for data)
- Use structured extraction for specific data requirements

## ⚙️ Configuration Options

### Scraping Parameters
```python
# Example configuration for scrape operations
{
    "formats": ["markdown"],           # Output format
    "onlyMainContent": True,          # Extract main content only
    "waitFor": 1000,                  # Wait time for page load
    "timeout": 30000,                 # Request timeout
    "mobile": False,                  # Use mobile rendering
    "includeTags": ["article", "main"], # Include specific HTML tags
    "excludeTags": ["nav", "footer"]    # Exclude specific HTML tags
}
```

### Batch Processing
```python
# Example batch configuration
{
    "maxUrls": 50,                    # Maximum URLs to process
    "parallelLimit": 5,               # Parallel processing limit
    "options": {
        "formats": ["markdown"],
        "onlyMainContent": True
    }
}
```

### Crawling Parameters
```python
# Example crawl configuration
{
    "maxDepth": 2,                    # Crawl depth limit
    "limit": 100,                     # Maximum pages to crawl
    "allowExternalLinks": False,      # Stay within domain
    "deduplicateSimilarURLs": True    # Remove duplicate content
}
```

## 🚨 Important Notes

### Rate Limiting
- Firecrawl includes automatic rate limiting and retry logic
- Batch operations are queued and may take time to complete
- Monitor operation status for long-running tasks

### Resource Management
- Crawl operations can be resource-intensive
- Set appropriate limits to avoid timeouts or excessive token usage
- Use batch status checks for large operations

### API Usage
- Requires a valid Firecrawl API key for cloud operations
- Consider self-hosted deployment for high-volume usage
- Monitor credit usage through the Firecrawl dashboard

## 🔍 Troubleshooting

### Common Issues

**Connection Errors**
```bash
# Check Node.js installation
node --version

# Test Firecrawl MCP server
npx -y firecrawl-mcp
```

**API Key Issues**
```bash
# Verify API key is set
echo $FIRECRAWL_API_KEY

# Test API key validity
curl -H "Authorization: Bearer $FIRECRAWL_API_KEY" https://api.firecrawl.dev/v1/scrape
```

**Tool Not Found**
- Ensure ADK MCP server is properly configured
- Check that Node.js is installed and accessible
- Verify the Firecrawl MCP package can be installed

### Debug Commands
```bash
# Test MCP server connection
npx @modelcontextprotocol/inspector

# Run agent with debug output
adk web --debug
```

## 📚 Additional Resources

- **[Firecrawl Documentation](https://docs.firecrawl.dev)** - Complete API reference
- **[Firecrawl MCP Server](https://github.com/mendableai/firecrawl-mcp-server)** - Source code and examples
- **[MCP Specification](https://modelcontextprotocol.io/docs/spec)** - Protocol details
- **[ADK MCP Documentation](https://google.github.io/adk-docs/tools/mcp-tools/)** - Integration guide

## 🎯 Real-World Applications

### Data Collection & Research
- Market research and competitor analysis
- Academic research and paper collection
- News monitoring and trend analysis
- Product catalog extraction
- Social media content analysis

### Content Management
- Website migration and content auditing
- SEO analysis and optimization
- Content quality assessment
- Documentation extraction
- Knowledge base creation

### Business Intelligence
- Lead generation and contact extraction
- Price monitoring and comparison
- Review and sentiment analysis
- Industry trend tracking
- Regulatory compliance monitoring