import json
from datetime import datetime
from typing import Dict, Any
import re


def parse_facebook_posts(data):
    posts = []
    try:
        for post in data["data"]["viewer"]["news_feed"]["edges"]:
            posts.append(parse_facebook_post(post["node"]))
    except Exception as e:
        print(f"Error parsing post data: {e}")
    return posts


def parse_facebook_post(story_node: Dict[str, Any]) -> Dict[str, Any]:
    try:
        post_info = {
            "post_id": story_node.get("post_id"),
            "story_id": story_node.get("id"),
            "creation_time": None,
            "creation_time_formatted": None,
            "url": None,
        }
        creation_time_sources = [
            story_node.get("creation_time"),
            (story_node.get("comet_sections") or {}).get("context_layout", {}).get("story", {}).get("creation_time"),
            (story_node.get("comet_sections") or {}).get("timestamp", {}).get("story", {}).get("creation_time"),
        ]
        for source in creation_time_sources:
            if source:
                post_info["creation_time"] = source
                post_info["creation_time_formatted"] = datetime.fromtimestamp(source).strftime("%Y-%m-%d %H:%M:%S")
                break
        url_sources = [
            (story_node.get("comet_sections") or {}).get("content", {}).get("story", {}).get("wwwURL"),
            (story_node.get("comet_sections") or {}).get("feedback", {}).get("story", {}).get("story_ufi_container", {}).get("story", {}).get("url"),
            (story_node.get("comet_sections") or {})
            .get("feedback", {})
            .get("story", {})
            .get("story_ufi_container", {})
            .get("story", {})
            .get("shareable_from_perspective_of_feed_ufi", {})
            .get("url"),
            story_node.get("wwwURL"),
            story_node.get("url"),
        ]
        for source in url_sources:
            if source:
                post_info["url"] = source
                break
        message_info = extract_message_content(story_node)
        post_info.update(message_info)
        actors_info = extract_actors_info(story_node)
        post_info.update(actors_info)
        attachments_info = extract_attachments(story_node)
        post_info.update(attachments_info)
        engagement_info = extract_engagement_data(story_node)
        post_info.update(engagement_info)
        privacy_info = extract_privacy_info(story_node)
        post_info.update(privacy_info)
        return post_info
    except (KeyError, IndexError, TypeError) as e:
        print(f"Error parsing post data: {e}")
        return {}


def extract_message_content(story_node: Dict[str, Any]) -> Dict[str, Any]:
    message_info = {"message_text": "", "hashtags": [], "mentions": [], "links": []}
    try:
        message_sources = [
            (story_node.get("message") or {}).get("text", ""),
            ((((story_node.get("comet_sections") or {}).get("content") or {}).get("story") or {}).get("message") or {}).get("text", ""),
        ]
        for source in message_sources:
            if source:
                message_info["message_text"] = source
                break
        message_data = story_node.get("message", {})
        if "ranges" in message_data:
            for range_item in message_data["ranges"]:
                entity = range_item.get("entity", {})
                entity_type = entity.get("__typename")

                if entity_type == "Hashtag":
                    hashtag_text = message_info["message_text"][range_item["offset"] : range_item["offset"] + range_item["length"]]
                    message_info["hashtags"].append(
                        {
                            "text": hashtag_text,
                            "url": entity.get("url"),
                            "id": entity.get("id"),
                        }
                    )
                elif entity_type == "User":
                    mention_text = message_info["message_text"][range_item["offset"] : range_item["offset"] + range_item["length"]]
                    message_info["mentions"].append(
                        {
                            "text": mention_text,
                            "url": entity.get("url"),
                            "id": entity.get("id"),
                        }
                    )
    except (KeyError, TypeError):
        pass
    return message_info


def extract_actors_info(story_node: Dict[str, Any]) -> Dict[str, Any]:
    actors_info = {
        "author_name": "",
        "author_id": "",
        "author_url": "",
        "author_profile_picture": "",
        "is_verified": False,
        "page_info": {},
    }
    try:
        actors = story_node.get("actors", [])
        if actors:
            main_actor = actors[0]
            actors_info.update(
                {
                    "author_name": main_actor.get("name", ""),
                    "author_id": main_actor.get("id", ""),
                    "author_url": main_actor.get("url", ""),
                }
            )
        context_sections = (story_node.get("comet_sections") or {}).get("context_layout", {})
        if context_sections:
            actor_photo = (context_sections.get("story") or {}).get("comet_sections", {}).get("actor_photo", {})
            if actor_photo:
                story_actors = (actor_photo.get("story") or {}).get("actors", [])
                if story_actors:
                    profile_pic = story_actors[0].get("profile_picture", {})
                    actors_info["author_profile_picture"] = profile_pic.get("uri", "")
    except (KeyError, TypeError, IndexError):
        pass
    return actors_info


