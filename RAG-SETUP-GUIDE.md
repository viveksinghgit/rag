# RAG System Complete Setup & Usage Guide

## Overview

This is a complete **Retrieval-Augmented Generation (RAG)** system featuring:
- 🗂️ **Qdrant**: Vector database for semantic search
- 🤖 **Ollama**: Local LLM service
- ⚡ **FastAPI**: Backend API
- ⚛️  **React**: Frontend chat interface
- 🔄 **LiteLLM**: Fallback for cloud LLMs (Groq, Mistral, OpenAI)

---

## Architecture 

```
┌─────────────────────────────────────────────────────────┐
│                   React Frontend                        │
│                    (Port 3000)                          │
└──────────────────────────┬──────────────────────────────┘
                           │
                ┌──────────▼──────────┐
                │  FastAPI Backend    │
                │   (Port 8000)       │
                └──┬────────────┬─────┘
                   │            │
        ┌──────────▼──┐  ┌──────▼────────────┐
        │   Ollama    │  │  Qdrant Vector   │
        │  (LLM+Embed)│  │  Database        │
        │ (Port 11434)│  │  (Port 6333)     │
        └─────────────┘  └──────────────────┘
```

---

## Prerequisites

- Docker & Docker Compose
- Python 3.9+
- 8GB+ RAM
- 20GB+ disk space (for Ollama models)

---

## Quick Start

### 1. Clone & Setup

```bash
cd /home/vs/projects/rag
```

### 2. Create .env File

```bash
cat > .env << 'EOF'
# Environment
DEBUG=true
ENVIRONMENT=local

# Qdrant
QDRANT_ADMIN_KEY=your-admin-key

# LLM Configuration - Choose provider
LLM_PROVIDER=ollama              # or 'litellm'
EMBEDDING_PROVIDER=ollama         # or 'litellm'

# Ollama Configuration
OLLAMA_MODEL=qwen2.5:0.5b         # or larger models: llama3.2:1b, qwen2.5:1.5b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
QDRANT_VECTOR_SIZE=768

# Optional: LiteLLM Configuration (for cloud models)
# LITELLM_GROQ_API_KEY=your-groq-key
# LITELLM_MISTRAL_API_KEY=your-mistral-key
# LITELLM_LLM_MODEL=groq/mixtral-8x7b-32768
EOF
```

### 3. Start Services

```bash
docker-compose up --build
```

