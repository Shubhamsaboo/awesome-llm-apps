# ──────────────────────────────────────────────────────────────────────────────
#  Voice RAG Agent  –  100 % Free Stack
#  • Text generation  : Groq  (llama-3.1-8b-instant)
#  • Embeddings       : FastEmbed  (local, no API key)
#  • Vector DB        : Qdrant Cloud  (free tier)
#  • Text-to-Speech   : edge-tts  (Microsoft Edge TTS, free & no API key)
# ──────────────────────────────────────────────────────────────────────────────

from typing import Any, Dict, List, Tuple
import asyncio
import concurrent.futures
import hashlib
import os
import tempfile
import uuid
from datetime import datetime

import edge_tts
import streamlit as st
from dotenv import load_dotenv
from fastembed import TextEmbedding
from groq import Groq, APIError
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams

load_dotenv()

# ── Constants ─────────────────────────────────────────────────────────────────
COLLECTION_NAME = "voice-rag-agent"

# edge-tts voices (free, no key required)
VOICE_OPTIONS: List[str] = [
    "en-US-ChristopherNeural",   # Male  – clear, authoritative
    "en-US-AriaNeural",          # Female – warm, conversational
    "en-US-GuyNeural",           # Male  – casual, friendly
    "en-US-JennyNeural",         # Female – professional
    "en-GB-SoniaNeural",         # Female – British accent
    "en-GB-RyanNeural",          # Male   – British accent
    "en-AU-NatashaNeural",       # Female – Australian accent
    "en-CA-ClaraNeural",         # Female – Canadian accent
    "en-IN-NeerjaNeural",        # Female – Indian accent
]
DEFAULT_VOICE = "en-US-ChristopherNeural"

# Groq model  (free tier, very fast)
TEXT_RESPONSE_MODEL = "llama-3.1-8b-instant"
# A more powerful model is available in Groq's free tier, but it can be slower and may hit rate limits more quickly.  Uncomment the line below to use it instead of llama-3.1-8b-instant.
# TEXT_RESPONSE_MODEL = "llama-3.3-70b-versatile"

# ── Environment helpers ────────────────────────────────────────────────────────

def load_environment_defaults() -> Dict[str, str]:
    """Load configuration defaults from environment variables / Streamlit secrets."""
    defaults = {
        "qdrant_url":    os.getenv("QDRANT_URL", ""),
        "qdrant_api_key": os.getenv("QDRANT_API_KEY", ""),
        "groq_api_key":  os.getenv("GROQ_API_KEY", ""),
    }
    try:
        defaults["qdrant_url"]     = defaults["qdrant_url"]     or st.secrets.get("QDRANT_URL", "")
        defaults["qdrant_api_key"] = defaults["qdrant_api_key"] or st.secrets.get("QDRANT_API_KEY", "")
        defaults["groq_api_key"]   = defaults["groq_api_key"]   or st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        pass
    return defaults


def build_connection_signature(qdrant_url: str, qdrant_api_key: str) -> str:
    """Create a stable fingerprint for the active Qdrant connection."""
    return hashlib.sha256(f"{qdrant_url}|{qdrant_api_key}".encode()).hexdigest()


# ── Session state ─────────────────────────────────────────────────────────────

