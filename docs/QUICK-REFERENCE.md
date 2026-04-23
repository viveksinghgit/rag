# RAG System Quick Reference

## 🚀 Start Everything

```bash
cd rag
docker-compose up --build
```

**What starts:**
- Ollama (LLM + embeddings) on port 11434
- Qdrant (vector DB) on port 6333
- FastAPI backend on port 8000
- React frontend on port 3000

## 📝 Configure Provider

### Option 1: Local Ollama (Recommended for testing)
```bash
# .env
LLM_PROVIDER=ollama
EMBEDDING_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5:0.5b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
QDRANT_VECTOR_SIZE=768
```

### Option 2: Cloud LLM (Groq/Mistral)
```bash
# .env
LLM_PROVIDER=litellm
LITELLM_GROQ_API_KEY=your-key
LITELLM_LLM_MODEL=groq/qwen/qwen3-32b
```

## 📚 Document Ingestion

```bash
# Ingest all docs (reads docs/ + Azure Blob Storage)
curl -X POST http://localhost:8000/ingest

# Or via the UI: click "Re-ingest Documents" in the settings panel

# Ingest from a specific directory
docker exec rag-backend python scripts/ingest_docs.py --docs-dir /path/to/docs

# Upload a file to Blob Storage (cloud deployments)
# Use the Upload Document button in the chat UI settings panel
```

## 🧪 Test the System

```bash
# Run complete E2E test
docker exec rag-backend python scripts/test_rag_e2e.py
```

## 🌐 Access Services

| Service | URL |
|---------|-----|
| Chat UI | http://localhost:3000 |
| API Docs | http://localhost:8000/docs |
| Qdrant Dashboard | http://localhost:6333 |
| Ollama | http://localhost:11434 |

## 📡 Example API Call

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?", "top_k": 5}'
```

## 🔍 Debugging

```bash
# Check service status
docker-compose ps

# View logs
docker logs rag-backend -f
docker logs rag-ollama -f
docker logs rag-qdrant -f

# Pull Ollama models
docker exec rag-ollama ollama pull qwen2.5:0.5b
docker exec rag-ollama ollama pull nomic-embed-text
docker exec rag-ollama ollama pull mistral

# Check Ollama is ready
docker exec rag-ollama ollama list
```

## 🛑 Stop Everything

```bash
docker-compose down
```

## 💾 Save/Restore Volumes

```bash
# Backup vector DB
docker cp rag-qdrant:/qdrant/storage ./backup/qdrant

# Backup Ollama models
docker cp rag-ollama:/root/.ollama ./backup/ollama
```

## ⚙️ Configuration Defaults

```
QDRANT_VECTOR_SIZE: 1024 (Mistral Embed, cloud) / 768 (nomic-embed-text, local)
CHUNK_SIZE: 512 tokens
TOP_K_RETRIEVAL: 5 documents
SIMILARITY_THRESHOLD: 0.5
OLLAMA_TIMEOUT: 180 seconds
```

## 🚨 Common Issues

| Issue | Solution |
|-------|----------|
| Ollama not downloading models | First run takes 2-5 min, check: `docker logs rag-ollama` |
| "Connection refused" on queries | Wait for all services healthy: `docker-compose ps` |
| Embedding dimension mismatch | Vector size must match model: 1024 (mistral-embed), 768 (nomic-embed-text) |
| Out of memory | Increase Docker memory or use smaller model |
| Frontend not loading | Check backend health: `curl http://localhost:8000/health` |

## 📊 Performance Tips

1. **First query slower** (model loading) - ~30-60 sec
2. **Repeated queries fast** - ~1-2 sec (due to caching)
3. **Use qwen2.5:0.5b** for constrained local testing
4. **Groq API** fastest cloud option
5. **Increase top_k** for more context (slower)

---

**More details**: See [RAG-SETUP-GUIDE.md](RAG-SETUP-GUIDE.md)
