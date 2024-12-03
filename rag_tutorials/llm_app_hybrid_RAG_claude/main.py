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

@cl.on_chat_start
async def start() -> None:
    try:
        logger.info("Chat session started")
        cl.user_session.set("chat_history", [])

        # Helper function to validate and get API key - so that if the user enters the wrong key, they can try again
        async def get_valid_api_key(key_type: str, validation_prefix: tuple) -> str:
            while True:
                key_response = await cl.AskUserMessage(
                    content=f"Please enter your {key_type} API key:",
                    timeout=180
                ).send()

                if not key_response or 'output' not in key_response:
                    await cl.Message(content=f"❌ {key_type} API key is required").send()
                    continue

                key_value = key_response['output'].strip()
                if not any(key_value.startswith(prefix) for prefix in validation_prefix):
                    await cl.Message(
                        content=f"❌ Invalid {key_type} API key format. Please try again."
                    ).send()
                    continue
                
                return key_value

        # this is the helper function to validate and get DB URL, so that if the user enters the wrong URL, they can try again
        async def get_valid_db_url() -> str:
            valid_db_prefixes = ('postgresql://', 'mysql://', 'sqlite:///')
            while True:
                db_url_response = await cl.AskUserMessage(
                    content="Please enter your Database URL:\nSupported formats:\n- PostgreSQL: postgresql://user:pass@host:port/db\n- MySQL: mysql://user:pass@host:port/db\n- SQLite: sqlite:///path/to/db.sqlite",
                    timeout=180
                ).send()

                if not db_url_response or 'output' not in db_url_response:
                    await cl.Message(content="❌ Database URL is required").send()
                    continue

                db_url_value = db_url_response['output'].strip()
                if not any(db_url_value.startswith(prefix) for prefix in valid_db_prefixes):
                    await cl.Message(
                        content="❌ Invalid database URL format. Must start with one of:\n- postgresql://\n- mysql://\n- sqlite://\nPlease try again."
                    ).send()
                    continue
                
                return db_url_value

        # Get and validate API keys with retry
        openai_key = await get_valid_api_key("OpenAI", ("sk-", "sk-proj-"))
        anthropic_key = await get_valid_api_key("Anthropic", ("sk-ant-",))
        cohere_key = await get_valid_api_key("Cohere", ("",))  # Cohere keys don't have a specific prefix
        
        # Get and validate DB URL with retry
        db_url = await get_valid_db_url()

        # Store validated values in user_env
        user_env = {
            "OPENAI_API_KEY": openai_key,
            "ANTHROPIC_API_KEY": anthropic_key,
            "COHERE_API_KEY": cohere_key,
            "DB_URL": db_url
        }

        # Store in user session
        cl.user_session.set("env", user_env)
        logger.info("API keys stored in user session")

        # Initialize RAGLite config with retry
        while True:
            try:
                global my_config
                my_config = initialize_config(user_env)
                await cl.Message(content="✅ Successfully configured with your API keys!").send()
                break
            except Exception as e:
                logger.error(f"Configuration error: {str(e)}")
                await cl.Message(content=f"❌ Error configuring with provided keys: {str(e)}\nPlease check your credentials and try again.").send()
                # Retry getting all credentials
                openai_key = await get_valid_api_key("OpenAI", ("sk-", "sk-proj-"))
                anthropic_key = await get_valid_api_key("Anthropic", ("sk-ant-",))
                cohere_key = await get_valid_api_key("Cohere", ("",))
                db_url = await get_valid_db_url()
                user_env.update({
                    "OPENAI_API_KEY": openai_key,
                    "ANTHROPIC_API_KEY": anthropic_key,
                    "COHERE_API_KEY": cohere_key,
                    "DB_URL": db_url
                })
                cl.user_session.set("env", user_env)

        async def get_valid_documents() -> List[cl.File]:
            while True:
                files = await cl.AskFileMessage(
                    content="Please upload one or more PDF documents to begin!",
                    accept=["application/pdf"],
                    max_size_mb=20,
                    max_files=5
                ).send()

                if not files:
                    await cl.Message(content="❌ No files were uploaded. Please try again.").send()
                    continue
                
                return files

        # Process documents with retry for each file
        async def process_documents(files: List[cl.File]) -> bool:
            """Process uploaded documents with retry functionality for failed files."""
            processed_files = set()
            files_to_process = files.copy()
            
            while files_to_process:
                current_file = files_to_process.pop(0)
                
                if current_file.name in processed_files:
                    continue
                    
                logger.info(f"Processing file: {current_file.name}")
                step = cl.Step(name=f"Processing {current_file.name}...")
                async with step:  # Use step as context manager
                    try:
                        process_document(current_file.path)
                        processed_files.add(current_file.name)
                        await cl.Message(
                            content=f"✅ The Document '{current_file.name}' is processed successfully."
                        ).send()
                    except Exception as e:
                        logger.error(f"Failed to process '{current_file.name}': {str(e)}")
                        error_message = f"❌ Failed to process '{current_file.name}': {str(e)}"
                        
                        # Ask user if they want to retry this file
                        retry = await cl.AskUserMessage(
                            content=f"{error_message}\nWould you like to try uploading this file again? (yes/no)",
                            timeout=180
                        ).send()
                        
                        if retry and retry['output'].lower().strip() == 'yes':
                            new_file = await cl.AskFileMessage(
                                content=f"Please upload '{current_file.name}' again:",
                                accept=["application/pdf"],
                                max_size_mb=20,
                                max_files=1
                            ).send()
                            
                            if new_file:
                                files_to_process.append(new_file[0])
                
                # Ensure step is completed
                await step.end()
            
            if not processed_files:
                await cl.Message(content="❌ No documents were processed successfully. Please try uploading new documents.").send()
                return False
            
            # Send final success message and return to chat
            final_msg = cl.Message(content="✅ Document processing completed. You can now ask questions!")
            await final_msg.send()
            return True

        # Main document processing loop
        while True:
            files = await get_valid_documents()
            if await process_documents(files):
                break
            
            # Ask if user wants to try uploading different documents
            retry = await cl.AskUserMessage(
                content="Would you like to try uploading different documents? (yes/no)",
                timeout=180
            ).send()
            
            if not retry or retry['output'].lower().strip() != 'yes':
                await cl.Message(content="❌ Stopping due to document processing failures.").send()
                return

    except Exception as e:
        logger.error(f"Error in chat start: {str(e)}")
        await cl.Message(content=f"Error initializing chat: {str(e)}").send()

@cl.on_message
async def message_handler(message: cl.Message) -> None:
    try:
        msg = cl.Message(content="Thinking...")
        await msg.send()
        
        query = message.content.strip()
        chat_history = cl.user_session.get("chat_history", [])
        
        # Search for relevant chunks using global config
        reranked_chunks = perform_search(query)
        
        if reranked_chunks:
            logger.info("Using RAG for response generation")
            try:
                # Convert chat history to proper format for RAG
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
                
                await msg.send()
                
            except Exception as e:
                logger.error(f"RAG error: {str(e)}")
                # If RAG fails, fall back to general Claude
                await handle_fallback(query, msg)
                return
                
        else:
            logger.info("No relevant chunks found, falling back to general Claude response")
            await handle_fallback(query, msg)
            return
            
        # Update chat history
        chat_history.append((query, full_response))
        cl.user_session.set("chat_history", chat_history)
            
    except Exception as e:
        error_msg = f"Error processing your question: {str(e)}"
        logger.error(error_msg)
        await msg.send(content=error_msg)  # Use send instead of update

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
