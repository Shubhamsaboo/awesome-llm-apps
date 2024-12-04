import os
import logging
import chainlit as cl
from raglite import RAGLiteConfig, insert_document, hybrid_search, retrieve_chunks, rerank_chunks, rag
from rerankers import Reranker
from typing import List, Tuple
from pathlib import Path
from chainlit.input_widget import TextInput
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

my_config = None

# System prompt for local LLM
RAG_SYSTEM_PROMPT = """
You are a friendly and knowledgeable assistant that provides complete and insightful answers.
Answer the user's question using only the context below.
When responding, you MUST NOT reference the existence of the context, directly or indirectly.
Instead, you MUST treat the context as if its contents are entirely part of your working memory.
""".strip()

def initialize_config(settings: dict) -> RAGLiteConfig:
    """Initialize RAGLite configuration with local models."""
    try:
        return RAGLiteConfig(
            db_url=settings["DBUrl"],
            llm=f"llama-cpp-python/{settings['LLMPath']}",
            embedder=f"llama-cpp-python/{settings['EmbedderPath']}",
            embedder_normalize=True,
            chunk_max_size=2000,
            embedder_sentence_window_size=2,
            reranker=(
                ("en", Reranker("ms-marco-MiniLM-L-12-v2", model_type="flashrank")),
                ("other", Reranker("ms-marco-MultiBERT-L-12", model_type="flashrank")),
            )
        )
    except KeyError as e:
        raise ValueError(f"Missing required setting: {e}")

def process_document(file_path: str) -> None:
    """Process and embed a document into the database."""
    logger.info(f"Starting to process document: {file_path}")
    try:
        import time
        start_time = time.time()

        # Inserting document into PostgreSQL database
        insert_document(Path(file_path), config=my_config)

        processing_time = time.time() - start_time
        logger.info(f"Document processed and embedded in {processing_time:.2f} seconds")

    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        raise

def perform_search(query: str) -> List[dict]:
    """Perform hybrid search and reranking on the query."""
    logger.info(f"Performing hybrid search for: {query}")
    try:
        chunk_ids, scores = hybrid_search(query, num_results=10, config=my_config)
        logger.debug(f"Found {len(chunk_ids)} chunks with scores: {scores}")

        if not chunk_ids:
            logger.info("No relevant chunks found in database")
            return []

        chunks = retrieve_chunks(chunk_ids, config=my_config)
        reranked_chunks = rerank_chunks(query, chunks, config=my_config)
        return reranked_chunks
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return []

@cl.on_settings_update
async def handle_settings_update(settings: dict):
    """Handle settings updates when user submits the form."""
    try:
        def validate_path(path: str, path_type: str) -> bool:
            if not path:
                raise ValueError(f"{path_type} path is required")
            return True

        def validate_db_url(url: str) -> bool:
            if not url:
                raise ValueError("Database URL is required")
            if not url.startswith(('sqlite://', 'postgresql://')):
                raise ValueError("Invalid database URL format")
            return True

        # Validate settings
        validate_path(settings["LLMPath"], "LLM")
        validate_path(settings["EmbedderPath"], "Embedder")
        validate_db_url(settings["DBUrl"])

        global my_config
        my_config = initialize_config(settings)
        cl.user_session.set("settings", settings)
        
        await cl.Message(content="✅ Successfully configured with local models!").send()

        # Ask for file upload
        files = await cl.AskFileMessage(
            content="Please upload one or more PDF documents to begin!",
            accept=["application/pdf"],
            max_size_mb=20,
            timeout=300,
            max_files=5
        ).send()

        if files:
            success = False
            
            # Process uploaded files
            for file in files:
                logger.info(f"Starting to process file: {file.name}")
                
                # Create new message for each file
                await cl.Message(f"Processing {file.name}...").send()

                try:
                    logger.info(f"Embedding document: {file.path}")
                    process_document(file_path=file.path)
                    
                    success = True
                    await cl.Message(f"✅ Successfully processed: {file.name}").send()
                    logger.info(f"Successfully processed and embedded: {file.name}")

                except Exception as proc_error:
                    error_msg = f"Failed to process {file.name}: {str(proc_error)}"
                    logger.error(error_msg)
                    await cl.Message(f"❌ {error_msg}").send()
                    continue

            if success:
                # Send completion message
                await cl.Message(
                    content="✅ Documents are ready! You can now ask questions about them."
                ).send()
                
                # Store session state
                cl.user_session.set("documents_loaded", True)
                
                # Reset the chat interface
                await cl.Message(content="Ask your first question:").send()
                
                # Clear any existing message elements
                cl.user_session.set("message_elements", [])
                
            else:
                await cl.Message(
                    content="❌ No documents were successfully processed. Please try uploading again."
                ).send()

    except Exception as e:
        error_msg = f"❌ Error with provided settings: {str(e)}"
        logger.error(error_msg)
        await cl.Message(content=error_msg).send()


