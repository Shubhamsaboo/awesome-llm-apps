import json
import logging
from typing import Dict, Any, List
from sentence_transformers import util
import torch
from backend.llm.llm_provider import LLMProvider

logger = logging.getLogger(__name__)


class TaxonomyBuilder:
    """Agent that builds taxonomy from topics"""
    
    def __init__(self, llm_provider: LLMProvider, prompt_template: str, 
                 mode: str = "agent_based", batch_size: int = 200):
        self.llm = llm_provider
        self.prompt_template = prompt_template
        self.mode = mode  # agent_based or semantic
        self.batch_size = batch_size
        self.categories = {}
        self.topic_to_category = {}
    
    def build_taxonomy(self, topics: List[str], existing_categories: Dict[str, List[str]] = None) -> Dict[str, Any]:
        """
        Build taxonomy from topics.
        
        Args:
            topics: List of unique topic strings
            existing_categories: Optional existing category mappings
            
        Returns:
            Dict with complete taxonomy
        """
        try:
            if existing_categories:
                self.categories = existing_categories.copy()
                # Build reverse mapping
                for category, topic_list in self.categories.items():
                    for topic in topic_list:
                        self.topic_to_category[topic] = category
            
            if self.mode == "agent_based":
                return self._build_agent_based(topics)
            elif self.mode == "semantic":
                return self._build_semantic_based(topics)
            else:
                raise ValueError(f"Unknown mode: {self.mode}")
                
        except Exception as e:
            logger.error(f"Error building taxonomy: {str(e)}")
            raise
    
    def _build_agent_based(self, topics: List[str]) -> Dict[str, Any]:
        """Build taxonomy using agent in iterative batches"""
        logger.info("Building taxonomy using agent-based mode")
        
        unprocessed = list(set(topics))  # Remove duplicates
        
        for batch_idx in range(0, len(unprocessed), self.batch_size):
            batch = unprocessed[batch_idx:batch_idx + self.batch_size]
            
            if batch_idx == 0:
                # First batch: Create initial categories
                logger.info(f"Processing first batch of {len(batch)} topics")
                self._process_batch_create(batch)
            else:
                # Subsequent batches: Match or create new categories
                logger.info(f"Processing batch {batch_idx // self.batch_size + 1} of {len(batch)} topics")
                self._process_batch_match(batch)
        
        return {
            "categories": self.categories,
            "topic_to_category": self.topic_to_category,
            "total_categories": len(self.categories),
            "total_topics": len(self.topic_to_category),
        }
    
    def _process_batch_create(self, topics: List[str]) -> None:
        """Create categories for first batch"""
        try:
            prompt = self.prompt_template.format(
                existing_categories=json.dumps(self.categories, indent=2) or "{}",
                topics_batch=json.dumps(topics)
            )
            
            result = self.llm.generate_json(prompt)
            
            # Handle different response formats
            if isinstance(result, dict):
                result = [result]
            
            if isinstance(result, list):
                for item in result:
                    if isinstance(item, dict):
                        topic = item.get("topic") or item.get("name", "")
                        category = item.get("assigned_category") or item.get("category", "Unknown")
                        if topic:
                            self._add_topic_to_category(topic, category)
                    else:
                        logger.warning(f"Unexpected item type in batch: {type(item)}")
            else:
                logger.error(f"Unexpected result type: {type(result)}, value: {result}")
            
        except Exception as e:
            logger.error(f"Error in batch create: {str(e)}", exc_info=True)
    
    def _process_batch_match(self, topics: List[str]) -> None:
        """Match topics to existing categories or create new ones"""
        try:
            prompt = self.prompt_template.format(
                existing_categories=json.dumps(list(self.categories.keys()), indent=2),
                topics_batch=json.dumps(topics)
            )
            
            result = self.llm.generate_json(prompt)
            
            # Handle different response formats
            if isinstance(result, dict):
                result = [result]
            
            if isinstance(result, list):
                for item in result:
                    if isinstance(item, dict):
                        topic = item.get("topic") or item.get("name", "")
                        category = item.get("assigned_category") or item.get("category", "Unknown")
                        if topic:
                            self._add_topic_to_category(topic, category)
                    else:
                        logger.warning(f"Unexpected item type in batch: {type(item)}")
            else:
                logger.error(f"Unexpected result type: {type(result)}, value: {result}")
            
        except Exception as e:
            logger.error(f"Error in batch match: {str(e)}", exc_info=True)
    
    def _build_semantic_based(self, topics: List[str]) -> Dict[str, Any]:
        """Build taxonomy using semantic similarity"""
        logger.info("Building taxonomy using semantic-based mode")
        
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')
            
            unprocessed = list(set(topics))
            
            # Encode all topics
            embeddings = model.encode(unprocessed)
            
            # Cluster similar topics
            for i, topic in enumerate(unprocessed):
                if topic not in self.topic_to_category:
                    # Find most similar existing category
                    best_category = None
                    best_score = 0.6  # Threshold
                    
                    if self.categories:
                        category_names = list(self.categories.keys())
                        category_embeddings = model.encode(category_names)
                        similarity_scores = util.pytorch_cos_sim(embeddings[i], category_embeddings)[0]
                        
                        best_idx = torch.argmax(similarity_scores).item()
                        best_score = similarity_scores[best_idx].item()
                        
                        if best_score > 0.6:
                            best_category = category_names[best_idx]
                    
                    if best_category:
                        self._add_topic_to_category(topic, best_category)
                    else:
                        # Create new category
                        new_category = self._generate_category_name(topic)
                        self._add_topic_to_category(topic, new_category)
        
        except Exception as e:
            logger.error(f"Error in semantic taxonomy building: {str(e)}")
        
        return {
            "categories": self.categories,
            "topic_to_category": self.topic_to_category,
            "total_categories": len(self.categories),
            "total_topics": len(self.topic_to_category),
        }
    
    def _generate_category_name(self, topic: str) -> str:
        """Generate a category name from topic"""
        # Simple heuristic: use first 3-4 words
        words = topic.split()[:4]
        return " ".join(words)
    
    def _add_topic_to_category(self, topic: str, category: str) -> None:
        """Add topic to a category"""
        if category not in self.categories:
            self.categories[category] = []
        if topic not in self.categories[category]:
            self.categories[category].append(topic)
        self.topic_to_category[topic] = category
