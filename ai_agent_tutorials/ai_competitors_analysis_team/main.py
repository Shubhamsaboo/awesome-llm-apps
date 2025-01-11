from exa_py import Exa
from phi.agent import Agent
from phi.tools.firecrawl import FirecrawlTools
from phi.model.openai import OpenAIChat
from phi.tools.duckduckgo import DuckDuckGo

exa = Exa(api_key="")

firecrawl_tools = FirecrawlTools(
    api_key="fc-",
    scrape=False,
    crawl=True,
    limit=5
)

firecrawl_agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini", api_key="sk-proj-"),
    tools=[firecrawl_tools, DuckDuckGo() ],
    show_tool_calls=True,
    markdown=True
)

analysis_agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini", api_key="sk-proj-"),
    show_tool_calls=True,
    markdown=True
)

def get_competitor_urls(url=None, description=None):

    if url:
        result = exa.find_similar(
            url=url,
            num_results=2,
            exclude_source_domain=True,
            category="company"
        )
    elif description:
        result = exa.search(
            description,
            type="neural",
            category="company",
            use_autoprompt=True,
            num_results=2
        )
    else:
        raise ValueError("Please provide either a URL or a description.")
    
    competitor_urls = [item.url for item in result.results]
    return competitor_urls

def extract_competitor_info(competitor_url: str):
    try:
        crawl_response = firecrawl_agent.run(f"Crawl and summarize {competitor_url}")
        crawled_data = crawl_response.content
        
        structured_info = firecrawl_agent.run(
            f"""Extract the following information from the crawled data:
            - Product pricing and features: Extract exact pricing numbers from their pricing page.
            - Technology stack information
            - Marketing messaging/positioning
            - Customer testimonials/case studies
            - Latest news and developements (use DuckDuckGo to search for the latest news and developements)

            Crawled Data:
            {crawled_data}
            """
        )
        
        return {
            "competitor": competitor_url,
            "data": structured_info.content
        }
    except Exception as e:
        return {
            "competitor": competitor_url,
            "error": str(e)
        }

def generate_analysis_report(competitor_data: list):
    combined_data = "\n\n".join([str(data) for data in competitor_data])
    
    report = analysis_agent.run(
        f"""Analyze the following competitor data and identify market opportunities to improve my own company:
        {combined_data}

        Tasks:
        1. Identify market gaps and opportunities based on competitor offerings
        2. Analyze competitor weaknesses that we can capitalize on
        3. Recommend unique features or capabilities we should develop
        4. Suggest pricing and positioning strategies to gain competitive advantage
        5. Outline specific growth opportunities in underserved market segments
        6. Provide actionable recommendations for product development and go-to-market strategy

        Focus on finding opportunities where we can differentiate and do better than competitors.
        Highlight any unmet customer needs or pain points we can address.
        """
    )
    return report.content

def main():
    competitor_urls = get_competitor_urls(url="https://www.harvey.ai")
    print(f"Competitor URLs: {competitor_urls}")
    
    competitor_data = []
    for url in competitor_urls:
        print(f"\nAnalyzing Competitor: {url}")
        competitor_info = extract_competitor_info(url)
        competitor_data.append(competitor_info)
    
    analysis_report = generate_analysis_report(competitor_data)
    
    print("\nCompetitor Analysis Report:")
    print(analysis_report)

if __name__ == "__main__":
    main()