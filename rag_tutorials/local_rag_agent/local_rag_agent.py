# Import necessary libraries
from agno.agent import Agent
from agno.models.ollama import Ollama
from agno.knowledge.pdf_url import PDFUrlKnowledgeBase
from agno.vectordb.qdrant import Qdrant
from agno.embedder.ollama import OllamaEmbedder
from agno.playground import Playground, serve_playground_app

# Define the collection name for the vector database
collection_name = "thai-recipe-index"

# Set up Qdrant as the vector database with the embedder
vector_db = Qdrant(
    collection=collection_name,
    url="http://localhost:6333/",
    embedder=OllamaEmbedder()
)

# Define the knowledge base with the specified PDF URL
knowledge_base = PDFUrlKnowledgeBase(
    urls=["https://phi-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf"],
    vector_db=vector_db,
)

# Load the knowledge base, comment out after the first run to avoid reloading
knowledge_base.load(recreate=True, upsert=True)

# Create the Agent using Ollama's llama3.2 model and the knowledge base
agent = Agent(
    name="Local RAG Agent",
    model=Ollama(id="llama3.2"),
    knowledge=knowledge_base,
)

# UI for RAG agent
app = Playground(agents=[agent]).get_app()

# Run the Playground app
if __name__ == "__main__":
    serve_playground_app("local_rag_agent:app", reload=True)
