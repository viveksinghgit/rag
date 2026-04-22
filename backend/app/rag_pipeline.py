"""RAG Pipeline - Core retrieval-augmented generation orchestration."""
import logging
import time
from typing import Dict, Any, List
from app.utils.embedding import get_embedding_manager
from app.utils.retriever import get_retriever
from app.utils.llm_router import get_llm_router
from app.config import settings

logger = logging.getLogger(__name__)


class RAGPipeline:
    """Core RAG orchestration - chains retrieval, context building, and LLM generation."""

    def __init__(self):
        """Initialize RAG pipeline components."""
        self.embedding_manager = get_embedding_manager()
        self.retriever = get_retriever()
        self.llm_router = get_llm_router()

    def query(
        self,
        user_query: str,
        top_k: int = 5,
        include_sources: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute RAG query - retrieve context and generate response.

        Args:
            user_query: User's question
            top_k: Number of documents to retrieve
            include_sources: Whether to include source documents

        Returns:
            Dictionary with answer, sources, metadata
        """
        start_time = time.time()
        logger.info(f"📥 RAG Query: {user_query[:100]}...")

        try:
            # Step 1: Embed the query
            step1_start = time.time()
            query_embedding = self.embedding_manager.embed_query(user_query)
            step1_time = time.time() - step1_start
            logger.debug(f"Step 1 (Embedding): {step1_time:.3f}s")

            # Step 2: Retrieve similar documents
            step2_start = time.time()
            retrieved_docs = self.retriever.search(
                query_vector=query_embedding,
                limit=top_k,
                score_threshold=settings.similarity_threshold,
            )
            step2_time = time.time() - step2_start
            logger.debug(f"Step 2 (Retrieval): {step2_time:.3f}s, docs: {len(retrieved_docs)}")

            # Step 3: Build context for LLM
            context_text = self._build_context(retrieved_docs)
            
            # Step 4: Generate LLM response
            step4_start = time.time()
            llm_result = self._generate_response(user_query, context_text)
            step4_time = time.time() - step4_start
            logger.debug(f"Step 4 (LLM): {step4_time:.3f}s")

            # Step 5: Format response
            total_time = time.time() - start_time

            response = {
                "answer": llm_result["answer"],
                "sources": self._format_sources(retrieved_docs) if include_sources else [],
                "tokens_used": llm_result["tokens_used"],
                "execution_time_ms": int(total_time * 1000),
                "metadata": {
                    "query": user_query,
                    "retrieval_limit": top_k,
                    "retrieved_count": len(retrieved_docs),
                    "similarity_threshold": settings.similarity_threshold,
                    "model": llm_result.get("provider"),
                    "step_timings": {
                        "embedding_ms": int(step1_time * 1000),
                        "retrieval_ms": int(step2_time * 1000),
                        "llm_ms": int(step4_time * 1000),
                    },
                    "cost_estimate": llm_result.get("cost_estimate", 0),
                },
            }

            logger.info(
                f"✓ RAG Query Complete: {total_time:.2f}s, "
                f"tokens: {llm_result['tokens_used']}, "
                f"sources: {len(retrieved_docs)}"
            )

            return response

        except Exception as e:
            logger.error(f"✗ RAG Query Failed: {str(e)}", exc_info=True)
            raise

    def _build_context(self, documents: List[Dict[str, Any]]) -> str:
        """Build context string from retrieved documents."""
        if not documents:
            return "No relevant documents found."

        context_parts = ["## Retrieved Context:\n"]
        remaining_chars = settings.context_window_limit

        for i, doc in enumerate(documents, 1):
            doc_text = doc["text"]
            if remaining_chars <= 0:
                break

            included_text = doc_text[:remaining_chars]
            remaining_chars -= len(included_text)

            context_parts.append(
                f"\n### Document {i} (Source: {doc['source']}, Score: {doc['score']:.2f})"
            )
            context_parts.append(f"\n{included_text}")

        return "\n".join(context_parts)

    def _generate_response(
        self,
        query: str,
        context: str,
    ) -> Dict[str, Any]:
        """Generate LLM response using query and context."""
        system_prompt = (
            "You are a helpful assistant. Use the provided context to answer questions. "
            "Only use facts that appear in the context. "
            "If the context doesn't contain relevant information, say so. "
            "Do not invent model names, vector sizes, ports, or configuration values."
        )

        combined_prompt = f"""Context for answering the question:

{context}

---

Question: {query}

Please provide a clear, concise answer based on the above context."""

        result = self.llm_router.get_llm_response(
            prompt=combined_prompt,
            system_prompt=system_prompt,
            temperature=0.1,
            max_tokens=500,
        )

        return result

    def _format_sources(
        self, documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Format retrieved documents as sources."""
        sources = []

        for doc in documents:
            sources.append(
                {
                    "text": doc["text"][:200],  # Preview
                    "source": doc["source"],
                    "score": round(doc["score"], 3),
                    "chunk_index": doc.get("chunk_index", 0),
                }
            )

        return sources

    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics for monitoring."""
        return {
            "embedding": self.embedding_manager.get_embedding_stats(),
            "collection": self.retriever.get_collection_info(),
            "llm_usage": self.llm_router.get_usage_stats(),
        }


# Singleton instance
_pipeline = None


def get_rag_pipeline() -> RAGPipeline:
    """Get or create RAG pipeline singleton."""
    global _pipeline
    if _pipeline is None:
        _pipeline = RAGPipeline()
    return _pipeline
