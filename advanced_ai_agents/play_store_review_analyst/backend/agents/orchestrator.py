import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import yaml

from backend.llm.gemini_provider import GeminiProvider
from backend.llm.openai_provider import OpenAIProvider
from backend.llm.local_provider import LocalProvider
from backend.scraper import PlayStoreScraper, DataValidator
from .structure_analyzer import StructureAnalyzer
from .topic_extractor import TopicExtractor
from .trend_analyzer import TrendAnalyzer
from backend.utils.progress_tracker import ProgressTracker

logger = logging.getLogger(__name__)


class AnalysisOrchestrator:
    """Orchestrates the multi-agent analysis pipeline"""
    
    def __init__(self, config_path: str = "config/config.yaml", 
                 llm_config_path: str = "config/llm_config.yaml"):
        """
        Initialize orchestrator with configuration.
        
        Args:
            config_path: Path to main config file
            llm_config_path: Path to LLM config file
        """
        self.config = self._load_yaml(config_path)
        self.llm_config = self._load_yaml(llm_config_path)
        self.llm_provider = self._initialize_llm()
        
        # Initialize modules
        self.scraper = PlayStoreScraper(
            delay_seconds=self.config.get("scraper", {}).get("delay_seconds", 2),
            reviews_per_batch=self.config.get("scraper", {}).get("reviews_per_batch", 2000)
        )
        
    def _load_yaml(self, filepath: str) -> Dict[str, Any]:
        """Load YAML configuration file"""
        try:
            with open(filepath, "r") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Error loading {filepath}: {str(e)}")
            return {}
    
    def _initialize_llm(self):
        """Initialize LLM provider based on config"""
        try:
            provider_name = self.llm_config.get("llm", {}).get("provider", "gemini").lower()
            model = self.llm_config.get("llm", {}).get("model", "gemini-1.5-flash")
            temperature = self.llm_config.get("llm", {}).get("temperature", 0.3)
            max_tokens = self.llm_config.get("llm", {}).get("max_tokens", 2000)

            # Get API keys from config
            api_keys = self.llm_config.get("api_keys", {})
            gemini_key = api_keys.get("gemini")
            openai_key = api_keys.get("openai")
            claude_key = api_keys.get("claude")  # NEW
            groq_key = api_keys.get("groq")  # NEW


            if provider_name == "groq":  # NEW
                if not groq_key:
                    raise ValueError("Groq API key not found in config")
                from backend.llm.groq_provider import GroqProvider
                return GroqProvider(api_key=groq_key, model=model, temperature=temperature, max_tokens=max_tokens)
            elif provider_name == "claude":  # NEW
                if not claude_key:
                    raise ValueError("Claude API key not found in config")
                from backend.llm.claude_provider import ClaudeProvider
                return ClaudeProvider(api_key=claude_key, model=model, temperature=temperature, max_tokens=max_tokens)
            elif provider_name == "gemini":
                if not gemini_key:
                    raise ValueError("Gemini API key not found in config")
                return GeminiProvider(api_key=gemini_key, model=model, temperature=temperature, max_tokens=max_tokens)
            elif provider_name == "openai":
                if not openai_key:
                    raise ValueError("OpenAI API key not found in config")
                return OpenAIProvider(api_key=openai_key, model=model, temperature=temperature, max_tokens=max_tokens)
            elif provider_name == "local":
                local_config = self.llm_config.get("local_llm", {})
                return LocalProvider(
                    base_url=local_config.get("base_url", "http://localhost:11434"),
                    model=local_config.get("model", "llama2"),
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            else:
                logger.warning(f"Unknown provider {provider_name}, defaulting to Gemini")
                if not gemini_key:
                    raise ValueError("Gemini API key not found in config")
                return GeminiProvider(api_key=gemini_key, model=model, temperature=temperature, max_tokens=max_tokens)
                
        except Exception as e:
            logger.error(f"Error initializing LLM: {str(e)}")
            raise
    
    def run_analysis(self, app_identifier: str, target_date: str = None,
                 use_existing: bool = False, resume_extraction: bool = False,
                 clear_progress: bool = False) -> Dict[str, Any]:
        """
        Run complete analysis pipeline.

        Args:
            app_identifier: App ID or name (e.g., "com.swiggy.android")
            target_date: Target date for analysis (YYYY-MM-DD)
            use_existing: Use existing scraped reviews
            resume_extraction: Resume from previous extraction progress
            clear_progress: Clear all progress and start fresh

        Returns:
            Dict with analysis results
        """
        try:
            logger.info(f"Starting analysis for {app_identifier}")

            # Step 1: Find app
            logger.info("Step 1: Finding app...")
            app_info = self.scraper.find_app(app_identifier)
            if not app_info:
                raise ValueError(f"Could not find app: {app_identifier}")

            app_id = app_info.get("appId")
            if not app_id:
                raise ValueError(f"App ID not found in app info: {app_info}")
            # Sanitize app name - remove invalid filename characters (Windows: < > : " / \ | ? *)
            app_name = app_info.get("title", app_id.split(".")[-1])
            # Replace invalid characters with underscores
            for char in ['<', '>', ':', '"', '/', '\\', '|', '?', '*']:
                app_name = app_name.replace(char, '_')
            app_name = app_name.replace(" ", "_").lower()

            tracker = ProgressTracker(app_name)

            # Step 1.5: Clear progress if requested (BEFORE checking for existing data)
            if clear_progress:
                logger.info("Step 1.5: Clearing all progress for fresh start...")
                tracker.clear_all_progress()
                logger.info("✓ Progress cleared - starting fresh")

            # Step 2: Check for LLM change (SUBTASK 3)
            logger.info("Step 2: Checking for LLM provider/model changes...")
            existing_extraction = tracker.load_extraction_progress()
            if existing_extraction:
                prev_provider = existing_extraction.get("llm_provider")
                prev_model = existing_extraction.get("llm_model")
                current_provider = self.llm_config.get("llm", {}).get("provider")
                current_model = self.llm_config.get("llm", {}).get("model")

                if prev_provider != current_provider or prev_model != current_model:
                    logger.warning(f"LLM changed: {prev_provider}/{prev_model} → {current_provider}/{current_model}")

                    # Get existing data summary for context
                    existing_summary = tracker.get_existing_data_summary()

                    return {
                        "status": "llm_changed",
                        "app_name": app_name,
                        "previous_llm": f"{prev_provider}/{prev_model}",
                        "current_llm": f"{current_provider}/{current_model}",
                        "existing_data": existing_summary,
                        "message": (
                            f"You previously used {prev_provider} ({prev_model}) to process this data. "
                            f"Your config now uses {current_provider} ({current_model}). "
                            f"Using different LLMs may produce inconsistent results. "
                            f"Please clear progress to start fresh with the new LLM."
                        ),
                        "requires_clear": True
                    }

            # Step 3: Check for existing reviews
            logger.info("Step 3: Checking for existing reviews...")
            existing_summary = tracker.get_existing_data_summary()

            if existing_summary and not use_existing:
                # Reviews exist but user hasn't chosen what to do yet
                logger.info(f"Found existing reviews: {existing_summary.get('total_reviews', 0)} reviews")
                return {
                    "status": "existing_data_found",
                    "app_name": app_name,
                    "existing_data": existing_summary,
                    "message": "Reviews already scraped for this app. Do you want to use existing reviews or re-scrape?"
                }

            # Step 4: Scrape or load reviews
            if existing_summary and use_existing:
                # User chose to use existing reviews
                logger.info("Using existing reviews...")
                reviews_file = existing_summary.get("reviews_file")
                if not reviews_file:
                    raise ValueError("Existing reviews file path not found")
            else:
                # Scrape fresh reviews
                logger.info("Scraping fresh reviews...")
                start_date = self.config.get("data", {}).get("start_date", "2024-06-01")
                reviews_file = self.scraper.scrape_reviews(
                    app_id, start_date, target_date, app_name
                )

            if not reviews_file:
                raise ValueError("Failed to get reviews - no data file available")

            all_reviews = self.scraper.load_reviews(reviews_file)

            # Step 5: Validate data
            logger.info("Step 5: Validating data...")
            required_fields = self.config.get("data", {}).get("required_fields", ["content", "at", "score"])
            complete_reviews, incomplete_reviews = DataValidator.split_data(all_reviews, required_fields)
            logger.info(f"Data split: {len(complete_reviews)} complete, {len(incomplete_reviews)} incomplete")
            
            if not complete_reviews:
                raise ValueError("No complete reviews found")

            # Step 6: Analyze structure
            logger.info("Step 6: Analyzing data structure...")
            analyzer = StructureAnalyzer(
                self.llm_provider,
                self.llm_config.get("prompts", {}).get("structure_analyzer", "")
            )
            structure = analyzer.analyze(DataValidator.get_sample(complete_reviews, 3))

            # Step 7: Extract topics (batch or one-by-one based on config)
            topic_config = self.config.get("topic_extraction", {})
            processing_mode = topic_config.get("mode", "day")
            batch_size = topic_config.get("batch_size", 500)

            logger.info(f"Step 7: Extracting topics (mode: {processing_mode})...")

            extractor = TopicExtractor(
                self.llm_provider,
                self.llm_config.get("prompts", {}).get("topic_classifier", ""),
                processing_mode=processing_mode,
                batch_size=batch_size,
                batch_prompt=self.llm_config.get("prompts", {}).get("batch_topic_classifier", "")
            )
            # extraction_result = extractor.extract_topics(complete_reviews)
            extraction_result = extractor.extract_topics(
                complete_reviews,
                app_name=app_name,
                llm_provider=self.llm_config.get("llm", {}).get("provider"),
                llm_model=self.llm_config.get("llm", {}).get("model"),
                resume=resume_extraction
            )
            topics_list = extraction_result.get("topics", [])
            topic_to_reviews = extraction_result.get("topic_to_reviews", {})
            review_to_topics = extraction_result.get("review_to_topics", {})
            
            # Save the mappings
            extractor.save_mappings("mappings", app_name)
            
            logger.info(f"✓ Extracted {len(topics_list)} unique topics")
            logger.info(f"✓ Classified {extraction_result.get('total_reviews_classified', 0)} reviews")

            # Step 8: Analyze trends (using topics directly)
            logger.info("Step 8: Analyzing trends...")
            trend_analyzer = TrendAnalyzer(
                self.llm_provider,
                self.llm_config.get("prompts", {}).get("trend_analyzer", "")
            )
            trend_result = trend_analyzer.analyze_trends(
                complete_reviews,
                topic_to_reviews,
                review_to_topics,
                target_date,
                self.config.get("output", {}).get("trend_window_days", 30)
            )
            
            # Get LLM usage statistics
            llm_stats = self.llm_provider.get_stats()
            
            logger.info("="*60)
            logger.info("✅ ANALYSIS COMPLETE!")
            logger.info("="*60)
            logger.info(f"📊 LLM Statistics:")
            logger.info(f"   Model: {llm_stats['model']}")
            logger.info(f"   Total API Calls: {llm_stats['total_calls']}")
            logger.info(f"   Estimated Tokens: ~{llm_stats['estimated_tokens']:,}")
            logger.info("="*60)
            
            return {
                "status": "success",
                "app_name": app_name,
                "app_id": app_id,
                "total_reviews": len(complete_reviews),
                "incomplete_reviews": len(incomplete_reviews),
                "topics_extracted": len(topics_list),
                "trend_analysis": trend_result,
                "llm_stats": llm_stats,
            }
            
        except Exception as e:
            logger.error(f"Error in analysis pipeline: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
            }
