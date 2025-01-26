import asyncio
import streamlit as st
from browser_use import Agent, SystemPrompt
from langchain_anthropic import ChatAnthropic

def create_ui() -> tuple[str, str]:
    st.title("🎭 AI Meme Generator with Browser Use")
    
    # Sidebar for API key
    with st.sidebar:
        st.header("Configuration")
        api_key = st.text_input("Enter your Anthropic API Key:", type="password")
    
    # Main content
    st.info("""
    🤖 This browser agent will help you generate loads of memes by going to imgflip.com and searching for the perfect template for your given query.
    """)
    
    query = st.text_input(
        "What would you like to generate a meme for?",
        placeholder="Example: India losing against New Zealand in the final of the world cup",
        help="Try to be specific and include context for better results"
    )
    
    return api_key, query

async def generate_meme(query: str, api_key: str) -> None:
    """
    Generates a meme using browser automation.
    
    Args:
        query (str): User's meme request
        api_key (str): Anthropic API key
    """
    llm = ChatAnthropic(
        model="claude-3-5-sonnet-20240620",
        api_key=api_key
    )

    task_description = (
        "You are a meme generator expert. You are given a query and you need to generate a meme for it.\n"
        "1. Go to https://imgflip.com/memetemplates \n"
        "2. Click on the Search bar in the middle and search for ONLY ONE MAIN ACTION VERB (like 'bully', 'laugh', 'cry') in this query: '{0}'\n"
        "3. Choose any meme template that metaphorically fits the meme topic: '{0}'\n"
        "   by clicking on the 'Add Caption' button below it\n"
        "4. Write a Top Text (setup/context) and Bottom Text (punchline/outcome) related to '{0}'.\n" 
        "5. Check the preview making sure it is funny and a meaningful meme. Adjust text directly if needed. \n"
        "6. Look at the meme and text on it, if it doesnt make sense, PLEASE retry by filling the text boxes with different text. \n"
        "7. Click on the Generate meme button to generate the meme\n"
    ).format(query)

    agent = Agent(
        task=task_description,
        llm=llm,
        max_actions_per_step=5,
        max_failures=25
    )

    with st.spinner("🎨 Generating your meme... Please wait"):
        await agent.run()

def main() -> None:
    """
    Main function to run the Streamlit app.
    """
    st.set_page_config(page_title="AI Meme Generator", page_icon="🎭")
    
    api_key, query = create_ui()
    
    if st.button("Generate Meme", disabled=not (api_key and query)):
        if not api_key:
            st.error("Please enter your Anthropic API key in the sidebar")
            return
        if not query:
            st.error("Please enter what meme you'd like to generate")
            return
            
        asyncio.run(generate_meme(query, api_key))

if __name__ == '__main__':
    main()
