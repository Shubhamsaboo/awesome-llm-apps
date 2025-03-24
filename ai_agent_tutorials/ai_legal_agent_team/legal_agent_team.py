import streamlit as st
from agno.agent import Agent
from agno.knowledge.pdf import PDFKnowledgeBase, PDFReader
from agno.vectordb.qdrant import Qdrant
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.models.openai import OpenAIChat
from agno.embedder.openai import OpenAIEmbedder
import tempfile
import os
from agno.document.chunking.document import DocumentChunking

def init_session_state():
    """Initialize session state variables"""
    if 'openai_api_key' not in st.session_state:
        st.session_state.openai_api_key = None
    if 'qdrant_api_key' not in st.session_state:
        st.session_state.qdrant_api_key = None
    if 'qdrant_url' not in st.session_state:
        st.session_state.qdrant_url = None
    if 'vector_db' not in st.session_state:
        st.session_state.vector_db = None
    if 'legal_team' not in st.session_state:
        st.session_state.legal_team = None
    if 'knowledge_base' not in st.session_state:
        st.session_state.knowledge_base = None
    # Add a new state variable to track processed files
    if 'processed_files' not in st.session_state:
        st.session_state.processed_files = set()

COLLECTION_NAME = "legal_documents"  # Define your collection name

def init_qdrant():
    """Initialize Qdrant client with configured settings."""
    if not all([st.session_state.qdrant_api_key, st.session_state.qdrant_url]):
        return None
    try:
        # Create Agno's Qdrant instance which implements VectorDb
        vector_db = Qdrant(
            collection=COLLECTION_NAME,
            url=st.session_state.qdrant_url,
            api_key=st.session_state.qdrant_api_key,
            embedder=OpenAIEmbedder(
                id="text-embedding-3-small", 
                api_key=st.session_state.openai_api_key
            )
        )
        return vector_db
    except Exception as e:
        st.error(f"🔴 Qdrant connection failed: {str(e)}")
        return None

def process_document(uploaded_file, vector_db: Qdrant):
    """
    Process document, create embeddings and store in Qdrant vector database
    
    Args:
        uploaded_file: Streamlit uploaded file object
        vector_db (Qdrant): Initialized Qdrant instance from Agno
    
    Returns:
        PDFKnowledgeBase: Initialized knowledge base with processed documents
    """
    if not st.session_state.openai_api_key:
        raise ValueError("OpenAI API key not provided")
        
    os.environ['OPENAI_API_KEY'] = st.session_state.openai_api_key
    
    try:
        # Save the uploaded file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(uploaded_file.getvalue())
            temp_file_path = temp_file.name
        
        st.info("Loading and processing document...")
        
        # Create a PDFKnowledgeBase with the vector_db
        knowledge_base = PDFKnowledgeBase(
            path=temp_file_path,  # Single string path, not a list
            vector_db=vector_db,
            reader=PDFReader(),
            chunking_strategy=DocumentChunking(
                chunk_size=1000,
                overlap=200
            )
        )
        
        # Load the documents into the knowledge base
        with st.spinner('📤 Loading documents into knowledge base...'):
            try:
                knowledge_base.load(recreate=True, upsert=True)
                st.success("✅ Documents stored successfully!")
            except Exception as e:
                st.error(f"Error loading documents: {str(e)}")
                raise
        
        # Clean up the temporary file
        try:
            os.unlink(temp_file_path)
        except Exception:
            pass
            
        return knowledge_base
            
    except Exception as e:
        st.error(f"Document processing error: {str(e)}")
        raise Exception(f"Error processing document: {str(e)}")

