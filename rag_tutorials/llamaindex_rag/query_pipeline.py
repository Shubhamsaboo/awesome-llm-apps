import os
from dotenv import load_dotenv

from llama_index.core import VectorStoreIndex
from llama_index.core import StorageContext

from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.huggingface import HuggingFaceInferenceAPIEmbedding
from llama_index.llms.groq import Groq

from qdrant_client import QdrantClient


class QueryAnsweringPipeline:

    def __init__(
        self,
        collection_name="rag_documents"
    ):
        load_dotenv()

        self.collection_name = collection_name

        # Load keys
        self.qdrant_url = os.getenv("QDRANT_URL")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")
        self.hf_api_key = os.getenv("HF_API_KEY")
        self.groq_api_key = os.getenv("GROQ_API_KEY")

        # Initialize components
        self.embed_model = self._init_embedding_model()
        self.vector_store = self._init_vector_store()
        self.llm = self._init_llm()

        # Build query engine
        self.query_engine = self._build_query_engine()


    # ---------------------------------------------------
    # Embedding Model (Must match ingestion model)
    # ---------------------------------------------------
    def _init_embedding_model(self):

        return HuggingFaceInferenceAPIEmbedding(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            token=self.hf_api_key
        )


    # ---------------------------------------------------
    # Qdrant Vector Store
    # ---------------------------------------------------
    def _init_vector_store(self):

        client = QdrantClient(
            url=self.qdrant_url,
            api_key=self.qdrant_api_key
        )

        return QdrantVectorStore(
            client=client,
            collection_name=self.collection_name
        )


    # ---------------------------------------------------
    # Groq LLM
    # ---------------------------------------------------
    def _init_llm(self):

        return Groq(
            model="llama-3.3-70b-versatile",
            api_key=self.groq_api_key,
            temperature=0.2
        )


    # ---------------------------------------------------
    # Build Query Engine
    # ---------------------------------------------------
    def _build_query_engine(self):

        storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store
        )

        index = VectorStoreIndex.from_vector_store(
            vector_store=self.vector_store,
            storage_context=storage_context,
            embed_model=self.embed_model
        )

        return index.as_query_engine(
            llm=self.llm
        )


    # ---------------------------------------------------
    # Ask Question
    # ---------------------------------------------------
    def query(self, question: str):

        response = self.query_engine.query(question)
        return str(response)


# ============================================================
# Example Usage
# ============================================================

if __name__ == "__main__":

    pipeline = QueryAnsweringPipeline()

    while True:
        user_query = input("\nAsk Question (type 'exit' to quit): ")

        if user_query.lower() == "exit":
            break

        answer = pipeline.query(user_query)
        print("\nAnswer:\n", answer)
