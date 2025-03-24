from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path
import os
from firecrawl import FirecrawlApp
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams
from fastembed import TextEmbedding
from agents import Agent, ModelSettings, function_tool, Runner
from openai import OpenAI, AsyncOpenAI
from openai.helpers import LocalAudioPlayer
import textwrap
import tempfile
import uuid
import numpy as np
from typing import Callable
from urllib.parse import urlparse
from dotenv import load_dotenv
import asyncio
import json
from datetime import datetime
import time

load_dotenv()



def setup_qdrant_collection(qdrant_url: str, qdrant_api_key: str, collection_name: str = "docs_embeddings"):
    print("\n--- Step 1: Setting up Qdrant Collection ---")
    try:
        client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        print("✓ Connected to Qdrant")
        
        embedding_model = TextEmbedding()
        test_embedding = list(embedding_model.embed(["test"]))[0]
        embedding_dim = len(test_embedding)
        print(f"✓ Embedding model ready (dimension: {embedding_dim})")
        
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=embedding_dim, distance=Distance.COSINE)
        )
        print(f"✓ Created collection: {collection_name}")
        
        return client, embedding_model
    
    except Exception as e:
        if "already exists" in str(e):
            print(f"✓ Collection {collection_name} already exists")
            return client, embedding_model
        raise e

def crawl_documentation(firecrawl_api_key: str, url: str, output_dir: Optional[str] = None):
    print("\n--- Step 2: Crawling Documentation ---")
    try:
        firecrawl = FirecrawlApp(api_key=firecrawl_api_key)
        print(f"✓ Initialized Firecrawl")
        
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            print(f"✓ Created output directory: {output_dir}")
        
        print(f"Starting crawl of {url}...")
        
        pages = []
        
        response = firecrawl.crawl_url(
            url,
            params={
                'limit': 5,
                'scrapeOptions': {
                    'formats': ['markdown', 'html']
                }
            }
        )
        
        while True:
            if response.get('status') == 'scraping':
                print(f"Progress: {response.get('completed', 0)}/{response.get('total', 0)} pages")
                print(f"Credits used: {response.get('creditsUsed', 0)}")
            
            for page in response.get('data', []):
                content = page.get('markdown') or page.get('html', '')
                metadata = page.get('metadata', {})
                source_url = metadata.get('sourceURL', '')
                
                if output_dir and content:
                    filename = f"{uuid.uuid4()}.md"
                    filepath = os.path.join(output_dir, filename)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                
                pages.append({
                    "content": content,
                    "url": source_url,
                    "metadata": {
                        "title": metadata.get('title', ''),
                        "description": metadata.get('description', ''),
                        "language": metadata.get('language', 'en'),
                        "crawl_date": datetime.now().isoformat()
                    }
                })
                
                print(f"✓ Processed page: {metadata.get('title', 'Untitled')}")
            
            next_url = response.get('next')
            if not next_url:
                break
                
            response = firecrawl.get(next_url)
            time.sleep(1)
        
        print(f"✓ Crawled {len(pages)} pages")
        return pages
    
    except Exception as e:
        print(f"Error crawling documentation: {str(e)}")
        raise e

def store_embeddings(client: QdrantClient, embedding_model: TextEmbedding, pages: List[Dict], collection_name: str):
    print("\n--- Step 3: Generating and Storing Embeddings ---")
    try:
        for page in pages:
            embedding = list(embedding_model.embed([page["content"]]))[0]
            
            client.upsert(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        id=str(uuid.uuid4()),
                        vector=embedding.tolist(),
                        payload={
                            "content": page["content"],
                            "url": page["url"],
                            **page["metadata"]
                        }
                    )
                ]
            )
            print(f"✓ Stored embedding for: {page['metadata']['title'] or page['url']}")
        
        print(f"✓ Stored {len(pages)} embeddings in Qdrant")
    
    except Exception as e:
        print(f"Error storing embeddings: {str(e)}")
        raise e

def setup_agents(openai_api_key: str):
    print("\n--- Step 4: Setting up OpenAI Agents ---")
    try:
        # Set OpenAI API key in environment
        os.environ["OPENAI_API_KEY"] = openai_api_key
        print("✓ Set OpenAI API key in environment")
        
        processor_agent = Agent(
            name="Documentation Processor",
            instructions="""You are a helpful documentation assistant. Your task is to:
            1. Analyze the provided documentation content
            2. Answer the user's question clearly and concisely
            3. Include relevant examples when available
            4. Cite the source URLs when referencing specific content
            5. Keep responses natural and conversational
            6. Format your response in a way that's easy to speak out loud""",
            model="gpt-4o"
        )
        print("✓ Set up Documentation Processor Agent")

        tts_agent = Agent(
            name="Text-to-Speech Agent",
            instructions="""You are a text-to-speech agent. Your task is to:
            1. Convert the processed documentation response into natural speech
            2. Maintain proper pacing and emphasis
            3. Handle technical terms clearly
            4. Keep the tone professional but friendly
            5. Use appropriate pauses for better comprehension
            6. Ensure the speech is clear and well-articulated""",
            model="gpt-4o-mini-tts"
        )
        print("✓ Set up TTS Agent")
        
        return processor_agent, tts_agent
    
    except Exception as e:
        print(f"Error setting up agents: {str(e)}")
        raise e

