# RAG Azure — 1-Click Deploy Retrieval-Augmented Generation

**Cost-efficient, production-ready RAG system deployable to Azure in 5 minutes. Run locally with a single `docker-compose up`.**

[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fviveksinghgit%2Frag%2Fmain%2Fterraform%2Fazuredeploy.json)

> The Deploy to Azure button requires `terraform/azuredeploy.json` (ARM template) to be generated from the Terraform config — see [docs/DEPLOYMENT-OPTIONS.md](docs/DEPLOYMENT-OPTIONS.md).

---

## What is RAG?

**Retrieval-Augmented Generation** is an AI technique that makes language models more accurate and grounded by combining two steps:

1. **Retrieve** — find relevant document chunks from your knowledge base using semantic (vector) search
2. **Generate** — feed those chunks as context to an LLM so it answers using your actual documents rather than hallucinating

This system embeds your documents into vectors stored in Qdrant, and on every query it retrieves the most similar chunks before calling Groq/Mistral/Ollama.

---

## Quick Start — Local (5 minutes)

```bash
# 1. Clone
git clone https://github.com/viveksinghgit/rag.git
cd rag

# 2. Copy and review the env template (default works out of the box with Ollama)
cp .env.example .env        # already provided — no keys needed for local Ollama mode

# 3. Start everything (Ollama + Qdrant + FastAPI + React UI)
docker-compose up --build

# 4. Open the UI
open http://localhost:3000
```

The first run pulls the Ollama models (`qwen2.5:0.5b` + `nomic-embed-text`) which takes 2-5 minutes depending on your connection. Subsequent starts are fast.

**Default local stack:**
| Service | URL | Notes |
|---|---|---|
| React UI | http://localhost:3000 | Chat interface with RAG explanation |
| FastAPI backend | http://localhost:8000 | REST API + `/docs` Swagger UI |
| Qdrant vector DB | http://localhost:6333 | Key: `local-rag-admin-key` |
| Ollama LLM | http://localhost:11434 | Local model, no API keys needed |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Browser                           │
│          (React SPA — chat + RAG explanation panel)         │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP / HTTPS
                          ▼
┌─────────────────────────────────────────────────────────────┐
│         FastAPI Backend (Python 3.11)                       │
│                                                             │
│  POST /query  →  RAG Pipeline                               │
│  POST /ingest →  Document Ingestion                         │
│  GET  /health →  Service Status                             │
│  GET  /config →  Non-sensitive config                       │
│                                                             │
│  ┌─────────────────┐    ┌──────────────────────────────┐   │
│  │  EmbeddingMgr   │    │        LLMRouter             │   │
│  │  (LRU cache)    │    │  Ollama (local) or           │   │
│  └────────┬────────┘    │  LiteLLM → Groq / Mistral   │   │
│           │             └──────────────────────────────┘   │
└───────────┼─────────────────────────────────────────────────┘
            │ embed query
            ▼
┌───────────────────────┐
│   Qdrant Vector DB    │   ← stores document embeddings
│   (768-dim COSINE)    │   ← semantic search top-K
└───────────────────────┘
```

### Query flow (end-to-end)

```
1. User types:    "What is machine learning?"
                   ↓
2. Embed query:   Convert to 768-dim vector (Ollama nomic-embed-text or Mistral)
                   ↓
3. Vector search: Qdrant returns top-5 most similar document chunks
                   ↓
4. Build context: Combine chunks into a prompt prefix
                   ↓
5. LLM call:      Groq mixtral-8x7b or local qwen2.5 generates the answer
                   ↓
6. Response:      Answer + sources + confidence scores + timing/tokens
                   ↓
