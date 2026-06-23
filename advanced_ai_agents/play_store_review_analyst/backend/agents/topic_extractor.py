import json
import logging
from typing import Dict, Any, List, Set, Optional
from collections import defaultdict
from datetime import datetime
from backend.utils.progress_tracker import ProgressTracker
from backend.llm.llm_provider import LLMProvider
from pathlib import Path

logger = logging.getLogger(__name__)


class TopicExtractor:
    """Agent that extracts and dynamically builds topics from reviews"""
    
    def __init__(self, llm_provider: LLMProvider, classification_prompt: str,
                 processing_mode: str = "single", batch_size: int = 10, 
                 batch_prompt: str = None):
        """
        Initialize TopicExtractor with flexible processing modes.
        
        Args:
            llm_provider: LLM provider instance
            classification_prompt: Template for single review classification
            processing_mode: "single", "batch", or "day" (default: "single")
            batch_size: Number of reviews per batch (only for "batch" mode)
            batch_prompt: Template for batch/day processing
        """
        self.llm = llm_provider
        self.classification_prompt_template = classification_prompt
        self.batch_prompt_template = batch_prompt
        self.discovered_topics: List[str] = []
        self.topic_to_reviews: Dict[str, List[str]] = {}
        self.review_to_topics: Dict[str, Dict[str, Any]] = {}
        self.progress_tracker: Optional[ProgressTracker] = None
        self.processed_review_ids: Set[str] = set()
        
        # Processing mode configuration
        self.processing_mode = processing_mode.lower()
        if self.processing_mode not in ["single", "batch", "day"]:
            logger.warning(f"Invalid processing mode '{processing_mode}', defaulting to 'single'")
            self.processing_mode = "batch"
        
        self.batch_size = batch_size
        
        # Legacy compatibility
        self.batch_mode = (self.processing_mode == "batch")
    
    def extract_topics(self, reviews: List[Dict[str, Any]], app_name: str = None, 
                      llm_provider: str = None, llm_model: str = None,
                      resume: bool = False) -> Dict[str, Any]:
        """
        Extract topics from reviews using configured processing mode.
        
        Args:
            reviews: List of review dictionaries
            app_name: App name for progress tracking
            llm_provider: LLM provider name
            llm_model: LLM model name
            resume: Whether to resume from previous progress
            
        Returns:
            Dict with topics, mappings, and metadata
        """
        # Initialize progress tracker
        if app_name:
            self.progress_tracker = ProgressTracker(app_name)
            
            # Load existing progress if resuming (SUBTASK 2 & 4)
            if resume:
                existing_progress = self.progress_tracker.load_extraction_progress()
                if existing_progress:
                    # LLM change detection is now handled at orchestrator level (SUBTASK 3)
                    # So we can safely load progress here
                    logger.info(f"✅ Resuming extraction from previous progress")
                    self.discovered_topics = existing_progress.get('discovered_topics', [])
                    self.topic_to_reviews = existing_progress.get('topic_to_reviews', {})
                    self.review_to_topics = existing_progress.get('review_to_topics', {})
                    self.processed_review_ids = set(self.review_to_topics.keys())

                    logger.info(f"   Loaded {len(self.discovered_topics)} topics")
                    logger.info(f"   Already categorized: {len(self.processed_review_ids)} reviews")
        
        if self.processing_mode == "day":
            return self._extract_topics_by_day(reviews, llm_provider, llm_model)
        elif self.processing_mode == "batch":
            return self._extract_topics_batch(reviews, llm_provider, llm_model)
        else:
            return self._extract_topics_single(reviews, llm_provider, llm_model)
    
    def _extract_topics_by_day(self, reviews: List[Dict[str, Any]],
                              llm_provider: str = None, llm_model: str = None) -> Dict[str, Any]:
        """
        Extract topics DAY-WISE - processes all reviews from the same day together.
        More logical grouping than arbitrary batch sizes.
        """
        total_reviews = len(reviews)
        logger.info(f"="*60)
        logger.info(f"🎯 Starting DAY-WISE topic extraction for {total_reviews} reviews")
        logger.info(f"="*60)

        # Log resume info if applicable (SUBTASK 4)
        if self.processed_review_ids:
            logger.info(f"📦 Resuming from previous session")
            logger.info(f"   Already processed: {len(self.processed_review_ids)} reviews")
            logger.info(f"   Existing topics: {len(self.discovered_topics)}")

        new_topics_count = 0
        skipped_reviews = 0
        already_processed_count = 0
        
        try:
            # Group reviews by date
            reviews_by_date = self._group_reviews_by_date(reviews)
            total_days = len(reviews_by_date)
            
            logger.info(f"📅 Grouped reviews into {total_days} unique days")
            
            # Sort dates chronologically for logical processing
            sorted_dates = sorted(reviews_by_date.keys())
            
            # Process each day's reviews together
            for day_num, date_key in enumerate(sorted_dates, 1):
                day_reviews = reviews_by_date[date_key]
                logger.info(f"\n📅 Processing Day {day_num}/{total_days}: {date_key}")
                logger.info(f"   📝 Reviews in this day: {len(day_reviews)}")
                logger.info(f"   📚 Current seed topics: {len(self.discovered_topics)} topics")
                
                # Filter out empty reviews and already processed ones (SUBTASK 4)
                valid_reviews = []
                for review in day_reviews:
                    review_id = review.get("reviewId")
                    if not review_id:
                        skipped_reviews += 1
                        continue

                    content = review.get("content", "").strip()
                    if not content:
                        skipped_reviews += 1
                        continue

                    # Skip if already processed (SUBTASK 4 - Deduplication)
                    if review_id in self.processed_review_ids:
                        already_processed_count += 1
                        continue

                    valid_reviews.append(review)
                
                if not valid_reviews:
                    logger.info(f"   ⏭️  Skipping {date_key} - all reviews already processed or empty")
                    continue

                logger.info(f"   🆕 Processing {len(valid_reviews)} new reviews")
                
                # Process this day's reviews as a batch
                day_results = self._classify_batch_reviews(valid_reviews, f"day_{date_key}")
                
                if day_results:
                    day_new_topics = 0
                    day_matched_topics = 0
                    
                    # Process each result
                    for review_id, classification in day_results.items():
                        if classification:
                            topic = classification["topic"]
                            
                            # Check if this is a new topic
                            is_new = topic not in self.discovered_topics
                            if is_new:
                                self.discovered_topics.append(topic)
                                new_topics_count += 1
                                day_new_topics += 1
                                logger.info(f"     ✨ NEW TOPIC #{len(self.discovered_topics)}: '{topic}'")
                            else:
                                day_matched_topics += 1
                            
                            # Store mappings immediately
                            self.review_to_topics[review_id] = classification
                            self.processed_review_ids.add(review_id)  # Mark as processed

                            if topic not in self.topic_to_reviews:
                                self.topic_to_reviews[topic] = []
                            self.topic_to_reviews[topic].append(review_id)
                    
                    # Day summary with match rate
                    match_rate = (day_matched_topics / len(day_results) * 100) if day_results else 0
                    logger.info(f"   📊 Day {date_key} done | Total topics: {len(self.discovered_topics)} | "
                              f"New: {day_new_topics} | Matched: {day_matched_topics} ({match_rate:.1f}%)")

                    # CRITICAL: Save progress after each day
                    if self.progress_tracker:
                        self.progress_tracker.save_extraction_progress({
                            "categorized_count": len(self.review_to_topics),
                            "total_topics": len(self.discovered_topics),
                            "last_day_processed": date_key,
                            "days_processed": day_num,
                            "discovered_topics": self.discovered_topics,
                            "topic_to_reviews": self.topic_to_reviews,
                            "review_to_topics": self.review_to_topics,
                            "llm_provider": llm_provider,
                            "llm_model": llm_model,
                            "completed": False
                        })
                        logger.info(f"   💾 Progress saved")
            
            # Mark as completed
            if self.progress_tracker:
                self.progress_tracker.save_extraction_progress({
                    "categorized_count": len(self.review_to_topics),
                    "total_topics": len(self.discovered_topics),
                    "last_day_processed": sorted_dates[-1] if sorted_dates else None,
                    "days_processed": total_days,
                    "discovered_topics": self.discovered_topics,
                    "topic_to_reviews": self.topic_to_reviews,
                    "review_to_topics": self.review_to_topics,
                    "llm_provider": llm_provider,
                    "llm_model": llm_model,
                    "completed": True
                })

            # Create final result
            result = {
                "topics": self.discovered_topics,
                "topic_to_reviews": self.topic_to_reviews,
                "review_to_topics": self.review_to_topics,
                "total_topics": len(self.discovered_topics),
                "total_reviews_classified": len(self.review_to_topics),
                "new_topics_discovered": new_topics_count,
                "skipped_reviews": skipped_reviews,
                "total_days_processed": total_days
            }

            logger.info(f"\n{'='*60}")
            logger.info(f"✅ DAY-WISE TOPIC EXTRACTION COMPLETE!")
            logger.info(f"{'='*60}")
            logger.info(f"  📊 Total topics discovered: {len(self.discovered_topics)}")
            logger.info(f"  ✨ New topics: {new_topics_count}")
            logger.info(f"  ✓ Total classified: {len(self.review_to_topics)}")
            logger.info(f"  🔄 Already processed (skipped): {already_processed_count}")
            logger.info(f"  ⏭️  Skipped (empty): {skipped_reviews}")
            logger.info(f"  📅 Total days processed: {total_days}")
            logger.info(f"{'='*60}\n")

            return result
            
        except Exception as e:
            logger.error(f"❌ Error extracting topics in day-wise mode: {str(e)}", exc_info=True)
            raise
    
    def _group_reviews_by_date(self, reviews: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group reviews by their date (day).
        
        Args:
            reviews: List of review dictionaries
            
        Returns:
            Dict mapping date_string -> list of reviews for that date
        """
        reviews_by_date = defaultdict(list)
        
        for review in reviews:
            date_str = review.get("at", "")
            
            if not date_str:
                # If no date, use "unknown_date"
                date_key = "unknown_date"
            else:
                # Try to parse date and extract just the date part (YYYY-MM-DD)
                try:
                    # Handle various date formats
                    # Common formats: "2024-01-15", "2024-01-15T10:30:00", "January 15, 2024", etc.
                    if "T" in date_str:
                        date_key = date_str.split("T")[0]
                    elif " " in date_str and len(date_str.split()) > 2:
                        # Try parsing full date string
                        try:
                            dt = datetime.strptime(date_str, "%B %d, %Y")
                            date_key = dt.strftime("%Y-%m-%d")
                        except ValueError:
                            # If parsing fails, use the date as-is
                            date_key = date_str.split()[0] if date_str else "unknown_date"
                    else:
                        # Assume it's already in a simple format
                        date_key = date_str.split()[0] if date_str else "unknown_date"
                except Exception as e:
                    logger.debug(f"Could not parse date '{date_str}': {e}")
                    date_key = "unknown_date"
            
            reviews_by_date[date_key].append(review)
        
        return dict(reviews_by_date)
    
    def _extract_topics_single(self, reviews: List[Dict[str, Any]],
                              llm_provider: str = None, llm_model: str = None) -> Dict[str, Any]:
        """Extract topics ONE BY ONE"""
        total_reviews = len(reviews)
        logger.info(f"="*60)
        logger.info(f"🎯 Starting ONE-BY-ONE topic extraction for {total_reviews} reviews")
        logger.info(f"="*60)

        # Log resume info if applicable (SUBTASK 4)
        if self.processed_review_ids:
            logger.info(f"📦 Resuming from previous session")
            logger.info(f"   Already processed: {len(self.processed_review_ids)} reviews")
            logger.info(f"   Existing topics: {len(self.discovered_topics)}")

        new_topics_count = 0
        skipped_reviews = 0
        already_processed_count = 0
        batch_save_interval = 10  # Save progress every 10 reviews in single mode
        
        try:
            for idx, review in enumerate(reviews, 1):
                review_id = review.get("reviewId", f"review_{idx}")

                # Skip if already processed (SUBTASK 4 - Deduplication)
                if review_id in self.processed_review_ids:
                    already_processed_count += 1
                    continue

                content = review.get("content", "").strip()

                if not content:
                    skipped_reviews += 1
                    logger.debug(f"Skipping review {idx}/{total_reviews} - empty content")
                    continue
                
                # Process this single review
                logger.info(f"📝 Processing review {idx}/{total_reviews} (ID: {review_id[:20]}...)")
                
                classification = self._classify_single_review(review, idx)
                
                if classification:
                    topic = classification["topic"]
                    
                    # Check if this is a new topic
                    is_new = topic not in self.discovered_topics
                    if is_new:
                        self.discovered_topics.append(topic)
                        new_topics_count += 1
                        logger.info(f"  ✨ NEW TOPIC #{len(self.discovered_topics)}: '{topic}'")
                    else:
                        logger.info(f"  ✓ Matched to existing topic: '{topic}'")
                    
                    # Store mappings immediately
                    self.review_to_topics[review_id] = classification
                    self.processed_review_ids.add(review_id)  # Mark as processed

                    if topic not in self.topic_to_reviews:
                        self.topic_to_reviews[topic] = []
                    self.topic_to_reviews[topic].append(review_id)

                # Progress update and save every batch_save_interval reviews
                if idx % batch_save_interval == 0 or idx == total_reviews:
                    logger.info(f"  📊 Progress: {idx}/{total_reviews} | Topics: {len(self.discovered_topics)} | New: {new_topics_count}")

                    # CRITICAL: Save progress periodically
                    if self.progress_tracker and len(self.review_to_topics) > 0:
                        self.progress_tracker.save_extraction_progress({
                            "categorized_count": len(self.review_to_topics),
                            "total_topics": len(self.discovered_topics),
                            "last_review_index": idx,
                            "discovered_topics": self.discovered_topics,
                            "topic_to_reviews": self.topic_to_reviews,
                            "review_to_topics": self.review_to_topics,
                            "llm_provider": llm_provider,
                            "llm_model": llm_model,
                            "completed": False
                        })
                        logger.info(f"  💾 Progress saved")
            
            # Mark as completed
            if self.progress_tracker:
                self.progress_tracker.save_extraction_progress({
                    "categorized_count": len(self.review_to_topics),
                    "total_topics": len(self.discovered_topics),
                    "last_review_index": total_reviews,
                    "discovered_topics": self.discovered_topics,
                    "topic_to_reviews": self.topic_to_reviews,
                    "review_to_topics": self.review_to_topics,
                    "llm_provider": llm_provider,
                    "llm_model": llm_model,
                    "completed": True
                })

            # Create final result
            result = {
                "topics": self.discovered_topics,
                "topic_to_reviews": self.topic_to_reviews,
                "review_to_topics": self.review_to_topics,
                "total_topics": len(self.discovered_topics),
                "total_reviews_classified": len(self.review_to_topics),
                "new_topics_discovered": new_topics_count,
                "skipped_reviews": skipped_reviews
            }

            logger.info(f"="*60)
            logger.info(f"✅ TOPIC EXTRACTION COMPLETE!")
            logger.info(f"="*60)
            logger.info(f"  📊 Total topics discovered: {len(self.discovered_topics)}")
            logger.info(f"  ✨ New topics: {new_topics_count}")
            logger.info(f"  ✓ Total classified: {len(self.review_to_topics)}")
            logger.info(f"  🔄 Already processed (skipped): {already_processed_count}")
            logger.info(f"  ⏭️  Skipped (empty): {skipped_reviews}")
            logger.info(f"="*60)

            return result
            
        except Exception as e:
            logger.error(f"❌ Error extracting topics: {str(e)}", exc_info=True)
            raise
    
    def _extract_topics_batch(self, reviews: List[Dict[str, Any]],
                          llm_provider: str = None, llm_model: str = None) -> Dict[str, Any]:
        """Extract topics in BATCHES - much faster and API-efficient"""
        total_reviews = len(reviews)
        logger.info(f"="*60)
        logger.info(f"🎯 Starting BATCH topic extraction for {total_reviews} reviews")
        logger.info(f"   Batch size: {self.batch_size}")
        logger.info(f"="*60)

        # Log resume info if applicable (SUBTASK 4)
        if self.processed_review_ids:
            logger.info(f"📦 Resuming from previous session")
            logger.info(f"   Already processed: {len(self.processed_review_ids)} reviews")
            logger.info(f"   Existing topics: {len(self.discovered_topics)}")

        new_topics_count = 0
        skipped_reviews = 0
        already_processed_count = 0
        batch_num = 0   
        
        try:
            # Process reviews in batches
            for i in range(0, total_reviews, self.batch_size):
                batch = reviews[i:i + self.batch_size]
                batch_num += 1
                batch_start = i + 1
                batch_end = min(i + self.batch_size, total_reviews)
                
                logger.info(f"\n📦 Processing batch {batch_num} (reviews {batch_start}-{batch_end}/{total_reviews})")
                logger.info(f"   📚 Current seed topics: {len(self.discovered_topics)} topics")
                
                # Filter out empty reviews and already processed ones (SUBTASK 4)
                valid_reviews = []
                for review in batch:
                    review_id = review.get("reviewId")
                    if not review_id:
                        skipped_reviews += 1
                        continue

                    content = review.get("content", "").strip()
                    if not content:
                        skipped_reviews += 1
                        continue

                    # Skip if already processed (SUBTASK 4 - Deduplication)
                    if review_id in self.processed_review_ids:
                        already_processed_count += 1
                        continue

                    valid_reviews.append(review)
                
                if not valid_reviews:
                    logger.info(f"   ⏭️  All reviews in batch already processed or empty, skipping")
                    continue
                
                logger.info(f"   🆕 Processing {len(valid_reviews)} new reviews")
                
                # Process this batch
                batch_results = self._classify_batch_reviews(valid_reviews, batch_num)
                
                if batch_results:
                    batch_new_topics = 0
                    batch_matched_topics = 0
                    
                    # Process each result
                    for review_id, classification in batch_results.items():
                        if classification:
                            topic = classification["topic"]
                            
                            # Check if this is a new topic
                            is_new = topic not in self.discovered_topics
                            if is_new:
                                self.discovered_topics.append(topic)
                                new_topics_count += 1
                                batch_new_topics += 1
                                logger.info(f"     ✨ NEW TOPIC #{len(self.discovered_topics)}: '{topic}'")
                            else:
                                batch_matched_topics += 1
                            
                            # Store mappings immediately
                            self.review_to_topics[review_id] = classification
                            self.processed_review_ids.add(review_id)  # Mark as processed
                            
                            if topic not in self.topic_to_reviews:
                                self.topic_to_reviews[topic] = []
                            self.topic_to_reviews[topic].append(review_id)
                    
                    # Progress update
                    match_rate = (batch_matched_topics / len(batch_results) * 100) if batch_results else 0
                    logger.info(f"   📊 Batch done | Topics: {len(self.discovered_topics)} | "
                            f"New: {batch_new_topics} | Matched: {batch_matched_topics} ({match_rate:.1f}%)")
                    
                    # CRITICAL: Save progress after each batch
                    if self.progress_tracker:
                        self.progress_tracker.save_extraction_progress({
                            "categorized_count": len(self.review_to_topics),
                            "total_topics": len(self.discovered_topics),
                            "last_batch_index": batch_end,
                            "discovered_topics": self.discovered_topics,
                            "topic_to_reviews": self.topic_to_reviews,
                            "review_to_topics": self.review_to_topics,
                            "llm_provider": llm_provider,
                            "llm_model": llm_model,
                            "completed": False
                        })
                        logger.info(f"   💾 Progress saved")
            
            # Mark as completed
            if self.progress_tracker:
                self.progress_tracker.save_extraction_progress({
                    "categorized_count": len(self.review_to_topics),
                    "total_topics": len(self.discovered_topics),
                    "last_batch_index": total_reviews,
                    "discovered_topics": self.discovered_topics,
                    "topic_to_reviews": self.topic_to_reviews,
                    "review_to_topics": self.review_to_topics,
                    "llm_provider": llm_provider,
                    "llm_model": llm_model,
                    "completed": True
                })
            
            # Create final result
            result = {
                "topics": self.discovered_topics,
                "topic_to_reviews": self.topic_to_reviews,
                "review_to_topics": self.review_to_topics,
                "total_topics": len(self.discovered_topics),
                "total_reviews_classified": len(self.review_to_topics),
                "new_topics_discovered": new_topics_count,
                "skipped_reviews": skipped_reviews
            }
            
            logger.info(f"\n{'='*60}")
            logger.info(f"✅ BATCH TOPIC EXTRACTION COMPLETE!")
            logger.info(f"{'='*60}")
            logger.info(f"  📊 Total topics: {len(self.discovered_topics)}")
            logger.info(f"  ✨ New topics: {new_topics_count}")
            logger.info(f"  ✓ Total classified: {len(self.review_to_topics)}")
            logger.info(f"  🔄 Already processed (skipped): {already_processed_count}")
            logger.info(f"  ⏭️  Skipped (empty): {skipped_reviews}")
            logger.info(f"  📦 Batches: {batch_num}")
            logger.info(f"{'='*60}\n")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in batch extraction: {str(e)}", exc_info=True)
            raise
        
    def _classify_batch_reviews(self, reviews: List[Dict[str, Any]], batch_identifier) -> Dict[str, Dict[str, Any]]:
        """
        Classify a batch of reviews at once.
        Works for both batch mode and day mode.
        
        Args:
            reviews: List of review dictionaries
            batch_identifier: Identifier for logging (batch number or day)
            
        Returns:
            Dict mapping review_id -> classification
        """
        try:
            # Create a dictionary for the batch with review_id as key
            reviews_dict = {}
            for idx, review in enumerate(reviews):
                review_id = review.get("reviewId", f"batch{batch_identifier}_review_{idx}")
                reviews_dict[review_id] = {
                    "content": review.get("content", ""),
                    "score": review.get("score", 0),
                    "date": review.get("at", "")
                }
            
            # Create batch prompt
            prompt = self._create_batch_classification_prompt(reviews_dict)
            
            # Get LLM response
            result = self.llm.generate_json(prompt)
            
            # Handle response - expecting dict with review_id as keys
            if not isinstance(result, dict):
                logger.warning(f"   ⚠️  Invalid batch response format for batch {batch_identifier}")
                return {}
            
            # Process and validate results
            classifications = {}
            for review_id, classification_data in result.items():
                if isinstance(classification_data, dict):
                    topic = classification_data.get("topic", "").strip()
                    if topic:
                        classifications[review_id] = {
                            "topic": topic,
                            "type": classification_data.get("type", "issue").lower(),
                            "confidence": classification_data.get("confidence", 0.8),
                            "review_id": review_id,
                            "score": reviews_dict.get(review_id, {}).get("score", 0)
                        }
            
            logger.info(f"   ✓ Classified {len(classifications)}/{len(reviews)} reviews")
            return classifications
            
        except Exception as e:
            logger.error(f"   ❌ Error classifying batch {batch_identifier}: {str(e)}", exc_info=True)
            return {}
    
    def _create_batch_classification_prompt(self, reviews_dict: Dict[str, Dict[str, Any]]) -> str:
        """Create prompt for classifying a batch of reviews using template from config"""

        # Format existing topics - show all topics to maximize matching
        if self.discovered_topics:
            # Show all topics with emphasis on matching them
            topics_list = "\n".join([f"  {i+1}. {t}" for i, t in enumerate(self.discovered_topics)])
            existing_topics_section = f"""EXISTING TOPICS (Total: {len(self.discovered_topics)}):
            {topics_list}

            ⚠️ CRITICAL: Before creating a NEW topic, carefully check if ANY of the above {len(self.discovered_topics)} topics match!
            Match aggressively - if a review is about similar issues, use the EXISTING topic name."""
        else:
            existing_topics_section = "No existing topics yet. Discover new topics from these reviews."

        # Format reviews - truncate long content to avoid token bloat
        reviews_section = "REVIEWS TO CLASSIFY:\n"
        for review_id, review_data in reviews_dict.items():
            content = review_data['content']
            # Limit content to 150 chars to keep prompt concise
            truncated_content = content[:150] + "..." if len(content) > 150 else content
            # Escape quotes to prevent JSON issues
            truncated_content = truncated_content.replace('"', '\\"')
            
            reviews_section += f"\n\"{review_id}\": {{\n"
            reviews_section += f"  \"content\": \"{truncated_content}\",\n"
            reviews_section += f"  \"score\": {review_data['score']},\n"
            reviews_section += f"  \"date\": \"{review_data['date']}\"\n"
            reviews_section += "},\n"

        # Use the template from config with placeholder replacement
        prompt = self.batch_prompt_template.format(
            existing_topics=existing_topics_section,
            reviews_section=reviews_section
        )

        return prompt
    
    def _classify_single_review(self, review: Dict[str, Any], review_idx: int) -> Dict[str, Any]:
        """
        Classify a single review into a topic.
        Either match to existing topic or create new one.
        
        Returns:
            Dict with topic, type, and confidence
        """
        try:
            review_id = review.get("reviewId", f"review_{review_idx}")
            content = review.get("content", "")
            score = review.get("score", 0)
            date = review.get("at", "")
            
            # Create prompt with current seed topics
            prompt = self._create_classification_prompt(content, score, date)
            
            # Get LLM response
            result = self.llm.generate_json(prompt)
            
            # Handle response
            if isinstance(result, list) and len(result) > 0:
                result = result[0]
            
            if not isinstance(result, dict):
                logger.warning(f"  ⚠️  Invalid response format for review {review_idx}")
                return None
            
            # Extract classification
            topic = result.get("topic", "").strip()
            topic_type = result.get("type", "issue").lower()
            confidence = result.get("confidence", 0.8)
            
            if not topic:
                logger.warning(f"  ⚠️  No topic extracted for review {review_idx}")
                return None
            
            return {
                "topic": topic,
                "type": topic_type,  # issue, request, feedback, other
                "confidence": confidence,
                "review_id": review_id,
                "score": score
            }
            
        except Exception as e:
            logger.error(f"  ❌ Error classifying review {review_idx}: {str(e)}", exc_info=True)
            return None
    
    def _create_classification_prompt(self, content: str, score: int, date: str) -> str:
        """Create prompt for classifying a single review"""
        
        # Format existing topics for display
        if self.discovered_topics:
            existing_topics_section = f"EXISTING TOPICS (Total: {len(self.discovered_topics)}):\n" + \
                                     "\n".join([f"  {i+1}. {t}" for i, t in enumerate(self.discovered_topics)])
        else:
            existing_topics_section = "No existing topics yet. This is one of the first reviews - discover a new topic."
        
        # Use prompt template from config
        return self.classification_prompt_template.format(
            existing_topics=existing_topics_section,
            review_content=content,
            review_score=score,
            review_date=date
        )
    
    def save_mappings(self, output_dir: str, app_name: str) -> None:
        """Save the mappings to JSON files"""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)
            
            # Save topic_to_reviews mapping
            topic_file = output_path / f"{app_name}_topic_to_reviews.json"
            with open(topic_file, "w", encoding="utf-8") as f:
                json.dump(self.topic_to_reviews, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved topic-to-reviews mapping: {topic_file}")
            
            # Save review_to_topics mapping
            review_file = output_path / f"{app_name}_review_to_topics.json"
            with open(review_file, "w", encoding="utf-8") as f:
                json.dump(self.review_to_topics, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved review-to-topics mapping: {review_file}")
            
        except Exception as e:
            logger.error(f"Error saving mappings: {str(e)}", exc_info=True)