"""FastAPI Application Entry Point - RAG Azure Backend."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import time

from app.config import settings
from app.models import QueryRequest, QueryResponse, HealthResponse, SourceDocument
from app.rag_pipeline import get_rag_pipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    
    # Initialize RAG pipeline
    try:
        pipeline = get_rag_pipeline()
        logger.info("✓ RAG Pipeline initialized")
        logger.info(f"  • LLM Provider: {settings.llm_provider}")
        logger.info(f"  • LLM Model: {settings.ollama_model if settings.llm_provider == 'ollama' else settings.litellm_llm_model}")
        logger.info(f"  • Embedding Model: {settings.ollama_embedding_model if settings.embedding_provider == 'ollama' else settings.litellm_embedding_model}")
        logger.info(f"  • Qdrant: {settings.qdrant_host}:{settings.qdrant_port}")
    except Exception as e:
        logger.error(f"⚠️  Warning: RAG Pipeline initialization failed: {str(e)}")
        logger.error("Some endpoints may fail until backend dependencies are available")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")


# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Retrieval-Augmented Generation API on Azure",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Process a RAG query.
    
    Endpoint: POST /query
    Request body:
    {
        "query": "What is machine learning?",
        "top_k": 5
    }
    
    Returns a QueryResponse with the generated answer and source documents.
    """
    try:
        logger.info(f"Processing query: {request.query[:100]}...")
        
        # Get RAG pipeline
        pipeline = get_rag_pipeline()
        
        # Execute RAG query
        result = pipeline.query(
            user_query=request.query,
            top_k=request.top_k,
            include_sources=True,
        )
        
        # Convert to response model
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
            execution_time_ms=result["execution_time_ms"]
        )
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest")
async def ingest_documents():
    """
    Trigger document ingestion (batch processing).
    
    This endpoint will call the ingestion pipeline to:
    1. Read documents from docs/ folder or Blob Storage
    2. Split into chunks
    3. Generate embeddings
    4. Upsert to Qdrant
    """
    try:
        import subprocess
        from pathlib import Path
        
        logger.info("Starting document ingestion pipeline...")
        
        # Run ingestion script
        ingestion_script = Path(__file__).parent.parent / "scripts" / "ingest_docs.py"
        
        result = subprocess.run(
            ["python", str(ingestion_script), "--docs-dir", "docs"],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )
        
        if result.returncode == 0:
            logger.info("✓ Ingestion completed successfully")
            return {
                "status": "success",
                "message": "Document ingestion completed",
                "output": result.stdout[-500:],  # Last 500 chars
            }
        else:
            logger.error(f"Ingestion failed: {result.stderr}")
            raise HTTPException(
                status_code=500,
                detail=f"Ingestion failed: {result.stderr[-200:]}",
            )
    except subprocess.TimeoutExpired:
        logger.error("Ingestion timed out after 5 minutes")
        raise HTTPException(status_code=504, detail="Ingestion timed out")
    except Exception as e:
        logger.error(f"Error during ingestion: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/config")
async def get_config():
    """
    Get current configuration (non-sensitive).
    
    Useful for debugging and verifying deployment settings.
    """
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
        "embedding_model": settings.ollama_embedding_model if settings.embedding_provider == "ollama" else settings.litellm_embedding_model,
        "llm_model": settings.ollama_model if settings.llm_provider == "ollama" else settings.litellm_llm_model,
        "retrieval_limit": settings.retrieval_limit,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level="info",
    )
