# Import the required libraries
import streamlit as st
from phi.assistant import Assistant
from phi.tools.duckduckgo import DuckDuckGo
from phi.llm.openai import OpenAIChat

# Set up the Streamlit app
st.title("AI Web Search Assistant 🤖")
st.caption("This app allows you to search the web using GPT-4o")

# Get OpenAI API key from user
openai_access_token = st.text_input("OpenAI API Key", type="password")

# If OpenAI API key is provided, create an instance of Assistant
if openai_access_token:
    # Create an instance of the Assistant
    assistant = Assistant(
    llm=OpenAIChat(
        model="gpt-4o",
        max_tokens=1024,
        temperature=0.9,
        api_key=openai_access_token) , tools=[DuckDuckGo()], show_tool_calls=True
    )

    # Get the search query from the user
    query= st.text_input("Enter the Search Query", type="default")
    
    if query:
        # Search the web using the AI Assistant
        response = assistant.run(query, stream=False)
        st.write(response)