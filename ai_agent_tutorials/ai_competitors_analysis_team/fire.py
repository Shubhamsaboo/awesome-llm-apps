from phi.agent import Agent
from phi.tools.firecrawl import FirecrawlTools
from phi.model.openai import OpenAIChat

firecrawl_tools = FirecrawlTools(
    api_key="",
    scrape=False,
    crawl=True,
    limit=5
)

agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini", api_key=""),
    tools=[firecrawl_tools],
    show_tool_calls=True,
    markdown=True
)

def extract_competitor_info(competitor_url: str):
    crawl_response = agent.run(f"Crawl and summarize {competitor_url}")
    crawled_data = crawl_response.content
    
    structured_info = agent.run(
        f"""Extract the following information from the crawled data:
        - Product pricing and features - exact pricing numbers from their pricing page
        - Technology stack information
        - Marketing messaging/positioning
        - Customer testimonials/case studies

        Crawled Data:
        {crawled_data}
        """
    )
    
    return structured_info.content

if __name__ == "__main__":
    competitor_url = "https://www.equal.in"
    competitor_info = extract_competitor_info(competitor_url)
    print(f"Competitor: {competitor_url}")
    print(competitor_info)