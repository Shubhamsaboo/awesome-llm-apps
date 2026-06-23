import json
import logging
import time
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from google_play_scraper import app, reviews, Sort
from backend.utils.progress_tracker import ProgressTracker
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PlayStoreScraper:
    """Google Play Store review scraper with batching support and enhanced error handling"""
    
    def __init__(self, data_dir: str = "data", delay_seconds: float = 2, 
                 reviews_per_batch: int = 200, max_retries: int = 3):
        """
        Initialize the scraper.
        
        Args:
            data_dir: Directory to save review files
            delay_seconds: Delay between API calls to avoid rate limiting
            reviews_per_batch: Number of reviews to fetch per batch (max 200 for Play Store)
            max_retries: Maximum retry attempts for failed requests
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.delay_seconds = delay_seconds
        # Play Store API limit is 200 per request
        self.reviews_per_batch = min(reviews_per_batch, 200)
        self.max_retries = max_retries
        
        print(f"✓ Scraper initialized")
        print(f"  - Data directory: {self.data_dir.absolute()}")
        print(f"  - Reviews per batch: {self.reviews_per_batch}")
        print(f"  - Delay between requests: {self.delay_seconds}s")
    
    def extract_app_id(self, app_input: str) -> Optional[str]:
        """
        Extract app ID from URL or return the app ID directly.
        
        Args:
            app_input: Either a Play Store URL or an app package ID
            
        Returns:
            App package ID or None if invalid
        """
        if not app_input or not isinstance(app_input, str):
            print("❌ Invalid input: empty or not a string")
            return None
        
        app_input = app_input.strip()
        print(f"\n🔍 Parsing input: {app_input[:100]}...")
        
        # Check if it's a URL
        if "play.google.com" in app_input or app_input.startswith("http"):
            print("  - Detected URL format")
            # Extract app ID from URL
            match = re.search(r'id=([a-zA-Z0-9._]+)', app_input)
            if match:
                app_id = match.group(1)
                print(f"  ✓ Extracted app ID: {app_id}")
                return app_id
            else:
                print("  ❌ Could not extract app ID from URL")
                return None
        else:
            # Assume it's already an app ID
            # Validate format (should be like com.company.app)
            if re.match(r'^[a-zA-Z0-9._]+$', app_input):
                print(f"  ✓ Valid app ID format: {app_input}")
                return app_input
            else:
                print(f"  ❌ Invalid app ID format: {app_input}")
                return None
        
    def find_app(self, app_identifier: str) -> Optional[Dict[str, Any]]:
        """
        Find app by package ID or URL.
        
        Args:
            app_identifier: Package ID or Play Store URL
        
        Returns:
            App info dict or None if not found
        """
        print(f"\n{'='*60}")
        print(f"🔍 APP LOOKUP")
        print(f"{'='*60}")
        
        # Extract app ID from URL if needed
        app_id = self.extract_app_id(app_identifier)
        
        if not app_id:
            print("❌ Failed to parse app identifier")
            return None
        
        print(f"\n📱 Fetching app details for: {app_id}")
        
        # Try multiple times with different parameters
        for attempt in range(self.max_retries):
            try:
                if attempt > 0:
                    print(f"  🔄 Retry attempt {attempt + 1}/{self.max_retries}")
                
                print(f"  - Calling Play Store API...")
                 
                result = app(
                    app_id,
                    lang='en',
                    country='us'
                )
                
                if result and isinstance(result, dict):
                    print(f"\n✓ APP FOUND!")
                    print(f"  - Title: {result.get('title', 'Unknown')}")
                    print(f"  - Package: {result.get('appId', app_id)}")
                    print(f"  - Developer: {result.get('developer', 'Unknown')}")
                    print(f"  - Rating: {result.get('score', 'N/A')}")
                    print(f"  - Total Reviews: {result.get('reviews', 'N/A'):,}" if result.get('reviews') else "  - Total Reviews: N/A")
                    print(f"  - Installs: {result.get('realInstalls', result.get('installs', 'N/A'))}")
                    return result
                
            except Exception as e:
                error_msg = str(e)
                print(f"  ❌ Attempt {attempt + 1} failed: {error_msg}")
                logger.error(f"App lookup error (attempt {attempt + 1}): {error_msg}", exc_info=True)
                
                # Check for specific error types
                if "404" in error_msg or "not found" in error_msg.lower():
                    print(f"\n❌ APP NOT FOUND")
                    print(f"  The app '{app_id}' does not exist or is not available in the US Play Store.")
                    print(f"\n💡 Tips:")
                    print(f"  - Verify the package ID is correct")
                    print(f"  - Check if the app is available in your region")
                    print(f"  - Try accessing the app directly: https://play.google.com/store/apps/details?id={app_id}")
                    return None
                
                # Wait before retry
                if attempt < self.max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"  ⏳ Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
        
        print(f"\n❌ Failed to fetch app after {self.max_retries} attempts")
        return None
    
    def scrape_reviews(self, app_id: str, start_date: str = "2024-06-01",
                  end_date: Optional[str] = None, app_name: Optional[str] = None,
                  max_reviews: int = 2000) -> Optional[str]:
        """
        Scrape reviews from Google Play Store - SIMPLIFIED VERSION.
        Just fetches the requested number of reviews without continuation token complexity.

        Args:
            app_id: Package ID of the app (e.g., "com.swiggy.android")
            start_date: Start date for review scraping (YYYY-MM-DD)
            end_date: End date for review scraping (YYYY-MM-DD), defaults to today
            app_name: Optional app name for file naming
            max_reviews: Maximum number of reviews to fetch (default: 2000)

        Returns:
            Path to saved JSONL file or None if failed
        """
        print(f"\n{'='*60}")
        print(f"📱 STARTING REVIEW SCRAPING")
        print(f"{'='*60}")

        # Extract app ID if URL was passed
        app_id = self.extract_app_id(app_id)
        if not app_id:
            print("❌ Invalid app ID")
            return None

        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        # Validate dates
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")

            if start_dt > end_dt:
                print("❌ Start date must be before end date")
                return None

            print(f"📅 Date range: {start_date} to {end_date}")
            print(f"   ({(end_dt - start_dt).days} days)")

        except ValueError as e:
            print(f"❌ Invalid date format: {str(e)}")
            print("   Use YYYY-MM-DD format")
            return None

        # Setup output file
        if not app_name:
            app_name = app_id.split(".")[-1] if app_id else "app"

        from backend.utils.progress_tracker import ProgressTracker
        tracker = ProgressTracker(app_name)
        output_file = tracker.reviews_file

        print(f"💾 Output file: {output_file.name}")
        print(f"\n🚀 Starting simple scrape for: {app_id}")
        print(f"   Fetching up to {max_reviews:,} reviews...")

        all_reviews = []
        total_fetched = 0
        total_in_range = 0

        try:
            # SIMPLIFIED: Just fetch reviews in one go, no continuation token
            print(f"\n📥 Fetching reviews...")

            result = reviews(
                app_id,
                lang='en',
                # country='us',
                country='in',
                sort=Sort.NEWEST,
                count=min(max_reviews, 200)  # Play Store API max is 200 per request
            )

            # Handle API response
            if isinstance(result, tuple) and len(result) == 2:
                batch_reviews, _ = result
            else:
                print(f"  ⚠️  Unexpected API response format")
                return None

            if not batch_reviews:
                print(f"  ℹ️  No reviews returned")
                return None

            print(f"  ✓ Received {len(batch_reviews)} reviews from API")
            total_fetched = len(batch_reviews)

            # Filter reviews by date range
            print(f"\n🔍 Filtering by date range...")
            for review in batch_reviews:
                try:
                    # Parse review date
                    review_date_raw = review.get("at", "")
                    if not review_date_raw:
                        continue

                    # Handle both datetime objects and strings
                    if isinstance(review_date_raw, datetime):
                        review_date = review_date_raw
                    elif isinstance(review_date_raw, str):
                        try:
                            review_date = datetime.fromisoformat(review_date_raw.replace('Z', '+00:00'))
                        except:
                            review_date = datetime.strptime(review_date_raw[:10], "%Y-%m-%d")
                    else:
                        continue

                    review_date_simple = review_date.replace(tzinfo=None)

                    # Check if in date range
                    if start_dt <= review_date_simple <= end_dt:
                        # Convert datetime to ISO string for JSON serialization
                        at_str = review_date_simple.isoformat() if isinstance(review.get('at'), datetime) else review.get('at')
                        repliedAt_str = review.get('repliedAt').isoformat() if isinstance(review.get('repliedAt'), datetime) else review.get('repliedAt')

                        all_reviews.append({
                            'reviewId': review.get('reviewId'),
                            'userName': review.get('userName'),
                            'userImage': review.get('userImage'),
                            'content': review.get('content'),
                            'score': review.get('score'),
                            'thumbsUpCount': review.get('thumbsUpCount'),
                            'reviewCreatedVersion': review.get('reviewCreatedVersion'),
                            'at': at_str,
                            'replyContent': review.get('replyContent'),
                            'repliedAt': repliedAt_str,
                            'appVersion': review.get('appVersion'),
                        })
                        total_in_range += 1

                except Exception as e:
                    logger.warning(f"Error parsing review: {str(e)}")
                    continue

            # Save results
            print(f"\n{'='*60}")
            print(f"💾 SAVING RESULTS")
            print(f"{'='*60}")

            if all_reviews:
                self._save_reviews(all_reviews, output_file)
                print(f"✓ Saved {len(all_reviews)} reviews to:")
                print(f"  {output_file.absolute()}")

                # Summary statistics
                print(f"\n📊 SUMMARY")
                print(f"{'='*60}")
                print(f"Total reviews fetched: {total_fetched:,}")
                print(f"Reviews in date range: {total_in_range:,}")

                if all_reviews:
                    scores = [r['score'] for r in all_reviews if r.get('score')]
                    if scores:
                        avg_score = sum(scores) / len(scores)
                        print(f"Average rating: {avg_score:.2f}/5")

                        # Rating distribution
                        rating_dist = {i: scores.count(i) for i in range(1, 6)}
                        print(f"\nRating distribution:")
                        for rating in range(5, 0, -1):
                            count = rating_dist.get(rating, 0)
                            bar = "█" * (count // max(1, max(rating_dist.values()) // 20))
                            print(f"  {rating}★: {count:4d} {bar}")

                return str(output_file)
            else:
                print("⚠️  No reviews found in the specified date range")
                print(f"   Date range: {start_date} to {end_date}")
                print(f"\n💡 Tips:")
                print(f"   - Try a wider date range")
                print(f"   - Check if the app has any reviews")
                print(f"   - Verify the app is available in the US region")
                return None

        except Exception as e:
            print(f"\n❌ CRITICAL ERROR: {str(e)}")
            logger.error(f"Critical scraping error: {str(e)}", exc_info=True)
            return None
    
    def _save_reviews(self, reviews_list: List[Dict[str, Any]], filepath: Path) -> None:
        """Save reviews to JSONL file"""
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                for review in reviews_list:
                    f.write(json.dumps(review, ensure_ascii=False) + "\n")
            print(f"  ✓ File written successfully")
        except Exception as e:
            print(f"  ❌ Error writing file: {str(e)}")
            raise
    
    def load_reviews(self, filepath: str) -> List[Dict[str, Any]]:
        """Load reviews from JSONL file"""
        print(f"\n📂 Loading reviews from: {filepath}")
        reviews_list = []
        
        try:
            if not Path(filepath).exists():
                print(f"❌ File not found: {filepath}")
                return []
            
            with open(filepath, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    if line.strip():
                        try:
                            reviews_list.append(json.loads(line))
                        except json.JSONDecodeError as e:
                            print(f"⚠️  Error parsing line {line_num}: {str(e)}")
                            continue
            
            print(f"✓ Loaded {len(reviews_list)} reviews")
            return reviews_list
            
        except Exception as e:
            print(f"❌ Error loading reviews: {str(e)}")
            logger.error(f"Load error: {str(e)}", exc_info=True)
            return []


# Example usage
if __name__ == "__main__":
    print("="*60)
    print("Google Play Store Review Scraper")
    print("="*60)
    
    # Initialize scraper
    scraper = PlayStoreScraper(
        data_dir="data",
        delay_seconds=2,
        reviews_per_batch=200
    )
    
    # Example: Scrape Swiggy reviews
    # Can accept either format:
    app_input = "com.swiggy.android"
    # OR: app_input = "https://play.google.com/store/apps/details?id=com.swiggy.android"
    
    # First, verify the app exists
    app_info = scraper.find_app(app_input)
    
    if app_info:
        # Scrape reviews from last 3 months
        output_file = scraper.scrape_reviews(
            app_id=app_input,
            start_date="2024-07-01",
            end_date="2024-10-16",
            app_name="swiggy",
            max_reviews=5000
        )
        
        if output_file:
            print(f"\n✅ SUCCESS! Reviews saved to: {output_file}")
            
            # Load and display sample
            reviews = scraper.load_reviews(output_file)
            if reviews:
                print(f"\n📝 Sample review:")
                sample = reviews[0]
                print(f"  User: {sample.get('userName', 'Anonymous')}")
                print(f"  Rating: {sample.get('score', 'N/A')}/5")
                print(f"  Date: {sample.get('at', 'N/A')}")
                content = sample.get('content', 'N/A')
                print(f"  Content: {content[:100]}{'...' if len(content) > 100 else ''}")
        else:
            print("\n❌ FAILED: Could not scrape reviews")
    else:
        print("\n❌ FAILED: Could not find app")
        print("\n💡 Troubleshooting:")
        print("  1. Check your internet connection")
        print("  2. Verify the package ID is correct")
        print("  3. Try installing google-play-scraper: pip install google-play-scraper")
        print("  4. Check if you can access Play Store in your browser")