import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)


class DataValidator:
    """Validate and filter review data"""
    
    REQUIRED_FIELDS = ["content", "at", "score"]
    MIN_REVIEW_LENGTH = 5
    
    @classmethod
    def validate_review(cls, review: Dict[str, Any], required_fields: List[str] = None) -> bool:
        """
        Validate if a review has all required fields.
        
        Args:
            review: Review dictionary
            required_fields: List of required field names
            
        Returns:
            True if valid, False otherwise
        """
        if required_fields is None:
            required_fields = cls.REQUIRED_FIELDS
        
        # Check all required fields exist and are not empty
        for field in required_fields:
            if field not in review or not review[field]:
                return False
        
        # Check minimum review length
        content = review.get("content", "")
        if isinstance(content, str) and len(content.strip()) < cls.MIN_REVIEW_LENGTH:
            return False
        
        return True
    
    @classmethod
    def split_data(cls, reviews: List[Dict[str, Any]], 
                   required_fields: List[str] = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Split reviews into complete and incomplete.
        
        Args:
            reviews: List of review dictionaries
            required_fields: List of required field names
            
        Returns:
            Tuple of (complete_reviews, incomplete_reviews)
        """
        if required_fields is None:
            required_fields = cls.REQUIRED_FIELDS
        
        complete = []
        incomplete = []
        
        for review in reviews:
            if cls.validate_review(review, required_fields):
                complete.append(review)
            else:
                incomplete.append(review)
        
        logger.info(f"Data split: {len(complete)} complete, {len(incomplete)} incomplete")
        return complete, incomplete
    
    @classmethod
    def get_sample(cls, reviews: List[Dict[str, Any]], sample_size: int = 10) -> List[Dict[str, Any]]:
        """Get a sample of reviews"""
        return reviews[:sample_size]
