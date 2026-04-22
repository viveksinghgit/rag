"""Embedding Management - Vector generation and management."""
import logging
from typing import List, Dict, Any
from app.utils.llm_router import get_llm_router
from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingManager:
    """Manages text embedding generation using LiteLLM."""

    def __init__(self):
        """Initialize embedding manager."""
        self.router = get_llm_router()
        self.embedding_cache = {}
        self.cache_hits = 0
        self.cache_misses = 0

    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a user query.

        Args:
            query: User query string

        Returns:
            Vector embedding with the configured Qdrant dimension
        """
        # Check cache
        cache_key = hash(query) % (2**32)
        if cache_key in self.embedding_cache:
            self.cache_hits += 1
            logger.debug(f"Cache hit for query embedding")
            return self.embedding_cache[cache_key]

        # Generate embedding
        result = self.router.embed_text(query)
        embedding = result["embedding"]

        # Store in cache
        self.embedding_cache[cache_key] = embedding
        self.cache_misses += 1

        return embedding

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for document chunks.

        Args:
            texts: List of document chunk texts

        Returns:
            List of embeddings with the configured Qdrant dimension
        """
        logger.info(f"Embedding {len(texts)} document chunks")

        result = self.router.embed_texts(texts)
        embeddings = result["embeddings"]

        logger.info(f"✓ Generated {len(embeddings)} embeddings")

        return embeddings

    def embed_document(self, text: str) -> List[float]:
        """Embed a single document chunk."""
        result = self.router.embed_text(text)
        return result["embedding"]

    def get_embedding_stats(self) -> Dict[str, Any]:
        """Get embedding cache statistics."""
        total_lookups = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_lookups * 100) if total_lookups > 0 else 0

        return {
            "cache_size": len(self.embedding_cache),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": hit_rate,
        }

    def clear_cache(self):
        """Clear embedding cache."""
        self.embedding_cache.clear()
        logger.info("Embedding cache cleared")


# Singleton instance
_manager = None


def get_embedding_manager() -> EmbeddingManager:
    """Get or create embedding manager singleton."""
    global _manager
    if _manager is None:
        _manager = EmbeddingManager()
    return _manager
