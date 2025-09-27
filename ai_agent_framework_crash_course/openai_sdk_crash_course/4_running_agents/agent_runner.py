import streamlit as st
import asyncio
import time
import json
from datetime import datetime
from agents import Agent, Runner, RunConfig, SQLiteSession
from agents.exceptions import (
    AgentsException,
    MaxTurnsExceeded,
    ModelBehaviorError,
    UserError
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Agent Runner Demo",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize agents
@st.cache_resource
def initialize_agents():
    """Initialize agents for different demonstrations"""
    
    execution_agent = Agent(
        name="Execution Demo Agent",
        instructions="""
        You are a helpful assistant demonstrating different execution patterns.
        
        Provide clear, informative responses that help users understand:
        - Synchronous execution (blocking)
        - Asynchronous execution (non-blocking)
        - Streaming execution (real-time)
        
        Keep responses appropriate for the execution method being demonstrated.
        """
    )
    
    conversation_agent = Agent(
        name="Conversation Agent",
        instructions="You are a helpful assistant that remembers conversation context. Reply concisely but reference previous context when relevant."
    )
    
    config_agent = Agent(
        name="Configuration Demo Agent",
        instructions="You are a helpful assistant that demonstrates run configuration options. Be precise and informative."
    )
    
    streaming_agent = Agent(
        name="Streaming Demo Agent",
        instructions="""
        You are a helpful assistant that demonstrates streaming capabilities.
        
        When asked to write long content, be comprehensive and detailed.
        When asked technical questions, provide thorough explanations.
        """
    )
    
    return execution_agent, conversation_agent, config_agent, streaming_agent

# Session management
class StreamingCapture:
    def __init__(self):
        self.events = []
        self.content = ""
        self.start_time = None
        self.end_time = None
    
    def reset(self):
        self.events = []
        self.content = ""
        self.start_time = None
        self.end_time = None

# Initialize session state
if 'session_manager' not in st.session_state:
    st.session_state.session_manager = {}
if 'streaming_capture' not in st.session_state:
    st.session_state.streaming_capture = StreamingCapture()

# Main UI
def main():
    st.title("🚀 Agent Runner Demo")
    st.markdown("**Demonstrates OpenAI Agents SDK execution capabilities**")
    
    # Initialize agents
    execution_agent, conversation_agent, config_agent, streaming_agent = initialize_agents()
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Execution Configuration")
        
        demo_type = st.selectbox(
            "Select Demo Type",
            ["Execution Methods", "Conversation Management", "Run Configuration", "Streaming Events", "Exception Handling"]
        )
        
        st.divider()
        
        # Global settings
        st.subheader("Global Settings")
        
        # Model configuration
        model_choice = st.selectbox(
            "Model",
            ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
            index=0
        )
        
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            value=0.7,
            step=0.1
        )
        
        max_turns = st.number_input(
            "Max Turns",
            min_value=1,
            max_value=20,
            value=10
        )
    
    # Main content area
    if demo_type == "Execution Methods":
        render_execution_methods(execution_agent, model_choice, temperature, max_turns)
    elif demo_type == "Conversation Management":
        render_conversation_management(conversation_agent, model_choice, temperature, max_turns)
    elif demo_type == "Run Configuration":
        render_run_configuration(config_agent, model_choice, temperature, max_turns)
    elif demo_type == "Streaming Events":
        render_streaming_events(streaming_agent, model_choice, temperature, max_turns)
    elif demo_type == "Exception Handling":
        render_exception_handling(execution_agent, model_choice, temperature, max_turns)

