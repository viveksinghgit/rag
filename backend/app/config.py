"""Application Configuration Management."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


def _load_secret(env_var: str, file_env_var: str, default: str = None) -> Optional[str]:
    """Load secret from environment variable or file."""
    # Try direct env var first
    if env_var in os.environ:
        value = os.getenv(env_var)
        if value:
            return value
    
    # Try file-based secret
    file_path_var = os.getenv(file_env_var)
    if file_path_var:
        file_path = Path(file_path_var)
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    return f.read().strip()
            except Exception:
                pass
    
    return default


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "RAG Azure API"
    app_version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    environment: str = os.getenv("ENVIRONMENT", "production")

    # Server
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))

    # Qdrant Vector Database
    qdrant_host: str = os.getenv("QDRANT_HOST", "qdrant")
    qdrant_port: int = int(os.getenv("QDRANT_PORT", "6333"))
    qdrant_collection_name: str = os.getenv("QDRANT_COLLECTION_NAME", "documents")
    qdrant_vector_size: int = int(os.getenv("QDRANT_VECTOR_SIZE", "768"))
    qdrant_recreate_on_vector_mismatch: bool = (
        os.getenv("QDRANT_RECREATE_ON_VECTOR_MISMATCH", "true").lower() == "true"
    )
    qdrant_admin_key: Optional[str] = _load_secret(
        "QDRANT_ADMIN_KEY",
        "QDRANT_ADMIN_KEY_FILE",
        default="default-key"
    )

    # LLM Provider Selection: 'ollama' or 'litellm'
    llm_provider: str = os.getenv("LLM_PROVIDER", "ollama").lower()
    embedding_provider: str = os.getenv("EMBEDDING_PROVIDER", "ollama").lower()

    # Ollama Configuration (for local LLM)
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b")
    ollama_embedding_model: str = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
    ollama_timeout: int = int(os.getenv("OLLAMA_TIMEOUT", "180"))
    litellm_groq_api_key: Optional[str] = _load_secret(
        "LITELLM_GROQ_API_KEY",
        "LITELLM_GROQ_API_KEY_FILE"
    )
    litellm_mistral_api_key: Optional[str] = _load_secret(
        "LITELLM_MISTRAL_API_KEY",
        "LITELLM_MISTRAL_API_KEY_FILE"
    )
    litellm_api_key: Optional[str] = _load_secret(
        "LITELLM_API_KEY",
        "LITELLM_API_KEY_FILE"
    )
    litellm_embedding_model: str = os.getenv("LITELLM_EMBEDDING_MODEL", "mistral/mistral-embed")
    litellm_llm_model: str = os.getenv("LITELLM_LLM_MODEL", "groq/mixtral-8x7b-32768")

    # Embedding Configuration
    embedding_dimension: int = int(os.getenv("EMBEDDING_DIMENSION", str(qdrant_vector_size)))
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "512"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "50"))

    # RAG Configuration
    retrieval_limit: int = int(os.getenv("RETRIEVAL_LIMIT", "5"))  # Top-k documents
    similarity_threshold: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.5"))
    context_window_limit: int = int(os.getenv("CONTEXT_WINDOW_LIMIT", "2000"))

    # Azure Blob Storage (optional, for document storage)
    azure_storage_account_name: Optional[str] = os.getenv("AZURE_STORAGE_ACCOUNT_NAME", None)
    azure_storage_account_key: Optional[str] = _load_secret(
        "AZURE_STORAGE_ACCOUNT_KEY",
        "AZURE_STORAGE_ACCOUNT_KEY_FILE"
    )
    azure_storage_container: str = os.getenv("AZURE_STORAGE_CONTAINER", "documents")

    # CORS
    cors_origins: list = ["*"]  # In production, restrict to specific domains

    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


settings = Settings()
