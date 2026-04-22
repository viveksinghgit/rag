# Ollama Local RAG Operations Runbook

This runbook describes how the local RAG assistant should answer operational questions for the lightweight Ollama deployment.

## Service Topology

The local stack runs four primary services. The React frontend listens on port 3000, the FastAPI backend listens on port 8000, Qdrant listens on port 6333, and Ollama listens on port 11434. The backend is the only service that talks to both Qdrant and Ollama during a normal user query.

## Model Configuration

The default local language model is `qwen2.5:0.5b`. It is selected because it is small enough for constrained WSL and Docker setups. Larger local alternatives include `llama3.2:1b` and `qwen2.5:1.5b` after increasing available memory.

Document embeddings use `nomic-embed-text`. This model produces 768-dimensional vectors, so Qdrant must be configured with `QDRANT_VECTOR_SIZE=768`. If the collection was previously created with a different vector size, the local test setup may recreate the collection before re-ingesting documents.

## Query Flow

When a user asks a question, the backend embeds the query with Ollama, searches Qdrant for similar chunks, builds a context prompt, and sends that prompt to the local Ollama chat model. The final response should include an answer and source snippets from the retrieved documents.

## Troubleshooting

If queries fail with a vector size error, verify that the embedding model and `QDRANT_VECTOR_SIZE` agree. If generation fails, check that `docker exec rag-ollama ollama list` shows the configured language model. If retrieval returns no sources, run the ingestion script again and confirm that Qdrant contains points in the `documents` collection.
