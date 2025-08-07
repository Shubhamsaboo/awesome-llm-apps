import streamlit as st
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from agent import run_agent

st.set_page_config(page_title="Google ADK Plugins Tutorial", page_icon="🔌")

st.title("🔌 Google ADK Plugins Tutorial")
st.markdown("Demonstrates plugins for cross-cutting concerns like logging and monitoring.")

test_scenarios = {
    "Normal Conversation": "Hello! How are you?",
    "Simple Calculation": "Calculate 15 + 27",
    "Error Handling": "What is 10 divided by 0?"
}

selected_scenario = st.selectbox("Choose a test scenario:", list(test_scenarios.keys()))

if st.button("🚀 Run Test"):
    with st.spinner("Running..."):
        try:
            response = asyncio.run(run_agent(test_scenarios[selected_scenario]))
            st.success("**Agent Response:**")
            st.write(response)
        except Exception as e:
            st.error(f"Error: {str(e)}")

st.markdown("---")
custom_message = st.text_area("Or enter your own message:", placeholder="Type here...")

if st.button("🚀 Run Custom Message"):
    if custom_message.strip():
        with st.spinner("Processing..."):
            try:
                response = asyncio.run(run_agent(custom_message))
                st.success("**Agent Response:**")
                st.write(response)
            except Exception as e:
                st.error(f"Error: {str(e)}")
    else:
        st.warning("Please enter a message.")

with st.expander("📚 About Plugins"):
    st.markdown("""
    **Plugins** are custom code modules that execute at various stages of agent workflow lifecycle.
    
    **Key Features:**
    - 🔍 Request logging and modification
    - 🤖 Agent execution tracking  
    - 🔧 Tool usage monitoring
    - 📊 Final reporting and analytics
    
    **Plugin Callbacks:**
    - `on_user_message_callback()` - Modify user input
    - `before_agent_callback()` - Track agent starts
    - `before_tool_callback()` - Track tool usage
    - `after_run_callback()` - Generate reports
    """)

st.markdown("---")
st.markdown("*Part of the Google ADK Crash Course*")
