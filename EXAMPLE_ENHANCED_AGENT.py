"""
Enhanced AI Agent Example with Best Practices
==============================================

This example demonstrates:
- Proper error handling
- Beautiful UI with Streamlit
- Caching for performance
- Clear user feedback
- Comprehensive logging
- Type hints and documentation
"""

import streamlit as st
import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import logging
from datetime import datetime

# Import agno components
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# ============================================================================
# Configuration
# ============================================================================

class Config:
    """Application configuration"""
    APP_TITLE = "🤖 Enhanced AI Agent"
    APP_SUBTITLE = "Powered by GPT-4o with Best Practices"
    DEFAULT_MODEL = "gpt-4o-mini"
    MAX_RETRIES = 3
    TIMEOUT = 30

# ============================================================================
# Session State Management
# ============================================================================

def init_session_state() -> None:
    """Initialize Streamlit session state variables"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'agent' not in st.session_state:
        st.session_state.agent = None
    if 'api_key_valid' not in st.session_state:
        st.session_state.api_key_valid = False

# ============================================================================
# Agent Creation (with caching)
# ============================================================================

@st.cache_resource
def create_agent(api_key: str, model_id: str = Config.DEFAULT_MODEL) -> Optional[Agent]:
    """
    Create and cache an AI agent instance.
    
    Args:
        api_key: OpenAI API key
        model_id: Model identifier (default: gpt-4o-mini)
        
    Returns:
        Configured Agent instance or None if creation fails
    """
    try:
        agent = Agent(
            name="Enhanced Assistant",
            role="Helpful AI assistant with web search capabilities",
            model=OpenAIChat(id=model_id, api_key=api_key),
            tools=[DuckDuckGoTools()],
            instructions=[
                "Be helpful, accurate, and concise",
                "Use web search when you need current information",
                "Cite sources when using search results",
                "If you're unsure, say so clearly"
            ],
            show_tool_calls=True,
            markdown=True,
            debug_mode=False
        )
        logger.info(f"Agent created successfully with model: {model_id}")
        return agent
    except Exception as e:
        logger.error(f"Failed to create agent: {str(e)}")
        st.error(f"❌ Failed to create agent: {str(e)}")
        return None

# ============================================================================
# API Key Validation
# ============================================================================

def validate_api_key(api_key: str) -> bool:
    """
    Validate OpenAI API key format.
    
    Args:
        api_key: API key to validate
        
    Returns:
        True if key appears valid, False otherwise
    """
    if not api_key:
        return False
    
    # Basic format check
    if not api_key.startswith('sk-'):
        st.warning("⚠️ OpenAI API keys typically start with 'sk-'")
        return False
    
    if len(api_key) < 20:
        st.warning("⚠️ API key seems too short")
        return False
    
    return True

# ============================================================================
# UI Components
# ============================================================================

def render_sidebar() -> Optional[str]:
    """
    Render sidebar with configuration options.
    
    Returns:
        Valid API key or None
    """
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key input
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            help="Enter your OpenAI API key. Get one at https://platform.openai.com/api-keys",
            placeholder="sk-..."
        )
        
        if api_key and validate_api_key(api_key):
            st.success("✅ API key format looks valid")
            st.session_state.api_key_valid = True
        elif api_key:
            st.session_state.api_key_valid = False
            return None
        
        st.divider()
        
        # Model selection
        st.subheader("🎛️ Model Settings")
        model = st.selectbox(
            "Select Model",
            ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
            help="gpt-4o-mini is faster and cheaper, gpt-4o is more capable"
        )
        
        # Temperature slider
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            value=0.7,
            step=0.1,
            help="Higher values make output more random, lower values more deterministic"
        )
        
        st.divider()
        
        # Additional options
        st.subheader("🔧 Options")
        show_debug = st.checkbox("Show debug info", value=False)
        
        # Clear conversation button
        if st.button("🗑️ Clear Conversation", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        
        st.divider()
        
        # Info section
        with st.expander("ℹ️ About"):
            st.markdown("""
            **Enhanced AI Agent**
            
            This agent demonstrates best practices:
            - ✅ Proper error handling
            - ✅ Beautiful UI
            - ✅ Performance optimization
            - ✅ Clear user feedback
            - ✅ Web search capabilities
            
            **Features:**
            - Real-time web search
            - Conversation history
            - Multiple model options
            - Adjustable parameters
            """)
        
        # Stats
        with st.expander("📊 Stats"):
            st.metric("Messages", len(st.session_state.messages))
            st.metric("Model", model)
            st.metric("Temperature", temperature)
        
        return api_key if st.session_state.api_key_valid else None

def render_chat_message(role: str, content: str) -> None:
    """
    Render a chat message with appropriate styling.
    
    Args:
        role: Message role (user/assistant)
        content: Message content
    """
    with st.chat_message(role):
        st.markdown(content)

def render_error_message(error: str, details: Optional[str] = None) -> None:
    """
    Render an error message with optional details.
    
    Args:
        error: Error message
        details: Optional detailed error information
    """
    st.error(f"❌ {error}")
    if details:
        with st.expander("🔍 Error Details"):
            st.code(details)

# ============================================================================
# Main Application
# ============================================================================

def main():
    """Main application entry point"""
    
    # Page configuration
    st.set_page_config(
        page_title=Config.APP_TITLE,
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    init_session_state()
    
    # Header
    st.title(Config.APP_TITLE)
    st.caption(Config.APP_SUBTITLE)
    
    # Render sidebar and get API key
    api_key = render_sidebar()
    
    # Main content area
    if not api_key:
        st.info("👈 Please enter your OpenAI API key in the sidebar to begin")
        
        # Show example usage
        st.markdown("---")
        st.subheader("✨ What can this agent do?")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **🔍 Web Search**
            - Get current information
            - Research topics
            - Find latest news
            """)
        
        with col2:
            st.markdown("""
            **💬 Conversation**
            - Natural dialogue
            - Context awareness
            - Follow-up questions
            """)
        
        with col3:
            st.markdown("""
            **🎯 Smart Assistance**
            - Answer questions
            - Provide explanations
            - Help with tasks
            """)
        
        # Example queries
        st.markdown("---")
        st.subheader("💡 Example Queries")
        
        examples = [
            "What are the latest developments in AI?",
            "Explain quantum computing in simple terms",
            "What's the weather like in Tokyo today?",
            "Help me write a Python function to sort a list"
        ]
        
        for example in examples:
            st.markdown(f"- {example}")
        
        return
    
    # Create agent (cached)
    if st.session_state.agent is None:
        with st.spinner("🔄 Initializing agent..."):
            st.session_state.agent = create_agent(api_key)
        
        if st.session_state.agent is None:
            render_error_message(
                "Failed to initialize agent",
                "Please check your API key and try again"
            )
            return
    
    # Display chat history
    for message in st.session_state.messages:
        render_chat_message(message["role"], message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me anything..."):
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})
        render_chat_message("user", prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("🤔 Thinking..."):
                try:
                    # Call agent
                    response = st.session_state.agent.run(prompt)
                    
                    # Extract content
                    if hasattr(response, 'content'):
                        assistant_message = response.content
                    else:
                        assistant_message = str(response)
                    
                    # Display response
                    st.markdown(assistant_message)
                    
                    # Add to history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": assistant_message
                    })
                    
                    logger.info(f"Successfully processed query: {prompt[:50]}...")
                    
                except Exception as e:
                    error_msg = f"Error processing your request: {str(e)}"
                    logger.error(error_msg)
                    render_error_message(
                        "Something went wrong",
                        str(e)
                    )
                    
                    # Add error to history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"❌ {error_msg}"
                    })
    
    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.caption(f"💬 Messages: {len(st.session_state.messages)}")
    
    with col2:
        st.caption(f"🤖 Model: {Config.DEFAULT_MODEL}")
    
    with col3:
        st.caption(f"⏰ {datetime.now().strftime('%H:%M:%S')}")

# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"Application crashed: {str(e)}", exc_info=True)
        st.error(f"❌ Application Error: {str(e)}")
        st.info("Please refresh the page and try again")
