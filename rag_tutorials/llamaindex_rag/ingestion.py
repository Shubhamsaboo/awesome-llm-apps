import os
from dotenv import load_dotenv

from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext
)

from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.huggingface import HuggingFaceInferenceAPIEmbedding

from qdrant_client import QdrantClient


class DocumentIngestionPipeline:

    def __init__(
        self,
        data_dir="data",
        collection_name="rag_documents"
    ):
        load_dotenv()

        self.data_dir = data_dir
        self.collection_name = collection_name

        # Load environment variables
        self.qdrant_url = os.getenv("QDRANT_URL")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")
        self.hf_api_key = os.getenv("HF_API_KEY")

        # Initialize components
        self.embed_model = self._init_embedding_model()
        self.vector_store = self._init_vector_store()


    # ---------------------------------------------------
    # Embedding Model
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

        vector_store = QdrantVectorStore(
            client=client,
            collection_name=self.collection_name
        )

        return vector_store


    # ---------------------------------------------------
    # Load Documents
    # ---------------------------------------------------
    def load_documents(self):

        print("Loading documents...")
        documents = SimpleDirectoryReader(self.data_dir).load_data()

        return documents


    # ---------------------------------------------------
    # Run Ingestion
    # ---------------------------------------------------
    def run(self):

        documents = self.load_documents()

        storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store
        )

        print("Creating index and storing vectors...")

        VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            embed_model=self.embed_model
        )

        print("✅ Ingestion Completed!")


# ============================================================
# Run Pipeline
# ============================================================

if __name__ == "__main__":

    pipeline = DocumentIngestionPipeline(
        data_dir="data",
        collection_name="rag_documents"
    )

    pipeline.run()
