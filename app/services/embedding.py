# File: app/services/embedding.py
"""
Embedding service with lazy loading for low-memory environments.
The model is only loaded when first used, not at import time.
"""
from app.config import settings
import numpy as np
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self):
        self._model = None  # Lazy load - don't load at startup

    @property
    def model(self):
        """Lazy load the embedding model on first use."""
        if self._model is None:
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info("Embedding model loaded successfully")
        return self._model

    def encode(self, text: str) -> np.ndarray:
        """Encode text to embedding vector."""
        return self.model.encode(text)


embedding_service = EmbeddingService()
