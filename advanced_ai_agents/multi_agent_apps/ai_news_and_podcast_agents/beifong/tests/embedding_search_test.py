import argparse
import os
import numpy as np
import faiss
from openai import OpenAI
from db.config import get_tracking_db_path
from db.connection import execute_query
from utils.load_api_keys import load_api_key
from db.config import get_faiss_db_path

EMBEDDING_MODEL = "text-embedding-3-small"
FAISS_INDEX_PATH, FAIS_MAPPING_PATH = get_faiss_db_path()


def generate_query_embedding(client, query_text, model=EMBEDDING_MODEL):
    try:
        response = client.embeddings.create(input=query_text, model=model)
        return response.data[0].embedding, model
    except Exception as e:
        print(f"Error generating query embedding: {str(e)}")
        return None, None


def load_faiss_index(index_path=FAISS_INDEX_PATH):
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"FAISS index not found at {index_path}")
    return faiss.read_index(index_path)


def load_id_mapping(mapping_path=FAIS_MAPPING_PATH):
    if not os.path.exists(mapping_path):
        raise FileNotFoundError(f"ID mapping not found at {mapping_path}")
    return np.load(mapping_path).tolist()


def get_article_details(tracking_db_path, article_ids):
    if not article_ids:
        return []
    placeholders = ",".join(["?"] * len(article_ids))
    query = f"""
    SELECT id, title, url, published_date, summary 
    FROM crawled_articles
    WHERE id IN ({placeholders})
    """
    return execute_query(tracking_db_path, query, article_ids, fetch=True)


def search_articles(
    query_text,
    tracking_db_path=None,
    openai_api_key=None,
    index_path="databases/faiss/article_index.faiss",
    mapping_path="databases/faiss/article_id_map.npy",
    top_k=5,
    search_params=None,
):
    if tracking_db_path is None:
        tracking_db_path = get_tracking_db_path()
    if openai_api_key is None:
        openai_api_key = load_api_key()
        if not openai_api_key:
            raise ValueError("OpenAI API key is required")
    client = OpenAI(api_key=openai_api_key)
    query_embedding, _ = generate_query_embedding(client, query_text)
    if not query_embedding:
        raise ValueError("Failed to generate query embedding")
    query_vector = np.array([query_embedding]).astype(np.float32)
    try:
        faiss_index = load_faiss_index(index_path)
        id_map = load_id_mapping(mapping_path)
        if search_params:
            if isinstance(faiss_index, faiss.IndexIVF) and "nprobe" in search_params:
                faiss_index.nprobe = search_params["nprobe"]
                print(f"Set nprobe to {faiss_index.nprobe}")
            if hasattr(faiss_index, "hnsw") and "ef" in search_params:
                faiss_index.hnsw.efSearch = search_params["ef"]
                print(f"Set efSearch to {faiss_index.hnsw.efSearch}")
        index_type = "unknown"
        if isinstance(faiss_index, faiss.IndexFlatL2):
            index_type = "flat"
        elif isinstance(faiss_index, faiss.IndexIVFFlat):
            index_type = "ivfflat"
            print(f"Using IVF index with nprobe = {faiss_index.nprobe}")
        elif isinstance(faiss_index, faiss.IndexIVFPQ):
            index_type = "ivfpq"
            print(f"Using IVF-PQ index with nprobe = {faiss_index.nprobe}")
        elif hasattr(faiss_index, "hnsw"):
            index_type = "hnsw"
            print(f"Using HNSW index with efSearch = {faiss_index.hnsw.efSearch}")
        print(f"Searching {index_type} FAISS index with {len(id_map)} articles...")
        distances, indices = faiss_index.search(query_vector, top_k)
        result_article_ids = [id_map[idx] for idx in indices[0] if idx < len(id_map)]
        results = get_article_details(tracking_db_path, result_article_ids)
        for i, result in enumerate(results):
            distance = float(distances[0][i])
            similarity = float(np.exp(-distance))
            result["distance"] = distance
            result["similarity"] = similarity
            result["score"] = similarity
        return results
    except Exception as e:
        print(f"Error during search: {str(e)}")
        import traceback

        traceback.print_exc()
        return []


def print_search_results(results):
    if not results:
        print("No results found.")
        return
    print(f"\nFound {len(results)} results:\n")
    for i, result in enumerate(results):
        similarity_pct = result.get("similarity", 0) * 100
        print(f"{i + 1}. {result['title']}")
        print(f"   Relevance: {similarity_pct:.1f}%")
        if "distance" in result:
            print(f"   Vector distance: {result['distance']:.4f}")
        print(f"   Published: {result['published_date']}")
        print(f"   URL: {result['url']}")
        if len(result["summary"]) > 150:
            print(f"   Summary: {result['summary'][:150]}...")
        else:
            print(f"   Summary: {result['summary']}")
        print()


def parse_arguments():
    parser = argparse.ArgumentParser(description="Search for articles using FAISS")
    parser.add_argument(
        "query",
        help="Search query text",
    )
    parser.add_argument(
        "--api_key",
        help="OpenAI API Key (overrides environment variables)",
    )
    parser.add_argument(
        "--top_k",
        type=int,
        default=5,
        help="Number of results to return",
    )
    parser.add_argument(
        "--nprobe",
        type=int,
        help="Number of clusters to search (for IVF indexes)",
    )
    parser.add_argument(
        "--ef",
        type=int,
        help="Search depth (for HNSW indexes)",
    )
    parser.add_argument(
        "--index_path",
        default=FAISS_INDEX_PATH,
        help="Path to the FAISS index file",
    )
    parser.add_argument(
        "--mapping_path",
        default=FAIS_MAPPING_PATH,
        help="Path to the ID mapping file",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    api_key = args.api_key or load_api_key()
    if not api_key:
        print("Error: No OpenAI API key provided. Please provide via --api_key or set OPENAI_API_KEY in .env file")
        exit(1)
    search_params = {}
    if args.nprobe:
        search_params["nprobe"] = args.nprobe
    if args.ef:
        search_params["ef"] = args.ef
    try:
        results = search_articles(
            query_text=args.query,
            openai_api_key=api_key,
            top_k=args.top_k,
            index_path=args.index_path,
            mapping_path=args.mapping_path,
            search_params=search_params,
        )
        print_search_results(results)
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback

        traceback.print_exc()
        exit(1)
