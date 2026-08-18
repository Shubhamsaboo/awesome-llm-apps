import os
import sqlite3
import sys
from datetime import datetime, timezone

from playwright.sync_api import Error as PlaywrightError

from db.config import get_social_media_db_path
from tools.social.x_scraper import crawl_x_profile
from tools.social.xquik_scraper import MAX_TIMELINE_PAGES, crawl_xquik_timeline


def get_x_backend(environ=None):
    environ = os.environ if environ is None else environ
    backend = environ.get("X_SOCIAL_BACKEND", "browser").strip().lower()
    if backend not in {"browser", "xquik"}:
        raise ValueError("X_SOCIAL_BACKEND must be browser or xquik")
    return backend


def get_xquik_max_pages(environ=None):
    environ = os.environ if environ is None else environ
    raw_value = environ.get("XQUIK_MAX_PAGES", "1")
    try:
        max_pages = int(raw_value)
    except ValueError as error:
        raise ValueError("XQUIK_MAX_PAGES must be an integer") from error
    if not 1 <= max_pages <= MAX_TIMELINE_PAGES:
        raise ValueError(f"XQUIK_MAX_PAGES must be between 1 and {MAX_TIMELINE_PAGES}")
    return max_pages


def main():
    print(f"Starting X.com feed scraping at {datetime.now(timezone.utc).isoformat()}")
    db_path = get_social_media_db_path()

    try:
        backend = get_x_backend()
        print(f"Running X.com feed scraper with {backend} backend")
        if backend == "xquik":
            posts = crawl_xquik_timeline(
                db_file=db_path,
                max_pages=get_xquik_max_pages(),
            )
        else:
            posts = crawl_x_profile("home", db_file=db_path)
        print(f"X.com feed scraping completed at {datetime.now(timezone.utc).isoformat()}")
        print(f"Collected {posts} posts from feed")

    except (OSError, PlaywrightError, RuntimeError, TypeError, ValueError, sqlite3.Error) as e:
        print(f"Error executing X.com feed scraper: {e!s}")
        sys.exit(1)


if __name__ == "__main__":
    main()