def init_session_state() -> None:
    """Initialize Streamlit session state with sensible defaults."""
    env = load_environment_defaults()
    defaults: Dict[str, Any] = {
        "initialized":                  False,
        "qdrant_url":                   env["qdrant_url"],
        "qdrant_api_key":               env["qdrant_api_key"],
        "groq_api_key":                 env["groq_api_key"],
        "setup_complete":               False,
        "client":                       None,
        "embedding_model":              None,
        "qdrant_connection_signature":  "",
        "selected_voice":               DEFAULT_VOICE,
        "processed_documents":          {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def has_qdrant_credentials() -> bool:
    return bool(st.session_state.qdrant_url.strip() and st.session_state.qdrant_api_key.strip())


def has_groq_credentials() -> bool:
    return bool(st.session_state.groq_api_key.strip())


# ── Sidebar ───────────────────────────────────────────────────────────────────

def setup_sidebar() -> None:
    """Configure sidebar: API settings and voice selector."""
    with st.sidebar:
        st.title("🔑 Configuration")
        st.markdown("---")

        st.session_state.qdrant_url = st.text_input(
            "Qdrant URL",
            value=st.session_state.qdrant_url,
            type="password",
        ).strip()

        st.session_state.qdrant_api_key = st.text_input(
            "Qdrant API Key",
            value=st.session_state.qdrant_api_key,
            type="password",
        ).strip()

        st.session_state.groq_api_key = st.text_input(
            "Groq API Key",
            value=st.session_state.groq_api_key,
            type="password",
            help="Free key at console.groq.com – no credit card needed.",
        ).strip()

        st.markdown("---")
        st.markdown("### 🎤 Voice Settings")
        selected_voice = (
            st.session_state.selected_voice
            if st.session_state.selected_voice in VOICE_OPTIONS
            else DEFAULT_VOICE
        )
        st.session_state.selected_voice = st.selectbox(
            "Select Voice (edge-tts)",
            options=VOICE_OPTIONS,
            index=VOICE_OPTIONS.index(selected_voice),
            help="Microsoft Edge TTS voices — free, no API key required.",
        )

        st.markdown("---")
        st.markdown("### ✅ Status")
        if has_qdrant_credentials():
            st.success("Qdrant credentials ready")
        else:
            st.warning("Enter Qdrant URL and API key")

        if has_groq_credentials():
            st.success("Groq API key ready")
        else:
            st.warning("Enter Groq API key")


# ── Qdrant setup ──────────────────────────────────────────────────────────────

def setup_qdrant(qdrant_url: str, qdrant_api_key: str) -> Tuple[QdrantClient, TextEmbedding]:
    """Initialize Qdrant client and FastEmbed embedding model."""
    if not all([qdrant_url.strip(), qdrant_api_key.strip()]):
        raise ValueError("Qdrant credentials not provided")

    client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)

    embedding_model = TextEmbedding()
    test_embedding = list(embedding_model.embed(["test"]))[0]
    embedding_dim = len(test_embedding)

    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=embedding_dim, distance=Distance.COSINE),
        )

    return client, embedding_model


def ensure_qdrant_client() -> None:
    """Create or refresh the Qdrant client when credentials change."""
    if not has_qdrant_credentials():
        st.session_state.client = None
        st.session_state.embedding_model = None
        st.session_state.qdrant_connection_signature = ""
        st.session_state.setup_complete = False
        return

    current_sig = build_connection_signature(
        st.session_state.qdrant_url, st.session_state.qdrant_api_key
    )
    needs_refresh = (
        st.session_state.client is None
        or st.session_state.embedding_model is None
        or st.session_state.qdrant_connection_signature != current_sig
    )

    if needs_refresh:
        if (
            st.session_state.qdrant_connection_signature
            and st.session_state.qdrant_connection_signature != current_sig
        ):
            st.session_state.processed_documents = {}

        client, embedding_model = setup_qdrant(
            st.session_state.qdrant_url, st.session_state.qdrant_api_key
        )
        st.session_state.client = client
        st.session_state.embedding_model = embedding_model
        st.session_state.qdrant_connection_signature = current_sig

    st.session_state.setup_complete = bool(st.session_state.processed_documents)


# ── Document processing ───────────────────────────────────────────────────────

def get_file_signature(file: Any) -> str:
    """Generate a stable fingerprint for an uploaded file."""
    return hashlib.sha256(file.getvalue()).hexdigest()


def process_pdf(file: Any, document_id: str) -> List:
    """Load a PDF and split it into overlapping text chunks."""
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            temp_path = tmp.name
            tmp.write(file.getvalue())

        loader = PyPDFLoader(temp_path)
        documents = loader.load()

        timestamp = datetime.now().isoformat()
        for doc in documents:
            doc.metadata.update(
                {
                    "source_type":  "pdf",
                    "file_name":    file.name,
                    "document_id":  document_id,
                    "timestamp":    timestamp,
                }
            )

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_documents(documents)
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = i

        return chunks

    except Exception as exc:
        st.error(f"📄 PDF processing error: {exc}")
        return []
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


