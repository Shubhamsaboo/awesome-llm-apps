import streamlit as st
# from exa_py import Exa
from agno.agent import Agent
from agno.tools.firecrawl import FirecrawlTools
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools
import pandas as pd
import requests
from firecrawl import FirecrawlApp
from pydantic import BaseModel, Field
from typing import List, Optional
import json

# Streamlit UI
st.set_page_config(page_title="AI Competitor Intelligence Agent Team", layout="wide")

# Sidebar for API keys
st.sidebar.title("API Keys")
openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")
firecrawl_api_key = st.sidebar.text_input("Firecrawl API Key", type="password")

# Add search engine selection before API keys
search_engine = st.sidebar.selectbox(
    "Select Search Endpoint",
    options=["Perplexity AI - Sonar Pro", "Exa AI"],
    help="Choose which AI service to use for finding competitor URLs"
)

# Show relevant API key input based on selection
if search_engine == "Perplexity AI - Sonar Pro":
    perplexity_api_key = st.sidebar.text_input("Perplexity API Key", type="password")
    # Store API keys in session state
    if openai_api_key and firecrawl_api_key and perplexity_api_key:
        st.session_state.openai_api_key = openai_api_key
        st.session_state.firecrawl_api_key = firecrawl_api_key
        st.session_state.perplexity_api_key = perplexity_api_key
    else:
        st.sidebar.warning("Please enter all required API keys to proceed.")
else:  # Exa AI
    exa_api_key = st.sidebar.text_input("Exa API Key", type="password")
    # Store API keys in session state
    if openai_api_key and firecrawl_api_key and exa_api_key:
        st.session_state.openai_api_key = openai_api_key
        st.session_state.firecrawl_api_key = firecrawl_api_key
        st.session_state.exa_api_key = exa_api_key
    else:
        st.sidebar.warning("Please enter all required API keys to proceed.")

# Main UI
st.title("🧲 AI Competitor Intelligence Agent Team")
st.info(
    """
    This app helps businesses analyze their competitors by extracting structured data from competitor websites and generating insights using AI.
    - Provide a **URL** or a **description** of your company.
    - The app will fetch competitor URLs, extract relevant information, and generate a detailed analysis report.
    """
)
st.success("For better results, provide both URL and a 5-6 word description of your company!")

# Input fields for URL and description
url = st.text_input("Enter your company URL :")
description = st.text_area("Enter a description of your company (if URL is not available):")

