import os
import pickle
import logging
from neo4j import GraphDatabase
import faiss
import numpy as np
from app.config import settings

logger = logging.getLogger(__name__)


class Neo4jDriver:
    def __init__(self):
        try:
            self.driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            logger.info("Neo4j driver initialised")
        except Exception as e:
            logger.error(f"Neo4j driver init failed: {e}")
            self.driver = None

    def close(self):
        if self.driver:
            self.driver.close()

    def get_session(self):
        if not self.driver:
            raise ConnectionError("Neo4j driver is not initialised")
        return self.driver.session()

    def ping(self):
        """Verify database connectivity by running a test query."""
        if not self.driver:
            raise ConnectionError("Neo4j driver is not initialised")
        with self.driver.session() as session:
            session.run("RETURN 1")


class FaissIndex:
    def __init__(self):
        self.dimension = settings.VECTOR_DIM
        # Inner Product (Cosine Similarity if normalized)
        self.index = faiss.IndexFlatIP(self.dimension)
        self.id_map = {}  # Maps FAISS ID to Document ID
        self.current_id = 0
        self.index_path = "data/faiss_index.bin"
        self.map_path = "data/faiss_map.pkl"
        self.load()

    def add(self, embedding: np.ndarray, doc_id: str):
        if embedding.ndim == 1:
            embedding = embedding.reshape(1, -1)
        faiss.normalize_L2(embedding)
        self.index.add(embedding)
        self.id_map[self.current_id] = doc_id
        vector_id = self.current_id
        self.current_id += 1
        self.save()  # Auto-save on add (for simple persistence)
        return vector_id

    def search(self, query_vector: np.ndarray, top_k: int):
        if self.index.ntotal == 0:
            return [], []
        if query_vector.ndim == 1:
            query_vector = query_vector.reshape(1, -1)
        faiss.normalize_L2(query_vector)
        distances, indices = self.index.search(query_vector, top_k)
        return distances[0], indices[0]

    def save(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.map_path, "wb") as f:
            pickle.dump(
                {"id_map": self.id_map, "current_id": self.current_id}, f)

    def load(self):
        if os.path.exists(self.index_path) and os.path.exists(self.map_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.map_path, "rb") as f:
                data = pickle.load(f)
                self.id_map = data["id_map"]
                self.current_id = data["current_id"]

    def get_vector(self, vector_id: int) -> list:
        try:
            return self.index.reconstruct(vector_id).tolist()
        except BaseException:
            return []

    def count(self):
        return self.index.ntotal

    def remove_document(self, doc_id: str):
        """Soft delete: Remove from id_map so it's ignored in search."""
        keys_to_remove = [k for k, v in self.id_map.items() if v == doc_id]
        for k in keys_to_remove:
            del self.id_map[k]
        self.save()

    def update_document(self, doc_id: str, embedding: np.ndarray):
        """Update: Soft delete old vectors, add new one."""
        self.remove_document(doc_id)
        self.add(embedding, doc_id)


neo4j_driver = Neo4jDriver()
faiss_index = FaissIndex()
