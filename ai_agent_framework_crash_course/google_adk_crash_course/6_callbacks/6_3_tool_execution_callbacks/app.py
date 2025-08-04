#!/usr/bin/env python3
"""
Streamlit App for Tool Execution Callbacks Demo
"""

import streamlit as st
import sys
import os
import asyncio
from agent import run_agent

# Page configuration
st.set_page_config(
    page_title="Tool Execution Callbacks",
    page_icon="🔧",
    layout="wide"
)

# Title and description
st.title("🔧 Tool Execution Callbacks Demo")
st.markdown("""
This demo shows how to monitor tool execution using callbacks.
Watch the console output to see detailed tool execution tracking!
""")

# Sidebar with information
with st.sidebar:
    st.header("📊 Tool Execution Monitoring")
    st.markdown("""
    **Before Tool Callback**  
    - Triggered when a tool starts execution  
    - Logs tool name and input parameters  
    - Records agent name  
    - Stores start time for duration tracking

    **After Tool Callback**  
    - Triggered when a tool finishes execution  
    - Logs tool result  
    - Calculates and displays execution duration  
    - Handles errors (e.g., division by zero)
    """)
    
    st.markdown("---")
    st.markdown("### 🧮 Available Tools")
    st.markdown("""
    **Calculator Tool**:
    - Addition: `add`
    - Subtraction: `subtract`
    - Multiplication: `multiply`
    - Division: `divide`
    """)

# Main chat interface
st.header("💬 Chat with Tool Monitor")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask me to calculate something..."):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get agent response
    with st.chat_message("assistant"):
        with st.spinner("🔧 Tool is executing..."):
            response = asyncio.run(run_agent(prompt))
            st.markdown(response)
    
    # Add assistant response to chat
    st.session_state.messages.append({"role": "assistant", "content": response})

# Quick test buttons
st.markdown("---")
st.header("⚡ Quick Tests")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("➕ Addition Test"):
        test_message = "Calculate 15 + 27"
        st.session_state.messages.append({"role": "user", "content": test_message})
        with st.chat_message("user"):
            st.markdown(test_message)
        with st.chat_message("assistant"):
            with st.spinner("🔧 Tool is executing..."):
                response = asyncio.run(run_agent(test_message))
                st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

with col2:
    if st.button("➗ Division Test"):
        test_message = "What is 100 divided by 4?"
        st.session_state.messages.append({"role": "user", "content": test_message})
        with st.chat_message("user"):
            st.markdown(test_message)
        with st.chat_message("assistant"):
            with st.spinner("🔧 Tool is executing..."):
                response = asyncio.run(run_agent(test_message))
                st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

with col3:
    if st.button("❌ Error Test"):
        test_message = "Calculate 10 divided by 0"
        st.session_state.messages.append({"role": "user", "content": test_message})
        with st.chat_message("user"):
            st.markdown(test_message)
        with st.chat_message("assistant"):
            with st.spinner("🔧 Tool is executing..."):
                response = asyncio.run(run_agent(test_message))
                st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

# Clear chat button
if st.button("🗑️ Clear Chat History"):
    st.session_state.messages = []
    st.rerun()

# Information about callbacks
st.markdown("---")
st.header("📋 Tool Callback Output")
st.markdown("""
**Check your console/terminal** to see the tool execution output:

```
🔧 Tool calculator_tool started
📝 Parameters: {'operation': 'add', 'a': 15.0, 'b': 27.0}
📋 Agent: tool_execution_demo_agent

✅ Tool calculator_tool completed
⏱️ Duration: 0.0012s
📄 Result: 15 + 27 = 42
```
""")

# Footer
st.markdown("---")
st.markdown("*Watch the console output to see tool execution callbacks in action!*") 