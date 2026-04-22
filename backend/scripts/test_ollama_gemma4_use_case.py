#!/usr/bin/env python3
"""Smoke test for the local Ollama RAG use case."""
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.rag_pipeline import get_rag_pipeline
from scripts.ingest_sample_documents import DocumentIngester

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def find_runbook() -> Path:
    """Find the sample runbook in Docker or from the host checkout."""
    candidates = [
        Path("/app/docs/example_docs/ollama_gemma4_ops_runbook.md"),
        Path(__file__).resolve().parents[2] / "docs" / "example_docs" / "ollama_gemma4_ops_runbook.md",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    searched = ", ".join(str(candidate) for candidate in candidates)
    raise FileNotFoundError(f"Could not find local Ollama runbook. Searched: {searched}")


def main():
    """Ingest the local Ollama runbook and ask a question that needs retrieval."""
    runbook = find_runbook()

    logger.info("Testing local RAG use case with:")
    logger.info("  LLM provider: %s", settings.llm_provider)
    logger.info("  LLM model: %s", settings.ollama_model)
    logger.info("  Embedding model: %s", settings.ollama_embedding_model)
    logger.info("  Qdrant vector size: %s", settings.qdrant_vector_size)

    ingester = DocumentIngester()
    ingester.setup_collection()
    chunks = ingester.ingest_document(str(runbook), document_title="Ollama Local RAG Operations Runbook")
    if chunks == 0:
        raise RuntimeError("Runbook ingestion produced no chunks")

    pipeline = get_rag_pipeline()
    response = pipeline.query(
        user_query="Which model should I use for constrained local testing, and what vector size does Qdrant need?",
        top_k=3,
        include_sources=True,
    )

    result = {
        "answer": response["answer"],
        "sources": response["sources"],
        "tokens_used": response["tokens_used"],
        "execution_time_ms": response["execution_time_ms"],
    }

    print(json.dumps(result, indent=2))

    if not response["sources"]:
        raise RuntimeError("RAG query returned no sources")

    source_names = {source["source"] for source in response["sources"]}
    if "Ollama Local RAG Operations Runbook" not in source_names:
        raise RuntimeError(f"Expected runbook source, got: {sorted(source_names)}")

    logger.info("Local Ollama RAG smoke test passed")


if __name__ == "__main__":
    main()
