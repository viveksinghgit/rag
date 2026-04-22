"""Secrets Management Utility

Loads sensitive credentials from files instead of environment variables.
This helps prevent accidental commits of secrets to version control.
"""
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def load_secret_from_file(env_var_name: str, file_path_env_var: str, default: str = None) -> str:
    """
    Load a secret from a file path specified in an environment variable.
    
    Priority:
    1. If direct env_var_name exists, use it (for backward compatibility)
    2. If file_path_env_var exists, read from file
    3. Return default value
    
    Args:
        env_var_name: Name of direct environment variable (e.g., QDRANT_ADMIN_KEY)
        file_path_env_var: Name of file path environment variable (e.g., QDRANT_ADMIN_KEY_FILE)
        default: Default value if neither source exists
    
    Returns:
        Secret value from environment or file
    """
    # Try direct environment variable first (backward compatibility)
    if env_var_name in os.environ:
        value = os.getenv(env_var_name)
        if value:
            logger.debug(f"✓ Loaded {env_var_name} from environment variable")
            return value
    
    # Try file-based secret
    file_path_var = os.getenv(file_path_env_var)
    if file_path_var:
        file_path = Path(file_path_var)
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    value = f.read().strip()
                if value:
                    logger.debug(f"✓ Loaded {env_var_name} from file: {file_path}")
                    return value
            except Exception as e:
                logger.warning(f"⚠️  Failed to read secret from {file_path}: {str(e)}")
        else:
            logger.debug(f"Secret file not found: {file_path}")
    
    # Return default
    if default:
        logger.debug(f"Using default value for {env_var_name}")
    return default


def load_all_secrets() -> dict:
    """
    Load all secrets from files.
    
    Returns:
        Dictionary with all loaded secrets
    """
    secrets = {
        "qdrant_admin_key": load_secret_from_file(
            "QDRANT_ADMIN_KEY",
            "QDRANT_ADMIN_KEY_FILE",
            default="default-key"
        ),
        "groq_api_key": load_secret_from_file(
            "LITELLM_GROQ_API_KEY",
            "LITELLM_GROQ_API_KEY_FILE",
            default=None
        ),
        "mistral_api_key": load_secret_from_file(
            "LITELLM_MISTRAL_API_KEY",
            "LITELLM_MISTRAL_API_KEY_FILE",
            default=None
        ),
        "openai_api_key": load_secret_from_file(
            "LITELLM_API_KEY",
            "LITELLM_API_KEY_FILE",
            default=None
        ),
        "azure_storage_key": load_secret_from_file(
            "AZURE_STORAGE_ACCOUNT_KEY",
            "AZURE_STORAGE_ACCOUNT_KEY_FILE",
            default=None
        ),
    }
    
    # Log what was loaded
    loaded = [k for k, v in secrets.items() if v]
    logger.info(f"Loaded secrets: {', '.join(loaded)}")
    
    return secrets
