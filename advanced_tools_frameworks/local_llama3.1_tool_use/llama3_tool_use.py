import streamlit as st
import os
from phi.assistant import Assistant
from phi.llm.ollama import Ollama
from phi.tools.yfinance import YFinanceTools
from phi.tools.serpapi_tools import SerpApiTools

st.set_page_config(page_title="Llama-3 Tool Use", page_icon="🦙")

# Ensure SERPAPI_API_KEY is set
if 'SERPAPI_API_KEY' not in os.environ:
    st.error("Please set the SERPAPI_API_KEY environment variable.")
    st.stop()

def get_assistant(tools):
    return Assistant(
        name="llama3_assistant",
        llm=Ollama(model="llama3"),
        tools=tools,
        description="You are a helpful assistant that can access specific tools based on user selection.",
        show_tool_calls=True,
        debug_mode=True,
        # This setting adds the current datetime to the instructions
        add_datetime_to_instructions=True,

    )

st.title("🦙 Local Llama-3 Tool Use")
st.markdown("""
This app demonstrates function calling with the local Llama3 model using Ollama.
Select tools in the sidebar and ask relevant questions!
""")

# Sidebar for tool selection
st.sidebar.title("Tool Selection")
use_yfinance = st.sidebar.checkbox("YFinance (Stock Data)", value=True)
use_serpapi = st.sidebar.checkbox("SerpAPI (Web Search)", value=True)

# Initialize or update the assistant based on selected tools
tools = []
if use_yfinance:
    tools.append(YFinanceTools(stock_price=True, company_info=True))
if use_serpapi:
    tools.append(SerpApiTools())

if "assistant" not in st.session_state or st.session_state.get("tools") != tools:
    st.session_state.assistant = get_assistant(tools)
    st.session_state.tools = tools
    st.session_state.messages = []  # Reset messages when tools change

# Display current tool status
st.sidebar.markdown("### Current Tools:")
st.sidebar.markdown(f"- YFinance: {'Enabled' if use_yfinance else 'Disabled'}")
st.sidebar.markdown(f"- SerpAPI: {'Enabled' if use_serpapi else 'Disabled'}")

# Chat interface
for message in st.session_state.get("messages", []):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask a question based on the enabled tools"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_container = st.empty()
        response = ""
        for chunk in st.session_state.assistant.run(prompt):
            response += chunk
            response_container.write(response + "▌")
        response_container.write(response)
    st.session_state.messages.append({"role": "assistant", "content": response})

# Sidebar instructions
st.sidebar.markdown("""
### How to use:
1. Select the tools you want to use in the sidebar
2. Ask questions related to the enabled tools
3. The assistant will use only the selected tools to answe
### Note:
Make sure you have set the SERPAPI_API_KEY environment variable to use the SerpAPI tool.
""")

st.sidebar.markdown("""
### Sample questions:
- YFinance: "What's the current price of AAPL?"
- SerpAPI: "What are the latest developments in AI?"
- Both: "Compare TSLA stock price with recent news about Tesla's performance"
""")