@cl.on_chat_start
async def start() -> None:
    """Initialize chat and request model paths."""
    try:
        logger.info("Chat session started")
        cl.user_session.set("chat_history", [])
        
        await cl.Message(
            content="""# 🤖 Local LLM-Powered Hybrid Search-RAG Assistant

            Welcome! To get started:
            Enter your model paths and database URL below on the ChatSettings widget
            """
        ).send()
        
        await cl.ChatSettings([
            TextInput(
                id="LLMPath",
                label="LLM Path",
                initial="",
                placeholder="e.g., bartowski/Llama-3.2-3B-Instruct-GGUF/*Q4_K_M.gguf@4096"
            ),
            TextInput(
                id="EmbedderPath",
                label="Embedder Path",
                initial="",
                placeholder="e.g., lm-kit/bge-m3-gguf/*F16.gguf@1024"
            ),
            TextInput(
                id="DBUrl",
                label="Database URL",
                initial="",
                placeholder="sqlite:///raglite.sqlite or postgresql://user:pass@host:port/db"
            ),
        ]).send()

    except Exception as e:
        logger.error(f"Error in chat start: {str(e)}")
        await cl.Message(content=f"Error initializing chat: {str(e)}").send()

@cl.on_message
async def message_handler(message: cl.Message) -> None:
    """Handle user queries using local RAG."""
    try:
        if not cl.user_session.get("documents_loaded"):
            await cl.Message(content="❌ Please upload and process documents first!").send()
            return

        if not my_config:
            await cl.Message(content="❌ Please configure your model paths first!").send()
            return

        msg = cl.Message(content="")
        await msg.send()

        query = message.content.strip()
        if not query:
            await cl.Message(content="❌ Please enter a valid question.").send()
            return

        logger.info(f"Processing query: {query}")

        try:
            reranked_chunks = perform_search(query)

            if not reranked_chunks:
                await cl.Message(content="No relevant information found in the documents.").send()
                return

            chat_history = cl.user_session.get("chat_history", [])
            formatted_messages = []
            for user_msg, assistant_msg in chat_history:
                formatted_messages.append({"role": "user", "content": user_msg})
                formatted_messages.append({"role": "assistant", "content": assistant_msg})

            response_stream = rag(
                prompt=query,
                system_prompt=RAG_SYSTEM_PROMPT,
                search=hybrid_search,
                messages=formatted_messages,
                max_contexts=5,
                config=my_config
            )

            full_response = ""
            for chunk in response_stream:
                if chunk:
                    full_response += chunk
                    await msg.stream_token(chunk)

            if not full_response:
                await cl.Message(content="❌ No response generated. Please try rephrasing your question.").send()
                return

            chat_history.append((query, full_response))
            cl.user_session.set("chat_history", chat_history)

        except Exception as e:
            logger.error(f"RAG error: {str(e)}")
            await cl.Message(content=f"❌ Error generating response: {str(e)}").send()

    except Exception as e:
        error_msg = f"Error processing your question: {str(e)}"
        logger.error(error_msg)
        await cl.Message(content=f"❌ {error_msg}").send()

@cl.on_chat_end
async def on_chat_end():
    """Clean up session data when chat ends."""
    try:
        cl.user_session.clear()
        logger.info("Chat session ended, cleared session data")
    except Exception as e:
        logger.error(f"Error clearing session data: {e}")

if __name__ == "__main__":
    cl.run()
