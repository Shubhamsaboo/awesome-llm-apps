import streamlit as st
import nest_asyncio
from io import BytesIO
from phi.assistant import Assistant
from phi.document.reader.pdf import PDFReader
from phi.llm.openai import OpenAIChat
from phi.knowledge import AssistantKnowledge
from phi.tools.duckduckgo import DuckDuckGo
from phi.embedder.openai import OpenAIEmbedder
from phi.vectordb.pgvector import PgVector2
from phi.storage.assistant.postgres import PgAssistantStorage

# Apply nest_asyncio to allow nested event loops, required for running async functions in Streamlit
nest_asyncio.apply()

# Database connection string for PostgreSQL
DB_URL = "postgresql+psycopg://ai:ai@localhost:5532/ai"

# Function to set up the Assistant, utilizing caching for resource efficiency
@st.cache_resource
def setup_assistant(api_key: str) -> Assistant:
    llm = OpenAIChat(model="gpt-4o-mini", api_key=api_key)
    # Set up the Assistant with storage, knowledge base, and tools
    return Assistant(
        name="auto_rag_assistant",  # Name of the Assistant
        llm=llm,  # Language model to be used
        storage=PgAssistantStorage(table_name="auto_rag_storage", db_url=DB_URL),  
        knowledge_base=AssistantKnowledge(
            vector_db=PgVector2(
                db_url=DB_URL,  
                collection="auto_rag_docs",  
                embedder=OpenAIEmbedder(model="text-embedding-ada-002", dimensions=1536, api_key=api_key),  
            ),
            num_documents=3,  
        ),
        tools=[DuckDuckGo()],  # Additional tool for web search via DuckDuckGo
        instructions=[
            "Search your knowledge base first.",  
            "If not found, search the internet.",  
            "Provide clear and concise answers.",  
        ],
        show_tool_calls=True,  
        search_knowledge=True,  
        read_chat_history=True,  
        markdown=True,  
        debug_mode=True,  
    )

# Function to add a PDF document to the knowledge base
def add_document(assistant: Assistant, file: BytesIO):
    reader = PDFReader()
    docs = reader.read(file)
    if docs:
        assistant.knowledge_base.load_documents(docs, upsert=True)
        st.success("Document added to the knowledge base.")
    else:
        st.error("Failed to read the document.")

# Function to query the Assistant and return a response
def query_assistant(assistant: Assistant, question: str) -> str:
    return "".join([delta for delta in assistant.run(question)])

# Main function to handle Streamlit app layout and interactions
def main():
    st.set_page_config(page_title="AutoRAG", layout="wide")
    st.title("🤖 Auto-RAG: Autonomous RAG with GPT-4o")

    api_key = st.sidebar.text_input("Enter your OpenAI API Key 🔑", type="password")
    
    if not api_key:
        st.sidebar.warning("Enter your OpenAI API Key to proceed.")
        st.stop()

    assistant = setup_assistant(api_key)
    
    uploaded_file = st.sidebar.file_uploader("📄 Upload PDF", type=["pdf"])
    
    if uploaded_file and st.sidebar.button("🛠️ Add to Knowledge Base"):
        add_document(assistant, BytesIO(uploaded_file.read()))

    question = st.text_input("💬 Ask Your Question:")
    
    # When the user submits a question, query the assistant for an answer
    if st.button("🔍 Get Answer"):
        # Ensure the question is not empty
        if question.strip():
            with st.spinner("🤔 Thinking..."):
                # Query the assistant and display the response
                answer = query_assistant(assistant, question)
                st.write("📝 **Response:**", answer)
        else:
            # Show an error if the question input is empty
            st.error("Please enter a question.")

# Entry point of the application
if __name__ == "__main__":
    main()
