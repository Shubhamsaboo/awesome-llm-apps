"""
Streamlit Web Interface for Tutorial 1: Your First Agent

This provides an interactive web interface to test the personal assistant agent
with different execution methods.
"""

import os
import asyncio
import streamlit as st
from dotenv import load_dotenv
from agents import Agent, Runner

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Personal Assistant Agent",
    page_icon="🎯",
    layout="wide"
)

# Title and description
st.title("🎯 Personal Assistant Agent")
st.markdown("**Tutorial 1**: Your first OpenAI agent with different execution methods")

# Check API key
if not os.getenv("OPENAI_API_KEY"):
    st.error("❌ OPENAI_API_KEY not found. Please create a .env file with your OpenAI API key.")
    st.stop()

# Create the agent
@st.cache_resource
def create_agent():
    return Agent(
        name="Personal Assistant",
        instructions="""
        You are a helpful personal assistant.
        
        Your role is to:
        1. Answer questions clearly and concisely
        2. Provide helpful information and advice
        3. Be friendly and professional
        4. Offer practical solutions to problems
        
        When users ask questions:
        - Give accurate and helpful responses
        - Explain complex topics in simple terms
        - Offer follow-up suggestions when appropriate
        - Maintain a positive and supportive tone
        
        Keep responses concise but informative.
        """
    )

agent = create_agent()

# Sidebar with execution method selection
st.sidebar.title("Execution Methods")
execution_method = st.sidebar.selectbox(
    "Choose execution method:",
    ["Synchronous", "Asynchronous", "Streaming"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### About Execution Methods")

if execution_method == "Synchronous":
    st.sidebar.info("**Synchronous**: Blocks until response is complete. Simple and straightforward.")
elif execution_method == "Asynchronous":
    st.sidebar.info("**Asynchronous**: Non-blocking execution. Good for concurrent operations.")
else:
    st.sidebar.info("**Streaming**: Real-time response streaming. Great for long responses.")

# Main chat interface
st.markdown("### Chat Interface")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask your personal assistant anything..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate assistant response
    with st.chat_message("assistant"):
        try:
            if execution_method == "Synchronous":
                with st.spinner("Thinking..."):
                    result = Runner.run_sync(agent, prompt)
                    response = result.final_output
                    st.markdown(response)
            
            elif execution_method == "Asynchronous":
                with st.spinner("Processing asynchronously..."):
                    async def get_async_response():
                        result = await Runner.run(agent, prompt)
                        return result.final_output
                    
                    response = asyncio.run(get_async_response())
                    st.markdown(response)
            
            else:  # Streaming
                response_placeholder = st.empty()
                response_text = ""
                
                async def stream_response():
                    full_response = ""
                    async for event in Runner.run_streamed(agent, prompt):
                        if hasattr(event, 'content') and event.content:
                            full_response += event.content
                            response_placeholder.markdown(full_response + "▌")
                    
                    response_placeholder.markdown(full_response)
                    return full_response
                
                response = asyncio.run(stream_response())
            
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
            
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            st.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Clear chat button
if st.sidebar.button("Clear Chat History"):
    st.session_state.messages = []
    st.rerun()

# Example prompts
st.sidebar.markdown("---")
st.sidebar.markdown("### Example Prompts")

example_prompts = [
    "What are 3 productivity tips for remote work?",
    "Explain quantum computing in simple terms",
    "Write a short poem about technology",
    "How can I improve my focus and concentration?",
    "What's the difference between AI and machine learning?"
]

for prompt in example_prompts:
    if st.sidebar.button(prompt, key=f"example_{prompt[:20]}"):
        # Add the example prompt to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

# Footer with tutorial information
st.markdown("---")
st.markdown("""
### 📚 Tutorial Information

This is **Tutorial 1** of the OpenAI Agents SDK crash course. You're learning:
- ✅ Basic agent creation with the Agent class
- ✅ Different execution methods (sync, async, streaming)  
- ✅ Agent configuration with instructions
- ✅ Interactive web interfaces with Streamlit

**Next**: Try [Tutorial 2: Structured Output Agent](../2_structured_output_agent/) to learn about type-safe responses.
""")
