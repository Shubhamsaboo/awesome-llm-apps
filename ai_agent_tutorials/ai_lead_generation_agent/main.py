import requests
from phi.agent import Agent
from phi.tools.firecrawl import FirecrawlTools
from phi.model.openai import OpenAIChat

# Step 1: Search for relevant URLs using Firecrawl
def search_for_urls():
    url = "https://api.firecrawl.dev/v1/search"
    headers = {
        "Authorization": "Bearer fc-",  # Replace with your Firecrawl API key
        "Content-Type": "application/json"
    }
    company_description = "voice cloning open source models or api"
    query1 = f"quora websites where people are looking for {company_description} services"
    payload = {
        "query": query1,
        "limit": 3,  # Adjust the limit as needed
        "lang": "en",
        "location": "United States",
        "timeout": 60000,
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            results = data.get("data", [])
            return [result["url"] for result in results]
        else:
            print("Search request was not successful.")
            print(data.get("warning", "No warning provided."))
    else:
        print(f"Failed to retrieve data. Status code: {response.status_code}")
    return []

# Step 2: Set up the Firecrawl Agent
firecrawl_tools = FirecrawlTools(
    api_key="fc-",  # Replace with your Firecrawl API key
    scrape=True,    # Enable scraping to extract detailed content
    crawl=True,     # Enable crawling
    limit=5         # Limit the number of pages to crawl
)

# First Agent: Crawls the website and retrieves content
firecrawl_agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini", api_key="sk-proj-"),  # Replace with your OpenAI API key
    tools=[firecrawl_tools],  # Add Firecrawl tools
    show_tool_calls=False,    # Disable verbose tool call output
    markdown=True
)

# Second Agent: Processes verbose output and extracts user information
extraction_agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini", api_key="sk-proj-"),  # Replace with your OpenAI API key
    show_tool_calls=False,
    system_prompt="You are an expert at extracting user information from responses. You are given a long response of extracted and crawled website information and you need to extract the user information only. Focus on extracting information about both the question asker and the answerers, as they are potential leads.",
    markdown=True
)

# Step 3: Define a function to analyze user info directly from URLs
def analyze_user_info_from_urls(urls):
    user_info_list = []
    for website_url in urls:
        print(f"Analyzing website: {website_url}")
        
        # Step 3.1: Directly instruct the first agent to crawl and analyze the website
        analysis_prompt = (
            f"Visit the website {website_url} using Firecrawl and analyze its content to extract the following information:\n"
            "1. Username of the person asking the question.\n"
            "2. The content of their question.\n"
            "3. Usernames of people answering the question.\n"
            "4. The content of their answers.\n"
            "5. Any additional relevant information (e.g., timestamp, upvotes, links, user bio, location).\n\n"
            "Return the extracted information in a structured format."
        )
        
        # Step 3.2: Run the first agent with the analysis prompt
        analysis_response = firecrawl_agent.run(analysis_prompt)
        analysis_result = analysis_response.content
        
        # Step 3.3: Use the second agent to extract only the user information
        extraction_prompt = (
            f"Extract only the following user information from the content below:\n"
            "1. Username (for both question asker and answerers)\n"
            "2. Post content (question or answer)\n"
            "3. Timestamp\n"
            "4. Upvotes\n"
            "5. Links (if available)\n"
            "6. Any additional relevant information (e.g., user bio, location)\n\n"
            f"Content:\n{analysis_result}"
        )
        extraction_response = extraction_agent.run(extraction_prompt)
        extracted_info = extraction_response.content
        
        # Step 3.4: Store the results
        user_info_list.append({
            "website_url": website_url,
            "user_info": extracted_info
        })
    return user_info_list

# Step 4: Main workflow
def main():
    # Step 4.1: Search for relevant URLs
    urls = search_for_urls()
    print("Relevant URLs Found:")
    for url in urls:
        print(url)

    # Step 4.2: Analyze user info directly from the URLs
    user_info_list = analyze_user_info_from_urls(urls)

    # Step 4.3: Print the extracted information in a detailed format
    print("\nExtracted User Information:")
    for info in user_info_list:
        print(f"Website: {info['website_url']}")
        print(f"User Info:\n{info['user_info']}\n")

# Run the main workflow
if __name__ == "__main__":
    main()