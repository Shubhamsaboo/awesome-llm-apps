from phi.agent import Agent
from phi.model.openai import OpenAIChat
from phi.knowledge.pdf import PDFKnowledgeBase, PDFReader
from phi.vectordb.lancedb import LanceDb, SearchType
from phi.playground import Playground, serve_playground_app
from phi.tools.duckduckgo import DuckDuckGo

# Set up configurations
DB_URI = "tmp/legal_docs_db"

# Create a knowledge base for legal documents
knowledge_base = PDFKnowledgeBase(
    path="tmp/legal_docs",
    vector_db=LanceDb(
        table_name="legal_documents",
        uri=DB_URI,
        search_type=SearchType.vector
    ),
    reader=PDFReader(chunk=True),
    num_documents=5
)

# Create the agent
agent = Agent(
    model=OpenAIChat(id="gpt-4"),
    agent_id="legal-analysis-agent",
    knowledge=knowledge_base,
    tools=[DuckDuckGo()],
    show_tool_calls=True,
    markdown=True,
)

app = Playground(agents=[agent]).get_app()

if __name__ == "__main__":
    serve_playground_app("legal_agent:app", reload=True)