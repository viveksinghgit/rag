"""Document Ingestion Pipeline - Batch processing documents for RAG."""
import logging
import sys
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.document_processor import get_document_processor
from app.utils.embedding import get_embedding_manager
from app.utils.retriever import get_retriever
from app.config import settings


def ingest_documents(docs_directory: str = "docs"):
    """
    Main ingestion pipeline - load, process, embed, and index documents.

    Args:
        docs_directory: Path to directory containing .md files
    """
    logger.info("=" * 60)
    logger.info("🚀 Starting Document Ingestion Pipeline")
    logger.info("=" * 60)

    try:
        # Load documents
        logger.info(f"📂 Loading documents from '{docs_directory}'...")
        processor = get_document_processor()
        documents = processor.load_documents_from_directory(docs_directory)

        if not documents:
            logger.warning("⚠️  No documents found to ingest")
            return

        logger.info(f"✓ Loaded {len(documents)} document chunks")

        # Generate IDs
        logger.info("🔢 Generating document IDs...")
        documents = processor.generate_document_ids(documents, prefix="")
        logger.info(f"✓ Generated {len(documents)} document IDs")

        # Generate embeddings
        logger.info("🧮 Generating embeddings...")
        embedding_manager = get_embedding_manager()

        embeddings = embedding_manager.embed_documents(
            [doc["text"] for doc in documents]
        )

        # Attach embeddings to documents
        for doc, embedding in zip(documents, embeddings):
            doc["embedding"] = embedding

        logger.info(f"✓ Generated {len(embeddings)} embeddings")

        # Upsert to Qdrant
        logger.info("💾 Upserting documents to Qdrant...")
        retriever = get_retriever()

        # Convert IDs to integers (Qdrant requirement)
        for i, doc in enumerate(documents):
            doc["id"] = i  # Use sequential integer ID

        result = retriever.upsert_documents(documents)
        logger.info(f"✓ Upsert result: {result}")

        # Get collection info
        collection_info = retriever.get_collection_info()
        logger.info(f"📊 Collection info: {collection_info}")

        # Summary
        logger.info("=" * 60)
        logger.info("✅ Ingestion Complete!")
        logger.info(f"   • Documents ingested: {len(documents)}")
        logger.info(f"   • Vectors in collection: {collection_info.get('vectors_count', 'N/A')}")
        logger.info(f"   • Timestamp: {datetime.utcnow().isoformat()}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ Ingestion failed: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ingest documents for RAG")
    parser.add_argument(
        "--docs-dir",
        type=str,
        default="docs",
        help="Path to documents directory",
    )

    args = parser.parse_args()

    ingest_documents(args.docs_dir)