def main():
    st.set_page_config(page_title="Legal Document Analyzer", layout="wide")
    init_session_state()

    st.title("AI Legal Agent Team 👨‍⚖️")

    with st.sidebar:
        st.header("🔑 API Configuration")
   
        openai_key = st.text_input(
            "OpenAI API Key",
            type="password",
            value=st.session_state.openai_api_key if st.session_state.openai_api_key else "",
            help="Enter your OpenAI API key"
        )
        if openai_key:
            st.session_state.openai_api_key = openai_key

        qdrant_key = st.text_input(
            "Qdrant API Key",
            type="password",
            value=st.session_state.qdrant_api_key if st.session_state.qdrant_api_key else "",
            help="Enter your Qdrant API key"
        )
        if qdrant_key:
            st.session_state.qdrant_api_key = qdrant_key

        qdrant_url = st.text_input(
            "Qdrant URL",
            value=st.session_state.qdrant_url if st.session_state.qdrant_url else "",
            help="Enter your Qdrant instance URL"
        )
        if qdrant_url:
            st.session_state.qdrant_url = qdrant_url

        if all([st.session_state.qdrant_api_key, st.session_state.qdrant_url]):
            try:
                if not st.session_state.vector_db:
                    # Make sure we're initializing a QdrantClient here
                    st.session_state.vector_db = init_qdrant()
                    if st.session_state.vector_db:
                        st.success("Successfully connected to Qdrant!")
            except Exception as e:
                st.error(f"Failed to connect to Qdrant: {str(e)}")

        st.divider()

        if all([st.session_state.openai_api_key, st.session_state.vector_db]):
            st.header("📄 Document Upload")
            uploaded_file = st.file_uploader("Upload Legal Document", type=['pdf'])
            
            if uploaded_file:
                # Check if this file has already been processed
                if uploaded_file.name not in st.session_state.processed_files:
                    with st.spinner("Processing document..."):
                        try:
                            # Process the document and get the knowledge base
                            knowledge_base = process_document(uploaded_file, st.session_state.vector_db)
                            
                            if knowledge_base:
                                st.session_state.knowledge_base = knowledge_base
                                # Add the file to processed files
                                st.session_state.processed_files.add(uploaded_file.name)
                                
                                # Initialize agents
                                legal_researcher = Agent(
                                    name="Legal Researcher",
                                    role="Legal research specialist",
                                    model=OpenAIChat(id="gpt-4o"),
                                    tools=[DuckDuckGoTools()],
                                    knowledge=st.session_state.knowledge_base,
                                    search_knowledge=True,
                                    instructions=[
                                        "Find and cite relevant legal cases and precedents",
                                        "Provide detailed research summaries with sources",
                                        "Reference specific sections from the uploaded document",
                                        "Always search the knowledge base for relevant information"
                                    ],
                                    show_tool_calls=True,
                                    markdown=True
                                )

                                contract_analyst = Agent(
                                    name="Contract Analyst",
                                    role="Contract analysis specialist",
                                    model=OpenAIChat(id="gpt-4o"),
                                    knowledge=st.session_state.knowledge_base,
                                    search_knowledge=True,
                                    instructions=[
                                        "Review contracts thoroughly",
                                        "Identify key terms and potential issues",
                                        "Reference specific clauses from the document"
                                    ],
                                    markdown=True
                                )

                                legal_strategist = Agent(
                                    name="Legal Strategist", 
                                    role="Legal strategy specialist",
                                    model=OpenAIChat(id="gpt-4o"),
                                    knowledge=st.session_state.knowledge_base,
                                    search_knowledge=True,
                                    instructions=[
                                        "Develop comprehensive legal strategies",
                                        "Provide actionable recommendations",
                                        "Consider both risks and opportunities"
                                    ],
                                    markdown=True
                                )

                                # Legal Agent Team
                                st.session_state.legal_team = Agent(
                                    name="Legal Team Lead",
                                    role="Legal team coordinator",
                                    model=OpenAIChat(id="gpt-4o"),
                                    team=[legal_researcher, contract_analyst, legal_strategist],
                                    knowledge=st.session_state.knowledge_base,
                                    search_knowledge=True,
                                    instructions=[
                                        "Coordinate analysis between team members",
                                        "Provide comprehensive responses",
                                        "Ensure all recommendations are properly sourced",
                                        "Reference specific parts of the uploaded document",
                                        "Always search the knowledge base before delegating tasks"
                                    ],
                                    show_tool_calls=True,
                                    markdown=True
                                )
                                
                                st.success("✅ Document processed and team initialized!")
                                
                        except Exception as e:
                            st.error(f"Error processing document: {str(e)}")
                else:
                    # File already processed, just show a message
                    st.success("✅ Document already processed and team ready!")

            st.divider()
            st.header("🔍 Analysis Options")
            analysis_type = st.selectbox(
                "Select Analysis Type",
                [
                    "Contract Review",
                    "Legal Research",
                    "Risk Assessment",
                    "Compliance Check",
                    "Custom Query"
                ]
            )
        else:
            st.warning("Please configure all API credentials to proceed")

    # Main content area
    if not all([st.session_state.openai_api_key, st.session_state.vector_db]):
        st.info("👈 Please configure your API credentials in the sidebar to begin")
    elif not uploaded_file:
        st.info("👈 Please upload a legal document to begin analysis")
    elif st.session_state.legal_team:
        # Create a dictionary for analysis type icons
        analysis_icons = {
            "Contract Review": "📑",
            "Legal Research": "🔍",
            "Risk Assessment": "⚠️",
            "Compliance Check": "✅",
            "Custom Query": "💭"
        }

        # Dynamic header with icon
        st.header(f"{analysis_icons[analysis_type]} {analysis_type} Analysis")
  
        analysis_configs = {
            "Contract Review": {
                "query": "Review this contract and identify key terms, obligations, and potential issues.",
                "agents": ["Contract Analyst"],
                "description": "Detailed contract analysis focusing on terms and obligations"
            },
            "Legal Research": {
                "query": "Research relevant cases and precedents related to this document.",
                "agents": ["Legal Researcher"],
                "description": "Research on relevant legal cases and precedents"
            },
            "Risk Assessment": {
                "query": "Analyze potential legal risks and liabilities in this document.",
                "agents": ["Contract Analyst", "Legal Strategist"],
                "description": "Combined risk analysis and strategic assessment"
            },
            "Compliance Check": {
                "query": "Check this document for regulatory compliance issues.",
                "agents": ["Legal Researcher", "Contract Analyst", "Legal Strategist"],
                "description": "Comprehensive compliance analysis"
            },
            "Custom Query": {
                "query": None,
                "agents": ["Legal Researcher", "Contract Analyst", "Legal Strategist"],
                "description": "Custom analysis using all available agents"
            }
        }

        st.info(f"📋 {analysis_configs[analysis_type]['description']}")
        st.write(f"🤖 Active Legal AI Agents: {', '.join(analysis_configs[analysis_type]['agents'])}")  #dictionary!!

        # Replace the existing user_query section with this:
        if analysis_type == "Custom Query":
            user_query = st.text_area(
                "Enter your specific query:",
                help="Add any specific questions or points you want to analyze"
            )
        else:
            user_query = None  # Set to None for non-custom queries


        if st.button("Analyze"):
            if analysis_type == "Custom Query" and not user_query:
                st.warning("Please enter a query")
            else:
                with st.spinner("Analyzing document..."):
                    try:
                        # Ensure OpenAI API key is set
                        os.environ['OPENAI_API_KEY'] = st.session_state.openai_api_key
                        
                        # Combine predefined and user queries
                        if analysis_type != "Custom Query":
                            combined_query = f"""
                            Using the uploaded document as reference:
                            
                            Primary Analysis Task: {analysis_configs[analysis_type]['query']}
                            Focus Areas: {', '.join(analysis_configs[analysis_type]['agents'])}
                            
                            Please search the knowledge base and provide specific references from the document.
                            """
                        else:
                            combined_query = f"""
                            Using the uploaded document as reference:
                            
                            {user_query}
                            
                            Please search the knowledge base and provide specific references from the document.
                            Focus Areas: {', '.join(analysis_configs[analysis_type]['agents'])}
                            """

                        response = st.session_state.legal_team.run(combined_query)
                        
                        # Display results in tabs
                        tabs = st.tabs(["Analysis", "Key Points", "Recommendations"])
                        
                        with tabs[0]:
                            st.markdown("### Detailed Analysis")
                            if response.content:
                                st.markdown(response.content)
                            else:
                                for message in response.messages:
                                    if message.role == 'assistant' and message.content:
                                        st.markdown(message.content)
                        
                        with tabs[1]:
                            st.markdown("### Key Points")
                            key_points_response = st.session_state.legal_team.run(
                                f"""Based on this previous analysis:    
                                {response.content}
                                
                                Please summarize the key points in bullet points.
                                Focus on insights from: {', '.join(analysis_configs[analysis_type]['agents'])}"""
                            )
                            if key_points_response.content:
                                st.markdown(key_points_response.content)
                            else:
                                for message in key_points_response.messages:
                                    if message.role == 'assistant' and message.content:
                                        st.markdown(message.content)
                        
                        with tabs[2]:
                            st.markdown("### Recommendations")
                            recommendations_response = st.session_state.legal_team.run(
                                f"""Based on this previous analysis:
                                {response.content}
                                
                                What are your key recommendations based on the analysis, the best course of action?
                                Provide specific recommendations from: {', '.join(analysis_configs[analysis_type]['agents'])}"""
                            )
                            if recommendations_response.content:
                                st.markdown(recommendations_response.content)
                            else:
                                for message in recommendations_response.messages:
                                    if message.role == 'assistant' and message.content:
                                        st.markdown(message.content)

                    except Exception as e:
                        st.error(f"Error during analysis: {str(e)}")
    else:
        st.info("Please upload a legal document to begin analysis")

if __name__ == "__main__":
    main() 