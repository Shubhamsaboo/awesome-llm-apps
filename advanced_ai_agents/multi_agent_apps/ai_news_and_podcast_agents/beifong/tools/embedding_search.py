from agno.agent import Agent
import os
import numpy as np
import faiss
from openai import OpenAI
from db.config import get_tracking_db_path, get_faiss_db_path, get_sources_db_path
from db.connection import execute_query
from utils.load_api_keys import load_api_key
import traceback
import json

EMBEDDING_MODEL = "text-embedding-3-small"


def generate_query_embedding(query_text, model=EMBEDDING_MODEL):
    try:
        api_key = load_api_key("OPENAI_API_KEY")
        if not api_key:
            return None, "OpenAI API key not found"
        client = OpenAI(api_key=api_key)
        response = client.embeddings.create(input=query_text, model=model)
        return response.data[0].embedding, None
    except Exception as e:
        return None, str(e)


def load_faiss_index(index_path):
    if not os.path.exists(index_path):
        return None, f"FAISS index not found at {index_path}"
    try:
        return faiss.read_index(index_path), None
    except Exception as e:
        return None, f"Error loading FAISS index: {str(e)}"


def load_id_mapping(mapping_path):
    if not os.path.exists(mapping_path):
        return None, f"ID mapping not found at {mapping_path}"
    try:
        return np.load(mapping_path).tolist(), None
    except Exception as e:
        return None, f"Error loading ID mapping: {str(e)}"


def get_article_details(tracking_db_path, article_ids):
    if not article_ids:
        return []
    placeholders = ",".join(["?"] * len(article_ids))
    query = f"""
    SELECT id, title, url, published_date, summary, source_id, feed_id, content
    FROM crawled_articles
    WHERE id IN ({placeholders})
    """
    return execute_query(tracking_db_path, query, article_ids, fetch=True)


def get_source_names(source_ids):
    if not source_ids:
        return {}
    unique_ids = list(set([src_id for src_id in source_ids if src_id]))
    if not unique_ids:
        return {}
    try:
        sources_db_path = get_sources_db_path()
        check_query = """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='sources'
        """
        table_exists = execute_query(sources_db_path, check_query, fetch=True)
        if not table_exists:
            return {}
        placeholders = ",".join(["?"] * len(unique_ids))
        query = f"""
        SELECT id, name FROM sources
        WHERE id IN ({placeholders})
        """
        results = execute_query(sources_db_path, query, unique_ids, fetch=True)
        return {str(row["id"]): row["name"] for row in results} if results else {}
    except Exception as _:
        return {}


def embedding_search(agent: Agent, prompt: str) -> str:
    """
    Perform a semantic search using embeddings to find articles related to the query on internal articles databse which are crawled from preselected user rss feeds.
    This search uses vector representations to find semantically similar content,
    filtering for only high-quality matches (similarity score ≥ 85%).

    Args:
        agent: The Agno agent instance
        prompt: The search query

    Returns:
        Search results
    """
    print("Embedding Search Input:", prompt)
    tracking_db_path = get_tracking_db_path()
    index_path, mapping_path = get_faiss_db_path()
    top_k = 20
    similarity_threshold = 0.85
    if not os.path.exists(index_path) or not os.path.exists(mapping_path):
        return "Embedding search not available: index files not found. Continuing with other search methods."
    query_embedding, error = generate_query_embedding(prompt)
    if not query_embedding:
        return f"Semantic search unavailable: {error}. Continuing with other search methods."
    query_vector = np.array([query_embedding]).astype(np.float32)
    try:
        faiss_index, error = load_faiss_index(index_path)
        if error:
            return f"Semantic search unavailable: {error}. Continuing with other search methods."
        id_map, error = load_id_mapping(mapping_path)
        if error:
            return f"Semantic search unavailable: {error}. Continuing with other search methods."
        distances, indices = faiss_index.search(query_vector, top_k)
        results_with_metrics = []
        for i, idx in enumerate(indices[0]):
            if idx >= 0 and idx < len(id_map):
                distance = float(distances[0][i])
                similarity = float(np.exp(-distance)) if distance > 0 else 0
                if similarity >= similarity_threshold:
                    article_id = id_map[idx]
                    results_with_metrics.append((idx, distance, similarity, article_id))
        results_with_metrics.sort(key=lambda x: x[2], reverse=True)
        result_article_ids = [item[3] for item in results_with_metrics]
        if not result_article_ids:
            return "No high-quality semantic matches found (threshold: 85%). Continuing with other search methods."
        results = get_article_details(tracking_db_path, result_article_ids)
        source_ids = [result.get("source_id") for result in results if result.get("source_id")]
        source_names = get_source_names(source_ids)
        formatted_results = []
        for i, result in enumerate(results):
            article_id = result.get("id")
            similarity = next((item[2] for item in results_with_metrics if item[3] == article_id), 0)
            similarity_percent = int(similarity * 100)
            source_id = str(result.get("source_id", "unknown"))
            source_name = source_names.get(source_id, source_id)
            formatted_result = {
                "id": article_id,
                "title": f"{result.get('title', 'Untitled')} (Relevance: {similarity_percent}%)",
                "url": result.get("url", "#"),
                "published_date": result.get("published_date"),
                "description": result.get("summary", result.get("content", "")),
                "source_id": source_id,
                "source_name": source_name,
                "similarity": similarity,
                "categories": ["semantic"],
                "is_scrapping_required": False,
            }
            formatted_results.append(formatted_result)
        return f"Found {len(formatted_results)}, results: {json.dumps(formatted_results, indent=2)}"
    except Exception as e:
        traceback.print_exc()
        return f"Error in semantic search: {str(e)}. Continuing with other search methods."