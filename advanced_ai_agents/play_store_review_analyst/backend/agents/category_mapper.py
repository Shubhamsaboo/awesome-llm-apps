import json
import logging
from typing import Dict, List, Tuple, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class CategoryMapper:
    """Maps categories to IDs and creates topic-to-category mappings"""
    
    def __init__(self, categories_dir: str = "categories"):
        self.categories_dir = Path(categories_dir)
        self.categories_dir.mkdir(exist_ok=True)
    
    def create_mappings(self, validated_categories: Dict[str, List[str]], 
                       app_name: str) -> Tuple[Dict[str, int], Dict[int, List[str]]]:
        """
        Create ID mappings for categories.
        
        Args:
            validated_categories: Dict with category names as keys
            app_name: Name of the app for file storage
            
        Returns:
            Tuple of (category_name_to_id, category_id_to_topics)
        """
        try:
            # Create ID mappings
            category_name_to_id = {}
            category_id_to_topics = {}
            
            for idx, (category_name, topics) in enumerate(validated_categories.items(), 1):
                category_id = idx
                category_name_to_id[category_name] = category_id
                category_id_to_topics[category_id] = topics
            
            # Save mappings
            self._save_mappings(category_name_to_id, category_id_to_topics, app_name)
            
            logger.info(f"Created {len(category_name_to_id)} category mappings for {app_name}")
            return category_name_to_id, category_id_to_topics
            
        except Exception as e:
            logger.error(f"Error creating mappings: {str(e)}")
            raise
    
    def _save_mappings(self, category_name_to_id: Dict[str, int], 
                       category_id_to_topics: Dict[int, List[str]], 
                       app_name: str) -> None:
        """Save mapping files"""
        try:
            # Save name to ID mapping
            name_to_id_file = self.categories_dir / f"{app_name}_category_ids.json"
            with open(name_to_id_file, "w") as f:
                json.dump(category_name_to_id, f, indent=2)
            logger.info(f"Saved category IDs to {name_to_id_file}")
            
            # Save ID to topics mapping
            id_to_topics_file = self.categories_dir / f"{app_name}_id_to_topics.json"
            with open(id_to_topics_file, "w") as f:
                json.dump({str(k): v for k, v in category_id_to_topics.items()}, f, indent=2)
            logger.info(f"Saved ID to topics mapping to {id_to_topics_file}")
            
        except Exception as e:
            logger.error(f"Error saving mappings: {str(e)}")
            raise
    
    def load_mappings(self, app_name: str) -> Tuple[Dict[str, int], Dict[int, List[str]]]:
        """Load existing mappings"""
        try:
            name_to_id_file = self.categories_dir / f"{app_name}_category_ids.json"
            id_to_topics_file = self.categories_dir / f"{app_name}_id_to_topics.json"
            
            with open(name_to_id_file, "r") as f:
                category_name_to_id = json.load(f)
            
            with open(id_to_topics_file, "r") as f:
                id_to_topics_raw = json.load(f)
                category_id_to_topics = {int(k): v for k, v in id_to_topics_raw.items()}
            
            logger.info(f"Loaded mappings for {app_name}")
            return category_name_to_id, category_id_to_topics
            
        except Exception as e:
            logger.error(f"Error loading mappings: {str(e)}")
            raise
