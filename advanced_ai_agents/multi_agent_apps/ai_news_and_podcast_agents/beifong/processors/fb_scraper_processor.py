
import sys
from datetime import datetime
from db.config import get_social_media_db_path
from tools.social.fb_scraper import crawl_facebook_feed


def main():
    print(f"Starting facebook.com feed scraping at {datetime.now().isoformat()}")
    db_path = get_social_media_db_path()

    try:
        print("Running facebook.com feed scraper")
        posts = crawl_facebook_feed("https://facebook.com", db_file=db_path)
        print(f"facebook.com scraping completed at {datetime.now().isoformat()}")
        print(f"Collected {posts} posts from feed")

    except Exception as e:
        print(f"Error executing facebook.com feed scraper: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()