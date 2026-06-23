import json
import logging
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class ReviewClassifier:
    """Classifies reviews with category IDs based on topic mappings"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
    
    def classify_reviews(self, reviews: List[Dict[str, Any]], 
                        topics_extracted: List[Dict[str, Any]],
                        category_name_to_id: Dict[str, int],
                        app_name: str) -> str:
        """
        Classify reviews and assign category IDs.
        
        Args:
            reviews: List of original reviews
            topics_extracted: List of extracted topics with review IDs
            category_name_to_id: Mapping of category names to IDs
            app_name: Name of the app
            
        Returns:
            Path to classified reviews file
        """
        try:
            # Create mapping from review ID to category ID
            review_to_category = {}
            
            for topic_item in topics_extracted:
                if isinstance(topic_item, dict):
                    review_id = topic_item.get("review_id")
                    topic = topic_item.get("topic", "")
                    
                    # Find which category this topic belongs to
                    for category_name, category_id in category_name_to_id.items():
                        # Simple heuristic: check if topic contains category name words
                        if self._topic_matches_category(topic, category_name):
                            if review_id not in review_to_category:
                                review_to_category[review_id] = category_id
                            break
            
            # Assign category IDs to reviews
            classified_reviews = []
            for review in reviews:
                review_copy = review.copy()
                review_id = review_copy.get("id") or review_copy.get("review_id")
                
                if review_id in review_to_category:
                    review_copy["category_id"] = review_to_category[review_id]
                else:
                    review_copy["category_id"] = None  # Uncategorized
                
                classified_reviews.append(review_copy)
            
            # Save classified reviews
            output_file = self.data_dir / f"{app_name}_classified_reviews.jsonl"
            self._save_classified_reviews(classified_reviews, output_file)
            
            logger.info(f"Classified {len(classified_reviews)} reviews")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Error classifying reviews: {str(e)}")
            raise
    
    def _topic_matches_category(self, topic: str, category: str) -> bool:
        """Check if topic matches category"""
        # Simple substring matching - can be improved
        topic_lower = topic.lower()
        category_lower = category.lower()
        
        # Check if any significant words match
        topic_words = set(topic_lower.split())
        category_words = set(category_lower.split())
        
        # Remove common words
        common_words = {'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                       'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
                       'could', 'may', 'might', 'can', 'must', 'not', 'no', 'yes'}
        
        topic_words = topic_words - common_words
        category_words = category_words - common_words
        
        # Check overlap
        overlap = topic_words & category_words
        return len(overlap) > 0 or category_lower in topic_lower
    
    def _save_classified_reviews(self, reviews: List[Dict[str, Any]], filepath: Path) -> None:
        """Save classified reviews to JSONL"""
        with open(filepath, "w", encoding="utf-8") as f:
            for review in reviews:
                f.write(json.dumps(review) + "\n")