7. UI display:    Chat bubble with expandable sources panel
```

---

## Cost Breakdown (Azure)

| Component | Service | Est. Cost/mo |
|---|---|---|
| Backend | App Service B1 | $13 |
| Vector DB | Container Instances (Qdrant) | $25–35 |
| Storage | Blob Storage LRS | $2–3 |
| LLM | Groq API (100K tokens/mo) | $1–5 |
| **Total** | | **$41–56/mo** |

Groq is ~20–50× cheaper than Azure OpenAI for the same models.

---

## Features

- **Local-first**: Full stack runs offline with Ollama — no API keys required
- **1-click Azure deploy**: Terraform + ARM template for production
- **Multi-provider LLM routing**: Groq → Mistral fallback via LiteLLM
- **Semantic search**: Qdrant with cosine similarity on 768-dim vectors
- **Source tracking**: Every answer cites source documents + confidence scores
- **Educational UI**: Built-in explanation of how RAG works — great for demos
- **Document ingestion**: Drop `.md` files in `docs/example_docs/` and re-ingest

---

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 |
| Backend | FastAPI + Python 3.11 |
| Vector DB | Qdrant |
| LLM routing | LiteLLM |
| LLM (cloud) | Groq `mixtral-8x7b-32768` (primary), Mistral (fallback) |
| LLM (local) | Ollama `qwen2.5:0.5b` |
| Embeddings (local) | Ollama `nomic-embed-text` (768-dim) |
| Embeddings (cloud) | Mistral Embed |
| Container | Docker + docker-compose |
| IaC | Terraform (Azure) |
| Hosting | Azure App Service + Container Instances + Blob Storage |

---

## Documentation

| Doc | Description |
|---|---|
| [docs/LOCAL-DEVELOPMENT.md](docs/LOCAL-DEVELOPMENT.md) | Local setup and workflow |
| [docs/DEPLOYMENT-OPTIONS.md](docs/DEPLOYMENT-OPTIONS.md) | Azure, Docker, and other deployment methods |
| [docs/README-ARCHITECTURE.md](docs/README-ARCHITECTURE.md) | Deep technical architecture |
| [docs/SETUP-GUIDE.md](docs/SETUP-GUIDE.md) | Step-by-step setup guide |
| [docs/DOCKER-SETUP.md](docs/DOCKER-SETUP.md) | Docker configuration details |
| [docs/COST-BREAKDOWN.md](docs/COST-BREAKDOWN.md) | Detailed cost analysis |
| [docs/FAQ.md](docs/FAQ.md) | Common questions |
| [docs/CHAT-USAGE-GUIDE.md](docs/CHAT-USAGE-GUIDE.md) | Chat UI guide: questions, settings, API usage |
| [docs/QUICK-REFERENCE.md](docs/QUICK-REFERENCE.md) | Command cheat sheet |
| [docs/NEXT-STEPS.md](docs/NEXT-STEPS.md) | Roadmap |

---

## Project Structure

```
rag/
├── backend/                    # FastAPI Python backend
│   ├── app/
│   │   ├── main.py             # Routes: /query /ingest /health /config
│   │   ├── config.py           # Pydantic settings (env vars + secret files)
│   │   ├── models.py           # Request/response schemas
│   │   ├── rag_pipeline.py     # RAG orchestration
│   │   └── utils/
│   │       ├── embedding.py    # Embedding manager with LRU cache
│   │       ├── llm_router.py   # Ollama / LiteLLM routing
│   │       ├── retriever.py    # Qdrant client wrapper
│   │       └── document_processor.py
│   ├── scripts/
│   │   ├── ingest_docs.py      # Document ingestion pipeline
│   │   └── ingest_sample_documents.py
│   ├── Dockerfile              # Multi-stage build (~300MB runtime)
│   └── requirements.txt
├── frontend/                   # React 18 SPA
│   └── src/
│       ├── App.jsx             # Health check + layout
│       ├── App.css
│       ├── api.js              # Axios HTTP client
│       └── components/
│           └── ChatInterface.jsx  # Chat + RAG intro panel
├── terraform/                  # Azure IaC
│   ├── main.tf                 # App Service, Container Instances, Storage
│   ├── variables.tf            # Input variables with validation
│   ├── outputs.tf              # Deployment outputs
│   └── terraform.tfvars.example
├── docs/                       # All documentation
│   ├── example_docs/           # Sample docs auto-ingested on startup
│   └── *.md
├── .env.example                # Config template — copy to .env
├── docker-compose.yml          # Local dev orchestration
└── .gitignore                  # Excludes .env, secrets/, *.key, *.tfvars
```

---

## Security

| Status | Item |
|---|---|
| ✅ | Secrets loaded from env vars or files — never hardcoded |
| ✅ | `secrets/` and `.env` excluded from git via `.gitignore` |
| ✅ | HTTPS enforced on Azure (App Service + TLS 1.2+) |
| ✅ | Qdrant API key required (set via `QDRANT__SERVICE__API_KEY`) |
| ✅ | Terraform marks sensitive vars with `sensitive = true` |
| ⚠️ | No user authentication (planned for Phase 2) |
| ⚠️ | CORS allows `*` in dev — restrict in production |

**For production**, enable Azure Key Vault, add Azure AD authentication, and restrict CORS origins.

---

## Troubleshooting

### "Qdrant invalid key" error
The backend and Qdrant must share the same key. In docker-compose both use `${QDRANT_ADMIN_KEY:-local-rag-admin-key}`:
```bash
# Wipe old volumes and restart fresh
docker-compose down -v
docker-compose up --build
```

### Backend not responding
```bash
# Check logs
docker-compose logs backend

# Or on Azure
az webapp log tail --name <app-name> --resource-group <rg-name>
```

### Documents not appearing in answers
```bash
# Trigger ingestion
curl -X POST http://localhost:8000/ingest

# Or click "Re-ingest Documents" in the UI settings panel
```

### Ollama model download is slow
The first `docker-compose up` downloads `qwen2.5:0.5b` (~400MB) and `nomic-embed-text` (~250MB). Subsequent starts reuse cached volumes.

---

## Azure Deployment (Manual)

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Fill in: app_name, resource_group_name, litellm_groq_api_key, qdrant_admin_key

terraform init
terraform plan
terraform apply
```

See [docs/DEPLOYMENT-OPTIONS.md](docs/DEPLOYMENT-OPTIONS.md) for full instructions including pushing your Docker image to Docker Hub or ACR.

---

## Roadmap

- [x] FastAPI backend + RAG pipeline
- [x] React chat UI with educational intro panel
- [x] Qdrant vector database integration
- [x] Ollama local LLM support
- [x] LiteLLM multi-provider routing (Groq + Mistral)
- [x] Docker-compose local stack
- [x] Terraform Azure infrastructure
- [ ] GitHub Actions CI/CD (auto-build + deploy)
- [ ] Azure AD authentication
- [ ] Streaming responses
- [ ] Rate limiting & query caching
- [ ] Application Insights monitoring

---

## Contributing

1. Fork → feature branch → pull request
2. Issues and discussions welcome on [GitHub](https://github.com/viveksinghgit/rag/issues)

---

MIT License · Built for efficient RAG deployment on Azure
