import time
import argparse
import random
import numpy as np
from openai import OpenAI
from db.config import get_tracking_db_path
from db.connection import db_connection, execute_query
from utils.load_api_keys import load_api_key

EMBEDDING_MODEL = "text-embedding-3-small"

def create_embedding_table(tracking_db_path):
    with db_connection(tracking_db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='article_embeddings'
        """)
        table_exists = cursor.fetchone() is not None
        if not table_exists:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS article_embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER NOT NULL,
                embedding BLOB NOT NULL,
                embedding_model TEXT NOT NULL,
                created_at TEXT NOT NULL,
                in_faiss_index INTEGER DEFAULT 0,
                FOREIGN KEY (article_id) REFERENCES crawled_articles(id)
            )
            """)
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_article_embeddings_article_id 
            ON article_embeddings(article_id)
            """)
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_article_embeddings_in_faiss 
            ON article_embeddings(in_faiss_index)
            """)
            conn.commit()
            print("Article embeddings table created successfully.")
        else:
            print("Article embeddings table already exists.")


def get_articles_without_embeddings(tracking_db_path, limit=20):
    query = """
    SELECT ca.id, ca.title, ca.summary, ca.content
    FROM crawled_articles ca
    WHERE ca.processed = 1 
    AND ca.ai_status = 'success'
    AND NOT EXISTS (
        SELECT 1 FROM article_embeddings ae 
        WHERE ae.article_id = ca.id
    )
    ORDER BY ca.published_date DESC
    LIMIT ?
    """
    return execute_query(tracking_db_path, query, (limit,), fetch=True)


def mark_articles_as_processing(tracking_db_path, article_ids):
    if not article_ids:
        return 0
    try:
        with db_connection(tracking_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(crawled_articles)")
            columns = [col[1] for col in cursor.fetchall()]
            if "embedding_status" in columns:
                placeholders = ",".join(["?"] * len(article_ids))
                query = f"""
                UPDATE crawled_articles 
                SET embedding_status = 'processing' 
                WHERE id IN ({placeholders})
                """
                cursor.execute(query, article_ids)
                conn.commit()
                return cursor.rowcount
            else:
                print("Note: embedding_status column doesn't exist in crawled_articles table.")
                print("Skipping article marking step (this is non-critical).")
                return len(article_ids)
    except Exception as e:
        print(f"Error marking articles as processing: {str(e)}")
        print("Continuing without marking articles (this is non-critical).")
        return 0


def generate_embedding(client, text, model=EMBEDDING_MODEL):
    try:
        response = client.embeddings.create(input=text, model=model)
        return response.data[0].embedding, model
    except Exception as e:
        print(f"Error generating embedding: {str(e)}")
        return None, None


def prepare_article_text(article):
    title = article.get("title", "")
    summary = article.get("summary", "")
    content = article.get("content", "")
    full_text = f"Title: {title}\n\nSummary: {summary}\n\nContent: {content}"
    return full_text


def store_embedding(tracking_db_path, article_id, embedding, model):
    from datetime import datetime
    import sqlite3
    embedding_blob = np.array(embedding, dtype=np.float32).tobytes()
    query = """
    INSERT INTO article_embeddings 
    (article_id, embedding, embedding_model, created_at, in_faiss_index)
    VALUES (?, ?, ?, ?, 0)
    """
    params = (article_id, embedding_blob, model, datetime.now().isoformat())
    try:
        execute_query(tracking_db_path, query, params)
        return True
    except sqlite3.IntegrityError:
        print(f"Warning: Embedding already exists for article {article_id}")
        return False
    except Exception as e:
        print(f"Error storing embedding: {str(e)}")
        return False


def process_articles_for_embedding(tracking_db_path=None, openai_api_key=None, batch_size=20, delay_range=(1, 3)):
    if tracking_db_path is None:
        tracking_db_path = get_tracking_db_path()
    if openai_api_key is None:
        raise ValueError("OpenAI API key is required")
    create_embedding_table(tracking_db_path)
    client = OpenAI(api_key=openai_api_key)
    articles = get_articles_without_embeddings(tracking_db_path, limit=batch_size)
    if not articles:
        print("No articles found that need embeddings")
        return {"total_articles": 0, "success_count": 0, "failed_count": 0}
    article_ids = [article["id"] for article in articles]
    mark_articles_as_processing(tracking_db_path, article_ids)
    stats = {"total_articles": len(articles), "success_count": 0, "failed_count": 0}
    for i, article in enumerate(articles):
        article_id = article["id"]
        try:
            print(f"[{i + 1}/{len(articles)}] Generating embedding for article {article_id}: {article['title']}")
            text = prepare_article_text(article)
            embedding, model = generate_embedding(client, text)
            if embedding:
                success = store_embedding(tracking_db_path, article_id, embedding, model)
                if success:
                    print(f"Successfully stored embedding for article {article_id}")
                    stats["success_count"] += 1
                else:
                    print(f"Failed to store embedding for article {article_id}")
                    stats["failed_count"] += 1
            else:
                print(f"Failed to generate embedding for article {article_id}")
                stats["failed_count"] += 1
        except Exception as e:
            print(f"Error processing article {article_id}: {str(e)}")
            stats["failed_count"] += 1
        if i < len(articles) - 1:
            delay = random.uniform(delay_range[0], delay_range[1])
            time.sleep(delay)
    return stats


def print_stats(stats):
    print("\nEmbedding Generation Statistics:")
    print(f"Total articles processed: {stats['total_articles']}")
    print(f"Successfully embedded: {stats['success_count']}")
    print(f"Failed: {stats['failed_count']}")


def parse_arguments():
    parser = argparse.ArgumentParser(description="Generate embeddings for processed articles")
    parser.add_argument("--api_key", help="OpenAI API Key (overrides environment variables)")
    parser.add_argument(
        "--batch_size",
        type=int,
        default=20,
        help="Number of articles to process in each batch",
    )
    return parser.parse_args()


def process_in_batches(
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
        batch_stats = process_articles_for_embedding(
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


if __name__ == "__main__":
    args = parse_arguments()
    api_key = args.api_key or load_api_key()
    if not api_key:
        print("Error: No OpenAI API key provided. Please provide via --api_key or set OPENAI_API_KEY in .env file")
        exit(1)
    stats = process_in_batches(
        openai_api_key=api_key,
        batch_size=args.batch_size,
        total_batches=3,
    )
    print_stats(stats)
