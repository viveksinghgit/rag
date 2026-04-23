"""Document Ingestion Pipeline - Batch processing documents for RAG."""
import logging
import sys
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.document_processor import get_document_processor
from app.utils.embedding import get_embedding_manager
from app.utils.retriever import get_retriever
from app.config import settings


def ingest_documents(docs_directories: list):
    """
    Main ingestion pipeline — load from one or more directories, embed, and index.

    Args:
        docs_directories: List of directory paths containing .md / .txt files
    """
    logger.info("=" * 60)
    logger.info("🚀 Starting Document Ingestion Pipeline")
    logger.info("=" * 60)

    processor = get_document_processor()
    all_documents = []

    for docs_dir in docs_directories:
        path = Path(docs_dir)
        if not path.exists():
            logger.warning("Directory not found, skipping: %s", docs_dir)
            continue
        logger.info("📂 Loading documents from '%s'...", docs_dir)
        docs = processor.load_documents_from_directory(docs_dir)
        logger.info("  ✓ Loaded %d chunks from %s", len(docs), docs_dir)
        all_documents.extend(docs)

    if not all_documents:
        logger.warning("⚠️  No documents found in any provided directory")
        return

    logger.info("✓ Total document chunks: %d", len(all_documents))

    logger.info("🔢 Generating document IDs...")
    all_documents = processor.generate_document_ids(all_documents, prefix="")

    logger.info("🧮 Generating embeddings...")
    embedding_manager = get_embedding_manager()
    embeddings = embedding_manager.embed_documents([doc["text"] for doc in all_documents])

    for doc, embedding in zip(all_documents, embeddings):
        doc["embedding"] = embedding
    logger.info("✓ Generated %d embeddings", len(embeddings))

    logger.info("💾 Upserting documents to Qdrant...")
    retriever = get_retriever()

    for i, doc in enumerate(all_documents):
        doc["id"] = i

    result = retriever.upsert_documents(all_documents)
    logger.info("✓ Upsert result: %s", result)

    collection_info = retriever.get_collection_info()
    logger.info("📊 Collection info: %s", collection_info)

    logger.info("=" * 60)
    logger.info("✅ Ingestion Complete!")
    logger.info("   • Documents ingested: %d", len(all_documents))
    logger.info("   • Vectors in collection: %s", collection_info.get("vectors_count", "N/A"))
    logger.info("   • Timestamp: %s", datetime.utcnow().isoformat())
    logger.info("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ingest documents for RAG")
    parser.add_argument(
        "--docs-dir",
        type=str,
        nargs="+",
        default=["docs"],
        help="One or more paths to document directories",
    )
    args = parser.parse_args()
    ingest_documents(args.docs_dir)
