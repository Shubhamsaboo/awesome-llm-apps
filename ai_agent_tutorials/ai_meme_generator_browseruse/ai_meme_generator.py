import asyncio
import streamlit as st
from browser_use import Agent, SystemPrompt
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
import re

async def generate_meme(query: str, api_key: str) -> None:
    llm = ChatAnthropic(
        model="claude-3-5-sonnet-20241022",
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
        "8. Copy the image link and give it as the output\n"
    ).format(query)

    agent = Agent(
        task=task_description,
        llm=llm,
        max_actions_per_step=5,
        max_failures=25
    )

    history = await agent.run()
    
    # Extract final result from agent history
    final_result = history.final_result()
    
    # Use regex to find the meme URL in the result
    url_match = re.search(r'https://imgflip\.com/i/(\w+)', final_result)
    if url_match:
        meme_id = url_match.group(1)
        # Convert to direct image URL format
        return f"https://i.imgflip.com/{meme_id}.jpg"
    return None

def main():
    st.title("AI Meme Generator - Browser Use")
    st.info("This AI browser agent does browser automation to generate memes based on your input with browser use. Please enter your API key and describe the meme you want to generate.")

    # Configuration Settings
    with st.sidebar:
        st.header("⚙️ Configuration Settings")
        api_key = st.text_input("Enter your Claude API Key", type="password")

    # Main content area
    st.markdown('<p style="font-size: 20px; font-weight: bold;">🎨 Describe the Meme You Want to Generate</p>', unsafe_allow_html=True)
    query = st.text_input("Enter your meme idea (e.g., 'Ilya's SSI quietly looking at the OpenAI vs Deepseek debate while diligently working on ASI')", "")

    if st.button("Generate Meme"):
        if api_key and query:
            with st.spinner("🤖 Generating your meme... This might take a minute"):
                try:
                    meme_url = asyncio.run(generate_meme(query, api_key))
                    
                    if meme_url:
                        st.success("🎉 Meme Generated Successfully!")
                        st.image(meme_url, caption="Your Generated Meme", use_container_width=True)
                        
                        # Display clickable link
                        st.markdown(f"**Meme Link:** [Open in ImgFlip]({meme_url})")
                    else:
                        st.error("Could not retrieve meme URL. Please try again.")
                        
                except Exception as e:
                    st.error(f"Error generating meme: {str(e)}")
        else:
            st.warning("⚠️ Please provide both API key and meme idea")

if __name__ == '__main__':
    main()