"""
HuggingFace Adapter - Fetches trending models from HuggingFace Hub.

This is a simplified, stateless adapter for the DevPulseAI reference implementation.
Uses the public HuggingFace API (no authentication required for basic access).
"""

import httpx
from typing import List, Dict, Any


def fetch_huggingface_models(limit: int = 5) -> List[Dict[str, Any]]:
    """
    Fetch trending/popular models from HuggingFace Hub.
    
    Args:
        limit: Maximum number of models to return.
        
    Returns:
        List of signal dictionaries with standardized schema.
    """
    base_url = "https://huggingface.co/api/models"
    params = {
        "sort": "likes",
        "direction": "-1",
        "limit": limit
    }
    
    signals = []
    
    try:
        response = httpx.get(base_url, params=params, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        
        for item in data:
            model_id = item.get("modelId", item.get("id", "unknown"))
            
            # Build description from model metadata
            tags = item.get("tags", [])
            pipeline = item.get("pipeline_tag", "")
            description_parts = []
            
            if pipeline:
                description_parts.append(f"Pipeline: {pipeline}")
            if tags:
                description_parts.append(f"Tags: {', '.join(tags[:5])}")
            
            description_parts.append(f"Downloads: {item.get('downloads', 0):,}")
            description_parts.append(f"Likes: {item.get('likes', 0):,}")
            
            signal = {
                "id": model_id,
                "source": "huggingface",
                "title": f"HF Model: {model_id}",
                "description": " | ".join(description_parts),
                "url": f"https://huggingface.co/{model_id}",
                "metadata": {
                    "downloads": item.get("downloads", 0),
                    "likes": item.get("likes", 0),
                    "pipeline_tag": pipeline,
                    "tags": tags[:10],
                    "author": item.get("author", "")
                }
            }
            signals.append(signal)
            
    except httpx.HTTPError as e:
        print(f"[HuggingFace Adapter] HTTP error: {e}")
    except Exception as e:
        print(f"[HuggingFace Adapter] Error: {e}")
    
    return signals


if __name__ == "__main__":
    # Quick test
    results = fetch_huggingface_models(limit=3)
    for r in results:
        print(f"- {r['title']}: {r['metadata']['likes']} likes")
