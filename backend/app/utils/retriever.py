"""Qdrant Retriever - Vector database interactions."""
import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from app.config import settings

logger = logging.getLogger(__name__)


class QdrantRetriever:
    """Manages interactions with Qdrant vector database."""

    def __init__(self, host: str, port: int, collection_name: str):
        """
        Initialize Qdrant retriever.

        Args:
            host: Qdrant server host
            port: Qdrant server port
            collection_name: Name of collection to use
        """
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.client = None

        self.connect()
        self.ensure_collection()

    def connect(self):
        """Connect to Qdrant server."""
        try:
            self.client = QdrantClient(
                host=self.host,
                port=self.port,
                api_key=settings.qdrant_admin_key,
                https=False,
                timeout=30,
            )
            info = self.client.get_collections()
            logger.info(f"✓ Connected to Qdrant at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"✗ Failed to connect to Qdrant: {str(e)}")
            raise

    def ensure_collection(self):
        """Ensure collection exists, create if not."""
        try:
            collections = self.client.get_collections()
            collection_names = [c.name for c in collections.collections]

            if self.collection_name not in collection_names:
                logger.info(f"Creating collection: {self.collection_name}")
                self._recreate_collection()
                logger.info(f"✓ Collection created: {self.collection_name}")
            else:
                self._recreate_if_vector_size_changed()
                logger.info(f"✓ Collection exists: {self.collection_name}")
        except Exception as e:
            logger.error(f"✗ Failed to ensure collection: {str(e)}")
            raise

    def _recreate_collection(self):
        """Create a clean collection using the configured vector size."""
        self.client.recreate_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=settings.qdrant_vector_size,
                distance=Distance.COSINE,
            ),
        )

    def _recreate_if_vector_size_changed(self):
        """Keep local test collections aligned with the active embedding model."""
        info = self.client.get_collection(self.collection_name)
        vectors_config = info.config.params.vectors
        current_size = self._get_vector_size(vectors_config)

        if current_size == settings.qdrant_vector_size:
            return

        message = (
            f"Collection '{self.collection_name}' uses vectors of size {current_size}, "
            f"but configuration expects {settings.qdrant_vector_size}."
        )
        if not settings.qdrant_recreate_on_vector_mismatch:
            raise ValueError(message)

        logger.warning("%s Recreating collection.", message)
        self._recreate_collection()

    def _get_vector_size(self, vectors_config) -> Optional[int]:
        """Extract vector size from Qdrant's unnamed or named vector config."""
        size = getattr(vectors_config, "size", None)
        if size is not None:
            return size

        if isinstance(vectors_config, dict) and vectors_config:
            first_vector = next(iter(vectors_config.values()))
            return getattr(first_vector, "size", None)

        return None

    def search(
        self,
        query_vector: List[float],
        limit: int = 5,
        score_threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents.

        Args:
            query_vector: Query embedding vector
            limit: Number of results to return
            score_threshold: Minimum similarity score (0-1)

        Returns:
            List of documents with scores and metadata
        """
        try:
            logger.debug(f"Searching for {limit} similar documents")

            if hasattr(self.client, "query_points"):
                response = self.client.query_points(
                    collection_name=self.collection_name,
                    query=query_vector,
                    limit=limit,
                    score_threshold=score_threshold,
                    with_payload=True,
                )
                results = response.points
            else:
                results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    limit=limit,
                    score_threshold=score_threshold,
                )

            documents = []
            for point in results:
                doc = {
                    "id": point.id,
                    "score": point.score,
                    "text": point.payload.get("text", ""),
                    "source": point.payload.get("source", "unknown"),
                    "chunk_index": point.payload.get("chunk_index", 0),
                    "metadata": point.payload,
                }
                documents.append(doc)

            logger.debug(f"✓ Found {len(documents)} similar documents")
            return documents

        except Exception as e:
            logger.error(f"✗ Search failed: {str(e)}", exc_info=True)
            raise

    def upsert_documents(
        self, documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Insert or update documents in Qdrant.

        Args:
            documents: List of documents with schema:
                {
                    "id": str,
                    "embedding": List[float],
                    "text": str,
                    "source": str,
                    "chunk_index": int,
                    "metadata": Dict
                }

        Returns:
            Operation status
        """
        try:
            logger.info(f"Upserting {len(documents)} documents to Qdrant")

            points = []
            for doc in documents:
                point = PointStruct(
                    id=int(doc["id"]),
                    vector=doc["embedding"],
                    payload={
                        "text": doc["text"],
                        "source": doc.get("source", ""),
                        "chunk_index": doc.get("chunk_index", 0),
                        **doc.get("metadata", {}),
                    },
                )
                points.append(point)

            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
            )

            logger.info(f"✓ Upserted {len(documents)} documents")
            return {
                "status": "success",
                "documents_upserted": len(documents),
            }

        except Exception as e:
            logger.error(f"✗ Upsert failed: {str(e)}", exc_info=True)
            raise

    def delete_documents(self, document_ids: List[int]) -> Dict[str, Any]:
        """
        Delete documents from Qdrant.

        Args:
            document_ids: List of document IDs to delete

        Returns:
            Operation status
        """
        try:
            logger.info(f"Deleting {len(document_ids)} documents from Qdrant")

            self.client.delete(
                collection_name=self.collection_name,
                points_selector=document_ids,
            )

            logger.info(f"✓ Deleted {len(document_ids)} documents")
            return {
                "status": "success",
                "documents_deleted": len(document_ids),
            }

        except Exception as e:
            logger.error(f"✗ Delete failed: {str(e)}", exc_info=True)
            raise

    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection statistics."""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "vectors_count": info.points_count,
                "vector_size": settings.qdrant_vector_size,
                "distance_metric": "cosine",
            }
        except Exception as e:
            logger.error(f"✗ Failed to get collection info: {str(e)}")
            return {}


# Singleton instance
_retriever = None


def get_retriever() -> QdrantRetriever:
    """Get or create Qdrant retriever singleton."""
    global _retriever
    if _retriever is None:
        _retriever = QdrantRetriever(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            collection_name=settings.qdrant_collection_name,
        )
    return _retriever