def extract_attachments(story_node: Dict[str, Any]) -> Dict[str, Any]:
    attachments_info = {"attachments": [], "photos": [], "videos": [], "links": []}
    try:
        attachments = story_node.get("attachments", [])
        for attachment in attachments:
            attachment_data = {
                "type": attachment.get("__typename", ""),
                "style_list": attachment.get("style_list", []),
            }
            if "photo" in attachment.get("style_list", []):
                target = attachment.get("target", {})
                if target.get("__typename") == "Photo":
                    styles = attachment.get("styles", {})
                    if styles:
                        media = (styles.get("attachment") or {}).get("media", {})
                        photo_info = {
                            "id": target.get("id"),
                            "url": media.get("url", ""),
                            "width": (media.get("viewer_image") or {}).get("width"),
                            "height": (media.get("viewer_image") or {}).get("height"),
                            "image_uri": "",
                            "accessibility_caption": media.get("accessibility_caption", ""),
                        }
                        resolution_renderer = media.get("comet_photo_attachment_resolution_renderer", {})
                        if resolution_renderer:
                            image = resolution_renderer.get("image", {})
                            photo_info["image_uri"] = image.get("uri", "")

                        attachments_info["photos"].append(photo_info)
            attachments_info["attachments"].append(attachment_data)
    except (KeyError, TypeError):
        pass
    return attachments_info


def extract_engagement_data(story_node: Dict[str, Any]) -> Dict[str, Any]:
    """Extract likes, comments, shares, and other engagement metrics"""
    engagement_info = {
        "reaction_count": 0,
        "comment_count": 0,
        "share_count": 0,
        "reactions_breakdown": {},
        "top_reactions": [],
    }
    try:
        feedback_story = (story_node.get("comet_sections") or {}).get("feedback", {}).get("story", {})
        if feedback_story:
            ufi_container = (feedback_story.get("story_ufi_container") or {}).get("story", {})
            if ufi_container:
                feedback_context = ufi_container.get("feedback_context", {})
                feedback_target = feedback_context.get("feedback_target_with_context", {})

                if feedback_target:
                    summary_renderer = feedback_target.get("comet_ufi_summary_and_actions_renderer", {})
                    if summary_renderer:
                        feedback_data = summary_renderer.get("feedback", {})
                        if "i18n_reaction_count" in feedback_data:
                            engagement_info["reaction_count"] = int(feedback_data["i18n_reaction_count"])
                        elif "reaction_count" in feedback_data and isinstance(feedback_data["reaction_count"], dict):
                            engagement_info["reaction_count"] = feedback_data["reaction_count"].get("count", 0)
                        if "i18n_share_count" in feedback_data:
                            engagement_info["share_count"] = int(feedback_data["i18n_share_count"])
                        elif "share_count" in feedback_data and isinstance(feedback_data["share_count"], dict):
                            engagement_info["share_count"] = feedback_data["share_count"].get("count", 0)
                        top_reactions = feedback_data.get("top_reactions", {})
                        if "edges" in top_reactions:
                            for edge in top_reactions["edges"]:
                                reaction_node = edge.get("node", {})
                                engagement_info["top_reactions"].append(
                                    {
                                        "reaction_id": reaction_node.get("id"),
                                        "name": reaction_node.get("localized_name"),
                                        "count": edge.get("reaction_count", 0),
                                    }
                                )
                    comment_rendering = feedback_target.get("comment_rendering_instance", {})
                    if comment_rendering:
                        comments = comment_rendering.get("comments", {})
                        engagement_info["comment_count"] = comments.get("total_count", 0)

    except (KeyError, TypeError, ValueError):
        pass
    return engagement_info


def extract_privacy_info(story_node: Dict[str, Any]) -> Dict[str, Any]:
    privacy_info = {"privacy_scope": "", "audience": ""}
    try:
        privacy_sources = [
            (story_node.get("comet_sections") or {}).get("context_layout", {}).get("story", {}).get("privacy_scope", {}),
            story_node.get("privacy_scope", {}),
            next(
                (
                    (meta.get("story") or {}).get("privacy_scope", {})
                    for meta in (story_node.get("comet_sections") or {})
                    .get("context_layout", {})
                    .get("story", {})
                    .get("comet_sections", {})
                    .get("metadata", [])
                    if isinstance(meta, dict) and meta.get("__typename") == "CometFeedStoryAudienceStrategy"
                ),
                {},
            ),
        ]
        for privacy_scope in privacy_sources:
            if privacy_scope and "description" in privacy_scope:
                privacy_info["privacy_scope"] = privacy_scope["description"]
                break
        if not privacy_info["privacy_scope"]:
            context_layout = (story_node.get("comet_sections") or {}).get("context_layout", {})
            if context_layout:
                story = context_layout.get("story", {})
                comet_sections = story.get("comet_sections", {})
                metadata = comet_sections.get("metadata", [])
                for meta_item in metadata:
                    if isinstance(meta_item, dict) and meta_item.get("__typename") == "CometFeedStoryAudienceStrategy":
                        story_data = meta_item.get("story", {})
                        privacy_scope = story_data.get("privacy_scope", {})
                        if privacy_scope:
                            privacy_info["privacy_scope"] = privacy_scope.get("description", "")
                            break
    except (KeyError, TypeError):
        pass
    return privacy_info


