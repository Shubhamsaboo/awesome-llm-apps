import time
import json
from tools.social.browser import create_browser_context
from tools.social.fb_post_extractor import parse_facebook_posts, normalize_facebook_posts_batch
from tools.social.x_agent import analyze_posts_sentiment
from tools.social.db import create_connection, setup_database, check_and_store_post, update_posts_with_analysis


def contains_facebook_posts(json_obj):
    if not isinstance(json_obj, dict):
        return False
    try:
        data = json_obj.get("data", {})
        viewer = data.get("viewer", {})
        news_feed = viewer.get("news_feed", {})
        edges = news_feed.get("edges", [])

        if isinstance(edges, list) and len(edges) > 0:
            for edge in edges:
                if isinstance(edge, dict) and "node" in edge:
                    node = edge["node"]
                    if isinstance(node, dict) and node.get("__typename") == "Story":
                        return True
        return False
    except (KeyError, TypeError, AttributeError):
        return False


def process_facebook_graphql_response(response_text, seen_post_ids, analysis_queue, queue_post_ids, conn):
    posts_processed = 0
    if not response_text:
        return posts_processed
    lines = response_text.split("\n")
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            json_obj = json.loads(line)
            if contains_facebook_posts(json_obj):
                parsed_posts = parse_facebook_posts(json_obj)
                if not parsed_posts:
                    continue
                normalized_posts = normalize_facebook_posts_batch(parsed_posts)
                for post_data in normalized_posts:
                    post_id = post_data.get("post_id")
                    if not post_id or post_id in seen_post_ids:
                        continue
                    seen_post_ids.add(post_id)
                    posts_processed += 1
                    needs_analysis = check_and_store_post(conn, post_data)
                    if needs_analysis and post_data.get("post_text"):
                        analysis_queue.append(post_data)
                        queue_post_ids.append(post_id)
        except json.JSONDecodeError:
            continue
        except Exception as e:
            print(f"Error processing Facebook post: {e}")
            continue

    return posts_processed


def crawl_facebook_feed(target_url="https://facebook.com", db_file="fb_posts.db"):
    conn = create_connection(db_file)
    setup_database(conn)
    seen_post_ids = set()
    analysis_queue = []
    queue_post_ids = []
    post_count = 0
    batch_size = 5
    scroll_count = 0

    with create_browser_context() as (browser_context, page):

        def handle_response(response):
            nonlocal post_count, analysis_queue, queue_post_ids
            url = response.url
            if "/api/graphql/" not in url:
                return
            try:
                content_type = response.headers.get("content-type", "")
                if 'text/html; charset="utf-8"' not in content_type:
                    return
                response_text = response.text()
                posts_found = process_facebook_graphql_response(response_text, seen_post_ids, analysis_queue, queue_post_ids, conn)
                if posts_found > 0:
                    post_count += posts_found
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
            except Exception:
                pass

        page.on("response", handle_response)
        page.goto(target_url)
        time.sleep(5)

        def scroll_page():
            page.evaluate("window.scrollBy(0, window.innerHeight)")

        try:
            while True:
                scroll_page()
                time.sleep(3)
                scroll_count += 1
                if scroll_count >= 50:
                    break
        except KeyboardInterrupt:
            pass

        if analysis_queue:
            try:
                analysis_results = analyze_posts_sentiment(analysis_queue)
                update_posts_with_analysis(conn, queue_post_ids, analysis_results)
            except Exception:
                pass

        conn.close()
        return post_count
