import asyncio
import streamlit as st
from browser_use import Agent, SystemPrompt
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
import re

async def generate_meme(query: str, model_choice: str, api_key: str) -> None:
    # Initialize the appropriate LLM based on user selection
    if model_choice == "Claude":
        llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            api_key=api_key
        )
    elif model_choice == "Deepseek":
        llm = ChatOpenAI(
            base_url='https://api.deepseek.com/v1',
            model='deepseek-chat',
            api_key=api_key,
            temperature=0.3
        )
    else:  # OpenAI
        llm = ChatOpenAI(
            model="gpt-4o",
            api_key=api_key,
            temperature=0.0
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
        "8. Copy the image link and give it as the output\n"
    ).format(query)

    agent = Agent(
        task=task_description,
        llm=llm,
        max_actions_per_step=5,
        max_failures=25,
        use_vision=(model_choice != "Deepseek")
    )

    history = await agent.run()
    
    # Extract final result from agent history
    final_result = history.final_result()
    
    # Use regex to find the meme URL in the result
    url_match = re.search(r'https://imgflip\.com/i/(\w+)', final_result)
    if url_match:
        meme_id = url_match.group(1)
        return f"https://i.imgflip.com/{meme_id}.jpg"
    return None

def main():
    # Custom CSS styling


    st.title("🥸 AI Meme Generator Agent - Browser Use")
    st.info("This AI browser agent does browser automation to generate memes based on your input with browser use. Please enter your API key and describe the meme you want to generate.")
    
    # Sidebar configuration
    with st.sidebar:
        st.markdown('<p class="sidebar-header">⚙️ Model Configuration</p>', unsafe_allow_html=True)
        
        # Model selection
        model_choice = st.selectbox(
            "Select AI Model",
            ["Claude", "Deepseek", "OpenAI"],
            index=0,
            help="Choose which LLM to use for meme generation"
        )
        
        # API key input based on model selection
        api_key = ""
        if model_choice == "Claude":
            api_key = st.text_input("Claude API Key", type="password", 
                                  help="Get your API key from https://console.anthropic.com")
        elif model_choice == "Deepseek":
            api_key = st.text_input("Deepseek API Key", type="password",
                                  help="Get your API key from https://platform.deepseek.com")
        else:
            api_key = st.text_input("OpenAI API Key", type="password",
                                  help="Get your API key from https://platform.openai.com")

    # Main content area
    st.markdown('<p class="header-text">🎨 Describe Your Meme Concept</p>', unsafe_allow_html=True)
    
    query = st.text_input(
        "Meme Idea Input",
        placeholder="Example: 'Ilya's SSI quietly looking at the OpenAI vs Deepseek debate while diligently working on ASI'",
        label_visibility="collapsed"
    )

    if st.button("Generate Meme 🚀"):
        if not api_key:
            st.warning(f"Please provide the {model_choice} API key")
            st.stop()
        if not query:
            st.warning("Please enter a meme idea")
            st.stop()

        with st.spinner(f"🧠 {model_choice} is generating your meme..."):
            try:
                meme_url = asyncio.run(generate_meme(query, model_choice, api_key))
                
                if meme_url:
                    st.success("✅ Meme Generated Successfully!")
                    st.image(meme_url, caption="Generated Meme Preview", use_container_width=True)
                    st.markdown(f"""
                        **Direct Link:** [Open in ImgFlip]({meme_url})  
                        **Embed URL:** `{meme_url}`
                    """)
                else:
                    st.error("❌ Failed to generate meme. Please try again with a different prompt.")
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.info("💡 If using OpenAI, ensure your account has GPT-4o access")

if __name__ == '__main__':
    main()