import feedparser
from datetime import datetime
import hashlib
from typing import List, Dict, Any, Optional


def get_hash(entries: List[Dict[str, str]]) -> str:
    texts = ""
    for entry in entries:
        texts += (
            str(entry.get("id", ""))
            + str(entry.get("title", ""))
            + str(entry.get("published_date", ""))
        )
    return hashlib.md5(texts.encode()).hexdigest()


def parse_feed_entries(entries: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    parsed_entries = []
    for entry in entries:
        content = entry.get("content") or entry.get("description") or ""
        published = (
            entry.get("published")
            or entry.get("updated")
            or entry.get("pubDate")
            or entry.get("created")
            or datetime.now().isoformat()
        )
        entry_id = entry.get("id") or entry.get("link", "")
        link = entry.get("link", "")
        summary = entry.get("summary", "")
        title = entry.get("title", "")
        parsed_entries.append(
            {
                "title": title,
                "link": link,
                "summary": summary,
                "content": content,
                "published_date": published,
                "entry_id": entry_id,
            }
        )
    return parsed_entries


def is_rss_feed(feed_data: Any) -> bool:
    return feed_data.bozo and hasattr(feed_data, "bozo_exception")


def get_feed_data(
    feed_url: str, etag: Optional[str] = None, modified: Optional[Any] = None
) -> Dict[str, Any]:
    feed_data = feedparser.parse(feed_url, etag=etag, modified=modified)
    if is_rss_feed(feed_data):
        return {
            "is_rss_feed": False,
            "parsed_entries": None,
            "modified": None,
            "status": None,
            "current_hash": None,
            "etag": None,
        }
    status = feed_data.get("status", 200)
    etag = feed_data.get("etag", None)
    modified = feed_data.get("modified")
    entries = feed_data.get("entries", [])
    parsed_entries = parse_feed_entries(entries)
    current_hash = get_hash(parsed_entries)
    return {
        "parsed_entries": parsed_entries,
        "modified": modified,
        "status": status,
        "current_hash": current_hash,
        "etag": etag,
        "is_rss_feed": True,
    }
