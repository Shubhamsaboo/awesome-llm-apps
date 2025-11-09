import streamlit as st
from agno.agent import Agent
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.models.google import Gemini
from agno.tools.reasoning import ReasoningTools
from agno.vectordb.lancedb import LanceDb, SearchType
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Agentic RAG with Reasoning", 
    page_icon="🧐", 
    layout="wide"
)

# Main title and description
st.title("🧐 Agentic RAG with Reasoning")
st.markdown("""
This app demonstrates an AI agent that:
1. **Retrieves** relevant information from knowledge sources
2. **Reasons** through the information step-by-step
3. **Answers** your questions with citations

Enter your API keys below to get started!
""")

# API Keys Section
st.subheader("🔑 API Keys")
col1, col2 = st.columns(2)
with col1:
    google_key = st.text_input(
        "Google API Key", 
        type="password",
        value=os.getenv("GOOGLE_API_KEY", ""),
        help="Get your key from https://aistudio.google.com/apikey"
    )
with col2:
    openai_key = st.text_input(
        "OpenAI API Key", 
        type="password",
        value=os.getenv("OPENAI_API_KEY", ""),
        help="Get your key from https://platform.openai.com/"
    )

# Check if API keys are provided
if google_key and openai_key:
    
    # Initialize URLs in session state
    if 'knowledge_urls' not in st.session_state:
        st.session_state.knowledge_urls = ["https://www.theunwindai.com/p/mcp-vs-a2a-complementing-or-supplementing"]  # Default URL
    if 'urls_loaded' not in st.session_state:
        st.session_state.urls_loaded = set()

    # Initialize knowledge base (cached to avoid reloading)
    @st.cache_resource(show_spinner="📚 Loading knowledge base...")
    def load_knowledge() -> Knowledge:
        """Load and initialize the knowledge base with vector database"""
        kb = Knowledge(
            vector_db=LanceDb(
                uri="tmp/lancedb",
                table_name="agno_docs",
                search_type=SearchType.vector,  # Use vector search
                embedder=OpenAIEmbedder(
                    api_key=openai_key
                ),
            ),
        )
        return kb

    # Initialize agent (cached to avoid reloading)
    @st.cache_resource(show_spinner="🤖 Loading agent...")
    def load_agent(_kb: Knowledge) -> Agent:
        """Create an agent with reasoning capabilities"""
        return Agent(
            model=Gemini(
                id="gemini-2.5-flash", 
                api_key=google_key
            ),
            knowledge=_kb,
            search_knowledge=True,  # Enable knowledge search
            tools=[ReasoningTools(add_instructions=True)],  # Add reasoning tools
            instructions=[
                "Include sources in your response.",
                "Always search your knowledge before answering the question.",
            ],
            markdown=True,  # Enable markdown formatting
        )

    # Load knowledge and agent
    knowledge = load_knowledge()
    
    # Load initial URLs if any (only load once per URL)
    for url in st.session_state.knowledge_urls:
        if url not in st.session_state.urls_loaded:
            knowledge.add_content(url=url)
            st.session_state.urls_loaded.add(url)
    
    agent = load_agent(knowledge)

    # Sidebar for knowledge management
    with st.sidebar:
        st.header("📚 Knowledge Sources")
        st.markdown("Add URLs to expand the knowledge base:")
        
        # Show current URLs
        st.write("**Current sources:**")
        for i, url in enumerate(st.session_state.knowledge_urls):
            st.text(f"{i+1}. {url}")
        
        # Add new URL
        st.divider()
        new_url = st.text_input(
            "Add new URL", 
            placeholder="https://www.theunwindai.com/p/mcp-vs-a2a-complementing-or-supplementing",
            help="Enter a URL to add to the knowledge base"
        )
        
        if st.button("➕ Add URL", type="primary"):
            if new_url:
                if new_url not in st.session_state.knowledge_urls:
                    st.session_state.knowledge_urls.append(new_url)
                with st.spinner("📥 Loading new documents..."):
                    if new_url not in st.session_state.urls_loaded:
                        knowledge.add_content(url=new_url)
                        st.session_state.urls_loaded.add(new_url)
                st.success(f"✅ Added: {new_url}")
                st.rerun()  # Refresh to show new URL
            else:
                st.error("Please enter a URL")

    # Main query section
    st.divider()
    st.subheader("🤔 Ask a Question")
    
    # Suggested prompts
    st.markdown("**Try these prompts:**")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("What is MCP?", use_container_width=True):
            st.session_state.query = "What is MCP (Model Context Protocol) and how does it work?"
    with col2:
        if st.button("MCP vs A2A", use_container_width=True):
            st.session_state.query = "How do MCP and A2A protocols differ, and are they complementary or competing?"
    with col3:
        if st.button("Agent Communication", use_container_width=True):
            st.session_state.query = "How do MCP and A2A work together in AI agent systems for communication and tool access?"
    
    # Query input
    query = st.text_area(
        "Your question:",
        value=st.session_state.get("query", "What is the difference between MCP and A2A protocols?"),
        height=100,
        help="Ask anything about the loaded knowledge sources"
    )
    
    # Run button
    if st.button("🚀 Get Answer with Reasoning", type="primary"):
        if query:
            # Create containers for streaming updates
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("### 🧠 Reasoning Process")
                reasoning_container = st.container()
                reasoning_placeholder = reasoning_container.empty()
            
            with col2:
                st.markdown("### 💡 Answer")
                answer_container = st.container()
                answer_placeholder = answer_container.empty()
            
            # Variables to accumulate content
            citations = []
            answer_text = ""
            reasoning_text = ""
            
            # Stream the agent's response
            with st.spinner("🔍 Searching and reasoning..."):
                for chunk in agent.run(
                    query,
                    stream=True,  # Enable streaming
                    stream_events=True,  # Stream all events including reasoning
                ):
                    # Update reasoning display
                    if hasattr(chunk, 'reasoning_content') and chunk.reasoning_content:
                        reasoning_text = chunk.reasoning_content
                        reasoning_placeholder.markdown(
                            reasoning_text, 
                            unsafe_allow_html=True
                        )
                    
                    # Update answer display
                    if hasattr(chunk, 'content') and chunk.content and isinstance(chunk.content, str):
                        answer_text += chunk.content
                        answer_placeholder.markdown(
                            answer_text, 
                            unsafe_allow_html=True
                        )
                    
                    # Collect citations
                    if hasattr(chunk, 'citations') and chunk.citations:
                        if hasattr(chunk.citations, 'urls') and chunk.citations.urls:
                            citations = chunk.citations.urls
            
            # Show citations if available
            if citations:
                st.divider()
                st.subheader("📚 Sources")
                for cite in citations:
                    title = cite.title or cite.url
                    st.markdown(f"- [{title}]({cite.url})")
        else:
            st.error("Please enter a question")

