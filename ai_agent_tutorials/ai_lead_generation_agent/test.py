import requests

# Define the API endpoint
url = "https://api.firecrawl.dev/v1/search"

# Set your API key in the headers
headers = {
    "Authorization": "Bearer fc-",
    "Content-Type": "application/json"
}

# Define the company name and keywords
company_name = "Rollout AI"
company_description = "voice cloning open source models or api"
keywords = "https://rollout.site"

query1 = f" reddit and quora websites where people are looking for {company_description} services"

# Set the payload
payload = {
    "query": query1,
    "limit": 10,  # Adjust the limit as needed
    "lang": "en",
    "location": "United States",
    "timeout": 60000,
}

# Send the POST request
response = requests.post(url, json=payload, headers=headers)

# Check if the request was successful
if response.status_code == 200:
    data = response.json()
    if data.get("success"):
        results = data.get("data", [])
        similar_company_urls = [result["url"] for result in results]
        print("Similar Company URLs:")
        for url in similar_company_urls:
            print(url)
    else:
        print("Search request was not successful.")
        print(data.get("warning", "No warning provided."))
else:
    print(f"Failed to retrieve data. Status code: {response.status_code}")



    firecrawl_tools = FirecrawlTools(
        api_key=st.session_state.firecrawl_api_key,
        scrape=False,
        crawl=True,
        limit=5
    )

    firecrawl_agent = Agent(
        model=OpenAIChat(id="gpt-4o-mini", api_key=st.session_state.openai_api_key),
        tools=[firecrawl_tools, DuckDuckGo()],
        show_tool_calls=True,
        markdown=True
    )

    analysis_agent = Agent(
        model=OpenAIChat(id="gpt-4o-mini", api_key=st.session_state.openai_api_key),
        show_tool_calls=True,
        markdown=True
    )