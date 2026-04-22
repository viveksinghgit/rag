# Local Development Setup

Complete guide to setting up and developing RAG Azure locally.

## Prerequisites

- Docker & Docker Compose installed
- Git installed  
- Code editor (VS Code recommended)
- API keys for LLM providers:
  - Groq: https://console.groq.com/keys
  - Mistral (optional): https://console.mistral.ai/api-keys/

## Quick Start (5 Minutes)

```bash
# 1. Clone the repository
git clone https://github.com/<your-org>/rag-azure.git
cd rag-azure

# 2. Copy environment template
cp backend/.env.example backend/.env

# 3. Edit .env with your API keys
nano backend/.env
# Add: LITELLM_GROQ_API_KEY=your-key-here

# 4. Start all services
docker-compose up --build

# 5. Access the application
# UI:  http://localhost:3000
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

## Architecture

```
Frontend (React)
Port 3000
↓
FastAPI Backend
Port 8000
├─ Qdrant Vector DB
│  Port 6333
└─ LiteLLM (external APIs: Groq, Mistral)
```

## File Structure

```
backend/
├── app/
│   ├── main.py          # FastAPI entry point
│   ├── config.py        # Configuration management
│   ├── models.py        # Pydantic schemas
│   └── utils/           # Utility functions (Phase 2)
├── scripts/
│   └── ingest_docs.py   # Document ingestion (Phase 2)
├── Dockerfile           # Container build
├── requirements.txt     # Python dependencies
└── .env.example         # Configuration template

frontend/
├── src/
│   ├── App.jsx              # Main component
│   ├── api.js               # API client
│   ├── App.css              # Styling
│   └── components/
│       └── ChatInterface.jsx # Chat UI
├── public/
│   └── index.html
└── package.json

docs/
└── example_docs/        # Sample documents for indexing

docker-compose.yml      # Local environment orchestration
```

## Service Details

### Backend (FastAPI + Python)
Located: `backend/`

```bash
# Logs
docker-compose logs backend -f

# Rebuild
docker-compose build backend

# Access interactive shell
docker-compose exec backend bash

# Run tests (when available)
docker-compose exec backend pytest
```

**Endpoints**:
- `GET /health` — Service health check
- `POST /query` — Submit a query
- `POST /ingest` — Trigger document ingestion
- `GET /config` — View configuration
- `GET /docs` — Swagger API documentation

### Vector Database (Qdrant)
Located: Container from `qdrant/qdrant:latest`

```bash
# Logs
docker-compose logs qdrant -f

# Access Qdrant dashboard
# http://localhost:6333/dashboard

# Health check
curl http://localhost:6333/health
```

**Data**:
- Persists in `qdrant_storage/` volume

### Frontend (React)
Located: `frontend/`

```bash
# Logs
docker-compose logs frontend -f

# Rebuild
docker-compose build frontend

# Access interactive shell
docker-compose exec frontend bash

# Run tests
docker-compose exec frontend npm test
```

**Features**:
- Hot-reload on file changes
- Network requests logged to browser console

## Common Tasks

### Adding a Document

1. Add Markdown file to `docs/example_docs/`

```bash
echo "# My Document\n\nContent here." > docs/example_docs/my_doc.md
```

2. Trigger ingestion:

```bash
curl -X POST http://localhost:8000/ingest
```

3. Query to verify:

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "my document content", "top_k": 5}'
```

### Viewing Backend Logs

```bash
# All backend logs
docker-compose logs backend -f

# Last 50 lines
docker-compose logs backend --tail 50

# Filter logs
docker-compose logs backend | grep ERROR
```

### Restarting Services

```bash
# Restart specific service
docker-compose restart backend

# Restart all services
docker-compose restart

# Stop and restart
docker-compose down && docker-compose up
```

### Clearing Data

```bash
# Stop all services
docker-compose down

# Remove all data volumes
docker-compose down -v

# Clean up unused Docker resources
docker system prune -a
```

## Environment Configuration

