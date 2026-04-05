import streamlit as st
from longtrainer.trainer import LongTrainer
import os

# ─── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="LongTrainer — Multi-Tenant RAG",
    page_icon="🤖",
    layout="wide",
)

# ─── Title ───────────────────────────────────────────────────────────────────
st.title("🤖 Multi-Tenant RAG with LongTrainer")
st.markdown(
    """
    This tutorial shows how **LongTrainer** makes it trivial to build production-ready,
    multi-tenant RAG applications.  
    Each *bot* gets its own **isolated knowledge base** and **persistent chat history** —
    no cross-contamination between users or tenants.

    > **What you'll learn**  
    > * Create isolated bots for different tenants with a single API call  
    > * Upload documents and URLs to a per-bot knowledge base  
    > * Chat with each bot independently — history is preserved per session  
    """
)

# ─── API Key ─────────────────────────────────────────────────────────────────
st.subheader("🔑 Configuration")
openai_key = st.text_input(
    "OpenAI API Key",
    type="password",
    value=os.getenv("OPENAI_API_KEY", ""),
    help="Get your key from https://platform.openai.com/",
)

if not openai_key:
    st.info("👋 Enter your OpenAI API Key above to get started.")
    st.stop()

os.environ["OPENAI_API_KEY"] = openai_key

# ─── Initialise LongTrainer ──────────────────────────────────────────────────
@st.cache_resource(show_spinner="⚙️  Initialising LongTrainer...")
def get_trainer(api_key: str) -> LongTrainer:
    return LongTrainer(openai_api_key=api_key)

trainer = get_trainer(openai_key)

# ─── Sidebar — Tenant / Bot Management ──────────────────────────────────────
with st.sidebar:
    st.header("👥 Tenant Management")

    # keep track of bots in session
    if "bots" not in st.session_state:
        st.session_state.bots: dict[str, str] = {}   # name → bot_id
    if "chat_histories" not in st.session_state:
        st.session_state.chat_histories: dict[str, list] = {}

    # Create a new bot / tenant
    st.subheader("➕ Create New Tenant Bot")
    new_bot_name = st.text_input("Tenant name", placeholder="e.g. Acme Corp")
    if st.button("Create Bot", type="primary") and new_bot_name:
        if new_bot_name not in st.session_state.bots:
            with st.spinner(f"Creating bot for {new_bot_name}…"):
                bot_id = trainer.initialize_bot_id()
            st.session_state.bots[new_bot_name] = bot_id
            st.session_state.chat_histories[new_bot_name] = []
            st.success(f"✅ Bot created for **{new_bot_name}**")
        else:
            st.warning(f"A bot for **{new_bot_name}** already exists.")

    st.divider()

    # Tenant selector
    if st.session_state.bots:
        st.subheader("🔄 Select Active Tenant")
        selected_tenant = st.selectbox(
            "Tenant",
            options=list(st.session_state.bots.keys()),
            label_visibility="collapsed",
        )
        st.session_state.active_tenant = selected_tenant
        st.caption(f"Bot ID: `{st.session_state.bots[selected_tenant]}`")
    else:
        st.info("Create a tenant bot above to get started.")
        st.session_state.active_tenant = None

# ─── Main area ───────────────────────────────────────────────────────────────
if not st.session_state.get("active_tenant"):
    st.warning("⬅️  Create a tenant bot in the sidebar to begin.")
    st.stop()

tenant = st.session_state.active_tenant
bot_id = st.session_state.bots[tenant]

st.subheader(f"📂 Knowledge Base — {tenant}")

tab_url, tab_chat = st.tabs(["📎 Add Knowledge", "💬 Chat"])

# ── Tab 1 : knowledge ingestion ───────────────────────────────────────────────
with tab_url:
    col_url, col_file = st.columns(2)

    with col_url:
        st.markdown("**Add a URL**")
        url_input = st.text_input("URL", placeholder="https://example.com/docs")
        if st.button("➕ Add URL") and url_input:
            with st.spinner("Loading URL into knowledge base…"):
                trainer.add_url_to_bot(bot_id, url_input)
            st.success(f"✅ URL added to **{tenant}**'s knowledge base.")

    with col_file:
        st.markdown("**Upload a Document** (PDF / DOCX / TXT)")
        uploaded = st.file_uploader(
            "Choose file",
            type=["pdf", "docx", "txt"],
            label_visibility="collapsed",
        )
        if uploaded and st.button("📤 Upload Document"):
            # save temporarily then ingest
            tmp_path = f"/tmp/{uploaded.name}"
            with open(tmp_path, "wb") as f:
                f.write(uploaded.getbuffer())
            with st.spinner("Processing document…"):
                trainer.add_document_to_bot(bot_id, tmp_path)
            st.success(f"✅ **{uploaded.name}** added to **{tenant}**'s knowledge base.")

    st.info(
        "💡 Each tenant's documents are **isolated** — one tenant cannot access another's data."
    )

# ── Tab 2 : chat ──────────────────────────────────────────────────────────────
with tab_chat:
    history = st.session_state.chat_histories[tenant]

    # Render existing messages
    for msg in history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    user_query = st.chat_input(f"Ask {tenant}'s bot a question…")
    if user_query:
        # Show user message immediately
        history.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        # Get bot response
        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                try:
                    chat_id = trainer.get_new_chat(bot_id)
                    response = trainer.chat(user_query, bot_id, chat_id)
                    answer = response if isinstance(response, str) else str(response)
                except Exception as e:
                    answer = f"⚠️ Error: {e}"
            st.markdown(answer)

        history.append({"role": "assistant", "content": answer})
        st.session_state.chat_histories[tenant] = history

# ─── How it works expander ───────────────────────────────────────────────────
st.divider()
with st.expander("📖 How This Works"):
    st.markdown(
        """
        ### LongTrainer Multi-Tenant Architecture

        ```
        ┌──────────────────────────────────────────────┐
        │               LongTrainer                    │
        │                                              │
        │  Tenant A  ──►  Bot-ID-A  ──►  VectorStore-A │
        │  Tenant B  ──►  Bot-ID-B  ──►  VectorStore-B │
        │  Tenant C  ──►  Bot-ID-C  ──►  VectorStore-C │
        └──────────────────────────────────────────────┘
        ```

        **Key LongTrainer concepts used here:**

        | Concept | What it does |
        |---------|--------------|
        | `initialize_bot_id()` | Provisions an isolated RAG namespace for a tenant |
        | `add_url_to_bot()` | Fetches, chunks & embeds a URL into the bot's vector store |
        | `add_document_to_bot()` | Parses & ingests PDF/DOCX/TXT files |
        | `get_new_chat()` | Creates a fresh conversation thread |
        | `chat()` | Retrieves context from the bot's store and streams an answer |

        Each call is **scoped entirely to one bot_id** — making production multi-tenancy
        a first-class citizen rather than an afterthought.
        """
    )
