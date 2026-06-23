import json
import logging
from typing import Dict, Any, List
from backend.llm.llm_provider import LLMProvider

logger = logging.getLogger(__name__)


class CategoryValidator:
    """Agent that validates and merges similar categories"""
    
    def __init__(self, llm_provider: LLMProvider, prompt_template: str):
        self.llm = llm_provider
        self.prompt_template = prompt_template
    
    def validate_and_merge(self, categories: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        Validate categories and merge similar ones.
        
        Args:
            categories: Dict with category names as keys and lists of topics as values
            
        Returns:
            Validated and merged categories dict
        """
        try:
            logger.info(f"Validating {len(categories)} categories")
            
            # Get merge suggestions from LLM
            merge_suggestions = self._get_merge_suggestions(list(categories.keys()))
            
            # Apply merges
            merged_categories = self._apply_merges(categories, merge_suggestions)
            
            logger.info(f"Validation complete: {len(categories)} -> {len(merged_categories)} categories")
            return merged_categories
            
        except Exception as e:
            logger.error(f"Error in category validation: {str(e)}")
            return categories  # Return original if error
    
    def _get_merge_suggestions(self, category_names: List[str]) -> List[Dict[str, Any]]:
        """Get merge suggestions from LLM"""
        try:
            # Don't bother if there are too few categories
            if len(category_names) < 2:
                logger.info("Less than 2 categories, skipping validation")
                return []
            
            prompt = self.prompt_template.format(
                categories=json.dumps(category_names, indent=2)
            )
            
            result = self.llm.generate_json(prompt)
            
            # Handle different response formats
            if isinstance(result, dict):
                result = [result]
            
            if isinstance(result, list):
                # Validate each suggestion has required fields
                valid_suggestions = []
                for suggestion in result:
                    if isinstance(suggestion, dict):
                        if "original_categories" in suggestion and "merged_name" in suggestion:
                            valid_suggestions.append(suggestion)
                        else:
                            logger.warning(f"Invalid suggestion format: {suggestion}")
                return valid_suggestions
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting merge suggestions: {str(e)}", exc_info=True)
            return []
    
    def _apply_merges(self, categories: Dict[str, List[str]], 
                      merge_suggestions: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Apply merge suggestions to categories"""
        merged = categories.copy()
        
        for suggestion in merge_suggestions:
            original_cats = suggestion.get("original_categories", [])
            merged_name = suggestion.get("merged_name", "")
            
            if not merged_name or len(original_cats) < 2:
                continue
            
            # Merge topics from all original categories
            merged_topics = []
            for orig_cat in original_cats:
                if orig_cat in merged:
                    merged_topics.extend(merged[orig_cat])
                    del merged[orig_cat]
            
            # Remove duplicates while preserving order
            merged_topics = list(dict.fromkeys(merged_topics))
            merged[merged_name] = merged_topics
        
        return merged