**Wait for all services to be healthy:**
- ✓ Qdrant (http://localhost:6333)
- ✓ Ollama (http://localhost:11434)
- ✓ Backend (http://localhost:8000)
- ✓ Frontend (http://localhost:3000)

**Initial Ollama setup (~2-5 min on first run):**
```bash
# The small chat model and embedding model will auto-download
# Monitor Ollama logs:
docker logs rag-ollama -f
```

---

## Configuration

### LLM Provider Options

#### Option A: Ollama (Local, Free) ✓ Recommended for Testing

```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5:0.5b          # lightweight local model
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

**Available Ollama Models:**
```bash
# Pull models into Ollama
docker exec rag-ollama ollama pull qwen2.5:0.5b    # Lightweight default
docker exec rag-ollama ollama pull llama3.2:1b     # Better quality, still small
docker exec rag-ollama ollama pull qwen2.5:1.5b    # Stronger local model
docker exec rag-ollama ollama pull mistral          # Fast, good quality
docker exec rag-ollama ollama pull neural-chat      # Medium speed
docker exec rag-ollama ollama pull llama2            # Larger, slower
```

#### Option B: LiteLLM with Cloud Providers

```env
LLM_PROVIDER=litellm
LITELLM_GROQ_API_KEY=your-api-key
LITELLM_LLM_MODEL=groq/mixtral-8x7b-32768
LITELLM_EMBEDDING_MODEL=mistral-embed
```

**Supported Providers:**
- **Groq**: Fast, free tier available → https://console.groq.com
- **Mistral**:  High-quality models → https://console.mistral.ai
- **OpenAI**: GPT models → https://platform.openai.com

---

## Using the System

### Access the Chat Interface

```
Frontend:  http://localhost:3000
API Docs:  http://localhost:8000/docs
Qdrant UI: http://localhost:6333/dashboard
```

### Complete Workflow

#### Step 1: Ingest Documents

```bash
# Ingest sample documents
docker exec rag-backend python scripts/ingest_sample_documents.py --sample

# Or ingest a custom file
docker exec rag-backend python scripts/ingest_sample_documents.py --file /path/to/file.txt

# List indexed documents
docker exec rag-backend python scripts/ingest_sample_documents.py --list
```

#### Step 2: Run End-to-End Test

```bash
# Test the complete RAG pipeline
docker exec rag-backend python scripts/test_rag_e2e.py
```

**This will:**
1. ✓ Create Qdrant collection
2. ✓ Ingest 4 sample documents (~20 chunks)
3. ✓ Run 5 test queries
4. ✓ Generate `test_results.json`

#### Step 3: Use Chat Interface

1. Open http://localhost:3000
2. Type a question
3. Get RAG-powered answer with source documents

---

## API Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "app_name": "RAG Azure API",
  "version": "1.0.0",
  "environment": "local"
}
```

### Query with RAG
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "top_k": 5
  }'
```

Response:
```json
{
  "answer": "Machine learning is a subset of AI...",
  "sources": [
    {
      "text": "Machine Learning is a subset of...",
      "score": 0.94,
      "source": "Machine Learning Basics"
    }
  ],
  "tokens_used": 156,
  "execution_time_ms": 1234
}
```

---

## Sample Use Cases

### Use Case 1: Process Documentation

**Scenario:** Index your company's technical documentation and answer user questions

```bash
# 1. Place your docs in ./docs/
cp my-documentation.md ./docs/

# 2. Ingest
docker exec rag-backend python scripts/ingest_sample_documents.py --file /app/docs/my-documentation.md

# 3. Query via chat
# "How do I configure X?"
# System returns answer from your docs with source references
```

### Use Case 2: Knowledge Base

**Scenario:** Build a Q&A system over multiple documents

```bash
# Ingest all docs
for file in docs/*.md; do
  docker exec rag-backend python scripts/ingest_sample_documents.py --file "/app/$file"
done

# Now chat can reference any document
```

### Use Case 3: Real-Time Information

**Scenario:** Use with cloud LLM for the most current responses

```env
# Switch to cloud provider for latest model
LLM_PROVIDER=litellm
LITELLM_GROQ_API_KEY=your-key
LITELLM_LLM_MODEL=groq/mixtral-8x7b-32768
```

---

## Troubleshooting

### Services Not Starting

```bash
# Check Qdrant
docker logs rag-qdrant

# Check Ollama
docker logs rag-ollama

# Check Backend
docker logs rag-backend

# View all services
docker-compose ps
```

### Ollama Model Issues

```bash
# List available models
docker exec rag-ollama ollama list

# Check Ollama is running
docker exec rag-ollama ollama list

# Pull models manually
docker exec rag-ollama ollama pull qwen2.5:0.5b
docker exec rag-ollama ollama pull nomic-embed-text
```

### Embedding/Vector Size Mismatch

```env
# Ensure consistent vector sizes
QDRANT_VECTOR_SIZE=768        # nomic-embed-text output dimension
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

### Memory Issues

```bash
# Increase Docker memory if needed (in docker-compose.yml)
# environment:
#   - OLLAMA_MEMORY_LIMIT=8gb

docker-compose down
docker-compose up --build
```

### Cold Start Times

First query after startup may take 30-60 seconds (model loading). Subsequent queries are fast.

---

## Performance Optimization

### Query Optimization
```python
# Increase retrieval limit for more context
{
  "query": "Your question",
  "top_k": 10  # Default 5, increase for more context
}
```

### Embedding Caching
Queries are cached - repeated questions are instant.

### Model Selection
- **Gemma:7b** - Fast (recommended for testing)
- **Mistral** - Better quality (slower)
- **Llama2:7b** - Good balance
- **Groq API** - Fastest for cloud LLMs

---

## Adding More Documents

### Supported Formats
- Plain text (.txt)
- Markdown (.md)
- Add support for .pdf, .docx by extending `DocumentProcessor`

### Batch Ingestion
```bash
# Create docs directory
mkdir -p ./my_docs

# Add your documents
cp *.md ./my_docs/

# Ingest all
for file in ./my_docs/*.md; do
  docker exec rag-backend python scripts/ingest_sample_documents.py --file "/app$file"
done
```

---

## Monitoring & Logs

### View Collection Stats
```bash
# Check indexed documents
docker exec rag-backend python -c "
from qdrant_client import QdrantClient
client = QdrantClient(host='qdrant', port=6333)
collection = client.get_collection('documents')
print(f'Point count: {collection.points_count}')
"
```

### Monitor Token Usage
```bash
# Check in backend logs
docker logs rag-backend | grep "tokens_used"
```

---

## Next Steps

1. **Customize Models**: Try different Ollama models for speed/quality tradeoff
2. **Add Documents**: Ingest your own documents
3. **Extend Frontend**: Customize React UI for your use case
4. **Production Deployment**: Use the Terraform scripts in ./terraform/ for Azure deployment
5. **API Integration**: Call `/query` endpoint from your applications

---

## Architecture Files

- **Backend**: `./backend/app/`
  - `main.py` - FastAPI entry point
  - `rag_pipeline.py` - RAG orchestration
  - `utils/llm_router.py` - LLM provider routing
  - `utils/embedding.py` - Embedding management
  - `utils/retriever.py` - Document retrieval

- **Frontend**: `./frontend/src/`
  - `App.jsx` - Main React component
  - `components/ChatInterface.jsx` - Chat UI
  - `api.js` - Backend API client

- **Vector DB**: Qdrant runs in Docker
  - Web UI: http://localhost:6333
  - REST API: http://localhost:6333/api

- **Local LLM**: Ollama runs in Docker
  - API: http://localhost:11434

---

## Support & Resources

- **Qdrant Documentation**: https://qdrant.tech/documentation/
- **Ollama Models**: https://ollama.ai/library
- **FastAPI**: https://fastapi.tiangolo.com/
- **LiteLLM**: https://docs.litellm.ai/
- **React**: https://react.dev/

---

## File Structure

```
rag/
├── backend/
│   ├── app/
│   │   ├── main.py (FastAPI app)
│   │   ├── config.py (Configuration)
│   │   ├── rag_pipeline.py (RAG logic)
│   │   └── utils/
│   │       ├── embedding.py (Embedding manager)
│   │       ├── llm_router.py (LLM routing)
│   │       └── retriever.py (Vector search)
│   └── scripts/
│       ├── ingest_sample_documents.py (Document ingestion)
│       └── test_rag_e2e.py (E2E testing)
├── frontend/
│   └── src/
│       └── components/ChatInterface.jsx
├── docker-compose.yml (Services)
└── docs/
    └── example_docs/ (Sample documents)
```

---

**Happy RAGing! 🚀**
