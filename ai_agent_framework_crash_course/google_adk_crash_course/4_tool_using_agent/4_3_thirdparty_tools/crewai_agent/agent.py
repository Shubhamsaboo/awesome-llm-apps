from google.adk.agents import LlmAgent
from google.adk.tools.crewai_tool import CrewaiTool
from crewai_tools import (
    ScrapeWebsiteTool,
    DirectorySearchTool,
    FileReadTool
)

scrape_website_tool = CrewaiTool(
    name="scrape_website",
    description="Scrape and extract content from websites",
    tool=ScrapeWebsiteTool(
        config=dict(
            llm=dict(
                provider="google",
                config=dict(model="gemini-3-flash-preview"),
            ),
            embedder=dict(
                provider="google",
                config=dict(
                    model="gemini-embedding-001",
                    task_type="retrieval_document",
                ),
            ),
        )
    )
)

directory_search_tool = CrewaiTool(
    name="directory_search",
    description="Search for files and directories in the local filesystem",
    tool=DirectorySearchTool(
        config=dict(
            llm=dict(
                provider="google",
                config=dict(model="gemini-3-flash-preview"),
            ),
            embedder=dict(
                provider="google",
                config=dict(
                    model="gemini-embedding-001",
                    task_type="retrieval_document",
                ),
            ),
        )
    )
)

file_read_tool = CrewaiTool(
    name="file_read",
    description="Read and analyze content from files",
    tool=FileReadTool(
        config=dict(
            llm=dict(
                provider="google",
                config=dict(model="gemini-3-flash-preview"),
            ),
            embedder=dict(
                provider="google",
                config=dict(
                    model="gemini-embedding-001",
                    task_type="retrieval_document",
                ),
            ),
        )
    )
)

# Create an agent with CrewAI tools
root_agent = LlmAgent(
    name="crewai_agent",
    model="gemini-3-flash-preview",
    description="A versatile agent that uses CrewAI tools for web scraping, file operations, and content analysis",
    instruction="""
    You are a versatile assistant with access to powerful CrewAI tools for web scraping, 
    file operations, and content analysis.
    
    Your capabilities include:
    
    **Web Operations:**
    - Website content search and analysis
    - Web scraping and data extraction
    - Content retrieval from specific URLs
    - Website structure analysis
    
    **File Operations:**
    - Directory and file system search
    - File reading and content analysis
    - Local file processing
    - Document analysis
    
    **Available Tools:**
    - `ScrapeWebsiteTool`: Extract and scrape content from web pages
    - `DirectorySearchTool`: Search local directories and file systems
    - `FileReadTool`: Read and analyze local files
    
    **Guidelines:**
    1. For web content analysis, use ScrapeWebsiteTool
    2. For file operations, use DirectorySearchTool and FileReadTool
    3. Always explain what tool you're using and why
    4. Provide clear summaries of extracted content
    5. Handle errors gracefully and suggest alternatives
    6. Respect website terms of service and robots.txt
    
    **Example workflows:**
    - "Search for pricing information on company.com" → Use ScrapeWebsiteTool
    - "Extract all headings from this webpage" → Use ScrapeWebsiteTool
    - "Find all Python files in this directory" → Use DirectorySearchTool
    - "Read and summarize this document" → Use FileReadTool
    - "Analyze the structure of this website" → Use ScrapeWebsiteTool
    
    **Use Cases:**
    - Content research and analysis
    - Web scraping for data extraction
    - File system exploration
    - Document processing and analysis
    - Website structure analysis
    
    Always provide helpful, accurate information and explain your process clearly.
    Be respectful of website policies and handle sensitive information appropriately.
    """,
    tools=[
        scrape_website_tool,
        directory_search_tool,
        file_read_tool
    ]
) 