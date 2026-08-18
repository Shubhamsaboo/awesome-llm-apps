import time
from contextlib import suppress

from playwright.sync_api import Error as PlaywrightError

from tools.social.browser import create_browser_context
from tools.social.db import create_connection, setup_database
from tools.social.x_ingestion import PostIngestor
from tools.social.x_post_extractor import x_post_extractor

MAX_SCROLLS = 30


def crawl_x_profile(profile_url, db_file="x_posts.db", analyze_posts=None):
    if not profile_url.startswith("http"):
        profile_url = f"https://x.com/{profile_url}"

    conn = create_connection(db_file)
    setup_database(conn)
    ingestor = PostIngestor(conn, analyze_posts=analyze_posts)
    scroll_count = 0

    try:
        with create_browser_context() as (_browser_context, page):
            page.goto(profile_url)
            time.sleep(5)

            try:
                while True:
                    tweet_articles = page.query_selector_all('article[role="article"]')
                    for article in tweet_articles:
                        show_more = article.query_selector('button[data-testid="tweet-text-show-more-link"]')
                        if show_more:
                            with suppress(PlaywrightError):
                                show_more.click()
                                time.sleep(1)

                        tweet_html = article.evaluate("(element) => element.outerHTML")
                        ingestor.add(x_post_extractor(tweet_html))

                    page.evaluate("window.scrollBy(0, 800)")
                    time.sleep(3)

                    scroll_count += 1
                    if scroll_count >= MAX_SCROLLS:
                        break
            except KeyboardInterrupt:
                pass
    finally:
        try:
            ingestor.flush()
        finally:
            conn.close()
    return ingestor.post_count
