import streamlit as st
import os
from agno.agent import Agent
from agno.embedder.openai import OpenAIEmbedder
from agno.knowledge.url import UrlKnowledge
from agno.models.openai import OpenAIChat
from agno.vectordb.lancedb import LanceDb, SearchType

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Agentic RAG with GPT-5",
    page_icon="🧠",
    layout="wide"
)

# Main title and description
st.title("🧠 Agentic RAG with GPT-5")
st.markdown("""
This app demonstrates an intelligent AI agent that:
1. **Retrieves** relevant information from knowledge sources using LanceDB
2. **Answers** your questions clearly and concisely

Enter your OpenAI API key in the sidebar to get started!
""")

# Sidebar for API key and settings
with st.sidebar:
    st.header("🔧 Configuration")
    
    # OpenAI API Key
    openai_key = st.text_input(
        "OpenAI API Key",
        type="password",
        value=os.getenv("OPENAI_API_KEY", ""),
        help="Get your key from https://platform.openai.com/"
    )

    # Add URLs to knowledge base
    st.subheader("🌐 Add Knowledge Sources")
    new_url = st.text_input(
        "Add URL",
        placeholder="https://docs.agno.com/introduction",
        help="Enter a URL to add to the knowledge base"
    )
    
    if st.button("➕ Add URL", type="primary"):
        if new_url:
            st.session_state.urls_to_add = new_url
            st.success(f"URL added to queue: {new_url}")
        else:
            st.error("Please enter a URL")

# Check if API key is provided
if openai_key:
    # Initialize knowledge base (cached to avoid reloading)
    @st.cache_resource(show_spinner="📚 Loading knowledge base...")
    def load_knowledge() -> UrlKnowledge:
        """Load and initialize the knowledge base with LanceDB"""
        kb = UrlKnowledge(
            urls=["https://docs.agno.com/introduction/agents.md"],  # Default URL
            vector_db=LanceDb(
                uri="tmp/lancedb",
                table_name="agentic_rag_docs",
                search_type=SearchType.vector,  # Use vector search
                embedder=OpenAIEmbedder(
                    api_key=openai_key
                ),
            ),
        )
        kb.load(recreate=True)  # Load documents into LanceDB
        return kb

    # Initialize agent (cached to avoid reloading)
    @st.cache_resource(show_spinner="🤖 Loading agent...")
    def load_agent(_kb: UrlKnowledge) -> Agent:
        """Create an agent with reasoning capabilities"""
        return Agent(
            model=OpenAIChat(
                id="gpt-5-nano",
                api_key=openai_key
            ),
            knowledge=_kb,
            search_knowledge=True,  # Enable knowledge search
            instructions=[
                "Always search your knowledge before answering the question.",
                "Provide clear, well-structured answers in markdown format.",
                "Use proper markdown formatting with headers, lists, and emphasis where appropriate.",
                "Structure your response with clear sections and bullet points when helpful.",
            ],
            markdown=True,  # Enable markdown formatting
        )

    # Load knowledge and agent
    knowledge = load_knowledge()
    agent = load_agent(knowledge)
    
    # Display current URLs in knowledge base
    if knowledge.urls:
        st.sidebar.subheader("📚 Current Knowledge Sources")
        for i, url in enumerate(knowledge.urls, 1):
            st.sidebar.markdown(f"{i}. {url}")
    
    # Handle URL additions
    if hasattr(st.session_state, 'urls_to_add') and st.session_state.urls_to_add:
        with st.spinner("📥 Loading new documents..."):
            knowledge.urls.append(st.session_state.urls_to_add)
            knowledge.load(
                recreate=False,  # Don't recreate DB
                upsert=True,     # Update existing docs
                skip_existing=True  # Skip already loaded docs
            )
        st.success(f"✅ Added: {st.session_state.urls_to_add}")
        del st.session_state.urls_to_add
        st.rerun()

    # Main query section
    st.divider()
    st.subheader("🤔 Ask a Question")
    
    # Suggested prompts
    st.markdown("**Try these prompts:**")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("What is Agno?", use_container_width=True):
            st.session_state.query = "What is Agno and how do Agents work?"
    with col2:
        if st.button("Teams in Agno", use_container_width=True):
            st.session_state.query = "What are Teams in Agno and how do they work?"
    with col3:
        if st.button("Build RAG system", use_container_width=True):
            st.session_state.query = "Give me a step-by-step guide to building a RAG system."
    
    # Query input
    query = st.text_area(
        "Your question:",
        value=st.session_state.get("query", "What are AI Agents?"),
        height=100,
        help="Ask anything about the loaded knowledge sources"
    )
    
    # Run button
    if st.button("🚀 Get Answer", type="primary"):
        if query:
            # Create container for answer
            st.markdown("### 💡 Answer")
            answer_container = st.container()
            answer_placeholder = answer_container.empty()
            
            # Variables to accumulate content
            answer_text = ""
            
            # Stream the agent's response
            with st.spinner("🔍 Searching and generating answer..."):
                for chunk in agent.run(
                    query,
                    stream=True,  # Enable streaming
                ):
                    # Update answer display - only show content from RunResponseContent events
                    if hasattr(chunk, 'event') and chunk.event == "RunResponseContent":
                        if hasattr(chunk, 'content') and chunk.content and isinstance(chunk.content, str):
                            answer_text += chunk.content
                            answer_placeholder.markdown(
                                answer_text, 
                                unsafe_allow_html=True
                            )
        else:
            st.error("Please enter a question")

else:
    # Show instructions if API key is missing
    st.info("""
    👋 **Welcome! To use this app, you need:**
    
    - **OpenAI API Key** (set it in the sidebar)
      - Sign up at [platform.openai.com](https://platform.openai.com/)
      - Generate a new API key
    
    Once you enter the key, the app will load the knowledge base and agent.
    """)

# Footer with explanation
st.divider()
with st.expander("📖 How This Works"):
    st.markdown("""
    **This app uses the Agno framework to create an intelligent Q&A system:**
    
    1. **Knowledge Loading**: URLs are processed and stored in LanceDB vector database
    2. **Vector Search**: Uses OpenAI's embeddings for semantic search to find relevant information
    3. **GPT-5**: OpenAI's GPT-5 model processes the information and generates answers
    
    **Key Components:**
    - `UrlKnowledge`: Manages document loading from URLs
    - `LanceDb`: Vector database for efficient similarity search
    - `OpenAIEmbedder`: Converts text to embeddings using OpenAI's embedding model

    - `Agent`: Orchestrates everything to answer questions
    
    **Why LanceDB?**
    - Lightweight and easy to set up
    - No external database required
    - Fast vector search capabilities
    - Perfect for prototyping and small to medium-scale applications
    """)
