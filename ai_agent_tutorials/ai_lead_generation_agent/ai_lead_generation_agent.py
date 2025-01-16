import streamlit as st
import requests
from phi.agent import Agent
from phi.tools.firecrawl import FirecrawlTools
from phi.model.openai import OpenAIChat
from firecrawl import FirecrawlApp
from pydantic import BaseModel, Field
from typing import List
from composio_phidata import Action, ComposioToolSet

# Define a schema for a single user interaction (question or answer)
class QuoraUserInteractionSchema(BaseModel):
    username: str = Field(description="The username of the user who posted the question or answer")
    bio: str = Field(description="The bio or description of the user")
    post_type: str = Field(description="The type of post, either 'question' or 'answer'")
    timestamp: str = Field(description="When the question or answer was posted")
    upvotes: int = Field(default=0, description="Number of upvotes received")
    links: List[str] = Field(default_factory=list, description="Any links included in the post")

# Define a schema for the entire page, containing multiple interactions
class QuoraPageSchema(BaseModel):
    interactions: List[QuoraUserInteractionSchema] = Field(description="List of all user interactions (questions and answers) on the page")

# Step 1: Search for relevant URLs using Firecrawl
def search_for_urls(company_description, firecrawl_api_key):
    print("Step 1: Searching for relevant URLs using Firecrawl...")
    url = "https://api.firecrawl.dev/v1/search"
    headers = {
        "Authorization": f"Bearer {firecrawl_api_key}",
        "Content-Type": "application/json"
    }
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
            print(f"Found {len(results)} relevant URLs.")
            return [result["url"] for result in results]
        else:
            print("Search request was not successful.")
            print(data.get("warning", "No warning provided."))
    else:
        print(f"Failed to retrieve data. Status code: {response.status_code}")
    return []

# Step 2: Extract user info from URLs using Firecrawl's LLM extract
def extract_user_info_from_urls(urls, firecrawl_api_key):
    print("\nStep 2: Extracting user info from URLs using Firecrawl's LLM extract...")
    user_info_list = []
    firecrawl_app = FirecrawlApp(api_key=firecrawl_api_key)
    for website_url in urls:
        print(f"Extracting user info from: {website_url}")
        
        # Use Firecrawl's LLM extract to get structured data
        data = firecrawl_app.scrape_url(website_url, {
            'formats': ['extract'],
            'extract': {
                'schema': QuoraPageSchema.model_json_schema(),
            }
        })
        
        # Extract the interactions from the response
        extracted_data = data.get("extract", {})
        interactions = extracted_data.get("interactions", [])
        
        # Store the results
        user_info_list.append({
            "website_url": website_url,
            "user_info": interactions
        })
        print(f"Extracted {len(interactions)} interactions from {website_url}.")
    return user_info_list

# Step 3: Format the extracted user info into a flattened JSON structure
def format_user_info_to_flattened_json(user_info_list):
    print("\nStep 3: Formatting the extracted user info into a flattened JSON structure...")
    flattened_data = []
    
    for info in user_info_list:
        website_url = info["website_url"]
        user_info = info["user_info"]
        
        for interaction in user_info:
            flattened_interaction = {
                "Website URL": website_url,
                "Username": interaction.get("username", ""),
                "Bio": interaction.get("bio", ""),
                "Post Type": interaction.get("post_type", ""),
                "Timestamp": interaction.get("timestamp", ""),
                "Upvotes": interaction.get("upvotes", 0),
                "Links": ", ".join(interaction.get("links", [])),  # Convert list of links to a single string
            }
            flattened_data.append(flattened_interaction)
    
    print(f"Formatted {len(flattened_data)} interactions into flattened JSON.")
    return flattened_data

