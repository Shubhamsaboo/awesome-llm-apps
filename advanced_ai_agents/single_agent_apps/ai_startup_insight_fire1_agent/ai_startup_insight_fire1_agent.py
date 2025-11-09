from firecrawl import FirecrawlApp
import streamlit as st
import os
import json
from agno.agent import Agent
from agno.run.agent import RunOutput
from agno.models.openai import OpenAIChat

st.set_page_config(
    page_title="Startup Info Extraction",
    page_icon="🔍",
    layout="wide"
)

st.title("AI Startup Insight with Firecrawl's FIRE-1 Agent")

# Sidebar for API key
with st.sidebar:
    st.header("API Configuration")
    firecrawl_api_key = st.text_input("Firecrawl API Key", type="password")
    openai_api_key = st.text_input("OpenAI API Key", type="password")
    st.caption("Your API keys are securely stored and not shared.")
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("This tool extracts company information from websites using Firecrawl's FIRE-1 agent and provides AI-powered business analysis.")
    
    st.markdown("### How It Works")
    st.markdown("1. 🔍 **FIRE - 1 Agent** extracts structured data from websites")
    st.markdown("2. 🧠 **Agno Agent** analyzes the data for business insights")
    st.markdown("3. 📊 **Results** are presented in an organized format")
    

# Main content
# Add information about Firecrawl's capabilities
st.markdown("## 🔥 Firecrawl FIRE 1 Agent Capabilities")

col1, col2 = st.columns(2)

with col1:
    st.info("**Advanced Web Extraction**\n\nFirecrawl's FIRE 1 agent combined with the extract endpoint can intelligently navigate websites to extract structured data, even from complex layouts and dynamic content.")
    
    st.success("**Interactive Navigation**\n\nThe agent can interact with buttons, links, input fields, and other dynamic elements to access hidden information.")

with col2:
    st.warning("**Multi-page Processing**\n\nFIRE can handle pagination and multi-step processes, allowing it to gather comprehensive data across entire websites.")
    
    st.error("**Intelligent Data Structuring**\n\nThe agent automatically structures extracted information according to your specified schema, making it immediately usable.")

st.markdown("---")

st.markdown("### 🌐 Enter Website URLs")
st.markdown("Provide one or more company website URLs (one per line) to extract information.")

website_urls = st.text_area("Website URLs (one per line)", placeholder="https://example.com\nhttps://another-company.com")

# Define a JSON schema directly without Pydantic
extraction_schema = {
    "type": "object",
    "properties": {
        "company_name": {
            "type": "string",
            "description": "The official name of the company or startup"
        },
        "company_description": {
            "type": "string",
            "description": "A description of what the company does and its value proposition"
        },
        "company_mission": {
            "type": "string",
            "description": "The company's mission statement or purpose"
        },
        "product_features": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "Key features or capabilities of the company's products/services"
        },
        "contact_phone": {
            "type": "string",
            "description": "Company's contact phone number if available"
        }
    },
    "required": ["company_name", "company_description", "product_features"]
}



# Custom CSS for better UI
st.markdown("""
<style>
.stButton button {
    background-color: #FF4B4B;
    color: white;
    font-weight: bold;
    border-radius: 10px;
    padding: 0.5rem 1rem;
    border: none;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
}
.stButton button:hover {
    background-color: #FF2B2B;
    box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
    transform: translateY(-2px);
}
.css-1r6slb0 {
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
</style>
""", unsafe_allow_html=True)