def store_embeddings(
    client: QdrantClient,
    embedding_model: TextEmbedding,
    documents: List,
    collection_name: str,
) -> None:
    """Embed document chunks and upsert them into Qdrant."""
    batch_size = 32
    for start in range(0, len(documents), batch_size):
        batch = documents[start : start + batch_size]
        texts = [doc.page_content for doc in batch]
        embeddings = list(embedding_model.embed(texts))

        points = [
            models.PointStruct(
                id=str(uuid.uuid4()),
                vector=emb.tolist(),
                payload={"content": doc.page_content, **doc.metadata},
            )
            for doc, emb in zip(batch, embeddings)
        ]

        if points:
            client.upsert(collection_name=collection_name, points=points)


# ── RAG context builder ───────────────────────────────────────────────────────

def build_retrieval_context(search_results: List, query: str) -> Tuple[str, List[str]]:
    """Assemble a prompt-ready context block from Qdrant search hits."""
    context_lines = ["Based on the following documentation:"]
    sources: List[str] = []

    for i, result in enumerate(search_results, 1):
        payload = result.payload or {}
        content = (payload.get("content") or "").strip()
        if not content:
            continue

        source = payload.get("file_name", "Unknown Source")
        chunk_index = payload.get("chunk_index", "unknown")
        context_lines.append(f"From {source} (chunk {chunk_index}):\n{content}")
        sources.append(source)
        st.write(f"Document {i} from: {source}")

    if len(context_lines) == 1:
        raise ValueError("Retrieved documents did not contain readable content.")

    context_lines.append(f"User Question: {query}")
    context_lines.append("Please answer clearly, concisely, and in a way that can be read aloud.")
    unique_sources = list(dict.fromkeys(sources))
    return "\n\n".join(context_lines), unique_sources


# ── Groq text generation ──────────────────────────────────────────────────────

def generate_text_response(groq_api_key: str, context: str) -> str:
    """
    Call Groq's chat completions endpoint with llama-3.1-8b-instant.
    Direct API call – no custom agents module required.
    """
    groq_client = Groq(api_key=groq_api_key)

    completion = groq_client.chat.completions.create(
        model=TEXT_RESPONSE_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful documentation assistant. "
                    "Answer using only the provided context whenever possible. "
                    "Be concise, accurate, and conversational. "
                    "When the answer is not in the context, say so explicitly. "
                    "Cite source file names when referencing specific content."
                ),
            },
            {"role": "user", "content": context},
        ],
        temperature=0.2,
        max_tokens=1024,
    )

    text_response = (completion.choices[0].message.content or "").strip()
    if not text_response:
        raise ValueError("Groq returned an empty answer.")
    return text_response


# ── edge-tts voice generation ─────────────────────────────────────────────────

async def _tts_async(text: str, voice: str, output_path: str) -> None:
    """Async coroutine: save edge-tts speech to *output_path*."""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)


def generate_audio_response(text_response: str, voice: str) -> bytes:
    """
    Generate an MP3 audio clip from *text_response* using edge-tts.

    edge-tts is fully async.  To play well with Streamlit's synchronous
    execution model, we spin up a *fresh* event loop in a dedicated
    background thread so we never fight with Streamlit's own loop.
    """
    tmp_path: str | None = None
    try:
        # Write to a temp file because edge-tts streams to disk
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp_path = tmp.name

        def _run_in_new_thread() -> None:
            """Isolated event loop – completely separate from Streamlit's."""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(_tts_async(text_response, voice, tmp_path))
            finally:
                loop.close()
                asyncio.set_event_loop(None)

        # ThreadPoolExecutor ensures the coroutine runs in its own OS thread
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            pool.submit(_run_in_new_thread).result()  # blocks until audio is ready

        with open(tmp_path, "rb") as f:
            return f.read()

    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


