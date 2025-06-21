import json
import time
import random
import argparse
from bs4 import BeautifulSoup
from openai import OpenAI
from db.config import get_tracking_db_path
from db.articles import get_unprocessed_articles, update_article_status
from utils.load_api_keys import load_api_key

WEB_PAGE_ANALYSE_MODEL = "gpt-4o"
MODEL_INSTRUCTION = "You are a helpful assistant that analyzes articles and extracts structured information."


def extract_clean_text(raw_html, max_tokens=8000):
    soup = BeautifulSoup(raw_html, "html.parser")
    for element in soup(["script", "style", "nav", "header", "footer", "aside"]):
        element.decompose()
    text = soup.get_text(separator="\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    text = "\n".join(lines)
    approx_tokens = len(text) / 4
    if approx_tokens > max_tokens:
        text = text[: max_tokens * 4]
    return text


def process_article_with_ai(client, article, max_tokens=8000):
    clean_text = extract_clean_text(article["raw_content"], max_tokens)
    metadata = article.get("metadata", {})
    title = article["title"]
    url = article["url"]
    description = ""
    if metadata and isinstance(metadata, dict):
        if "description" in metadata:
            description = metadata["description"]
        elif "og" in metadata and "description" in metadata["og"]:
            description = metadata["og"]["description"]
    try:
        response = client.chat.completions.create(
            model=WEB_PAGE_ANALYSE_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": MODEL_INSTRUCTION,
                },
                {
                    "role": "user",
                    "content": f"""
                                Analyze this article and provide a structured output with three components:

                                1. A list of 3-5 relevant categories for this article
                                2. A concise 2-3 sentence summary of the article
                                3. The extracted main article content, removing any navigation, ads, or irrelevant elements

                                Article Title: {title}
                                Article URL: {url}
                                Description: {description}

                                Article Text:
                                {clean_text}

                                Provide your response as a JSON object with these keys:
                                - categories: an array of 3-5 relevant categories (as strings)
                                - summary: a 2-3 sentence summary of the article
                                - content: the cleaned main article content
                                """,
                },
            ],
            temperature=0.3,
            max_tokens=1500,
        )
        response_json = json.loads(response.choices[0].message.content)
        categories = response_json.get("categories", [])
        if isinstance(categories, str):
            categories = [cat.strip() for cat in categories.split(",") if cat.strip()]
        results = {
            "categories": categories,
            "summary": response_json.get("summary", ""),
            "content": response_json.get("content", ""),
        }
        return results, True, None
    except Exception as e:
        error_message = str(e)
        print(f"Error processing article with AI: {error_message}")
        return None, False, error_message


def analyze_articles(tracking_db_path=None, openai_api_key=None, batch_size=5, delay_range=(1, 3)):
    if tracking_db_path is None:
        tracking_db_path = get_tracking_db_path()
    if openai_api_key is None:
        raise ValueError("OpenAI API key is required")
    client = OpenAI(api_key=openai_api_key)
    articles = get_unprocessed_articles(tracking_db_path, limit=batch_size)
    stats = {"total_articles": len(articles), "success_count": 0, "failed_count": 0}
    for i, article in enumerate(articles):
        article_id = article["id"]
        title = article["title"]
        attempt = article.get("ai_attempts", 0) + 1
        print(f"[{i + 1}/{len(articles)}] Processing article: {title} (Attempt {attempt})")
        results, success, error_message = process_article_with_ai(client, article)
        update_article_status(tracking_db_path, article_id, results, success, error_message)
        if success:
            categories_display = ", ".join(results["categories"])
            print(f"Successfully processed article ID {article_id}")
            print(f"Categories: {categories_display}")
            print(f"Summary: {results['summary'][:100]}..." if len(results["summary"]) > 100 else f"Summary: {results['summary']}")
            stats["success_count"] += 1
        else:
            print(f"Failed to process article ID {article_id}: {error_message}")
            stats["failed_count"] += 1

        if i < len(articles) - 1:
            delay = random.uniform(delay_range[0], delay_range[1])
            time.sleep(delay)
    return stats


def print_stats(stats):
    print("\nAI Analysis Statistics:")
    print(f"Total articles processed: {stats['total_articles']}")
    print(f"Successfully analyzed: {stats['success_count']}")
    print(f"Failed: {stats['failed_count']}")


def analyze_in_batches(
    tracking_db_path=None,
    openai_api_key=None,
    batch_size=20,
    total_batches=1,
    delay_between_batches=10,
):
    if tracking_db_path is None:
        tracking_db_path = get_tracking_db_path()
    if openai_api_key is None:
        raise ValueError("OpenAI API key is required")
    total_stats = {"total_articles": 0, "success_count": 0, "failed_count": 0}
    for i in range(total_batches):
        print(f"\nProcessing batch {i + 1}/{total_batches}")
        batch_stats = analyze_articles(
            tracking_db_path=tracking_db_path,
            openai_api_key=openai_api_key,
            batch_size=batch_size,
        )
        total_stats["total_articles"] += batch_stats["total_articles"]
        total_stats["success_count"] += batch_stats["success_count"]
        total_stats["failed_count"] += batch_stats["failed_count"]
        if batch_stats["total_articles"] == 0:
            print("No more articles to process")
            break
        if i < total_batches - 1:
            print(f"Waiting {delay_between_batches} seconds before next batch...")
            time.sleep(delay_between_batches)
    return total_stats


def parse_arguments():
    parser = argparse.ArgumentParser(description="Process articles with AI analysis")
    parser.add_argument("--api_key", help="OpenAI API Key (overrides environment variables)")
    parser.add_argument(
        "--batch_size",
        type=int,
        default=10,
        help="Number of articles to process in each batch",
    )
    parser.add_argument(
        "--total_batches",
        type=int,
        default=1,
        help="Total number of batches to process",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    api_key = args.api_key or load_api_key()
    if not api_key:
        print("Error: No OpenAI API key provided. Please provide via --api_key or set OPENAI_API_KEY in .env file")
        exit(1)
    stats = analyze_in_batches(
        openai_api_key=api_key,
        batch_size=args.batch_size,
        total_batches=args.total_batches,
    )
    print_stats(stats)