def normalize_facebook_post(fb_post_data):
    normalized = {
        "platform": "facebook.com",
        "post_id": fb_post_data.get("post_id", ""),
        "user_display_name": fb_post_data.get("author_name", ""),
        "user_handle": extract_handle_from_url(fb_post_data.get("author_url", "")),
        "user_profile_pic_url": fb_post_data.get("author_profile_picture", ""),
        "post_timestamp": format_timestamp(fb_post_data.get("creation_time")),
        "post_display_time": fb_post_data.get("creation_time_formatted", ""),
        "post_url": fb_post_data.get("url", ""),
        "post_text": fb_post_data.get("message_text", ""),
        "post_mentions": format_mentions(fb_post_data.get("mentions", [])),
        "engagement_reply_count": fb_post_data.get("comment_count", 0),
        "engagement_retweet_count": fb_post_data.get("share_count", 0),
        "engagement_like_count": fb_post_data.get("reaction_count", 0),
        "engagement_bookmark_count": 0,
        "engagement_view_count": 0,
        "media": format_media(fb_post_data),
        "media_count": calculate_media_count(fb_post_data),
        "is_ad": False,
        "sentiment": None,
        "categories": None,
        "tags": None,
        "analysis_reasoning": None,
    }
    return normalized


def extract_handle_from_url(author_url: str) -> str:
    if not author_url:
        return ""
    patterns = [
        r"facebook\.com/([^/?]+)",
        r"facebook\.com/profile\.php\?id=(\d+)",
        r"facebook\.com/pages/[^/]+/(\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, author_url)
        if match:
            return match.group(1)
    return ""


def format_timestamp(creation_time) -> str:
    if not creation_time:
        return ""
    try:
        if isinstance(creation_time, (int, float)):
            dt = datetime.fromtimestamp(creation_time)
            return dt.isoformat()
        elif isinstance(creation_time, str):
            return creation_time
    except (ValueError, TypeError):
        pass
    return ""


def format_mentions(mentions):
    if not mentions:
        return ""
    mention_texts = []
    for mention in mentions:
        if isinstance(mention, dict):
            text = mention.get("text", "")
            if text and not text.startswith("@"):
                text = f"@{text}"
            mention_texts.append(text)
        elif isinstance(mention, str):
            if not mention.startswith("@"):
                mention = f"@{mention}"
            mention_texts.append(mention)
    return ",".join(mention_texts)


def format_media(fb_post_data: Dict[str, Any]) -> str:
    media_items = []
    photos = fb_post_data.get("photos", [])
    for photo in photos:
        if isinstance(photo, dict):
            media_item = {
                "type": "image",
                "url": photo.get("image_uri") or photo.get("url", ""),
                "width": photo.get("width"),
                "height": photo.get("height"),
                "id": photo.get("id"),
                "accessibility_caption": photo.get("accessibility_caption", ""),
            }
            media_item = {k: v for k, v in media_item.items() if v is not None}
            media_items.append(media_item)

    videos = fb_post_data.get("videos", [])
    for video in videos:
        if isinstance(video, dict):
            media_item = {
                "type": "video",
                "url": video.get("url", ""),
                "id": video.get("id"),
            }
            media_item = {k: v for k, v in media_item.items() if v is not None}
            media_items.append(media_item)

    attachments = fb_post_data.get("attachments", [])
    for attachment in attachments:
        if isinstance(attachment, dict):
            attachment_type = attachment.get("type", "")
            style_list = attachment.get("style_list", [])
            if "photo" in style_list:
                media_item = {"type": "image", "attachment_type": attachment_type}
                media_items.append(media_item)
            elif "video" in style_list:
                media_item = {"type": "video", "attachment_type": attachment_type}
                media_items.append(media_item)
    return media_items or []


def calculate_media_count(fb_post_data):
    count = 0
    count += len(fb_post_data.get("photos", []))
    count += len(fb_post_data.get("videos", []))
    attachments = fb_post_data.get("attachments", [])
    for attachment in attachments:
        if isinstance(attachment, dict):
            style_list = attachment.get("style_list", [])
            if any(style in style_list for style in ["photo", "video"]):
                count += 1
    return count


def normalize_facebook_posts_batch(fb_posts_data):
    normalized_posts = []
    for fb_post in fb_posts_data:
        try:
            normalized_post = normalize_facebook_post(fb_post)
            if normalized_post.get("post_id"):
                normalized_posts.append(normalized_post)
        except Exception as e:
            print(f"Error normalizing Facebook post: {e}")
            continue
    return normalized_posts


if __name__ == "__main__":
    with open("fb_post_input.json", "r", encoding="utf-8") as f:
        facebook_data = json.load(f)

    parsed_post = parse_facebook_posts(facebook_data)
    normalized_post = normalize_facebook_posts_batch(parsed_post)
    print(normalized_post)