else:
    # Show instructions if API keys are missing
    st.info("""
    👋 **Welcome! To use this app, you need:**
    
    1. **Google API Key** - For Gemini AI model
       - Sign up at [aistudio.google.com](https://aistudio.google.com/apikey)
    
    2. **OpenAI API Key** - For embeddings
       - Sign up at [platform.openai.com](https://platform.openai.com/)
    
    Once you have both keys, enter them above to start!
    """)

# Footer with explanation
st.divider()
with st.expander("📖 How This Works"):
    st.markdown("""
    **This app uses the Agno framework to create an intelligent Q&A system:**
    
    1. **Knowledge Loading**: URLs are processed and stored in a vector database (LanceDB)
    2. **Vector Search**: Uses OpenAI's embeddings for semantic search to find relevant information
    3. **Reasoning Tools**: The agent uses special tools to think through problems step-by-step
    4. **Gemini AI**: Google's Gemini model processes the information and generates answers
    
    **Key Components:**
    - `Knowledge`: Manages document loading from URLs
    - `LanceDb`: Vector database for efficient similarity search
    - `OpenAIEmbedder`: Converts text to embeddings using OpenAI's embedding model
    - `ReasoningTools`: Enables step-by-step reasoning
    - `Agent`: Orchestrates everything to answer questions
    """)