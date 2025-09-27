import numpy as np
import faiss
import time


dimension = 128
nb_vectors = 10000
np.random.seed(42)
database = np.random.random((nb_vectors, dimension)).astype("float32")
query = np.random.random((1, dimension)).astype("float32")

start_time = time.time()
index = faiss.IndexFlatL2(dimension)
index.add(database)
print(f"Index built in {time.time() - start_time:.4f} seconds")
print(f"Index contains {index.ntotal} vectors")

k = 5
start_time = time.time()
distances, indices = index.search(query, k)
print(f"Search completed in {time.time() - start_time:.4f} seconds")
print("\nSearch Results:")
print("Query vector finds these nearest neighbors (indices):", indices[0])
print("With these distances:", distances[0])
print("\nFAISS is working correctly!")
