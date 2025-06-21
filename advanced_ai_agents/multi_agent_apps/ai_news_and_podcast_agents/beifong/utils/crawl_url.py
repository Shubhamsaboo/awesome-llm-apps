import requests
from bs4 import BeautifulSoup
import random
from typing import Dict, List, TypedDict


class MetadataDict(TypedDict):
    title: str
    description: str
    og: Dict[str, str]
    twitter: Dict[str, str]
    other_meta: Dict[str, str]


class WebData(TypedDict):
    raw_html: str
    metadata: MetadataDict


USER_AGENTS: List[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
]
HEADERS: Dict[str, str] = {
    "User-Agent": random.choice(USER_AGENTS),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


def extract_meta_tags(soup: BeautifulSoup) -> MetadataDict:
    metadata: MetadataDict = {
        "title": "",
        "description": "",
        "og": {},
        "twitter": {},
        "other_meta": {},
    }
    title_tag = soup.find("title")
    if title_tag:
        metadata["title"] = title_tag.text.strip()
    for meta in soup.find_all("meta"):
        name = meta.get("name", "").lower()
        prop = meta.get("property", "").lower()
        content = meta.get("content", "")
        if prop.startswith("ogg:"):
            og_key = prop[3:]
            metadata["og"][og_key] = content
        elif prop.startswith("twitter:") or name.startswith("twitter:"):
            twitter_key = prop[8:] if prop.startswith("twitter:") else name[8:]
            metadata["twitter"][twitter_key] = content
        elif name in ["description", "keywords", "author", "robots", "viewport"]:
            metadata["other_meta"][name] = content
            if name == "description":
                metadata["description"] = content
    return metadata


def get_web_data(url: str) -> WebData:
    HEADERS["User-Agent"] = random.choice(USER_AGENTS)
    response = requests.get(url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")
    metadata = extract_meta_tags(soup)
    body = str(soup.find("body"))
    return {"raw_html": body, "metadata": metadata}