# ── Main query pipeline ───────────────────────────────────────────────────────

def process_query(
    query: str,
    client: QdrantClient,
    embedding_model: TextEmbedding,
    collection_name: str,
    groq_api_key: str,
    voice: str,
) -> Dict:
    """
    End-to-end RAG pipeline:
        embed query → search Qdrant → build context →
        generate text (Groq) → generate audio (edge-tts)
    """
    try:
        if not groq_api_key.strip():
            raise ValueError("Groq API key not provided.")

        # ── Step 1: embed query and search ────────────────────────────────
        st.info("🔄 Step 1: Generating query embedding and searching documents…")
        query_embedding = list(embedding_model.embed([query]))[0]
        st.write(f"Embedding size: {len(query_embedding)}")

        search_response = client.query_points(
            collection_name=collection_name,
            query=query_embedding.tolist(),
            limit=3,
            with_payload=True,
        )
        search_results = search_response.points if hasattr(search_response, "points") else []
        st.write(f"Retrieved {len(search_results)} relevant document(s)")

        if not search_results:
            raise ValueError("No relevant documents found in the vector database.")

        # ── Step 2: build context ──────────────────────────────────────────
        st.info("🔄 Step 2: Preparing context from search results…")
        context, sources = build_retrieval_context(search_results, query)

        # ── Step 3: Groq text generation ───────────────────────────────────
        st.info(f"🔄 Step 3: Generating text response with Groq ({TEXT_RESPONSE_MODEL})…")
        text_response = generate_text_response(groq_api_key, context)
        st.write(f"Text response length: {len(text_response)} characters")

        # ── Step 4: edge-tts audio synthesis ──────────────────────────────
        st.info(f"🔄 Step 4: Synthesising audio with edge-tts ({voice})…")
        audio_bytes = generate_audio_response(text_response, voice)
        st.write(f"Audio size: {len(audio_bytes):,} bytes")

        st.success("✅ Query processing complete!")
        return {
            "status":          "success",
            "text_response":   text_response,
            "audio_bytes":     audio_bytes,
            "audio_file_name": f"voice_response_{voice}.mp3",
            "sources":         sources,
        }

    except APIError as exc:
        # Catch Groq-specific API errors (auth, rate-limit, network, …)
        error_msg = f"Groq API error: {exc}"
        st.error(f"❌ {error_msg}")
        return {"status": "error", "error": error_msg, "query": query}

    except Exception as exc:
        st.error(f"❌ Error during query processing: {exc}")
        return {"status": "error", "error": str(exc), "query": query}


# ── Streamlit app entry point ─────────────────────────────────────────────────

