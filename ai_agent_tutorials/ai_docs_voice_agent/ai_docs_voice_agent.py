from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path
import os
from firecrawl import FirecrawlApp
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams
from agents import Agent, ModelSettings, function_tool
from agents.voice.model import TTSModel, TTSModelSettings
from agents.voice.models.openai_tts import OpenAITTSModel
from openai import OpenAI
import textwrap
import tempfile
import uuid
import numpy as np
from typing import Callable
from urllib.parse import urlparse

@dataclass
class VoiceAgentConfig:
    """Configuration for the Voice AI Agent."""
    firecrawl_api_key: str
    qdrant_url: str
    qdrant_api_key: str
    openai_api_key: str
    collection_name: str = "docs_embeddings"
    tts_voice: str = "alloy"  # Default voice from OpenAI TTS

    def __post_init__(self):
        """Validate URLs after initialization."""
        # Validate Qdrant URL
        parsed = urlparse(self.qdrant_url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Invalid Qdrant URL. Must include scheme (http:// or https://)")

class VoiceAgent:
    """A voice-enabled AI agent for documentation support."""
    
    def __init__(self, config: VoiceAgentConfig):
        """Initialize the Voice Agent with configuration."""
        self.config = config
        self.firecrawl = FirecrawlApp(api_key=config.firecrawl_api_key)
        self.qdrant = QdrantClient(
            url=config.qdrant_url,
            api_key=config.qdrant_api_key
        )
        self.openai = OpenAI(api_key=config.openai_api_key)
        self._setup_collection()
        self._setup_tts()

    def _setup_tts(self) -> None:
        """Set up the TTS model with OpenAI's voice settings."""
        tts_settings = TTSModelSettings(
            voice=self.config.tts_voice,
            buffer_size=120,
            dtype=np.int16,
            instructions="You will receive partial sentences. Do not complete the sentence just read out the text.",
            speed=1.0  # Normal speed
        )
        self.tts_model = OpenAITTSModel(
            model="tts-1",
            settings=tts_settings,
            openai_api_key=self.config.openai_api_key
        )

    def _setup_collection(self) -> None:
        """Set up the Qdrant collection for document embeddings."""
        try:
            self.qdrant.create_collection(
                collection_name=self.config.collection_name,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
            )
        except Exception as e:
            print(f"Collection might already exist: {e}")

    @function_tool
    def crawl_documentation(self, url: str) -> str:
        """Crawl documentation website and store in Qdrant."""
        try:
            # Crawl the documentation
            crawl_status = self.firecrawl.crawl_url(
                url,
                params={
                    'limit': 100,
                    'scrapeOptions': {'formats': ['markdown', 'html']}
                },
                poll_interval=30
            )
            
            # Process and store crawled content
            for page in crawl_status.pages:
                content = page.content
                # Generate embedding
                embedding = self.openai.embeddings.create(
                    model="text-embedding-ada-002",
                    input=content
                ).data[0].embedding
                
                # Store in Qdrant
                self.qdrant.upsert(
                    collection_name=self.config.collection_name,
                    points=[
                        models.PointStruct(
                            id=str(uuid.uuid4()),
                            vector=embedding,
                            payload={
                                "content": content,
                                "url": page.url
                            }
                        )
                    ]
                )
            
            return "Documentation successfully crawled and stored"
        except Exception as e:
            return f"Error crawling documentation: {str(e)}"

    @function_tool
    def retrieve_relevant_content(self, query: str) -> str:
        """Retrieve relevant content from Qdrant based on user query."""
        try:
            # Generate query embedding
            query_embedding = self.openai.embeddings.create(
                model="text-embedding-ada-002",
                input=query
            ).data[0].embedding
            
            # Search in Qdrant
            search_result = self.qdrant.search(
                collection_name=self.config.collection_name,
                query_vector=query_embedding,
                limit=3
            )
            
            # Combine relevant content
            relevant_content = "\n\n".join(
                [hit.payload["content"] for hit in search_result]
            )
            
            return relevant_content
        except Exception as e:
            return f"Error retrieving content: {str(e)}"

    @function_tool
    def generate_voice_response(self, text: str) -> str:
        """Generate voice response using OpenAI's TTS model."""
        try:
            # Create temporary file for audio
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                # Generate speech using OpenAI TTS
                audio_data = self.tts_model.run(text)
                
                # Save the audio data
                temp_file.write(audio_data)
                temp_file.flush()
                return temp_file.name
        except Exception as e:
            return f"Error generating voice response: {str(e)}"

    def process_query(self, query: str) -> Dict[str, str]:
        """Process user query and return both text and voice response."""
        # Create agent for processing
        agent = Agent(
            name="Documentation Support Agent",
            instructions="You are a helpful documentation support agent. Provide clear and concise answers based on the documentation.",
            model="gpt-4o",
            tools=[self.retrieve_relevant_content, self.generate_voice_response]
        )
        
        # Get relevant content
        relevant_content = self.retrieve_relevant_content(query)
        
        # Generate response using agent
        response = agent.run(
            f"Based on this documentation content: {relevant_content}\n\nUser question: {query}"
        )
        
        # Generate voice response
        voice_file = self.generate_voice_response(response)
        
        return {
            "text_response": response,
            "voice_file": voice_file
        }

def main():
    """Example usage of the VoiceAgent."""
    config = VoiceAgentConfig(
        firecrawl_api_key="fc-YOUR_API_KEY",
        qdrant_url="https://your-qdrant-url:6333",  # Make sure to include https://
        qdrant_api_key="YOUR_QDRANT_API_KEY",
        openai_api_key="YOUR_OPENAI_API_KEY",
        tts_voice="alloy"  # You can choose from: alloy, echo, fable, onyx, nova, shimmer
    )
    
    try:
        agent = VoiceAgent(config)
        
        # Example: Crawl documentation
        docs_url = "https://example.com/docs"
        agent.crawl_documentation(docs_url)
        
        # Example: Process a query
        query = "How do I install the package?"
        result = agent.process_query(query)
        
        print(f"Text Response: {result['text_response']}")
        print(f"Voice Response saved to: {result['voice_file']}")
    except Exception as e:
        print(f"Error: {str(e)}")
        print("Please check your API keys and URLs are correct.")

if __name__ == "__main__":
    main()