async def process_query(
    query: str,
    client: QdrantClient,
    embedding_model: TextEmbedding,
    processor_agent: Agent,
    tts_agent: Agent,
    collection_name: str,
    openai_api_key: str
):
    print("\n--- Step 5: Processing Query ---")
    try:
        # Generate query embedding
        print("Generating query embedding...")
        query_embedding = list(embedding_model.embed([query]))[0]
        print(f"✓ Generated query embedding with shape: {len(query_embedding)}")
        print(f"Vector sample (first 5 elements): {query_embedding[:5]}")
        
        # Try to get collection info first
        print("\nVerifying collection status...")
        try:
            collection_info = client.get_collection(collection_name)
            print(f"Collection exists with {collection_info.points_count} points")
        except Exception as e:
            print(f"Warning: Could not get collection info: {str(e)}")
        
        # Attempt search with query parameter (confirmed working)
        print("\nAttempting vector search...")
        try:
            print("Querying with 'query' parameter...")
            search_response = client.query_points(
                collection_name=collection_name,
                query=query_embedding.tolist(),
                limit=3,
                with_payload=True
            )
            print("✓ Query successful")
            
            # Debug search response
            print("\nSearch Response Debug:")
            print(f"Response type: {type(search_response)}")
            
            # Get points from the response
            if hasattr(search_response, 'points'):
                search_results = search_response.points
            else:
                search_results = []
                
            print(f"\n✓ Found {len(search_results)} relevant documents")
            
            if not search_results:
                raise Exception("No relevant documents found in the vector database")
            
            # Build context from search results
            context = "Based on the following documentation:\n\n"
            for result in search_results:
                payload = result.payload
                if not payload:
                    print(f"Warning: Result missing payload")
                    continue
                    
                url = payload.get('url', 'Unknown URL')
                content = payload.get('content', '')
                score = getattr(result, 'score', 'N/A')
                
                print(f"\nDocument from {url}")
                print(f"Relevance score: {score}")
                context += f"From {url}:\n{content}\n\n"
            
            context += f"\nUser Question: {query}\n\n"
            context += "Please provide a clear, concise answer that can be easily spoken out loud."
            
            # Process response with agents
            print("\nProcessing with Documentation Agent...")
            processor_result = await Runner.run(processor_agent, context)
            processor_response = processor_result.final_output
            print("✓ Generated text response")
            
            print("\nProcessing with TTS Agent...")
            tts_result = await Runner.run(tts_agent, processor_response)
            tts_response = tts_result.final_output
            print("✓ Generated TTS instructions")
            
            # Generate and play audio
            print("\nGenerating audio response...")
            async_openai = AsyncOpenAI(api_key=openai_api_key)
            async with async_openai.audio.speech.with_streaming_response.create(
                model="tts-1",
                voice="alloy",
                input=processor_response,
                instructions=tts_response,
                response_format="pcm"
            ) as response:
                print("✓ Streaming audio response")
                await LocalAudioPlayer().play(response)
                
            return {
                "status": "success",
                "text_response": processor_response,
                "tts_instructions": tts_response,
                "sources": [r.payload.get("url", "Unknown URL") for r in search_results if r.payload],
                "query_details": {
                    "vector_size": len(query_embedding),
                    "results_found": len(search_results),
                    "collection_name": collection_name
                }
            }
            
        except Exception as e:
            print(f"Error during vector search: {str(e)}")
            print("Full error details:")
            import traceback
            traceback.print_exc()
            raise
    
    except Exception as e:
        print(f"\nError processing query: {str(e)}")
        print("Full error details:")
        import traceback
        traceback.print_exc()
        
        return {
            "status": "error",
            "error": str(e),
            "error_details": traceback.format_exc(),
            "query": query
        }

async def main():
    try:
        env_vars = get_env_vars()
        print("✓ Loaded environment variables")
        
        client, embedding_model = setup_qdrant_collection(
            env_vars["QDRANT_URL"],
            env_vars["QDRANT_API_KEY"]
        )
        
        pages = crawl_documentation(
            env_vars["FIRECRAWL_API_KEY"],
            "https://docs.agentmail.to/api-reference",
            "crawled_docs"
        )
        
        store_embeddings(client, embedding_model, pages, "docs_embeddings")
        
        processor_agent, tts_agent = setup_agents(env_vars["OPENAI_API_KEY"])
        
        query = "What are the required parameters for List Threads API of Agent Mail?"
        result = await process_query(
            query,
            client,
            embedding_model,
            processor_agent,
            tts_agent,
            "docs_embeddings",
            env_vars["OPENAI_API_KEY"]
        )
        
        print("\n--- Final Results ---")
        print(json.dumps(result, indent=2))
        
    except ValueError as e:
        print(f"\nConfiguration Error: {str(e)}")
        print("\nPlease ensure your .env file contains all required variables:")
        print("FIRECRAWL_API_KEY=your_key")
        print("QDRANT_URL=your_qdrant_url")
        print("QDRANT_API_KEY=your_qdrant_key")
        print("OPENAI_API_KEY=your_openai_key")
    except Exception as e:
        print(f"\nError: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())