# Initialize API keys and tools
if "openai_api_key" in st.session_state and "firecrawl_api_key" in st.session_state:
    if (search_engine == "Perplexity AI - Sonar Pro" and "perplexity_api_key" in st.session_state) or \
       (search_engine == "Exa AI" and "exa_api_key" in st.session_state):
        
        # Initialize Exa only if selected
        if search_engine == "Exa AI":
            exa = Exa(api_key=st.session_state.exa_api_key)

        firecrawl_tools = FirecrawlTools(
            api_key=st.session_state.firecrawl_api_key,
            scrape=False,
            crawl=True,
            limit=5
        )

        firecrawl_agent = Agent(
            model=OpenAIChat(id="gpt-4o", api_key=st.session_state.openai_api_key),
            tools=[firecrawl_tools, DuckDuckGoTools()],
            show_tool_calls=True,
            markdown=True
        )

        analysis_agent = Agent(
            model=OpenAIChat(id="gpt-4o", api_key=st.session_state.openai_api_key),
            show_tool_calls=True,
            markdown=True
        )

        # New agent for comparing competitor data
        comparison_agent = Agent(
            model=OpenAIChat(id="gpt-4o", api_key=st.session_state.openai_api_key),
            show_tool_calls=True,
            markdown=True
        )

        def get_competitor_urls(url: str = None, description: str = None) -> list[str]:
            if not url and not description:
                raise ValueError("Please provide either a URL or a description.")

            if search_engine == "Perplexity AI - Sonar Pro":
                perplexity_url = "https://api.perplexity.ai/chat/completions"
                
                content = "Find me 3 competitor company URLs similar to the company with "
                if url and description:
                    content += f"URL: {url} and description: {description}"
                elif url:
                    content += f"URL: {url}"
                else:
                    content += f"description: {description}"
                content += ". ONLY RESPOND WITH THE URLS, NO OTHER TEXT."

                payload = {
                    "model": "sonar-pro",
                    "messages": [
                        {
                            "role": "system",
                            "content": "Be precise and only return 3 company URLs ONLY."
                        },
                        {
                            "role": "user",
                            "content": content
                        }
                    ],
                    "max_tokens": 1000,
                    "temperature": 0.2,
                }
                
                headers = {
                    "Authorization": f"Bearer {st.session_state.perplexity_api_key}",
                    "Content-Type": "application/json"
                }

                try:
                    response = requests.post(perplexity_url, json=payload, headers=headers)
                    response.raise_for_status()
                    urls = response.json()['choices'][0]['message']['content'].strip().split('\n')
                    return [url.strip() for url in urls if url.strip()]
                except Exception as e:
                    st.error(f"Error fetching competitor URLs from Perplexity: {str(e)}")
                    return []

            else:  # Exa AI
                try:
                    if url:
                        result = exa.find_similar(
                            url=url,
                            num_results=3,
                            exclude_source_domain=True,
                            category="company"
                        )
                    else:
                        result = exa.search(
                            description,
                            type="neural",
                            category="company",
                            use_autoprompt=True,
                            num_results=3
                        )
                    return [item.url for item in result.results]
                except Exception as e:
                    st.error(f"Error fetching competitor URLs from Exa: {str(e)}")
                    return []

        class CompetitorDataSchema(BaseModel):
            company_name: str = Field(description="Name of the company")
            pricing: str = Field(description="Pricing details, tiers, and plans")
            key_features: List[str] = Field(description="Main features and capabilities of the product/service")
            tech_stack: List[str] = Field(description="Technologies, frameworks, and tools used")
            marketing_focus: str = Field(description="Main marketing angles and target audience")
            customer_feedback: str = Field(description="Customer testimonials, reviews, and feedback")

        def extract_competitor_info(competitor_url: str) -> Optional[dict]:
            try:
                # Initialize FirecrawlApp with API key
                app = FirecrawlApp(api_key=st.session_state.firecrawl_api_key)
                
                # Add wildcard to crawl subpages
                url_pattern = f"{competitor_url}/*"
                
                extraction_prompt = """
                Extract detailed information about the company's offerings, including:
                - Company name and basic information
                - Pricing details, plans, and tiers
                - Key features and main capabilities
                - Technology stack and technical details
                - Marketing focus and target audience
                - Customer feedback and testimonials
                
                Analyze the entire website content to provide comprehensive information for each field.
                """
                
                response = app.extract(
                    [url_pattern],
                    prompt=extraction_prompt,
                    schema=CompetitorDataSchema.model_json_schema()
                )
                
                # Handle ExtractResponse object
                try:
                    if hasattr(response, 'success') and response.success:
                        if hasattr(response, 'data') and response.data:
                            extracted_info = response.data
                            
                            # Create JSON structure
                            competitor_json = {
                                "competitor_url": competitor_url,
                                "company_name": extracted_info.get('company_name', 'N/A') if isinstance(extracted_info, dict) else getattr(extracted_info, 'company_name', 'N/A'),
                                "pricing": extracted_info.get('pricing', 'N/A') if isinstance(extracted_info, dict) else getattr(extracted_info, 'pricing', 'N/A'),
                                "key_features": extracted_info.get('key_features', [])[:5] if isinstance(extracted_info, dict) and extracted_info.get('key_features') else getattr(extracted_info, 'key_features', [])[:5] if hasattr(extracted_info, 'key_features') else ['N/A'],
                                "tech_stack": extracted_info.get('tech_stack', [])[:5] if isinstance(extracted_info, dict) and extracted_info.get('tech_stack') else getattr(extracted_info, 'tech_stack', [])[:5] if hasattr(extracted_info, 'tech_stack') else ['N/A'],
                                "marketing_focus": extracted_info.get('marketing_focus', 'N/A') if isinstance(extracted_info, dict) else getattr(extracted_info, 'marketing_focus', 'N/A'),
                                "customer_feedback": extracted_info.get('customer_feedback', 'N/A') if isinstance(extracted_info, dict) else getattr(extracted_info, 'customer_feedback', 'N/A')
                            }
                            
                            return competitor_json
                        else:
                            return None
                    else:
                        return None
                        
                except Exception as response_error:
                    return None
                    
            except Exception as e:
                return None

        def generate_comparison_report(competitor_data: list) -> None:
            # Create DataFrame directly from competitor data
            if not competitor_data:
                st.error("No competitor data available for comparison")
                return
            
            # Prepare data for DataFrame
            table_data = []
            for competitor in competitor_data:
                row = {
                    'Company': f"{competitor.get('company_name', 'N/A')} ({competitor.get('competitor_url', 'N/A')})",
                    'Pricing': competitor.get('pricing', 'N/A')[:100] + '...' if len(competitor.get('pricing', '')) > 100 else competitor.get('pricing', 'N/A'),
                    'Key Features': ', '.join(competitor.get('key_features', [])[:3]) if competitor.get('key_features') else 'N/A',
                    'Tech Stack': ', '.join(competitor.get('tech_stack', [])[:3]) if competitor.get('tech_stack') else 'N/A',
                    'Marketing Focus': competitor.get('marketing_focus', 'N/A')[:100] + '...' if len(competitor.get('marketing_focus', '')) > 100 else competitor.get('marketing_focus', 'N/A'),
                    'Customer Feedback': competitor.get('customer_feedback', 'N/A')[:100] + '...' if len(competitor.get('customer_feedback', '')) > 100 else competitor.get('customer_feedback', 'N/A')
                }
                table_data.append(row)
            
            # Create DataFrame
            df = pd.DataFrame(table_data)
            
            # Display the table
            st.subheader("Competitor Comparison")
            st.dataframe(df, use_container_width=True)
            
            # Also show raw data for debugging
            with st.expander("View Raw Competitor Data"):
                st.json(competitor_data)

        def generate_analysis_report(competitor_data: list):
            # Format the competitor data for the prompt
            formatted_data = json.dumps(competitor_data, indent=2)
            print("Analysis Data:", formatted_data)  # For debugging
            
            report = analysis_agent.run(
                f"""Analyze the following competitor data in JSON format and identify market opportunities to improve my own company:
                
                {formatted_data}

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

        # Run analysis when the user clicks the button
        if st.button("Analyze Competitors"):
            if url or description:
                with st.spinner("Fetching competitor URLs..."):
                    competitor_urls = get_competitor_urls(url=url, description=description)
                    st.write(f"Found {len(competitor_urls)} competitor URLs")
                
                if not competitor_urls:
                    st.error("No competitor URLs found!")
                    st.stop()
                
                competitor_data = []
                successful_extractions = 0
                failed_extractions = 0
                
                for i, comp_url in enumerate(competitor_urls):
                    with st.spinner(f"Analyzing Competitor {i+1}/{len(competitor_urls)}: {comp_url}"):
                        competitor_info = extract_competitor_info(comp_url)
                        
                        if competitor_info is not None:
                            competitor_data.append(competitor_info)
                            successful_extractions += 1
                            st.success(f"✓ Successfully analyzed {comp_url}")
                        else:
                            failed_extractions += 1
                            st.error(f"✗ Failed to analyze {comp_url}")
                
                if competitor_data:
                    st.success(f"Successfully analyzed {successful_extractions}/{len(competitor_urls)} competitors!")
                    
                    # Generate and display comparison report
                    with st.spinner("Generating comparison table..."):
                        generate_comparison_report(competitor_data)
                    
                    # Generate and display final analysis report
                    with st.spinner("Generating analysis report..."):
                        analysis_report = generate_analysis_report(competitor_data)
                        st.subheader("Competitor Analysis Report")
                        st.markdown(analysis_report)
                    
                    st.success("Analysis complete!")
                else:
                    st.error("Could not extract data from any competitor URLs")
                    st.write("This might be due to:")
                    st.write("- API rate limits (try again in a few minutes)")
                    st.write("- Website access issues (some sites block automated access)")
                    st.write("- Invalid URLs (try with a different company description)")
            else:
                st.error("Please provide either a URL or a description.")