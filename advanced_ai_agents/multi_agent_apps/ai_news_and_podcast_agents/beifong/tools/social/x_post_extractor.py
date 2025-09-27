import os
from bs4 import BeautifulSoup
import re
import json


def check_ad(soup):
    is_ad = False
    ad_label = soup.find(
        lambda tag: tag.name and tag.text and tag.text.strip() == "Ad" and "r-bcqeeo" in tag.get("class", []) if hasattr(tag, "get") else False
    )
    if ad_label:
        is_ad = True
    username_element = soup.select_one("div[data-testid='User-Name'] a[role='link'] span")
    if username_element and username_element.text.strip() in [
        "Premium",
        "Twitter",
        "X",
    ]:
        is_ad = True
    handle_element = soup.select_one("div[data-testid='User-Name'] div[dir='ltr'] span")
    if handle_element and "@premium" in handle_element.text:
        is_ad = True
    ad_tracking_links = soup.select("a[href*='referring_page=ad_'], a[href*='twclid=']")
    if ad_tracking_links:
        is_ad = True
    return is_ad


def x_post_extractor(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    data = {"platform": "x.com"}
    data["media"] = []
    data["is_ad"] = check_ad(soup)
    user_element = soup.find("div", {"data-testid": "User-Name"})
    if user_element:
        display_name_element = user_element.find(lambda tag: tag.name and (tag.name == "span" or tag.name == "div") and "Henrik" in tag.text)
        if display_name_element:
            data["user_display_name"] = display_name_element.text.strip()
        username_element = user_element.find(lambda tag: tag.name == "a" and "@" in tag.text)
        if username_element:
            data["user_handle"] = username_element.text.strip()
        profile_pic = soup.select_one("[data-testid='UserAvatar-Container-HenrikTaro'] img")
        if profile_pic and profile_pic.has_attr("src"):
            data["user_profile_pic_url"] = profile_pic["src"]

    time_element = soup.find("time")
    if time_element:
        if time_element.has_attr("datetime"):
            data["post_timestamp"] = time_element["datetime"]
        data["post_display_time"] = time_element.text.strip()

    post_link = soup.select_one("a[href*='/status/']")
    if post_link and post_link.has_attr("href"):
        status_url = post_link["href"]
        post_id_match = re.search(r"/status/(\d+)", status_url)
        if post_id_match:
            data["post_id"] = post_id_match.group(1)
            data["post_url"] = f"https://twitter.com{status_url}"

    text_element = soup.find("div", {"data-testid": "tweetText"})
    if text_element:
        data["post_text"] = text_element.get_text(strip=True)
        mentions = []
        mention_elements = text_element.select("a[href^='/'][role='link']")
        for mention in mention_elements:
            mention_text = mention.text.strip()
            if mention_text.startswith("@"):
                mentions.append(mention_text)

        if mentions:
            data["post_mentions"] = ",".join(mentions)

    reply_button = soup.find("button", {"data-testid": "reply"})
    if reply_button:
        count_span = reply_button.select_one("span[data-testid='app-text-transition-container'] span span")
        if count_span:
            data["engagement_reply_count"] = count_span.text.strip()

    retweet_button = soup.find("button", {"data-testid": "retweet"})
    if retweet_button:
        count_span = retweet_button.select_one("span[data-testid='app-text-transition-container'] span span")
        if count_span:
            data["engagement_retweet_count"] = count_span.text.strip()

    like_button = soup.find("button", {"data-testid": "like"})
    if like_button:
        count_span = like_button.select_one("span[data-testid='app-text-transition-container'] span span")
        if count_span:
            data["engagement_like_count"] = count_span.text.strip()

    bookmark_button = soup.find("button", {"data-testid": "bookmark"})
    if bookmark_button:
        count_span = bookmark_button.select_one("span[data-testid='app-text-transition-container'] span span")
        if count_span:
            data["engagement_bookmark_count"] = count_span.text.strip()

    views_element = soup.select_one("a[href*='/analytics']")
    if views_element:
        views_span = views_element.select_one("span[data-testid='app-text-transition-container'] span span")
        if views_span:
            data["engagement_view_count"] = views_span.text.strip()

    media_elements = soup.find_all("div", {"data-testid": "tweetPhoto"})
    for media in media_elements:
        img = media.find("img")
        if img and img.has_attr("src"):
            data["media"].append({"type": "image", "url": img["src"]})

    data["media_count"] = len(data["media"])

    return data