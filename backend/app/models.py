"""Pydantic Models for Request/Response Schemas."""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class QueryRequest(BaseModel):
    """Request schema for /query endpoint."""

    query: str = Field(..., description="User query string", min_length=1, max_length=2000)
    top_k: int = Field(5, description="Number of top documents to retrieve", ge=1, le=20)
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional filters for retrieval")


class SourceDocument(BaseModel):
    """Source document in query response."""

    text: str = Field(..., description="Document text chunk")
    score: float = Field(..., description="Similarity score (0-1)", ge=0.0, le=1.0)
    source: Optional[str] = Field(None, description="Document source/filename")
    chunk_index: Optional[int] = Field(None, description="Chunk index in source")


class QueryResponse(BaseModel):
    """Response schema for /query endpoint."""

    answer: str = Field(..., description="Generated answer from RAG pipeline")
    sources: List[SourceDocument] = Field([], description="Retrieved source documents")
    tokens_used: int = Field(0, description="Total tokens used in LLM call")
    execution_time_ms: float = Field(0.0, description="Query execution time in milliseconds")


class HealthResponse(BaseModel):
    """Response schema for /health endpoint."""

    status: str = Field("healthy", description="Health status")
    app_name: str = Field(..., description="Application name")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Environment (dev/staging/production)")


class DocumentMetadata(BaseModel):
    """Metadata for a document chunk."""

    source: str = Field(..., description="Source filename or URL")
    chunk_index: int = Field(..., description="Index of chunk in source")
    total_chunks: Optional[int] = Field(None, description="Total chunks in source")
    created_at: Optional[str] = Field(None, description="ISO timestamp when indexed")


class Document(BaseModel):
    """Document chunk for ingestion."""

    id: str = Field(..., description="Unique document ID")
    text: str = Field(..., description="Document text")
    metadata: DocumentMetadata = Field(..., description="Document metadata")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding (generated server-side)")
