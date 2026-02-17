# File: app/repositories/vector_repository.py
"""FAISS vector index repository"""
from typing import Optional, List, Tuple
import numpy as np
from app.repositories.base import BaseRepository
from app.database import FaissIndex
import logging

logger = logging.getLogger(__name__)


class VectorRepository:
    """Repository for FAISS vector operations"""
    
    def __init__(self, index: FaissIndex):
        self.index = index
    
    def add_vector(self, embedding: np.ndarray, doc_id: str) -> int:
        """Add a vector to the index"""
        return self.index.add(embedding, doc_id)
    
    def search(self, query_vector: np.ndarray, top_k: int) -> Tuple[np.ndarray, np.ndarray]:
        """Search for similar vectors"""
        distances, indices = self.index.search(query_vector, top_k)
        return distances, indices
    
    def get_document_id(self, vector_idx: int) -> Optional[str]:
        """Get document ID from FAISS index"""
        return self.index.id_map.get(vector_idx)
    
    def get_vector(self, vector_id: int) -> List[float]:
        """Retrieve a vector by ID"""
        return self.index.get_vector(vector_id)
    
    def count(self) -> int:
        """Get total number of vectors"""
        return self.index.count()
    
    def remove_document(self, doc_id: str):
        """Soft delete: remove document from index mapping"""
        self.index.remove_document(doc_id)
    
    def update_document(self, doc_id: str, embedding: np.ndarray):
        """Update document embedding"""
        self.index.update_document(doc_id, embedding)
    
    def get_all_mappings(self) -> dict:
        """Get all vector ID to document ID mappings"""
        return self.index.id_map
