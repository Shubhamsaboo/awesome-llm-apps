"""
Firecrawl Agent - Advanced Web Scraping with MCP Tools Integration

This example demonstrates how to connect an ADK agent to a Firecrawl MCP server
using the MCPToolset. The agent can perform advanced web scraping operations like
single page scraping, batch scraping, web crawling, content extraction, and deep research.
"""

import os
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

# Create the ADK agent with Firecrawl MCP tools
root_agent = LlmAgent(
    model='gemini-3-flash-preview',
    name='firecrawl_mcp_agent',
    instruction="""
    You are an advanced web scraping and research assistant powered by Firecrawl.
    
    You have access to comprehensive web scraping tools through the Model Context Protocol (MCP):
    
    🔧 **Available Tools:**
    - **firecrawl_scrape**: Extract content from a single URL with advanced options
    - **firecrawl_batch_scrape**: Efficiently scrape multiple URLs with parallel processing
    - **firecrawl_map**: Discover all URLs on a website for exploration
    - **firecrawl_search**: Search the web and extract content from results
    - **firecrawl_crawl**: Perform comprehensive website crawling with depth control
    - **firecrawl_extract**: Extract structured data using AI-powered analysis
    - **firecrawl_deep_research**: Conduct in-depth research with multi-source analysis
    - **firecrawl_generate_llmstxt**: Generate LLMs.txt files for domains
    - **firecrawl_check_crawl_status**: Monitor crawl job progress
    - **firecrawl_check_batch_status**: Monitor batch operation progress
    
    🎯 **Tool Selection Guide:**
    - **Single URL**: Use `firecrawl_scrape`
    - **Multiple known URLs**: Use `firecrawl_batch_scrape`
    - **Discover URLs**: Use `firecrawl_map`
    - **Web search**: Use `firecrawl_search`
    - **Structured data**: Use `firecrawl_extract`
    - **Deep research**: Use `firecrawl_deep_research`
    - **Full site analysis**: Use `firecrawl_crawl` (with caution on limits)
    
    🌟 **Key Features:**
    - Automatic rate limiting and retry logic
    - Parallel processing for batch operations
    - LLM-powered content extraction
    - Support for multiple output formats (Markdown, HTML, JSON)
    - Advanced filtering and content selection
    - Mobile and desktop rendering options
    
    💡 **Best Practices:**
    - Always explain which tool you're using and why
    - For large operations, inform users about potential wait times
    - Use batch operations for multiple URLs instead of individual scrapes
    - Leverage structured extraction for specific data needs
    - Respect rate limits and be considerate of target websites
    
    🚨 **Important Notes:**
    - Crawl operations can be resource-intensive; use appropriate limits
    - Batch operations are queued and may take time to complete
    - Always check the status of long-running operations
    - Some tools require a valid Firecrawl API key
    
    Be helpful, efficient, and always explain your approach to web scraping tasks.
    """,
    tools=[
        MCPToolset(
            connection_params=StdioServerParameters(
                command='npx',
                args=[
                    "-y",  # Auto-confirm npm package installation
                    "firecrawl-mcp",  # The Firecrawl MCP server package
                ],
                env={
                    # Note: Users need to set FIRECRAWL_API_KEY in their environment
                    # or add it to their system environment variables
                    "FIRECRAWL_API_KEY": os.getenv("FIRECRAWL_API_KEY", "")
                }
            ),
            # Optional: Filter which tools from the MCP server to expose
            # Uncomment the line below to limit to specific tools
            # tool_filter=['firecrawl_scrape', 'firecrawl_batch_scrape', 'firecrawl_search', 'firecrawl_map']
        )
    ],
)

# Export the agent for use with ADK web
__all__ = ['root_agent']

# Example usage in a script
if __name__ == "__main__":
    print("🔥 Firecrawl MCP Agent initialized!")
    print("\n🔧 Available Capabilities:")
    print("- Single page scraping with advanced options")
    print("- Batch processing of multiple URLs")
    print("- Website mapping and URL discovery")
    print("- Web search with content extraction")
    print("- Comprehensive website crawling")
    print("- AI-powered structured data extraction")
    print("- Deep research with multi-source analysis")
    print("- LLMs.txt generation for domains")
    
    print("\n🚀 To use this agent:")
    print("1. Set your Firecrawl API key: export FIRECRAWL_API_KEY=your_api_key")
    print("2. Run 'adk web' from the tutorials root directory")
    print("3. Select 'firecrawl_mcp_agent' from the dropdown")
    
    print("\n💡 Example commands to try:")
    print("   - 'Scrape the homepage of https://example.com'")
    print("   - 'Find all blog post URLs on https://blog.example.com'")
    print("   - 'Search for recent AI research papers and extract key information'")
    print("   - 'Extract product details from this e-commerce page: [URL]'")
    print("   - 'Perform deep research on sustainable energy technologies'")
    print("   - 'Crawl the documentation section of https://docs.example.com'")
    
    print("\n⚠️  Important Setup:")
    print("- Requires Node.js for the Firecrawl MCP server")
    print("- Requires a valid Firecrawl API key (get one at https://firecrawl.dev)")
    print("- Some operations may take time for large datasets") 