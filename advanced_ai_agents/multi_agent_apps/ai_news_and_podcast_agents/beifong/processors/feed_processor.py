import time
import random
from utils.rss_feed_parser import get_feed_data
from db.config import get_sources_db_path, get_tracking_db_path
from db.feeds import (
    get_active_feeds,
    count_active_feeds,
    get_feed_tracking_info,
    update_feed_tracking,
    store_feed_entries,
    update_tracking_info,
)


def fetch_and_process_feeds(sources_db_path=None, tracking_db_path=None, delay_between_feeds=2, batch_size=100):
    if sources_db_path is None:
        sources_db_path = get_sources_db_path()
    if tracking_db_path is None:
        tracking_db_path = get_tracking_db_path()
    total_feeds = count_active_feeds(sources_db_path)
    stats = {
        "total_feeds": total_feeds,
        "processed_feeds": 0,
        "new_entries": 0,
        "unchanged_feeds": 0,
        "failed_feeds": 0,
    }
    offset = 0
    while offset < total_feeds:
        feeds = get_active_feeds(sources_db_path, limit=batch_size, offset=offset)
        if not feeds:
            break
        update_tracking_info(tracking_db_path, feeds)
        for feed in feeds:
            feed_id = feed["id"]
            source_id = feed["source_id"]
            feed_url = feed["feed_url"]
            tracking_info = get_feed_tracking_info(tracking_db_path, feed_id)
            etag = tracking_info.get("last_etag") if tracking_info else None
            modified = tracking_info.get("last_modified") if tracking_info else None
            last_hash = tracking_info.get("entry_hash") if tracking_info else None
            try:
                feed_data = get_feed_data(feed_url, etag=etag, modified=modified)
                if not feed_data["is_rss_feed"]:
                    print(f"Feed {feed_url} is not a valid RSS feed")
                    stats["failed_feeds"] += 1
                    continue
                if feed_data["status"] == 304:
                    print(f"Feed {feed_url} not modified since last check")
                    stats["unchanged_feeds"] += 1
                    continue
                current_hash = feed_data["current_hash"]
                if last_hash and current_hash == last_hash:
                    print(f"Feed {feed_url} content unchanged based on hash")
                    stats["unchanged_feeds"] += 1
                    continue
                parsed_entries = feed_data["parsed_entries"]
                if parsed_entries:
                    new_entries = store_feed_entries(tracking_db_path, feed_id, source_id, parsed_entries)
                    stats["new_entries"] += new_entries
                    print(f"Stored {new_entries} new entries from {feed_url}")
                update_feed_tracking(
                    tracking_db_path,
                    feed_id,
                    feed_data["etag"],
                    feed_data["modified"],
                    current_hash,
                )
                stats["processed_feeds"] += 1
            except Exception as e:
                print(f"Error processing feed {feed_url}: {str(e)}")
                stats["failed_feeds"] += 1
            time.sleep(random.uniform(1, delay_between_feeds))
        offset += batch_size
    return stats


def print_stats(stats):
    print("\nFeed Processing Statistics:")
    print(f"Total feeds: {stats['total_feeds']}")
    print(f"Processed feeds: {stats['processed_feeds']}")
    print(f"Unchanged feeds: {stats['unchanged_feeds']}")
    print(f"Failed feeds: {stats['failed_feeds']}")
    print(f"New entries: {stats['new_entries']}")


if __name__ == "__main__":
    stats = fetch_and_process_feeds()
    print_stats(stats)
