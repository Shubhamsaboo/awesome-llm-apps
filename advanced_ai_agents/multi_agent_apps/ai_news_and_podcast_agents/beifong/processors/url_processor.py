from db.config import get_tracking_db_path
from db.feeds import get_uncrawled_entries
from db.articles import store_crawled_article, update_entry_status
from utils.crawl_url import get_web_data


def crawl_pending_entries(tracking_db_path=None, batch_size=20, delay_range=(1, 3), max_attempts=3):
    if tracking_db_path is None:
        tracking_db_path = get_tracking_db_path()
    entries = get_uncrawled_entries(tracking_db_path, limit=batch_size, max_attempts=max_attempts)
    stats = {
        "total_entries": len(entries),
        "success_count": 0,
        "failed_count": 0,
        "skipped_count": 0,
    }
    for entry in entries:
        entry_id = entry["id"]
        url = entry["link"]
        if not url or url.strip() == "":
            update_entry_status(tracking_db_path, entry_id, "skipped")
            stats["skipped_count"] += 1
            continue
        print(f"Crawling URL: {url}")
        try:
            web_data = get_web_data(url)
            if not web_data or not web_data["raw_html"]:
                print(f"No content retrieved for {url}")
                update_entry_status(tracking_db_path, entry_id, "failed")
                stats["failed_count"] += 1
                continue
            success = store_crawled_article(tracking_db_path, entry, web_data["raw_html"], web_data["metadata"])
            if success:
                update_entry_status(tracking_db_path, entry_id, "success")
                stats["success_count"] += 1
                print(f"Successfully crawled: {url}")
            else:
                update_entry_status(tracking_db_path, entry_id, "failed")
                stats["failed_count"] += 1
                print(f"Failed to store: {url} (likely duplicate)")
        except Exception as e:
            print(f"Error crawling {url}: {str(e)}")
            update_entry_status(tracking_db_path, entry_id, "failed")
            stats["failed_count"] += 1
    return stats


def print_stats(stats):
    print("\nCrawl Statistics:")
    print(f"Total entries processed: {stats['total_entries']}")
    print(f"Successfully crawled: {stats['success_count']}")
    print(f"Failed: {stats['failed_count']}")
    print(f"Skipped (no URL): {stats['skipped_count']}")


def crawl_in_batches(tracking_db_path=None, batch_size=20, total_batches=5, delay_between_batches=10):
    if tracking_db_path is None:
        tracking_db_path = get_tracking_db_path()
    total_stats = {
        "total_entries": 0,
        "success_count": 0,
        "failed_count": 0,
        "skipped_count": 0,
    }
    for i in range(total_batches):
        print(f"\nProcessing batch {i + 1}/{total_batches}")
        batch_stats = crawl_pending_entries(tracking_db_path=tracking_db_path, batch_size=batch_size)
        total_stats["total_entries"] += batch_stats["total_entries"]
        total_stats["success_count"] += batch_stats["success_count"]
        total_stats["failed_count"] += batch_stats["failed_count"]
        total_stats["skipped_count"] += batch_stats["skipped_count"]
        if batch_stats["total_entries"] == 0:
            print("No more entries to process")
            break
        if i < total_batches - 1:
            print(f"Waiting {delay_between_batches} seconds before next batch...")
    return total_stats


if __name__ == "__main__":
    stats = crawl_in_batches(batch_size=20, total_batches=50)
    print_stats(stats)
