import os
import tempfile
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.embedder.google import GeminiEmbedder
from agno.knowledge.reader.pdf_reader import PDFReader
from agno.models.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.vectordb.pgvector import PgVector, SearchType

# Load environment variables (NEON_DATABASE_URL, GEMINI_API_KEY) from .env
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))


def get_db_url() -> str:
    """Returns the Neon connection string in SQLAlchemy form, using the psycopg (v3) driver.

    Neon gives URLs like postgresql://user:pass@ep-xxx.neon.tech/neondb?sslmode=require,
    which SQLAlchemy would otherwise try to open with psycopg2."""
    url = (st.session_state.get("neon_database_url") or os.getenv("NEON_DATABASE_URL", "")).strip()
    for prefix in ("postgresql://", "postgres://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


def get_api_key():
    """Returns the Gemini API key from the sidebar input, falling back to the GEMINI_API_KEY env variable."""
    return st.session_state.get("gemini_api_key") or os.getenv("GEMINI_API_KEY")


@st.cache_resource
def setup_assistant(api_key: str, db_url: str) -> Agent:
    """Initializes an AutoRAG agent backed by Neon Postgres + pgvector.

    Neon suspends idle compute and drops open connections, so the shared engine
    uses pool_pre_ping to transparently replace stale connections.

    Args:
        api_key (str): The Gemini API key.
        db_url (str): SQLAlchemy connection URL for the Neon database.

    Returns:
        Agent: An agent that searches its knowledge base first, then the web."""
    
    engine = create_engine(db_url, pool_pre_ping=True, pool_recycle=300)

    knowledge = Knowledge(
        vector_db=PgVector(
            table_name="auto_rag_docs",
            db_engine=engine,
            search_type=SearchType.hybrid,
            embedder=GeminiEmbedder(id="gemini-embedding-001", dimensions=1536, api_key=api_key),
        ),
        max_results=3,
    )

    return Agent(
        id="auto_rag_neon_agent",
        model=Gemini(id="gemini-3.5-flash", api_key=api_key),
        db=PostgresDb(db_engine=engine, session_table="auto_rag_sessions"),
        knowledge=knowledge,
        search_knowledge=True,
        # Corporate TLS-inspection proxies can present certificates that ddgs rejects
        # (e.g. "CaUsedAsEndEntity"); WEB_SEARCH_VERIFY_SSL=false skips verification for web search only.
        tools=[DuckDuckGoTools(verify_ssl=os.getenv("WEB_SEARCH_VERIFY_SSL", "true").lower() != "false")],
        instructions=[
            "Search your knowledge base first.",
            "If not found, search the internet.",
            "Provide clear and concise answers.",
        ],
        add_history_to_context=True,
        markdown=True,
    )


def add_document(agent: Agent, uploaded_file):
    """Adds an uploaded PDF to the agent's knowledge base.

    The file is written to a temporary path because Knowledge.insert reads from disk.

    Args:
        agent (Agent): The agent whose knowledge base will be updated.
        uploaded_file: The Streamlit UploadedFile containing the PDF."""
    before = dict(list_documents(agent))
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(uploaded_file.getbuffer())
        tmp_path = tmp.name
    try:
        agent.knowledge.insert(name=uploaded_file.name, path=tmp_path, reader=PDFReader(), upsert=True)
    except Exception as e:
        st.error(f"Failed to add the document: {e}")
        return
    finally:
        os.remove(tmp_path)

    # Knowledge.insert logs embedding errors (e.g. an invalid Gemini key) instead of raising,
    # so confirm the chunks actually landed in Neon.
    chunks = dict(list_documents(agent)).get(uploaded_file.name, 0)
    if chunks:
        st.success(f"Added '{uploaded_file.name}' ({chunks} chunks) to the knowledge base.")
    elif uploaded_file.name in before:
        st.info(f"'{uploaded_file.name}' is already in the knowledge base.")
    else:
        st.error("No chunks were stored. Check that your Gemini API key is valid and see the terminal log.")


def list_documents(agent: Agent):
    """Returns (document name, chunk count) pairs stored in the Neon vector table."""
    vector_db = agent.knowledge.vector_db
    try:
        with vector_db.db_engine.connect() as conn:
            return conn.execute(text(
                f'SELECT name, count(*) FROM "{vector_db.schema}"."{vector_db.table_name}" GROUP BY name ORDER BY name'
            )).fetchall()
    except Exception:
        return []


WEB_TOOLS = {"web_search", "search_news"}


def show_source(response):
    """Shows whether the answer came from the knowledge base, the web, or the model alone.

    Hybrid search almost always returns the nearest chunks, so a knowledge base hit alone
    doesn't prove relevance; a successful web search means the agent needed to go beyond it."""
    tools = response.tools or []
    web_ok = [t for t in tools if t.tool_name in WEB_TOOLS and not t.tool_call_error]
    web_failed = [t for t in tools if t.tool_name in WEB_TOOLS and t.tool_call_error]

    # Collect "document (p. N)" citations from the knowledge base references
    pages = {}
    for ref in response.references or []:
        for doc in ref.references or []:
            if not isinstance(doc, dict):
                continue
            page = (doc.get("meta_data") or {}).get("page")
            pages.setdefault(doc.get("name") or "document", set()).update([page] if page else [])
    cited = "; ".join(f"{name} (p. {', '.join(map(str, sorted(p)))})" if p else name for name, p in pages.items())

    if web_ok:
        queries = ", ".join(f"“{t.tool_args.get('query')}”" for t in web_ok if t.tool_args)
        st.info(f"🌐 **Source: Web search** ({queries})"
                + ("\n\nThe knowledge base was searched first but didn't have the answer." if pages else ""))
    elif pages:
        st.success(f"📚 **Source: Knowledge base**: {cited}")
    else:
        st.warning("🤖 **Source: Model's general knowledge**: no knowledge base or web results were used.")
    if web_failed:
        st.caption("⚠️ A web search attempt failed (see terminal log).")


def main():
    """Streamlit UI for the AutoRAG app backed by Neon."""
    st.set_page_config(page_title="AutoRAG + Neon", layout="wide")
    st.title("🤖 Auto-RAG: Autonomous RAG with Gemini and Neon pgvector")

    with st.sidebar:
        st.header("🔐 Setup")
        url_input = st.text_input(
            "Neon connection string 🐘", type="password",
            placeholder="Loaded from .env" if os.getenv("NEON_DATABASE_URL") else "postgresql://user:pass@ep-xxx.neon.tech/neondb?sslmode=require",
            help="Overrides NEON_DATABASE_URL from .env. Copy it from Neon dashboard → Connect.",
        )
        if url_input:
            st.session_state.neon_database_url = url_input
        key_input = st.text_input(
            "Gemini API key 🔑", type="password",
            placeholder="Loaded from .env" if os.getenv("GEMINI_API_KEY") else "Required: paste your key",
            help="Overrides GEMINI_API_KEY from .env. Get one at https://aistudio.google.com/apikey",
        )
        if key_input:
            st.session_state.gemini_api_key = key_input

    db_url, api_key = get_db_url(), get_api_key()

    # Connect only once both settings are present; otherwise explain what is missing.
    assistant, problems = None, []
    if not db_url:
        problems.append("**Neon connection string** is missing: set `NEON_DATABASE_URL` in `.env` or paste it in the sidebar.")
    if not api_key:
        problems.append("**Gemini API key** is missing: set `GEMINI_API_KEY` in `.env` or paste it in the sidebar "
                        "(open the sidebar with ❯ at the top left). It is needed to embed PDFs and answer questions.")
    if not problems:
        try:
            assistant = setup_assistant(api_key, db_url)
        except Exception as e:
            problems.append(f"**Could not connect to Neon.** Check the connection string.\n\n`{e}`")

    with st.sidebar:
        neon_status = "✅" if assistant else ("⏳" if db_url and not api_key else "❌")
        st.caption(f"{neon_status} Neon   {'✅' if api_key else '❌'} Gemini key")
        st.divider()
        st.header("📚 Knowledge base")
        uploaded_file = st.file_uploader("📄 Upload PDF", type=["pdf"], disabled=assistant is None)
        if st.button("🛠️ Add to Knowledge Base", disabled=assistant is None or uploaded_file is None):
            with st.spinner("Embedding document into Neon..."):
                add_document(assistant, uploaded_file)
        if assistant:
            docs = list_documents(assistant)
            if docs:
                for name, chunks in docs:
                    st.markdown(f"- {name} · {chunks} chunks")
            else:
                st.caption("No documents yet. Upload a PDF above.")

    for problem in problems:
        st.warning(problem)

    question = st.text_input("💬 Ask Your Question:", disabled=assistant is None)

    if st.button("🔍 Get Answer", disabled=assistant is None):
        if question.strip():
            with st.spinner("🤔 Thinking..."):
                response = assistant.run(question)
                show_source(response)
                st.write("📝 **Response:**")
                st.markdown(response.content)
        else:
            st.error("Please enter a question.")


if __name__ == "__main__":
    main()
