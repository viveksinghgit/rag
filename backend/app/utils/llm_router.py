"""LLM Router - routes generation and embedding calls to Ollama or LiteLLM."""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import requests

from app.config import settings

logger = logging.getLogger(__name__)

litellm = None


def _get_litellm():
    """Import LiteLLM only when the configured provider needs it."""
    global litellm
    if litellm is None:
        import litellm as litellm_module

        litellm_module.drop_params = True
        litellm_module.add_function_to_prompt = True
        litellm = litellm_module
    return litellm


class OllamaClient:
    """Small HTTP client for Ollama's local API."""

    def __init__(self, host: str = "http://localhost:11434"):
        self.host = host.rstrip("/")
        self.api_url = f"{self.host}/api"
        logger.info("Ollama client initialized: %s", self.host)

    def _call_ollama(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        response = requests.post(
            f"{self.api_url}/{endpoint}",
            json=data,
            timeout=settings.ollama_timeout,
        )
        response.raise_for_status()
        return response.json()

    def generate(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> Dict[str, Any]:
        request_data = {
            "model": model,
            "prompt": prompt,
            "system": system_prompt or "",
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
            "stream": False,
        }

        response = self._call_ollama("generate", request_data)
        tokens_used = response.get("eval_count", 0) + response.get("prompt_eval_count", 0)

        return {
            "text": response.get("response", ""),
            "tokens_used": tokens_used,
            "prompt_tokens": response.get("prompt_eval_count", 0),
            "completion_tokens": response.get("eval_count", 0),
        }

    def embed(self, model: str, text: Union[str, List[str]]) -> Dict[str, Any]:
        is_batch = isinstance(text, list)
        response = self._call_ollama(
            "embed",
            {
                "model": model,
                "input": text if is_batch else [text],
            },
        )
        embeddings = response.get("embeddings", [])

        if is_batch:
            return {"embeddings": embeddings}
        return {"embedding": embeddings[0] if embeddings else []}

    def is_available(self) -> bool:
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as exc:
            logger.warning("Ollama service unavailable: %s", exc)
            return False


class LLMRouter:
    """Router for generation and embeddings."""

    def __init__(self):
        self.provider = settings.llm_provider
        self.embedding_provider = settings.embedding_provider
        self.token_counters: Dict[str, int] = {}
        self.ollama_client: Optional[OllamaClient] = None

        if self.provider == "ollama" or self.embedding_provider == "ollama":
            self.ollama_client = OllamaClient(settings.ollama_host)
            if not self.ollama_client.is_available():
                if self.provider == "ollama":
                    logger.warning("Ollama unavailable for LLM calls; falling back to LiteLLM")
                    self.provider = "litellm"
                if self.embedding_provider == "ollama":
                    logger.warning("Ollama unavailable for embeddings; falling back to LiteLLM")
                    self.embedding_provider = "litellm"

        if self.provider == "litellm" or self.embedding_provider == "litellm":
            self._configure_litellm()

        logger.info(
            "LLM router ready: llm=%s embedding=%s",
            self.provider,
            self.embedding_provider,
        )

    def _configure_litellm(self):
        litellm_module = _get_litellm()
        if settings.litellm_groq_api_key:
            litellm_module.groq_api_key = settings.litellm_groq_api_key
        if settings.litellm_mistral_api_key:
            litellm_module.mistral_api_key = settings.litellm_mistral_api_key
        if settings.litellm_api_key:
            litellm_module.api_key = settings.litellm_api_key

    def get_llm_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> Dict[str, Any]:
        if self.provider == "ollama":
            return self._get_ollama_response(prompt, system_prompt, temperature, max_tokens)
        return self._get_litellm_response(prompt, system_prompt, temperature, max_tokens)

    def _get_ollama_response(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> Dict[str, Any]:
        if self.ollama_client is None:
            raise RuntimeError("Ollama client is not initialized")

        result = self.ollama_client.generate(
            model=settings.ollama_model,
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        self._track_usage(result["tokens_used"])

        return {
            "answer": result["text"],
            "tokens_used": result["tokens_used"],
            "prompt_tokens": result["prompt_tokens"],
            "completion_tokens": result["completion_tokens"],
            "cost_estimate": 0.0,
            "provider": f"ollama/{settings.ollama_model}",
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _get_litellm_response(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> Dict[str, Any]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        litellm_module = _get_litellm()
        response = litellm_module.completion(
            model=settings.litellm_llm_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            fallbacks=["mistral/mistral-medium"],
        )

        tokens_used = response.usage.total_tokens
        self._track_usage(tokens_used)

        return {
            "answer": response.choices[0].message.content,
            "tokens_used": tokens_used,
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "cost_estimate": (tokens_used / 1000) * 0.0002,
            "provider": settings.litellm_llm_model,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def embed_text(self, text: str, model: Optional[str] = None) -> Dict[str, Any]:
        if self.embedding_provider == "ollama":
            return self._embed_ollama(text, model)
        return self._embed_litellm(text, model)

    def embed_texts(self, texts: List[str], model: Optional[str] = None) -> Dict[str, Any]:
        if not texts:
            return {"embeddings": [], "tokens_used": 0, "count": 0, "model": model}
        if self.embedding_provider == "ollama":
            return self._embed_texts_ollama(texts, model)
        return self._embed_texts_litellm(texts, model)

    def _embed_ollama(self, text: str, model: Optional[str] = None) -> Dict[str, Any]:
        if self.ollama_client is None:
            raise RuntimeError("Ollama client is not initialized")

        model = model or settings.ollama_embedding_model
        result = self.ollama_client.embed(model, text)
        embedding = result["embedding"]
        self._validate_embedding(embedding, model)

        return {
            "embedding": embedding,
            "tokens_used": 0,
            "cost_estimate": 0.0,
            "model": model,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _embed_texts_ollama(self, texts: List[str], model: Optional[str] = None) -> Dict[str, Any]:
        if self.ollama_client is None:
            raise RuntimeError("Ollama client is not initialized")

        model = model or settings.ollama_embedding_model
        result = self.ollama_client.embed(model, texts)
        embeddings = result["embeddings"]
        if embeddings:
            self._validate_embedding(embeddings[0], model)

        return {
            "embeddings": embeddings,
            "tokens_used": 0,
            "count": len(embeddings),
            "model": model,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _embed_litellm(self, text: str, model: Optional[str] = None) -> Dict[str, Any]:
        model = model or settings.litellm_embedding_model
        litellm_module = _get_litellm()
        response = litellm_module.embedding(model=model, input=[text])
        embedding = response.data[0]["embedding"]
        self._validate_embedding(embedding, model)

        return {
            "embedding": embedding,
            "tokens_used": response.usage.prompt_tokens,
            "cost_estimate": 0.0,
            "model": model,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _embed_texts_litellm(self, texts: List[str], model: Optional[str] = None) -> Dict[str, Any]:
        model = model or settings.litellm_embedding_model
        litellm_module = _get_litellm()
        response = litellm_module.embedding(model=model, input=texts)
        embeddings = [item["embedding"] for item in response.data]
        if embeddings:
            self._validate_embedding(embeddings[0], model)

        return {
            "embeddings": embeddings,
            "tokens_used": response.usage.prompt_tokens,
            "count": len(embeddings),
            "model": model,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _validate_embedding(self, embedding: List[float], model: str):
        actual_size = len(embedding)
        if actual_size != settings.qdrant_vector_size:
            raise ValueError(
                f"Embedding model '{model}' produced {actual_size} dimensions, "
                f"but QDRANT_VECTOR_SIZE is {settings.qdrant_vector_size}. "
                "Update QDRANT_VECTOR_SIZE or choose a matching embedding model."
            )

    def _track_usage(self, tokens: int):
        today = datetime.utcnow().date().isoformat()
        self.token_counters[today] = self.token_counters.get(today, 0) + tokens

    def get_usage_stats(self) -> Dict[str, Any]:
        total_tokens = sum(self.token_counters.values())
        return {
            "daily_breakdown": self.token_counters,
            "total_tokens": total_tokens,
            "estimated_cost": 0.0 if self.provider == "ollama" else (total_tokens / 1000) * 0.0002,
        }


_router = None


def get_llm_router() -> LLMRouter:
    """Get or create LLM router singleton."""
    global _router
    if _router is None:
        _router = LLMRouter()
    return _router
