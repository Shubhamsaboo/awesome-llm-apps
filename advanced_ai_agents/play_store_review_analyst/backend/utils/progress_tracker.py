import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ProgressTracker:
    """Track progress for scraping and extraction"""
    
    def __init__(self, app_name: str, data_dir: str = "data"):
        self.app_name = app_name
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # File paths
        self.extraction_progress_file = self.data_dir / f"{app_name}_extraction_progress.json"
        self.reviews_file = self.data_dir / f"{app_name}_reviews_latest.jsonl"
        self.scrape_progress_file = self.data_dir / f"{app_name}_scrape_progress.json"
        # self.extraction_progress_file = self.data_dir / f"{app_name}_extraction_progress.json"
        # self.reviews_file = self.data_dir / f"{app_name}_reviews_latest.jsonl"
    
    def save_extraction_progress(self, progress: Dict[str, Any]) -> None:
        """Save extraction/categorization progress"""
        try:
            save_data = progress.copy()
            save_data['last_updated'] = datetime.now().isoformat()
            
            with open(self.extraction_progress_file, 'w') as f:
                json.dump(save_data, f, indent=2)
            logger.info(f"✓ Saved extraction progress: {save_data.get('categorized_count', 0)} reviews categorized")
        except Exception as e:
            logger.error(f"Error saving extraction progress: {e}", exc_info=True)
    
    def load_extraction_progress(self) -> Optional[Dict[str, Any]]:
        """Load extraction progress"""
        try:
            if self.extraction_progress_file.exists():
                with open(self.extraction_progress_file, 'r') as f:
                    data = json.load(f)
                    logger.info(f"✓ Loaded extraction progress: {data.get('categorized_count', 0)} reviews")
                    return data
        except Exception as e:
            logger.error(f"Error loading extraction progress: {e}", exc_info=True)
        return None
    
    def get_existing_data_summary(self) -> Optional[Dict[str, Any]]:
        """Get summary of existing data for UI display"""
        try:
            # Check if reviews file exists
            if not self.reviews_file.exists():
                logger.debug(f"Reviews file not found: {self.reviews_file}")
                return None
            
            # Count reviews in file
            review_count = 0
            try:
                with open(self.reviews_file, 'r', encoding='utf-8') as f:
                    review_count = sum(1 for line in f if line.strip())
            except Exception as e:
                logger.error(f"Error counting reviews: {e}")
                return None
            
            if review_count == 0:
                logger.debug(f"Reviews file is empty: {self.reviews_file}")
                return None
            
            # Load extraction progress
            extraction_progress = self.load_extraction_progress()
            
            # Build summary
            summary = {
                "reviews_file": str(self.reviews_file),
                "total_reviews": review_count,
                "categorization_status": {
                    "total_categorized": 0,
                    "llm_provider": None,
                    "llm_model": None,
                    "completed": False
                }
            }
            
            # Add extraction progress if available
            if extraction_progress:
                summary["categorization_status"] = {
                    "total_categorized": extraction_progress.get("categorized_count", 0),
                    "llm_provider": extraction_progress.get("llm_provider"),
                    "llm_model": extraction_progress.get("llm_model"),
                    "completed": extraction_progress.get("completed", False)
                }
            
            logger.info(f"Generated summary: {review_count} reviews, {summary['categorization_status']['total_categorized']} categorized")
            return summary
            
        except Exception as e:
            logger.error(f"Error in get_existing_data_summary: {e}", exc_info=True)
            return None
    def clear_extraction_progress(self) -> None:
        """Clear extraction progress (when using different LLM or restarting)"""
        try:
            if self.extraction_progress_file.exists():
                self.extraction_progress_file.unlink()
                logger.info("✓ Cleared extraction progress")
        except Exception as e:
            logger.error(f"Error clearing extraction progress: {e}")
    
    def clear_all_progress(self) -> None:
        """Clear all progress (fresh start)"""
        try:
            if self.extraction_progress_file.exists():
                self.extraction_progress_file.unlink()
            if self.reviews_file.exists():
                self.reviews_file.unlink()
            logger.info("✓ Cleared all progress")
        except Exception as e:
            logger.error(f"Error clearing progress: {e}")

    def save_scrape_progress(self, progress: Dict[str, Any]) -> None:
        """Save scraping progress"""
        try:
            progress['last_updated'] = datetime.now().isoformat()
            with open(self.scrape_progress_file, 'w') as f:
                json.dump(progress, f, indent=2)
            logger.info(f"Saved scrape progress: {progress.get('total_scraped', 0)} reviews")
        except Exception as e:
            logger.error(f"Error saving scrape progress: {e}")