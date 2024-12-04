import os
import logging
import chainlit as cl
from raglite import RAGLiteConfig, insert_document, hybrid_search, retrieve_chunks, rerank_chunks, rag
from rerankers import Reranker
from typing import List
from pathlib import Path
from chainlit.action import Action
from chainlit.input_widget import TextInput
from chainlit import AskUserMessage
import anthropic

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize global config variable
my_config = None

# Define RAG system prompt
RAG_SYSTEM_PROMPT = """
You are a friendly and knowledgeable assistant that provides complete and insightful answers.
Answer the user's question using only the context below.
When responding, you MUST NOT reference the existence of the context, directly or indirectly.
Instead, you MUST treat the context as if its contents are entirely part of your working memory.
""".strip()

def initialize_config(user_env: dict) -> RAGLiteConfig:
    """Initialize RAGLite configuration with user-provided keys."""
    return RAGLiteConfig(
        db_url=user_env["DB_URL"],
        llm="claude-3-opus-20240229",
        embedder="text-embedding-3-large",
        embedder_normalize=True,
        chunk_max_size=2000,
        embedder_sentence_window_size=2,
        reranker=Reranker(
            "cohere",
            api_key=user_env["COHERE_API_KEY"],
            lang="en"
        )
    )

def process_document(file_path: str) -> None:
    """Process and embed a document into the database."""
    logger.info(f"Starting to process document: {file_path}")
    try:
        import time
        start_time = time.time()

        # Insert document into PostgreSQL database
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
        # First try hybrid search in the database
        chunk_ids, scores = hybrid_search(query, num_results=10, config=my_config)
        logger.debug(f"Found {len(chunk_ids)} chunks with scores: {scores}")

        if not chunk_ids:
            logger.info("No relevant chunks found in database")
            return []

        # Retrieve and rerank chunks
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
        def validate_key(key: str, key_type: str, valid_prefixes: tuple) -> bool:
            if not key:
                raise ValueError(f"{key_type} API key is required")
            if valid_prefixes and not any(key.startswith(prefix) for prefix in valid_prefixes):
                raise ValueError(f"Invalid {key_type} API key format")
            return True
              # Validate DB URL
        def validate_db_url(url: str) -> bool:
            valid_prefixes = ('postgresql://', 'mysql://', 'sqlite:///')
            if not url:
                raise ValueError("Database URL is required")
            if not any(url.startswith(prefix) for prefix in valid_prefixes):
                raise ValueError("Invalid database URL format")
            return True

        validate_key(settings["OpenAIApiKey"], "OpenAI", ("sk-", "sk-proj-"))
        validate_key(settings["AnthropicApiKey"], "Anthropic", ("sk-ant-",))
        validate_key(settings["CohereApiKey"], "Cohere", tuple())
        validate_db_url(settings["DBUrl"])
        # Store validated values in user_env
        user_env = {
            "OPENAI_API_KEY": settings["OpenAIApiKey"],
            "ANTHROPIC_API_KEY": settings["AnthropicApiKey"],
            "COHERE_API_KEY": settings["CohereApiKey"],
            "DB_URL": settings["DBUrl"]
        }

        global my_config
        my_config = initialize_config(user_env)
        cl.user_session.set("env", user_env)
        
        await cl.Message(content="✅ Successfully configured with your API keys!").send()

        # Ask for file upload with proper configuration
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
    """Initialize chat and request API keys."""
    try:
        logger.info("Chat session started")
        cl.user_session.set("chat_history", [])
        
        # Show settings form first
        await cl.ChatSettings([
            TextInput(
                id="OpenAIApiKey",
                label="OpenAI API Key",
                initial="",
                placeholder="Enter your OpenAI API Key (starts with 'sk-')"
            ),
            TextInput(
                id="AnthropicApiKey",
                label="Anthropic API Key",
                initial="",
                placeholder="Enter your Anthropic API Key (starts with 'sk-ant-')"
            ),
            TextInput(
                id="CohereApiKey",
                label="Cohere API Key",
                initial="",
                placeholder="Enter your Cohere API Key"
            ),
            TextInput(
                id="DBUrl",
                label="Database URL",
                initial="",
                placeholder="Enter your Database URL (e.g., postgresql://user:pass@host:port/db)"
            ),
        ]).send()

    except Exception as e:
        logger.error(f"Error in chat start: {str(e)}")
        await cl.Message(content=f"Error initializing chat: {str(e)}").send()

@cl.on_message
async def message_handler(message: cl.Message) -> None:
    """Handle user queries using RAG."""
    try:
        # Check if documents are loaded
        if not cl.user_session.get("documents_loaded"):
            await cl.Message(content="❌ Please upload and process documents first!").send()
            return

        if not my_config:
            await cl.Message(content="❌ Please configure your API keys first!").send()
            return

        # Create message for streaming
        msg = cl.Message(content="")
        await msg.send()

        query = message.content.strip()
        logger.info(f"Processing query: {query}")

        # Search for relevant chunks
        reranked_chunks = perform_search(query)

        if not reranked_chunks:
            logger.info("No relevant chunks found, falling back to general Claude response")
            await handle_fallback(query, msg)
            return

        # Use RAG for response generation
        try:
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
                full_response += chunk
                await msg.stream_token(chunk)

            # Update chat history
            chat_history.append((query, full_response))
            cl.user_session.set("chat_history", chat_history)

        except Exception as e:
            logger.error(f"RAG error: {str(e)}")
            await handle_fallback(query, msg)

    except Exception as e:
        error_msg = f"Error processing your question: {str(e)}"
        logger.error(error_msg)
        await cl.Message(content=error_msg).send()

async def handle_fallback(query: str, msg: cl.Message) -> None:
    """Handle fallback to Claude when RAG is not available or fails."""
    try:
        user_env = cl.user_session.get("env")
        client = anthropic.Anthropic(api_key=user_env["ANTHROPIC_API_KEY"])

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": query}
            ]
        )

        full_response = response.content[0].text
        await msg.send(content=full_response)

        # Update chat history
        chat_history = cl.user_session.get("chat_history", [])
        chat_history.append((query, full_response))
        cl.user_session.set("chat_history", chat_history)

    except Exception as e:
        error_msg = f"Fallback error: {str(e)}"
        logger.error(error_msg)
        await msg.send(content=error_msg)

if __name__ == "__main__":
    cl.run()