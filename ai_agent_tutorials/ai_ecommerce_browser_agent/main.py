import os
import sys
import asyncio
import streamlit as st
from langchain_openai import ChatOpenAI
from browser_use.agent.service import Agent
from browser_use.browser.browser import Browser, BrowserConfig

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Streamlit UI Setup
st.set_page_config(page_title="E-Commerce Product Finder", page_icon="🛒")

# Initialize session state
if 'search_triggered' not in st.session_state:
    st.session_state.search_triggered = False

# Sidebar for API Key
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("Enter OpenAI API Key:", type="password", key="api_key")
    st.markdown("---")
    st.header("Browser Settings")
    headless = st.checkbox("Run browser in headless mode", value=True)

# Main Content
st.title("🛒 Smart E-Commerce Product Finder")
st.markdown("""
### Find the Best Products Across Multiple Stores
1. Enter your product requirements below
2. Click the Start Search button
3. We'll search Amazon, Flipkart, and Walmart
4. Get the best options compared for you!
""")

# User Input Form
with st.form("product_inputs"):
    product_name = st.text_input("Product Name*", placeholder="e.g. wireless headphones")
    min_price, max_price = st.slider("Price Range ($)*", 0, 500, (50, 200))
    min_rating = st.slider("Minimum Rating*", 0.0, 5.0, 4.0)
    brand_preference = st.text_input("Preferred Brand (optional)", placeholder="e.g. Sony")
    submitted = st.form_submit_button("🚀 Start Search")

if submitted:
    # Validate required fields
    if not product_name:
        st.error("Please enter a product name")
        st.stop()
    if not st.session_state.api_key:
        st.error("Please enter your OpenAI API key in the sidebar")
        st.stop()
    
    st.session_state.search_triggered = True
    st.session_state.product_params = {
        'product_name': product_name,
        'min_price': min_price,
        'max_price': max_price,
        'min_rating': min_rating,
        'brand_preference': brand_preference
    }

if st.session_state.get('search_triggered', False):
    # Initialize browser and LLM
    browser = Browser(
        config=BrowserConfig(
            disable_security=True,
            headless=headless,
        )
    )
    
    llm = ChatOpenAI(model='gpt-4o-mini', api_key=st.session_state.api_key)
    
    # Get parameters from session state
    params = st.session_state.product_params
    
    # Create dynamic tasks
    search_tasks = []
    for site in ["Amazon", "Flipkart"]:
        task = f"""
        Go to {site}.in, search for {params['product_name']} {params['brand_preference']} with:
        - Price between ${params['min_price']} and ${params['max_price']}
        - Minimum rating of {params['min_rating']} stars
        Sort by price low to high, retrieve the 3 best options with their:
        - Product name
        - Price
        - Rating
        - Review count
        - Product URL
        """
        search_tasks.append(task)
    
    # Comparison task
    comparison_task = f"""
    Analyze and compare products from Amazon, Flipkart, and Walmart based on:
    - Price competitiveness (giving weight to lower prices)
    - Rating and review quality (minimum {params['min_rating']}+ stars)
    {"- Brand preference: " + params['brand_preference'] if params['brand_preference'] else ""}
    - Overall value for money
    Select and recommend the top 3 best overall options with detailed justification.
    """
    
    async def run_search():
        with st.spinner("🔍 Searching across e-commerce platforms..."):
            # Create search agents
            search_agents = [
                Agent(task=task, llm=llm, browser=browser)
                for task in search_tasks
            ]
            
            # Create comparison agent
            comparison_agent = Agent(task=comparison_task, llm=llm, browser=browser)
            
            # Run all agents
            search_results = await asyncio.gather(
                *[agent.run() for agent in search_agents]
            )
            comparison_result = await comparison_agent.run()
            
            # Display results
            st.subheader("📦 Platform Results")
            cols = st.columns(2)
            for idx, (col, result, site) in enumerate(zip(cols, search_results, ["Amazon", "Flipkart"])):
                with col:
                    st.markdown(f"**{site} Results**")
                    st.code(result.split("Final Answer")[-1].strip(), language="markdown")
            
            st.subheader("🏆 Smart Comparison Results")
            st.markdown(comparison_result.split("Final Answer")[-1].strip())
            
            await browser.close()
    
    asyncio.run(run_search())
    
    # Reset search trigger
    st.session_state.search_triggered = False