# Step 4: Create a new Phidata agent to interact with Google Sheets
def create_google_sheets_agent(composio_api_key, openai_api_key):
    print("\nStep 4: Creating a new Phidata agent to interact with Google Sheets...")
    # Initialize Composio Toolset
    composio_toolset = ComposioToolSet(api_key=composio_api_key)
    
    # Get the Google Sheets tool
    google_sheets_tool = composio_toolset.get_tools(actions=[Action.GOOGLESHEETS_SHEET_FROM_JSON])[0]
    
    # Create the agent
    google_sheets_agent = Agent(
        model=OpenAIChat(id="gpt-4o-mini", api_key=openai_api_key),
        tools=[google_sheets_tool],
        show_tool_calls=True,  # Enable verbose tool call output for debugging
        system_prompt="You are an expert at creating and updating Google Sheets. You will be given user information in JSON format, and you need to write it into a new Google Sheet.",
        markdown=True
    )
    print("Google Sheets agent created successfully.")
    return google_sheets_agent

# Step 5: Write formatted user info to Google Sheets
def write_to_google_sheets(flattened_data, composio_api_key, openai_api_key):
    print("\nStep 5: Writing formatted user info to Google Sheets...")
    # Create the Google Sheets agent
    google_sheets_agent = create_google_sheets_agent(composio_api_key, openai_api_key)
    
    # Create a new Google Sheet from the flattened JSON data
    print("Creating a new Google Sheet with the flattened JSON data...")
    create_sheet_response = google_sheets_agent.run(
        f"Create a new Google Sheet with the following data:\n"
        f"Title: Quora User Info\n"
        f"Sheet Name: Sheet1\n"
        f"Sheet JSON: {flattened_data}"
    )
    print("Create Sheet Response:", create_sheet_response.content)
    
    # Extract the Google Sheets link from the response
    if "https://docs.google.com/spreadsheets/d/" in create_sheet_response.content:
        google_sheets_link = create_sheet_response.content.split("https://docs.google.com/spreadsheets/d/")[1].split(" ")[0]
        google_sheets_link = f"https://docs.google.com/spreadsheets/d/{google_sheets_link}"
        return google_sheets_link
    return None

# Streamlit UI
def main():
    st.title("AI Lead Generation Agent")
    st.info("This firecrawl powered agent helps you generate leads from Quora by searching for relevant posts and extracting user information.")

    # Sidebar for API keys
    with st.sidebar:
        st.header("API Keys")
        firecrawl_api_key = st.text_input("Firecrawl API Key", type="password")
        openai_api_key = st.text_input("OpenAI API Key", type="password")
        composio_api_key = st.text_input("Composio API Key", type="password")

    # Main input for company description
    company_description = st.text_input("Enter your company description or the niche you want to find leads in:", placeholder="e.g. AI voice cloning, Video Generation AI tools")

    if st.button("Generate Leads"):
        if not all([firecrawl_api_key, openai_api_key, composio_api_key, company_description]):
            st.error("Please fill in all the API keys and the company description.")
        else:
            with st.spinner("Searching for relevant URLs..."):
                urls = search_for_urls(company_description, firecrawl_api_key)
            
            if urls:
                st.subheader("Quora Links Used:")
                for url in urls:
                    st.write(url)
                
                with st.spinner("Extracting user info from URLs..."):
                    user_info_list = extract_user_info_from_urls(urls, firecrawl_api_key)
                
                with st.spinner("Formatting user info..."):
                    flattened_data = format_user_info_to_flattened_json(user_info_list)
                
                with st.spinner("Writing to Google Sheets..."):
                    google_sheets_link = write_to_google_sheets(flattened_data, composio_api_key, openai_api_key)
                
                if google_sheets_link:
                    st.success("Lead generation and data writing to Google Sheets completed successfully!")
                    st.subheader("Google Sheets Link:")
                    st.markdown(f"[View Google Sheet]({google_sheets_link})")
                else:
                    st.error("Failed to retrieve the Google Sheets link.")
            else:
                st.warning("No relevant URLs found.")

if __name__ == "__main__":
    main()