Edit `backend/.env` for local development:

```bash
# Application
DEBUG=true              # Enable debug mode
ENVIRONMENT=local       # Environment type

# Qdrant
QDRANT_HOST=qdrant      # Docker service name 
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=documents

# LLM
LITELLM_GROQ_API_KEY=your-groq-key-here
LITELLM_LLM_MODEL=groq/mixtral-8x7b-32768
LITELLM_EMBEDDING_MODEL=mistral-embed

# RAG Configuration
RETRIEVAL_LIMIT=5
SIMILARITY_THRESHOLD=0.5
```

## Testing

### Manual Testing via cURL

```bash
# Health check
curl http://localhost:8000/health

# Get configuration
curl http://localhost:8000/config

# Submit a query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?", "top_k": 5}'

# Trigger ingestion
curl -X POST http://localhost:8000/ingest
```

### Using the Web UI

1. Navigate to http://localhost:3000
2. Test the chat interface
3. Check browser console (F12) for API logs

### Testing with Postman

1. Import API spec: `http://localhost:8000/openapi.json`
2. Create collection of requests
3. Test each endpoint

## Debugging

### Backend Issues

Enable debug mode in `.env`:
```bash
DEBUG=true
```

Then restart backend:
```bash
docker-compose restart backend
docker-compose logs backend -f
```

### Qdrant Connection Issues

```bash
# Test Qdrant is running
docker-compose ps

# Check Qdrant logs
docker-compose logs qdrant

# Verify connectivity
docker-compose exec backend curl http://qdrant:6333/health
```

### LLM Provider Issues

```bash
# Verify API keys are correct
docker-compose logs backend | grep "litellm"

# Test Groq connectivity
docker-compose exec backend python -c "
import requests
resp = requests.get('https://api.groq.com/openai/v1/models', 
    headers={'Authorization': 'Bearer YOUR_KEY'})
print(resp.json())
"
```

### Frontend Connection Issues

1. Check browser console (F12)
2. Check network tab for failed requests
3. Verify backend is running: `curl http://localhost:8000/health`
4. Verify API URL in frontend config

## Performance Optimization (Local)

### Reduce Image Size During build

```bash
# See final image size
docker-compose build backend --no-cache
docker image ls | grep rag-backend
```

Target: < 300MB

### Reduce Startup Time

```bash
# Use .dockerignore to exclude unnecessary files
cat > backend/.dockerignore << EOF
.git
__pycache__
*.pyc
.pytest_cache
.venv
EOF
```

### Watch File Performance

```bash
# Check if volumes are slowing down changes
docker-compose logs frontend | grep "compiled"
```

## IDE Integration (VS Code)

### Setup Python IntelliSense

1. Install Python extension
2. Ctrl+Shift+P → "Python: Select Interpreter"
3. Choose `.venv` or Docker interpreter

### Setup Node.js IntelliSense

1. Install ES7+ React/Redux/React-Native snippets
2. Extensions: Prettier, ESLint

### Debug Backend in VS Code

Add to `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI Debug",
      "type": "python",
      "request": "attach",
      "connect": {
        "host": "localhost",
        "port": 5678
      }
    }
  ]
}
```

## Troubleshooting

### "Port already in use"

```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>
```

### "Cannot find module" (Frontend)

```bash
docker-compose exec frontend npm install
```

### "Connection refused" (Backend → Qdrant)

```bash
# Ensure Qdrant is running
docker-compose ps

# Check network connectivity
docker-compose exec backend ping qdrant
```

### "Out of memory"

```bash
# Check Docker memory limits
docker stats

# Increase if needed
docker update --memory 4g <container_id>
```

## Next Steps

1. ✅ Deploy locally with docker-compose
2. 📝 Edit documents in `docs/example_docs/`
3. 🧪 Test API endpoints
4. 🐛 Explore code & make changes
5. 🚀 Ready for Azure deployment? See DEPLOYMENT-OPTIONS.md

---

For issues or questions, open a GitHub issue.