# Start extraction when button is clicked
if st.button("🚀 Start Analysis", type="primary"):
    if not website_urls.strip():
        st.error("Please enter at least one website URL")
    else:
        try:
            with st.spinner("Extracting information from website..."):
                # Initialize the FirecrawlApp with the API key
                app = FirecrawlApp(api_key=firecrawl_api_key)
                
                # Parse the input URLs more robustly
                # Split by newline, strip whitespace from each line, and filter out empty lines
                urls = [url.strip() for url in website_urls.split('\n') if url.strip()]
                
                # Debug: Show the parsed URLs
                st.info(f"Attempting to process these URLs: {urls}")
                
                if not urls:
                    st.error("No valid URLs found after parsing. Please check your input.")
                elif not openai_api_key:
                    st.warning("Please provide an OpenAI API key in the sidebar to get AI analysis.")
                else:
                    # Create tabs for each URL
                    tabs = st.tabs([f"Website {i+1}: {url}" for i, url in enumerate(urls)])
                    
                    # Initialize the Agno agent once (outside the loop)
                    if openai_api_key:
                        agno_agent = Agent(
                            model=OpenAIChat(id="gpt-4o", api_key=openai_api_key),
                            instructions="""You are an expert business analyst who provides concise, insightful summaries of companies.
                            You will be given structured data about a company including its name, description, mission, and product features.
                            Your task is to analyze this information and provide a brief, compelling summary that highlights:
                            1. What makes this company unique or innovative
                            2. The core value proposition for customers
                            3. The potential market impact or growth opportunities
                            
                            Keep your response under 150 words, be specific, and focus on actionable insights.
                            """,
                            markdown=True
                        )
                    
                    # Process each URL one at a time
                    for i, (url, tab) in enumerate(zip(urls, tabs)):
                        with tab:
                            st.markdown(f"### 🔍 Analyzing: {url}")
                            st.markdown("<hr style='border: 2px solid #FF4B4B; border-radius: 5px;'>", unsafe_allow_html=True)
                            
                            with st.spinner(f"FIRE agent is extracting information from {url}..."):
                                try:
                                    # Extract data for this single URL
                                    data = app.extract(
                                        [url],  # Pass as a list with a single URL
                                        params={
                                            'prompt': '''
Analyze this company website thoroughly and extract comprehensive information.

1. Company Information:
   - Identify the official company name
     Explain: This is the legal name the company operates under.
   - Extract a detailed yet concise description of what the company does
   - Find the company's mission statement or purpose
     Explain: What problem is the company trying to solve? How do they aim to make a difference?

2. Product/Service Information:
   - Identify 3-5 specific product features or service offerings
     Explain: What are the key things their product or service can do? Describe as if explaining to a non-expert.
   - Focus on concrete capabilities rather than marketing claims
     Explain: What does the product actually do, in simple terms, rather than how it's advertised?
   - Be specific about what the product/service actually does
     Explain: Give examples of how a customer might use this product or service in their daily life.

3. Contact Information:
   - Find direct contact methods (phone numbers)
     Explain: How can a potential customer reach out to speak with someone at the company?
   - Only extract contact information that is explicitly provided
     Explain: We're looking for official contact details, not inferring or guessing.

Important guidelines:
- Be thorough but concise in your descriptions
- Extract factual information, not marketing language
- If information is not available, do not make assumptions
- For each piece of information, provide a brief, simple explanation of what it means and why it's important
- Include a layman's explanation of what the company does, as if explaining to someone with no prior knowledge of the industry or technology involved
''',
                                            'schema': extraction_schema,
                                            'agent': {"model": "FIRE-1"}
                                        }
                                    )
                                    
                                    # Check if extraction was successful
                                    if data and data.get('data'):
                                        # Display extracted data
                                        st.subheader("📊 Extracted Information")
                                        company_data = data.get('data')
                                        
                                        # Display company name prominently
                                        if 'company_name' in company_data:
                                            st.markdown(f"{company_data['company_name']}")
                                            
                                        
                                        # Display other extracted fields
                                        for key, value in company_data.items():
                                            if key == 'company_name':
                                                continue  # Already displayed above
                                                
                                            display_key = key.replace('_', ' ').capitalize()
                                            
                                            if value:  # Only display if there's a value
                                                if isinstance(value, list):
                                                    st.markdown(f"**{display_key}:**")
                                                    for item in value:
                                                        st.markdown(f"- {item}")
                                                elif isinstance(value, str):
                                                    st.markdown(f"**{display_key}:** {value}")
                                                elif isinstance(value, bool):
                                                    st.markdown(f"**{display_key}:** {str(value)}")
                                                else:
                                                    st.write(f"**{display_key}:**", value)
                                        
                                        # Process with Agno agent
                                        if openai_api_key:
                                            with st.spinner("Generating AI analysis..."):
                                                # Run the agent with the extracted data
                                                agent_response: RunOutput = agno_agent.run(f"Analyze this company data and provide insights: {json.dumps(company_data)}")
                                                
                                                # Display the agent's analysis in a highlighted box
                                                st.subheader("🧠 AI Business Analysis")
                                                st.markdown(agent_response.content)
                                        
                                        # Show raw data in expander
                                        with st.expander("🔍 View Raw API Response"):
                                            st.json(data)
                                            
                                        # Add processing details
                                        with st.expander("ℹ️ Processing Details"):
                                            st.markdown("**FIRE Agent Actions:**")
                                            st.markdown("- 🔍 Scanned website content and structure")
                                            st.markdown("- 🖱️ Interacted with necessary page elements")
                                            st.markdown("- 📊 Extracted and structured data according to schema")
                                            st.markdown("- 🧠 Applied AI reasoning to identify relevant information")
                                            
                                            if 'status' in data:
                                                st.markdown(f"**Status:** {data['status']}")
                                            if 'expiresAt' in data:
                                                st.markdown(f"**Data Expires:** {data['expiresAt']}")
                                    else:
                                        st.error(f"No data was extracted from {url}. The website might be inaccessible, or the content structure may not match the expected format.")
                                        
                                except Exception as e:
                                    st.error(f"Error processing {url}: {str(e)}")
        except Exception as e:
            st.error(f"Error during extraction: {str(e)}")

