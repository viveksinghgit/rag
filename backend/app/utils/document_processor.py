"""Document Processing - Parsing and chunking documents."""
import re
import logging
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Processes documents for ingestion into RAG system."""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        """
        Initialize document processor.

        Args:
            chunk_size: Target chunk size (tokens, approximate)
            chunk_overlap: Overlap between chunks (tokens)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def parse_markdown(self, content: str) -> Dict[str, str]:
        """
        Parse Markdown document.

        Args:
            content: Raw Markdown content

        Returns:
            Parsed document with structure
        """
        # Remove code blocks for now (preserve text only)
        content = re.sub(r"```[\s\S]*?```", "", content)

        # Remove HTML comments
        content = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)

        # Extract title from H1
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        title = title_match.group(1) if title_match else "Untitled"

        return {
            "title": title,
            "content": content,
            "format": "markdown",
        }

    def chunk_text(self, text: str, source: str = "unknown") -> List[Dict[str, Any]]:
        """
        Split text into chunks for embedding.

        Args:
            text: Raw text to chunk
            source: Document source/filename

        Returns:
            List of chunks with metadata
        """
        # Simple word-based chunking (approximates tokens)
        words = text.split()
        if not words:
            return []

        chunk_size = max(1, self.chunk_size)
        chunk_overlap = max(0, min(self.chunk_overlap, chunk_size - 1))
        chunks = []
        chunk_index = 0

        i = 0
        while i < len(words):
            # Get chunk of desired size
            chunk_end = min(i + chunk_size, len(words))
            chunk_words = words[i:chunk_end]
            chunk_text = " ".join(chunk_words)

            # Skip empty chunks
            if chunk_text.strip():
                chunks.append(
                    {
                        "text": chunk_text,
                        "source": source,
                        "chunk_index": chunk_index,
                        "total_chunks": None,  # Set after all chunks created
                        "word_count": len(chunk_words),
                    }
                )
                chunk_index += 1

            if chunk_end >= len(words):
                break

            # Move to next chunk (with overlap)
            i = chunk_end - chunk_overlap

        # Update total chunks
        for chunk in chunks:
            chunk["total_chunks"] = len(chunks)

        logger.info(f"Chunked '{source}' into {len(chunks)} chunks")
        return chunks

    def split_text(
        self,
        text: str,
        chunk_size: int = None,
        chunk_overlap: int = None,
    ) -> List[str]:
        """Return plain text chunks for scripts that do not need metadata."""
        original_chunk_size = self.chunk_size
        original_chunk_overlap = self.chunk_overlap
        if chunk_size is not None:
            self.chunk_size = chunk_size
        if chunk_overlap is not None:
            self.chunk_overlap = chunk_overlap

        try:
            return [chunk["text"] for chunk in self.chunk_text(text)]
        finally:
            self.chunk_size = original_chunk_size
            self.chunk_overlap = original_chunk_overlap

    def load_documents_from_directory(
        self, directory: str
    ) -> List[Dict[str, Any]]:
        """
        Load all Markdown documents from a directory.

        Args:
            directory: Path to directory containing .md files

        Returns:
            List of loaded documents with metadata
        """
        path = Path(directory)
        documents = []

        if not path.exists():
            logger.warning(f"Directory not found: {directory}")
            return documents

        # Find all .md files
        md_files = list(path.glob("**/*.md"))
        logger.info(f"Found {len(md_files)} Markdown files")

        for file_path in md_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Parse Markdown
                parsed = self.parse_markdown(content)

                # Chunk document
                chunks = self.chunk_text(parsed["content"], source=file_path.name)

                # Create document objects
                for chunk in chunks:
                    documents.append(
                        {
                            "source_file": file_path.name,
                            "text": chunk["text"],
                            "source": chunk["source"],
                            "chunk_index": chunk["chunk_index"],
                            "total_chunks": chunk["total_chunks"],
                        }
                    )

                logger.info(f"✓ Loaded {file_path.name} ({len(chunks)} chunks)")

            except Exception as e:
                logger.error(f"✗ Failed to load {file_path.name}: {str(e)}")
                continue

        logger.info(f"✓ Loaded {len(documents)} total chunks from directory")
        return documents

    def generate_document_ids(
        self, documents: List[Dict[str, Any]], prefix: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Generate unique IDs for documents.

        Args:
            documents: List of document chunks
            prefix: Optional prefix for IDs

        Returns:
            Documents with assigned IDs
        """
        for i, doc in enumerate(documents):
            # Create ID from source + chunk index
            source_clean = doc["source"].replace(".md", "").replace(" ", "_")
            doc["id"] = (
                f"{prefix}{source_clean}_{doc['chunk_index']:04d}"
                if prefix
                else f"{source_clean}_{doc['chunk_index']:04d}"
            )

        return documents

    def get_text_statistics(self, text: str) -> Dict[str, Any]:
        """Get text statistics for diagnostics."""
        words = len(text.split())
        chars = len(text)
        estimated_tokens = words * 1.3  # Rough approximation

        return {
            "character_count": chars,
            "word_count": words,
            "estimated_tokens": int(estimated_tokens),
        }


# Singleton instance
_processor = None


def get_document_processor() -> DocumentProcessor:
    """Get or create document processor singleton."""
    global _processor
    if _processor is None:
        from app.config import settings
        _processor = DocumentProcessor(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
    return _processor