def render_execution_methods(agent, model_choice, temperature, max_turns):
    """Render the execution methods demo"""
    st.header("⚡ Execution Methods Demo")
    st.markdown("Compare synchronous, asynchronous, and streaming execution patterns.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("🔄 Synchronous (Blocking)")
        st.caption("Runner.run_sync() - Blocks until complete")
        
        with st.form("sync_form"):
            sync_input = st.text_area("Your message:", key="sync_input", value="Explain synchronous execution in simple terms")
            sync_submitted = st.form_submit_button("Run Sync")
            
            if sync_submitted and sync_input:
                with st.spinner("Processing synchronously..."):
                    start_time = time.time()
                    
                    try:
                        result = Runner.run_sync(agent, sync_input)
                        execution_time = time.time() - start_time
                        
                        st.success(f"✅ Completed in {execution_time:.2f}s")
                        st.write("**Response:**")
                        st.write(result.final_output)
                        
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
    
    with col2:
        st.subheader("⚡ Asynchronous (Non-blocking)")
        st.caption("Runner.run() - Returns awaitable")
        
        with st.form("async_form"):
            async_input = st.text_area("Your message:", key="async_input", value="Explain asynchronous execution benefits")
            async_submitted = st.form_submit_button("Run Async")
            
            if async_submitted and async_input:
                with st.spinner("Processing asynchronously..."):
                    start_time = time.time()
                    
                    try:
                        result = asyncio.run(Runner.run(agent, async_input))
                        execution_time = time.time() - start_time
                        
                        st.success(f"✅ Completed in {execution_time:.2f}s")
                        st.write("**Response:**")
                        st.write(result.final_output)
                        
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
    
    with col3:
        st.subheader("🌊 Streaming (Real-time)")
        st.caption("Runner.run_streamed() - Live updates")
        
        with st.form("streaming_form"):
            streaming_input = st.text_area("Your message:", key="streaming_input", value="Write a detailed explanation of streaming execution")
            streaming_submitted = st.form_submit_button("Run Streaming")
            
            if streaming_submitted and streaming_input:
                st.info("🔄 Streaming response...")
                
                # Create containers for streaming output
                response_container = st.empty()
                progress_container = st.empty()
                
                try:
                    full_response = ""
                    start_time = time.time()
                    
                    async def stream_response():
                        nonlocal full_response
                        async for event in Runner.run_streamed(agent, streaming_input):
                            if hasattr(event, 'content') and event.content:
                                full_response += event.content
                                response_container.write(f"**Response:**\n{full_response}")
                        
                        execution_time = time.time() - start_time
                        progress_container.success(f"✅ Streaming completed in {execution_time:.2f}s")
                    
                    asyncio.run(stream_response())
                    
                except Exception as e:
                    st.error(f"❌ Streaming error: {e}")

def render_conversation_management(agent, model_choice, temperature, max_turns):
    """Render the conversation management demo"""
    st.header("💬 Conversation Management Demo")
    st.markdown("Compare manual conversation threading vs automatic session management.")
    
    tab1, tab2 = st.tabs(["Manual Threading", "Session Management"])
    
    with tab1:
        st.subheader("🔧 Manual Conversation Threading")
        st.caption("Using result.to_input_list() for conversation history")
        
        # Initialize conversation history in session state
        if 'manual_conversation' not in st.session_state:
            st.session_state.manual_conversation = []
        
        with st.form("manual_form"):
            manual_input = st.text_input("Your message:")
            manual_submitted = st.form_submit_button("Send Message")
            
            if manual_submitted and manual_input:
                with st.spinner("Processing..."):
                    try:
                        # Build input list manually
                        input_list = st.session_state.manual_conversation.copy()
                        input_list.append({"role": "user", "content": manual_input})
                        
                        result = asyncio.run(Runner.run(agent, input_list))
                        
                        # Update conversation history
                        st.session_state.manual_conversation = result.to_input_list()
                        
                        st.success("Message sent!")
                        st.write(f"**Assistant:** {result.final_output}")
                        
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
        
        # Show conversation history
        if st.button("📋 Show Manual History"):
            if st.session_state.manual_conversation:
                st.write("**Conversation History:**")
                for i, item in enumerate(st.session_state.manual_conversation, 1):
                    role_emoji = "👤" if item['role'] == 'user' else "🤖"
                    st.write(f"{i}. {role_emoji} **{item['role'].title()}:** {item['content']}")
            else:
                st.info("No conversation history yet.")
        
        if st.button("🗑️ Clear Manual History"):
            st.session_state.manual_conversation = []
            st.success("Manual conversation history cleared!")
    
    with tab2:
        st.subheader("🔄 Automatic Session Management")
        st.caption("Using SQLiteSession for automatic conversation memory")
        
        session_id = "demo_conversation"
        
        with st.form("session_form"):
            session_input = st.text_input("Your message:")
            session_submitted = st.form_submit_button("Send Message")
            
            if session_submitted and session_input:
                with st.spinner("Processing..."):
                    try:
                        # Get or create session
                        if session_id not in st.session_state.session_manager:
                            st.session_state.session_manager[session_id] = SQLiteSession(session_id)
                        
                        session = st.session_state.session_manager[session_id]
                        result = asyncio.run(Runner.run(agent, session_input, session=session))
                        
                        st.success("Message sent!")
                        st.write(f"**Assistant:** {result.final_output}")
                        
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
        
        # Show session history
        if st.button("📋 Show Session History"):
            if session_id in st.session_state.session_manager:
                session = st.session_state.session_manager[session_id]
                try:
                    items = asyncio.run(session.get_items())
                    if items:
                        st.write("**Session History:**")
                        for i, item in enumerate(items, 1):
                            role_emoji = "👤" if item['role'] == 'user' else "🤖"
                            st.write(f"{i}. {role_emoji} **{item['role'].title()}:** {item['content']}")
                    else:
                        st.info("No session history yet.")
                except Exception as e:
                    st.error(f"❌ Error retrieving history: {e}")
            else:
                st.info("No session created yet.")
        
        if st.button("🗑️ Clear Session History"):
            if session_id in st.session_state.session_manager:
                try:
                    session = st.session_state.session_manager[session_id]
                    asyncio.run(session.clear_session())
                    del st.session_state.session_manager[session_id]
                    st.success("Session history cleared!")
                except Exception as e:
                    st.error(f"❌ Error clearing session: {e}")

def render_run_configuration(agent, model_choice, temperature, max_turns):
    """Render the run configuration demo"""
    st.header("⚙️ Run Configuration Demo")
    st.markdown("Demonstrates advanced run configuration options with RunConfig.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎛️ Basic Configuration")
        
        with st.form("basic_config_form"):
            st.write("**Model Settings:**")
            config_temperature = st.slider("Temperature", 0.0, 2.0, 0.1, 0.1, key="config_temp")
            config_top_p = st.slider("Top P", 0.0, 1.0, 0.9, 0.1, key="config_top_p")
            config_max_turns = st.number_input("Max Turns", 1, 20, 5, key="config_turns")
            
            config_input = st.text_area("Your message:", value="Explain the weather in exactly 3 sentences.")
            config_submitted = st.form_submit_button("Run with Config")
            
            if config_submitted and config_input:
                with st.spinner("Processing with configuration..."):
                    try:
                        run_config = RunConfig(
                            model=model_choice,
                            model_settings={
                                "temperature": config_temperature,
                                "top_p": config_top_p
                            },
                            max_turns=config_max_turns,
                            workflow_name="basic_config_demo"
                        )
                        
                        start_time = time.time()
                        result = asyncio.run(Runner.run(agent, config_input, run_config=run_config))
                        execution_time = time.time() - start_time
                        
                        st.success(f"✅ Completed in {execution_time:.2f}s")
                        st.write("**Response:**")
                        st.write(result.final_output)
                        
                        # Show configuration used
                        st.write("**Configuration Used:**")
                        st.json({
                            "model": model_choice,
                            "temperature": config_temperature,
                            "top_p": config_top_p,
                            "max_turns": config_max_turns
                        })
                        
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
    
    with col2:
        st.subheader("📊 Tracing Configuration")
        
        with st.form("tracing_config_form"):
            st.write("**Tracing Settings:**")
            workflow_name = st.text_input("Workflow Name", value="production_workflow")
            group_id = st.text_input("Group ID", value="user_session_456")
            user_id = st.text_input("User ID", value="user_123")
            feature_name = st.text_input("Feature", value="chat_assistance")
            
            tracing_input = st.text_area("Your message:", value="What are the benefits of structured logging?")
            tracing_submitted = st.form_submit_button("Run with Tracing")
            
            if tracing_submitted and tracing_input:
                with st.spinner("Processing with tracing..."):
                    try:
                        run_config = RunConfig(
                            model=model_choice,
                            tracing_disabled=False,
                            trace_include_sensitive_data=False,
                            workflow_name=workflow_name,
                            group_id=group_id,
                            trace_metadata={
                                "user_id": user_id,
                                "feature": feature_name,
                                "timestamp": datetime.now().isoformat()
                            }
                        )
                        
                        start_time = time.time()
                        result = asyncio.run(Runner.run(agent, tracing_input, run_config=run_config))
                        execution_time = time.time() - start_time
                        
                        st.success(f"✅ Completed with tracing in {execution_time:.2f}s")
                        st.write("**Response:**")
                        st.write(result.final_output)
                        
                        # Show tracing configuration
                        st.write("**Tracing Configuration:**")
                        st.json({
                            "workflow_name": workflow_name,
                            "group_id": group_id,
                            "metadata": {
                                "user_id": user_id,
                                "feature": feature_name
                            }
                        })
                        
                    except Exception as e:
                        st.error(f"❌ Error: {e}")

def render_streaming_events(agent, model_choice, temperature, max_turns):
    """Render the streaming events demo"""
    st.header("🌊 Streaming Events Demo")
    st.markdown("Demonstrates advanced streaming event processing and real-time analytics.")
    
    tab1, tab2 = st.tabs(["Basic Streaming", "Advanced Analytics"])
    
    with tab1:
        st.subheader("🎯 Basic Streaming with Event Processing")
        
        with st.form("streaming_basic_form"):
            streaming_input = st.text_area(
                "Your message:", 
                value="Write a comprehensive explanation of how machine learning works, including examples."
            )
            streaming_submitted = st.form_submit_button("Start Streaming")
            
            if streaming_submitted and streaming_input:
                st.info("🔄 Streaming in progress...")
                
                # Create containers
                response_container = st.empty()
                stats_container = st.empty()
                
                try:
                    full_response = ""
                    events_count = 0
                    start_time = time.time()
                    
                    async def process_streaming():
                        nonlocal full_response, events_count
                        
                        async for event in Runner.run_streamed(agent, streaming_input):
                            events_count += 1
                            
                            if hasattr(event, 'content') and event.content:
                                full_response += event.content
                                
                                # Update display
                                response_container.write(f"**Response:**\n{full_response}")
                                
                                # Update stats
                                elapsed = time.time() - start_time
                                char_count = len(full_response)
                                word_count = len(full_response.split())
                                
                                stats_container.metric(
                                    label="Streaming Progress",
                                    value=f"{char_count} chars, {word_count} words",
                                    delta=f"{elapsed:.1f}s elapsed"
                                )
                    
                    asyncio.run(process_streaming())
                    
                    final_time = time.time() - start_time
                    st.success(f"✅ Streaming completed! {events_count} events in {final_time:.2f}s")
                    
                except Exception as e:
                    st.error(f"❌ Streaming error: {e}")
    
    with tab2:
        st.subheader("📈 Advanced Streaming Analytics")
        
        with st.form("streaming_analytics_form"):
            analytics_input = st.text_area(
                "Your message:", 
                value="Explain the benefits and challenges of renewable energy in detail."
            )
            analytics_submitted = st.form_submit_button("Stream with Analytics")
            
            if analytics_submitted and analytics_input:
                st.info("🔄 Streaming with analytics...")
                
                # Create analytics containers
                response_container = st.empty()
                metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
                
                try:
                    analytics = {
                        "chunks": [],
                        "chunk_sizes": [],
                        "timestamps": [],
                        "content": ""
                    }
                    
                    start_time = time.time()
                    
                    async def process_analytics_streaming():
                        async for event in Runner.run_streamed(agent, analytics_input):
                            current_time = time.time()
                            
                            if hasattr(event, 'content') and event.content:
                                # Collect analytics
                                analytics["chunks"].append(event.content)
                                analytics["chunk_sizes"].append(len(event.content))
                                analytics["timestamps"].append(current_time - start_time)
                                analytics["content"] += event.content
                                
                                # Update display
                                response_container.write(f"**Response:**\n{analytics['content']}")
                                
                                # Update metrics
                                with metrics_col1:
                                    st.metric("Chunks", len(analytics["chunks"]))
                                
                                with metrics_col2:
                                    avg_chunk_size = sum(analytics["chunk_sizes"]) / len(analytics["chunk_sizes"])
                                    st.metric("Avg Chunk Size", f"{avg_chunk_size:.1f} chars")
                                
                                with metrics_col3:
                                    elapsed = current_time - start_time
                                    if elapsed > 0:
                                        chars_per_sec = len(analytics["content"]) / elapsed
                                        st.metric("Speed", f"{chars_per_sec:.1f} chars/s")
                    
                    asyncio.run(process_analytics_streaming())
                    
                    # Final analytics
                    total_time = time.time() - start_time
                    total_words = len(analytics["content"].split())
                    
                    st.success(f"✅ Analytics complete!")
                    
                    # Display final analytics
                    st.write("**Final Analytics:**")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Time", f"{total_time:.2f}s")
                    
                    with col2:
                        st.metric("Total Words", total_words)
                    
                    with col3:
                        st.metric("Total Chunks", len(analytics["chunks"]))
                    
                    with col4:
                        if total_time > 0:
                            st.metric("Words/Second", f"{total_words/total_time:.1f}")
                    
                except Exception as e:
                    st.error(f"❌ Analytics streaming error: {e}")

def render_exception_handling(agent, model_choice, temperature, max_turns):
    """Render the exception handling demo"""
    st.header("⚠️ Exception Handling Demo")
    st.markdown("Demonstrates proper exception handling for different SDK error scenarios.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🚫 MaxTurns Exception")
        st.caption("Trigger MaxTurnsExceeded exception")
        
        with st.form("maxturns_form"):
            max_turns_test = st.number_input("Max Turns (set low to trigger)", 1, 5, 2)
            maxturns_input = st.text_area(
                "Your message:", 
                value="Keep asking me questions and I'll keep responding. Let's have a long conversation."
            )
            maxturns_submitted = st.form_submit_button("Test MaxTurns")
            
            if maxturns_submitted and maxturns_input:
                try:
                    run_config = RunConfig(max_turns=max_turns_test)
                    result = asyncio.run(Runner.run(agent, maxturns_input, run_config=run_config))
                    st.success("✅ Completed without hitting max turns")
                    st.write(f"**Response:** {result.final_output}")
                    
                except MaxTurnsExceeded as e:
                    st.warning(f"⚠️ MaxTurnsExceeded: {e}")
                    st.info("This is expected when max_turns is set too low for complex conversations.")
                    
                except Exception as e:
                    st.error(f"❌ Unexpected error: {e}")
    
    with col2:
        st.subheader("🔧 General Exception Handling")
        st.caption("Comprehensive exception handling")
        
        with st.form("exception_form"):
            exception_input = st.text_area("Your message:", value="Tell me about artificial intelligence")
            exception_submitted = st.form_submit_button("Test Exception Handling")
            
            if exception_submitted and exception_input:
                try:
                    with st.spinner("Processing with full exception handling..."):
                        result = asyncio.run(Runner.run(agent, exception_input))
                        st.success("✅ Successfully processed")
                        st.write(f"**Response:** {result.final_output}")
                        
                except MaxTurnsExceeded as e:
                    st.warning(f"⚠️ Hit maximum turns limit: {e}")
                    st.info("Consider increasing max_turns or simplifying the request.")
                    
                except ModelBehaviorError as e:
                    st.error(f"🤖 Model behavior error: {e}")
                    st.info("The model produced unexpected output. Try rephrasing your request.")
                    
                except UserError as e:
                    st.error(f"👤 User error: {e}")
                    st.info("There's an issue with the request. Please check your input.")
                    
                except AgentsException as e:
                    st.error(f"🔧 SDK error: {e}")
                    st.info("An error occurred within the Agents SDK.")
                    
                except Exception as e:
                    st.error(f"❌ Unexpected error: {e}")
                    st.info("An unexpected error occurred. Please try again.")
    
    # Exception handling reference
    st.divider()
    st.subheader("📚 Exception Handling Reference")
    
    exception_info = {
        "MaxTurnsExceeded": "Agent hit the maximum conversation turns limit",
        "ModelBehaviorError": "LLM produced malformed or unexpected output",
        "UserError": "Invalid SDK usage or request parameters", 
        "AgentsException": "Base exception for all SDK-related errors",
        "InputGuardrailTripwireTriggered": "Input validation failed",
        "OutputGuardrailTripwireTriggered": "Output validation failed"
    }
    
    for exception, description in exception_info.items():
        st.write(f"**{exception}**: {description}")

# Footer
def render_footer():
    st.divider()
    st.markdown("""
    ### 🎯 Agent Runner Capabilities Demonstrated
    
    1. **Execution Methods**: Sync, async, and streaming execution patterns
    2. **Conversation Management**: Manual threading vs automatic sessions
    3. **Run Configuration**: Model settings, tracing, and workflow management
    4. **Streaming Events**: Real-time processing and analytics
    5. **Exception Handling**: Comprehensive error handling patterns
    
    **Key Benefits:**
    - Flexible execution patterns for different use cases
    - Automatic conversation memory with sessions
    - Advanced configuration for production deployments
    - Real-time streaming for better user experience
    - Robust error handling for production reliability
    """)

if __name__ == "__main__":
    main()
    render_footer()
