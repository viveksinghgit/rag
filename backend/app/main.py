"""FastAPI Application Entry Point - RAG Azure Backend."""
import shutil
import subprocess
import tempfile
import time
from contextlib import asynccontextmanager
from pathlib import Path

import logging

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import QueryRequest, QueryResponse, HealthResponse, SourceDocument
from app.rag_pipeline import get_rag_pipeline
from app.utils.blob_storage import get_blob_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    try:
        pipeline = get_rag_pipeline()
        logger.info("✓ RAG Pipeline initialized")
        logger.info(f"  • LLM Provider: {settings.llm_provider}")
        logger.info(
            f"  • LLM Model: {settings.ollama_model if settings.llm_provider == 'ollama' else settings.litellm_llm_model}"
        )
        logger.info(
            f"  • Embedding Model: {settings.ollama_embedding_model if settings.embedding_provider == 'ollama' else settings.litellm_embedding_model}"
        )
        logger.info(f"  • Qdrant: {settings.qdrant_host}:{settings.qdrant_port}")
    except Exception as e:
        logger.error(f"⚠️  RAG Pipeline init failed: {e}")
    yield
    logger.info("Shutting down application")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Retrieval-Augmented Generation API on Azure",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    try:
        logger.info(f"Processing query: {request.query[:100]}...")
        pipeline = get_rag_pipeline()
        result = pipeline.query(
            user_query=request.query,
            top_k=request.top_k,
            include_sources=True,
        )
        sources = [
            SourceDocument(
                text=src["text"],
                score=src["score"],
                source=src["source"],
                chunk_index=src.get("chunk_index"),
            )
            for src in result["sources"]
        ]
        return QueryResponse(
            answer=result["answer"],
            sources=sources,
            tokens_used=result["tokens_used"],
            execution_time_ms=result["execution_time_ms"],
        )
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a document to Azure Blob Storage for indexing."""
    blob = get_blob_client()
    if blob is None:
        raise HTTPException(
            status_code=503,
            detail="Azure Blob Storage not configured. Set AZURE_STORAGE_ACCOUNT_NAME and AZURE_STORAGE_ACCOUNT_KEY.",
        )
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    blob.upload(file.filename, content, file.content_type or "application/octet-stream")
    logger.info("Uploaded document: %s (%d bytes)", file.filename, len(content))
    return {
        "status": "success",
        "filename": file.filename,
        "size": len(content),
        "message": f"'{file.filename}' uploaded. Click 'Re-ingest Documents' to index it.",
    }


@app.get("/documents")
async def list_documents():
    """List documents stored in Azure Blob Storage."""
    blob = get_blob_client()
    if blob is None:
        return {"documents": [], "storage_configured": False}
    try:
        return {"documents": blob.list_blobs(), "storage_configured": True}
    except Exception as e:
        logger.error("Failed to list blobs: %s", e)
        return {"documents": [], "storage_configured": True, "error": str(e)}


@app.post("/ingest")
async def ingest_documents():
    """
    Trigger document ingestion.

    Ingests from two sources (whichever are available):
    1. docs/ — static project documents built into the image
    2. Azure Blob Storage "documents" container — user-uploaded files
    """
    try:
        logger.info("Starting document ingestion pipeline...")

        ingestion_script = Path(__file__).parent.parent / "scripts" / "ingest_docs.py"
        if not ingestion_script.exists():
            raise HTTPException(
                status_code=500,
                detail=f"Ingestion script not found: {ingestion_script}",
            )

        static_docs = Path(__file__).parent.parent / "docs"
        docs_dirs = [str(static_docs)] if static_docs.exists() else []

        tmp_dir = None
        blob = get_blob_client()
        if blob:
            tmp_dir = Path(tempfile.mkdtemp(prefix="rag_blob_"))
            try:
                n = blob.download_all_to_dir(tmp_dir)
                if n > 0:
                    logger.info("Downloaded %d files from Blob Storage", n)
                    docs_dirs.append(str(tmp_dir))
                else:
                    logger.info("No files in Blob Storage container")
            except Exception as exc:
                logger.warning("Blob download skipped: %s", exc)

        if not docs_dirs:
            return {"status": "error", "message": "No document sources found."}

        cmd = ["python", str(ingestion_script)]
        for d in docs_dirs:
            cmd += ["--docs-dir", d]

        logger.info("Running: %s", " ".join(cmd))
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        finally:
            if tmp_dir:
                shutil.rmtree(tmp_dir, ignore_errors=True)

        if result.returncode == 0:
            logger.info("✓ Ingestion completed successfully")
            return {
                "status": "success",
                "message": "Document ingestion completed",
                "output": result.stdout[-500:],
            }
        else:
            logger.error("Ingestion failed: %s", result.stderr)
            return {
                "status": "error",
                "message": "Document ingestion failed",
                "error": result.stderr[-500:],
                "return_code": result.returncode,
            }

    except subprocess.TimeoutExpired:
        logger.error("Ingestion timed out")
        return {"status": "error", "message": "Ingestion timed out after 5 minutes."}
    except Exception as e:
        logger.error("Error during ingestion: %s", e, exc_info=True)
        return {"status": "error", "message": str(e)}


@app.get("/config")
async def get_config():
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "debug": settings.debug,
        "qdrant_host": settings.qdrant_host,
        "qdrant_port": settings.qdrant_port,
        "qdrant_collection": settings.qdrant_collection_name,
        "qdrant_vector_size": settings.qdrant_vector_size,
        "llm_provider": settings.llm_provider,
        "embedding_provider": settings.embedding_provider,
        "embedding_model": (
            settings.ollama_embedding_model
            if settings.embedding_provider == "ollama"
            else settings.litellm_embedding_model
        ),
        "llm_model": (
            settings.ollama_model
            if settings.llm_provider == "ollama"
            else settings.litellm_llm_model
        ),
        "retrieval_limit": settings.retrieval_limit,
        "storage_configured": bool(
            settings.azure_storage_account_name and settings.azure_storage_account_key
        ),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.host, port=settings.port, log_level="info")
