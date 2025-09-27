import time
from tools.social.browser import create_browser_context
from tools.social.x_post_extractor import x_post_extractor
from tools.social.x_agent import analyze_posts_sentiment
from tools.social.db import create_connection, setup_database, check_and_store_post, update_posts_with_analysis


def crawl_x_profile(profile_url, db_file="x_posts.db"):
    if not profile_url.startswith("http"):
        profile_url = f"https://x.com/{profile_url}"

    conn = create_connection(db_file)
    setup_database(conn)
    seen_post_ids = set()
    analysis_queue = []
    queue_post_ids = []
    post_count = 0
    batch_size = 5
    scroll_count = 0

    with create_browser_context() as (browser_context, page):
        page.goto(profile_url)
        time.sleep(5)

        try:
            while True:
                tweet_articles = page.query_selector_all('article[role="article"]')
                for article in tweet_articles:
                    article_id = article.evaluate('(element) => element.getAttribute("id")')
                    if article_id in seen_post_ids:
                        continue

                    show_more = article.query_selector('button[data-testid="tweet-text-show-more-link"]')
                    if show_more:
                        try:
                            show_more.click()
                            time.sleep(1)
                        except Exception as e:
                            pass

                    tweet_html = article.evaluate("(element) => element.outerHTML")
                    post_data = x_post_extractor(tweet_html)

                    post_id = post_data.get("post_id")
                    if not post_id or post_data.get("is_ad", False):
                        continue

                    seen_post_ids.add(post_id)
                    post_count += 1

                    needs_analysis = check_and_store_post(conn, post_data)

                    if needs_analysis and post_data.get("post_text"):
                        analysis_queue.append(post_data)
                        queue_post_ids.append(post_id)

                if len(analysis_queue) >= batch_size:
                    analysis_batch = analysis_queue[:batch_size]
                    batch_post_ids = queue_post_ids[:batch_size]

                    analysis_queue = analysis_queue[batch_size:]
                    queue_post_ids = queue_post_ids[batch_size:]

                    try:
                        analysis_results = analyze_posts_sentiment(analysis_batch)

                        update_posts_with_analysis(conn, batch_post_ids, analysis_results)
                    except Exception:
                        pass

                page.evaluate("window.scrollBy(0, 800)")
                time.sleep(3)

                scroll_count += 1
                if scroll_count >= 30:
                    break

        except KeyboardInterrupt:
            if analysis_queue:
                try:
                    analysis_results = analyze_posts_sentiment(analysis_queue)
                    update_posts_with_analysis(conn, queue_post_ids, analysis_results)
                except Exception:
                    pass

            conn.close()
            return post_count
        return post_count