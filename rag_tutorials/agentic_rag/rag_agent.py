from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.knowledge.pdf_url import PDFUrlKnowledgeBase
from agno.vectordb.lancedb import LanceDb, SearchType
from agno.playground import Playground, serve_playground_app
from agno.tools.duckduckgo import DuckDuckGoTools

db_uri = "tmp/lancedb"
# Create a knowledge base from a PDF
knowledge_base = PDFUrlKnowledgeBase(
    urls=["https://phi-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf"],
    # Use LanceDB as the vector database
    vector_db=LanceDb(table_name="recipes", uri=db_uri, search_type=SearchType.vector),
)
# Load the knowledge base: Comment out after first run
knowledge_base.load(upsert=True)

rag_agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    agent_id="rag-agent",
    knowledge=knowledge_base, # Add the knowledge base to the agent
    tools=[DuckDuckGoTools()],
    show_tool_calls=True,
    markdown=True,
)

app = Playground(agents=[rag_agent]).get_app()

if __name__ == "__main__":
    serve_playground_app("rag_agent:app", reload=True)