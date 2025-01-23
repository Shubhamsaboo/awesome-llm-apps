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
    links: List[str] = Field(default_factory=list, description="The link to the user's profile or the question/answer post")

# Define a schema for the entire page, containing multiple interactions
class QuoraPageSchema(BaseModel):
    interactions: List[QuoraUserInteractionSchema] = Field(description="List of all user interactions (questions and answers) on the page")

# Step 1: Search for relevant URLs using Firecrawl
def search_for_urls(company_description, firecrawl_api_key, num_links):
    print("Step 1: Searching for relevant URLs using Firecrawl...")
    url = "https://api.firecrawl.dev/v1/search"
    headers = {
        "Authorization": f"Bearer {firecrawl_api_key}",
        "Content-Type": "application/json"
    }
    query1 = f"quora websites where people are looking for {company_description} services"
    payload = {
        "query": query1,
        "limit": num_links,  # Use the num_links parameter here
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

# Step 2: Extract user info from URLs using Firecrawl's scrape endpoint
def extract_user_info_from_urls(urls, firecrawl_api_key):
    print("\nStep 2: Extracting user info from URLs using Firecrawl's scrape endpoint...")
    user_info_list = []
    firecrawl_app = FirecrawlApp(api_key=firecrawl_api_key)
    
    try:
        # Use the new scrape endpoint with all URLs at once
        response = firecrawl_app.extract(
            urls,
            {
                'prompt': 'Extract all user information including username, bio, post type (question/answer), timestamp, upvotes, and links to user profile or Quora posts. Focus on identifying potential leads who are asking questions or providing answers related to the topic.',
                'schema': QuoraPageSchema.model_json_schema(),
            }
        )
        
        print("Raw response:", response)  # Debug print
        
        # Process the extracted data from the new response format
        if response.get('success') and response.get('status') == 'completed':
            # Get all interactions from the data
            interactions = response.get('data', {}).get('interactions', [])
            
            if interactions:
                # Store all interactions with their source URL
                for url in urls:
                    user_info_list.append({
                        "website_url": url,
                        "user_info": interactions  # Each URL gets all interactions since they're combined
                    })
                
                print(f"Extracted {len(interactions)} user interactions")
                print("Sample users found:")
                for user in interactions[:3]:  # Show first 3 users as sample
                    print(f"- {user['username']} ({user['post_type']}) - {user['bio'][:50]}...")
        else:
            print("Failed to get successful response or incomplete status")
            if response:
                print("Response status:", response.get('status'))
                print("Success flag:", response.get('success'))
    
    except Exception as e:
        print(f"Error during extraction: {str(e)}")
    
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
    
    try:
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
    except Exception as e:
        print(f"Error creating Google Sheet: {str(e)}")
    return None

def create_prompt_transformation_agent(openai_api_key):
    """Create a Phidata agent that transforms user queries into concise company descriptions."""
    return Agent(
        model=OpenAIChat(id="gpt-4-turbo", api_key=openai_api_key),
        system_prompt="""You are an expert at transforming detailed user queries into concise company descriptions.
Your task is to extract the core business/product focus in 3-4 words.

Examples:
Input: "Generate leads looking for AI-powered customer support chatbots for e-commerce stores."
Output: "AI customer support chatbots"

Input: "Find people interested in voice cloning technology for creating audiobooks and podcasts"
Output: "voice cloning technology"

Input: "Looking for users who need automated video editing software with AI capabilities"
Output: "AI video editing software"

Input: "Need to find businesses interested in implementing machine learning solutions for fraud detection"
Output: "ML fraud detection"

Always focus on the core product/service and keep it concise but clear.""",
        markdown=True
    )

# Modify the Streamlit UI
def main():
    st.title("🎯 AI Lead Generation Agent")
    st.info("This firecrawl powered agent helps you generate leads from Quora by searching for relevant posts and extracting user information.")

    # Sidebar for API keys and number of links
    with st.sidebar:
        st.header("API Keys")
        firecrawl_api_key = st.text_input("Firecrawl API Key", type="password")
        st.caption(" Get your Firecrawl API key from [Firecrawl's website](https://www.firecrawl.dev/app/api-keys)")
        openai_api_key = st.text_input("OpenAI API Key", type="password")
        st.caption(" Get your OpenAI API key from [OpenAI's website](https://platform.openai.com/api-keys)")
        composio_api_key = st.text_input("Composio API Key", type="password")
        st.caption(" Get your Composio API key from [Composio's website](https://composio.ai)")
        
        num_links = st.number_input("Number of links to search", min_value=1, max_value=10, value=3)
        
        if st.button("Reset"):
            st.session_state.clear()
            st.experimental_rerun()

    # Main input for detailed query
    user_query = st.text_area(
        "Describe what kind of leads you're looking for:",
        placeholder="e.g., Looking for users who need automated video editing software with AI capabilities",
        help="Be specific about the product/service and target audience. The AI will convert this into a focused search query."
    )

    if st.button("Generate Leads"):
        if not all([firecrawl_api_key, openai_api_key, composio_api_key, user_query]):
            st.error("Please fill in all the API keys and describe what leads you're looking for.")
        else:
            # First, transform the user query into a concise company description
            with st.spinner("Processing your query..."):
                transform_agent = create_prompt_transformation_agent(openai_api_key)
                company_description = transform_agent.run(f"Transform this query into a concise 3-4 word company description: {user_query}")
                st.write("🎯 Searching for:", company_description.content)
            
            with st.spinner("Searching for relevant URLs..."):
                urls = search_for_urls(company_description.content, firecrawl_api_key, num_links)
            
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