def main() -> None:
    st.set_page_config(
        page_title="Voice RAG Agent",
        page_icon="🎙️",
        layout="wide",
    )

    init_session_state()
    setup_sidebar()

    # ── Qdrant initialisation ──────────────────────────────────────────────
    qdrant_ready = False
    if has_qdrant_credentials():
        try:
            ensure_qdrant_client()
            qdrant_ready = True
        except Exception as exc:
            st.session_state.client = None
            st.session_state.embedding_model = None
            st.session_state.setup_complete = False
            st.error(f"Unable to initialise Qdrant: {exc}")
    else:
        st.session_state.client = None
        st.session_state.embedding_model = None
        st.session_state.setup_complete = False

    st.session_state.setup_complete = bool(st.session_state.processed_documents)

    # ── Page header ────────────────────────────────────────────────────────
    st.title("🎙️ Voice RAG Agent")
    st.info(
        "A **100 % free** voice-powered RAG system.  "
        "Configure your API keys in the sidebar, upload PDF documents, "
        "then ask questions to receive both a text answer and a spoken audio response."
    )

    # ── Credential warnings ────────────────────────────────────────────────
    if not has_qdrant_credentials():
        st.warning("⚠️  Provide Qdrant credentials in the sidebar (or via `.env`) before uploading documents.")
    if not has_groq_credentials():
        st.warning("⚠️  Provide a Groq API key in the sidebar (or via `.env`) before asking questions.")

    # ── PDF uploader ───────────────────────────────────────────────────────
    uploaded_files = st.file_uploader(
        "Upload PDF documents",
        type=["pdf"],
        accept_multiple_files=True,
        disabled=not qdrant_ready,
    )

    if uploaded_files:
        if st.session_state.client and st.session_state.embedding_model:
            for uploaded_file in uploaded_files:
                document_id = get_file_signature(uploaded_file)
                file_name   = uploaded_file.name

                if document_id in st.session_state.processed_documents:
                    st.info(f"⏩ Skipping already-processed PDF: {file_name}")
                    continue

                with st.spinner(f"Processing {file_name}…"):
                    try:
                        chunks = process_pdf(uploaded_file, document_id)
                        if chunks:
                            store_embeddings(
                                st.session_state.client,
                                st.session_state.embedding_model,
                                chunks,
                                COLLECTION_NAME,
                            )
                            st.session_state.processed_documents[document_id] = {
                                "file_name":   file_name,
                                "document_id": document_id,
                                "chunk_count": len(chunks),
                                "uploaded_at": datetime.now().isoformat(),
                            }
                            st.session_state.setup_complete = True
                            st.success(f"✅ Added: {file_name}  ({len(chunks)} chunks)")
                        else:
                            st.warning(f"No readable text extracted from {file_name}.")
                    except Exception as exc:
                        st.error(f"Error processing {file_name}: {exc}")
        else:
            st.error("Qdrant is not available. Check the URL and API key in the sidebar.")

    # ── Processed documents panel (sidebar) ───────────────────────────────
    if st.session_state.processed_documents:
        st.sidebar.markdown("---")
        st.sidebar.header("📚 Processed Documents")
        for record in st.session_state.processed_documents.values():
            st.sidebar.text(f"📄 {record['file_name']}  ({record['chunk_count']} chunks)")

    # ── Query input ────────────────────────────────────────────────────────
    query = st.text_input(
        "What would you like to know about your documents?",
        placeholder="e.g., How do I authenticate API requests?",
        disabled=not (st.session_state.setup_complete and has_groq_credentials()),
    )

    # ── Query processing and output ────────────────────────────────────────
    if query and st.session_state.setup_complete and has_groq_credentials():
        with st.status("Processing your query…", expanded=True) as status:
            try:
                result = process_query(
                    query,
                    st.session_state.client,
                    st.session_state.embedding_model,
                    COLLECTION_NAME,
                    st.session_state.groq_api_key,
                    st.session_state.selected_voice,
                )

                if result["status"] == "success":
                    status.update(label="✅ Query processed!", state="complete")

                    st.markdown("### 📝 Response")
                    st.write(result["text_response"])

                    if result.get("audio_bytes"):
                        voice_label = st.session_state.selected_voice
                        st.markdown(f"### 🔊 Audio Response  *(voice: {voice_label})*")
                        st.audio(result["audio_bytes"], format="audio/mp3", start_time=0)

                        st.download_button(
                            label="📥 Download Audio Response",
                            data=result["audio_bytes"],
                            file_name=result.get(
                                "audio_file_name",
                                f"voice_response_{voice_label}.mp3",
                            ),
                            mime="audio/mp3",
                        )

                    st.markdown("### 📎 Sources")
                    for source in result["sources"]:
                        st.markdown(f"- {source}")

                else:
                    status.update(label="❌ Error processing query", state="error")
                    st.error(f"Error: {result.get('error', 'Unknown error occurred')}")

            except Exception as exc:
                status.update(label="❌ Error processing query", state="error")
                st.error(f"Error processing query: {exc}")

    elif not st.session_state.setup_complete:
        st.info("👈 Configure the system in the sidebar and upload at least one PDF first.")
    elif not has_groq_credentials():
        st.info("👈 Add a Groq API key in the sidebar to start asking questions.")


if __name__ == "__main__":
    main()