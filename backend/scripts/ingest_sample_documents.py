#!/usr/bin/env python3
"""
Document Ingestion Script for RAG Pipeline
This script loads sample documents into the Qdrant vector database.
"""
import sys
import os
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.utils.document_processor import DocumentProcessor
from app.utils.embedding import get_embedding_manager
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class DocumentIngester:
    """Handles document ingestion into Qdrant."""

    def __init__(self):
        """Initialize document ingester."""
        self.client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            api_key=settings.qdrant_admin_key,
            https=False,
            timeout=30,
        )
        self.embedding_manager = get_embedding_manager()
        self.processor = DocumentProcessor()
        logger.info("✓ Document ingester initialized")

    def setup_collection(self):
        """Create Qdrant collection if it doesn't exist."""
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            existing = [c.name for c in collections.collections]
            
            if settings.qdrant_collection_name in existing:
                logger.info(f"✓ Collection '{settings.qdrant_collection_name}' already exists")
                return
            
            # Create new collection
            logger.info(f"Creating collection '{settings.qdrant_collection_name}'...")
            self.client.create_collection(
                collection_name=settings.qdrant_collection_name,
                vectors_config=VectorParams(
                    size=settings.qdrant_vector_size,
                    distance=Distance.COSINE,
                ),
            )
            logger.info("✓ Collection created successfully")
        except Exception as e:
            logger.error(f"✗ Failed to setup collection: {str(e)}")
            raise

    def ingest_document(self, file_path: str, document_title: str = None):
        """
        Ingest a single document.

        Args:
            file_path: Path to document file (txt or md)
            document_title: Optional title for the document
        """
        try:
            # Read file
            with open(file_path, 'r') as f:
                content = f.read()
            
            title = document_title or Path(file_path).stem
            logger.info(f"📄 Processing: {title}\n   File: {file_path}\n   Size: {len(content)} chars")

            # Split into chunks
            chunks = self.processor.split_text(
                content,
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap,
            )
            logger.info(f"   Split into {len(chunks)} chunks")

            # Generate embeddings
            embeddings = self.embedding_manager.embed_documents(chunks)
            logger.info(f"   Generated {len(embeddings)} embeddings")

            # Prepare points for Qdrant
            points = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                point = PointStruct(
                    id=hash(f"{title}-{i}") % (2**31),  # Generate unique ID
                    vector=embedding,
                    payload={
                        "text": chunk,
                        "source": title,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                    },
                )
                points.append(point)

            # Upload to Qdrant
            self.client.upsert(
                collection_name=settings.qdrant_collection_name,
                points=points,
            )
            logger.info(f"✓ Ingested {len(chunks)} chunks from '{title}'")
            return len(chunks)

        except Exception as e:
            logger.error(f"✗ Failed to ingest {file_path}: {str(e)}")
            return 0

    def ingest_sample_documents(self):
        """Ingest sample documents included with the project."""
        docs_dir = Path(__file__).parent.parent.parent / "docs" / "example_docs"
        
        if not docs_dir.exists():
            logger.warning(f"Sample documents directory not found: {docs_dir}")
            return
        
        logger.info(f"📚 Ingesting sample documents from: {docs_dir}")
        
        total_chunks = 0
        for doc_file in docs_dir.glob("*.md"):
            chunks = self.ingest_document(str(doc_file))
            total_chunks += chunks
        
        logger.info(f"✓ Total chunks ingested: {total_chunks}")
        return total_chunks

    def ingest_custom_document(self, file_path: str):
        """Ingest a custom document."""
        if not Path(file_path).exists():
            logger.error(f"File not found: {file_path}")
            return 0
        
        return self.ingest_document(file_path)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest documents into RAG vector database")
    parser.add_argument(
        "--file", "-f",
        help="Path to a specific file to ingest",
    )
    parser.add_argument(
        "--sample", "-s",
        action="store_true",
        help="Ingest sample documents",
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List currently indexed documents",
    )
    
    args = parser.parse_args()
    
    ingester = DocumentIngester()
    ingester.setup_collection()
    
    if args.list:
        # List documents
        try:
            resp = ingester.client.scroll(
                collection_name=settings.qdrant_collection_name,
                limit=100,
            )
            sources = set()
            for point in resp[0]:
                source = point.payload.get("source", "unknown")
                sources.add(source)
            
            print(f"\n📚 Indexed documents: {len(sources)}")
            for source in sorted(sources):
                print(f"   • {source}")
        except Exception as e:
            logger.error(f"Failed to list documents: {str(e)}")
    
    elif args.file:
        # Ingest specific file
        ingester.ingest_custom_document(args.file)
    
    elif args.sample:
        # Ingest sample documents
        ingester.ingest_sample_documents()
    
    else:
        # Default: ingest sample documents
        ingester.ingest_sample_documents()


if __name__ == "__main__":
    main()
