import os
import time
import argparse
import numpy as np
import faiss
from db.config import get_tracking_db_path, get_faiss_db_path
from db.connection import db_connection, execute_query


def initialize_faiss_index(dimension=1536, index_path=None, index_type="hnsw", n_list=100):
    if index_path and os.path.exists(index_path):
        print(f"Loading existing FAISS index from {index_path}")
        try:
            index = faiss.read_index(index_path)
            print(f"Loaded index with {index.ntotal} vectors")
            return index
        except Exception as e:
            print(f"Error loading FAISS index: {str(e)}")
            print("Creating a new index instead")
    print(f"Creating new FAISS index with dimension {dimension}, type: {index_type}")
    if index_type == "flat":
        return faiss.IndexFlatL2(dimension)

    elif index_type == "ivfflat":
        quantizer = faiss.IndexFlatL2(dimension)
        index = faiss.IndexIVFFlat(quantizer, dimension, n_list)
        print("Training IVF index with random vectors...")
        train_size = max(10000, n_list * 10)
        train_vectors = np.random.random((train_size, dimension)).astype(np.float32)
        index.train(train_vectors)
        index.nprobe = min(10, n_list // 10)
        return index
    elif index_type == "ivfpq":
        quantizer = faiss.IndexFlatL2(dimension)
        m = 16
        bits = 8
        index = faiss.IndexIVFPQ(quantizer, dimension, n_list, m, bits)
        print("Training IVF-PQ index with random vectors...")
        train_size = max(10000, n_list * 10)
        train_vectors = np.random.random((train_size, dimension)).astype(np.float32)
        index.train(train_vectors)
        index.nprobe = min(10, n_list // 10)
        return index
    elif index_type == "hnsw":
        m = 32
        ef_construction = 100
        index = faiss.IndexHNSWFlat(dimension, m)
        index.hnsw.efConstruction = ef_construction
        index.hnsw.efSearch = 64
        return index
    else:
        print(f"Unknown index type '{index_type}', falling back to IVF Flat")
        quantizer = faiss.IndexFlatL2(dimension)
        index = faiss.IndexIVFFlat(quantizer, dimension, n_list)
        print("Training IVF index with random vectors...")
        train_size = max(10000, n_list * 10)
        train_vectors = np.random.random((train_size, dimension)).astype(np.float32)
        index.train(train_vectors)
        index.nprobe = min(10, n_list // 10)
        return index


def save_faiss_index(index, index_path):
    try:
        index_dir = os.path.dirname(index_path)
        os.makedirs(index_dir, exist_ok=True)
        temp_path = f"{index_path}.tmp"
        faiss.write_index(index, temp_path)
        os.replace(temp_path, index_path)
        print(f"FAISS index saved to {index_path}")
        return True
    except Exception as e:
        print(f"Error saving FAISS index: {str(e)}")
        return False


def save_id_mapping(id_map, mapping_path):
    try:
        mapping_dir = os.path.dirname(mapping_path)
        os.makedirs(mapping_dir, exist_ok=True)
        np.save(mapping_path, np.array(id_map))
        print(f"ID mapping saved to {mapping_path}")
        return True
    except Exception as e:
        print(f"Error saving ID mapping: {str(e)}")
        try:
            print("Trying alternative save method...")
            simple_path = os.path.join(mapping_dir, "article_id_map.npy")
            np.save(simple_path, np.array(id_map))
            print(f"ID mapping saved to {simple_path} (alternative path)")
            return True
        except Exception as e:
            print(f"Alternative save method also failed: {str(e)}")
            return False


def load_id_mapping(mapping_path):
    if os.path.exists(mapping_path):
        try:
            return np.load(mapping_path).tolist()
        except Exception as e:
            print(f"Error loading ID mapping: {str(e)}")
    return []


def get_embeddings_not_in_index(tracking_db_path, limit=100):
    query = """
    SELECT ae.id, ae.article_id, ae.embedding, ae.embedding_model
    FROM article_embeddings ae
    WHERE ae.in_faiss_index = 0
    LIMIT ?
    """
    return execute_query(tracking_db_path, query, (limit,), fetch=True)


def mark_embeddings_as_indexed(tracking_db_path, embedding_ids):
    if not embedding_ids:
        return 0
    with db_connection(tracking_db_path) as conn:
        cursor = conn.cursor()
        placeholders = ",".join(["?"] * len(embedding_ids))
        query = f"""
        UPDATE article_embeddings 
        SET in_faiss_index = 1 
        WHERE id IN ({placeholders})
        """
        cursor.execute(query, embedding_ids)
        conn.commit()
        return cursor.rowcount


def add_embeddings_to_index(embeddings_data, faiss_index, id_map):
    if not embeddings_data:
        return 0, []
    embeddings = []
    article_ids = []
    embedding_ids = []
    for data in embeddings_data:
        try:
            embedding_blob = data["embedding"]
            embedding = np.frombuffer(embedding_blob, dtype=np.float32)

            if embedding.shape[0] != faiss_index.d:
                print(f"Embedding dimension mismatch: expected {faiss_index.d}, got {embedding.shape[0]}")
                continue
            embeddings.append(embedding)
            article_ids.append(data["article_id"])
            embedding_ids.append(data["id"])
        except Exception as e:
            print(f"Error processing embedding {data['id']}: {str(e)}")
    if not embeddings:
        return 0, []
    try:
        embeddings_array = np.vstack(embeddings).astype(np.float32)
        faiss_index.add(embeddings_array)
        for article_id in article_ids:
            id_map.append(article_id)
        print(f"Added {len(embeddings)} embeddings to FAISS index")
        return len(embeddings), embedding_ids
    except Exception as e:
        print(f"Error adding embeddings to FAISS index: {str(e)}")
        return 0, []


def process_embeddings_for_indexing(
    tracking_db_path=None,
    index_path=None,
    mapping_path=None,
    batch_size=100,
    index_type="ivfflat",
    n_list=100,
):
    if tracking_db_path is None:
        tracking_db_path = get_tracking_db_path()
    index_dir = os.path.dirname(index_path)
    os.makedirs(index_dir, exist_ok=True)
    id_map = load_id_mapping(mapping_path)
    with db_connection(tracking_db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='article_embeddings'
        """)
        table_exists = cursor.fetchone() is not None

        if not table_exists:
            print("article_embeddings table does not exist. Please run embedding_processor first.")
            return {"processed": 0, "added": 0, "errors": 0, "total_vectors": 0, "status": "table_missing"}
    sample_query = """
    SELECT embedding FROM article_embeddings LIMIT 1
    """
    sample = execute_query(tracking_db_path, sample_query, fetch=True, fetch_one=True)
    if not sample:
        print("No embeddings found in the database")
        default_dimension = 1536
        print(f"Using default dimension: {default_dimension}")

        faiss_index = initialize_faiss_index(
            dimension=default_dimension, index_path=index_path if os.path.exists(index_path) else None, index_type=index_type, n_list=n_list
        )
        return {
            "processed": 0,
            "added": 0,
            "errors": 0,
            "total_vectors": faiss_index.ntotal if hasattr(faiss_index, "ntotal") else 0,
            "status": "no_embeddings",
        }
    embedding_dimension = len(np.frombuffer(sample["embedding"], dtype=np.float32))
    print(f"Detected embedding dimension: {embedding_dimension}")
    faiss_index = initialize_faiss_index(dimension=embedding_dimension, index_path=index_path, index_type=index_type, n_list=n_list)
    embeddings_data = get_embeddings_not_in_index(tracking_db_path, limit=batch_size)
    if not embeddings_data:
        print("No new embeddings to add to the index")
        return {"processed": 0, "added": 0, "errors": 0, "total_vectors": faiss_index.ntotal, "status": "no_new_embeddings"}
    added_count, embedding_ids = add_embeddings_to_index(embeddings_data, faiss_index, id_map)
    if added_count > 0:
        save_faiss_index(faiss_index, index_path)
        save_id_mapping(id_map, mapping_path)
        marked_count = mark_embeddings_as_indexed(tracking_db_path, embedding_ids)
        print(f"Marked {marked_count} embeddings as indexed in the database")
    stats = {
        "processed": len(embeddings_data),
        "added": added_count,
        "errors": len(embeddings_data) - added_count,
        "total_vectors": faiss_index.ntotal,
        "index_type": index_type,
        "status": "success",
    }
    return stats


def process_in_batches(
    tracking_db_path=None,
    index_path=None,
    mapping_path=None,
    batch_size=100,
    total_batches=5,
    delay_between_batches=2,
    index_type="ivfflat",
    n_list=100,
):
    if tracking_db_path is None:
        tracking_db_path = get_tracking_db_path()
    total_stats = {"processed": 0, "added": 0, "errors": 0, "index_type": index_type}
    for i in range(total_batches):
        print(f"\nProcessing batch {i + 1}/{total_batches}")
        batch_stats = process_embeddings_for_indexing(
            tracking_db_path=tracking_db_path,
            index_path=index_path,
            mapping_path=mapping_path,
            batch_size=batch_size,
            index_type=index_type,
            n_list=n_list,
        )
        total_stats["processed"] += batch_stats["processed"]
        total_stats["added"] += batch_stats["added"]
        total_stats["errors"] += batch_stats["errors"]
        if "total_vectors" in batch_stats:
            total_stats["total_vectors"] = batch_stats["total_vectors"]
        if batch_stats["processed"] == 0:
            print("No more embeddings to process")
            break
        if i < total_batches - 1:
            print(f"Waiting {delay_between_batches} seconds before next batch...")
            time.sleep(delay_between_batches)
    return total_stats


def print_stats(stats):
    print("\nFAISS Indexing Statistics:")
    print(f"Total embeddings processed: {stats['processed']}")
    print(f"Successfully added to index: {stats['added']}")
    print(f"Errors: {stats['errors']}")
    if "total_vectors" in stats:
        print(f"Total vectors in index: {stats['total_vectors']}")
    if "index_type" in stats:
        print(f"Index type: {stats['index_type']}")
        if stats["index_type"] == "flat":
            print("Index performance: Most accurate but slowest for large datasets")
        elif stats["index_type"] == "ivfflat":
            print("Index performance: Good balance of accuracy and speed")
        elif stats["index_type"] == "ivfpq":
            print("Index performance: Memory efficient, good for very large datasets")
        elif stats["index_type"] == "hnsw":
            print("Index performance: Excellent search speed with good accuracy")


def parse_arguments():
    parser = argparse.ArgumentParser(description="Process embeddings and add to FAISS index")
    parser.add_argument(
        "--batch_size",
        type=int,
        default=100,
        help="Number of embeddings to process in each batch",
    )
    parser.add_argument(
        "--index_path",
        default="databases/faiss/article_index.faiss",
        help="Path to save the FAISS index",
    )
    parser.add_argument(
        "--mapping_path",
        default="databases/faiss/article_id_map.npy",
        help="Path to save the ID mapping file",
    )
    parser.add_argument(
        "--index_type",
        choices=["flat", "ivfflat", "ivfpq", "hnsw"],
        default="hnsw",
        help="Type of FAISS index to create",
    )
    parser.add_argument(
        "--n_list",
        type=int,
        default=100,
        help="Number of clusters for IVF-based indexes",
    )
    parser.add_argument(
        "--total_batches",
        type=int,
        default=5,
        help="Total number of batches to process",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    index_path, mapping_path = get_faiss_db_path()
    index_path = args.index_path or index_path
    mapping_path = args.mapping_path or mapping_path
    stats = process_in_batches(
        batch_size=args.batch_size,
        index_path=index_path,
        mapping_path=mapping_path,
        total_batches=args.total_batches,
        index_type=args.index_type,
        n_list=args.n_list,
    )
