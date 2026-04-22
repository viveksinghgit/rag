# Architecture Deep Dive

Comprehensive technical architecture of RAG Azure.

## System Components

### 1. Frontend (React SPA)

**Location**: `frontend/src/`

**Purpose**: User interface for querying and managing documents

**Technology Stack**:
- React 18 with functional components
- Axios for HTTP requests
- CSS for styling (no external libraries for MVP)

**Key Components**:
```
App.jsx (Root)
├── Header (Title, Status)
├── ChatInterface
│   ├── Messages Display
│   ├── Input Form
│   ├── Settings Panel
│   └── Ingestion Button
└── Error Handler
```

**State Flow**:
```
User Input
  ↓
ChatInterface (local state)
  ↓
api.js (HTTP request)
  ↓
Backend API
  ↓
Response
  ↓
Update messages state
  ↓
Re-render component
```

**API Calls** (from `api.js`):
- `GET /health` — Check backend status
- `GET /config` — Get configuration
- `POST /query` — Send query
- `POST /ingest` — Trigger ingestion

### 2. Backend (FastAPI)

**Location**: `backend/app/`

**Purpose**: Core RAG orchestration and API

**Architecture**:
```
main.py (Entry Point)
├── FastAPI app setup
├── CORS middleware
├── Routes
│   ├── /health
│   ├── /config
│   ├── /query → RAG Pipeline (Phase 2)
│   └── /ingest
└── Lifespan handler
```

**Request Flow**:
```
HTTP Request
  ↓
FastAPI routing
  ↓
Request validation (Pydantic models)
  ↓
Business logic
  ↓
Response serialization
  ↓
HTTP Response
```

**Configuration** (`config.py`):
- Uses Pydantic `BaseSettings`
- Loads from environment variables
- Type-safe and validated
- Example: `LITELLM_LLM_MODEL=groq/mixtral-8x7b-32768`

**Models** (`models.py`):
- `QueryRequest`: {query, top_k, filters}
- `QueryResponse`: {answer, sources, tokens_used, execution_time_ms}
- `SourceDocument`: {text, score, source, chunk_index}
- `Document`: {id, text, metadata, embedding}
- `HealthResponse`: {status, app_name, version, environment}

### 3. Vector Database (Qdrant)

**Purpose**: Store and search document embeddings

**Service**: Qdrant (open-source vector DB)

**Configuration**:
- Runs on Container Instance (ACI)
- Port: 6333 (internal only)
- Storage: 10GB persistent volume
- Collection: `documents` (default)
- Vector size: 768-dimensional for local Ollama `nomic-embed-text`

**Data Model**:
```json
{
  "id": "unique-doc-id",
  "vector": [0.123, 0.456, ...],  // 768 dimensions locally
  "payload": {
    "text": "Document chunk text",
    "source": "filename.md",
    "chunk_index": 0,
    "score": null  // Set during search
  }
}
```

**Operations** (Phase 2):
- `upsert()` — Add/update documents
- `search()` — Semantic similarity search
- `delete()` — Remove documents
- `scroll()` — Iterate all documents

### 4. LLM & Embedding Provider (LiteLLM)

**Purpose**: Cost-optimized routing to multiple LLM providers

**Routing Logic** (Phase 2):
```
Primary: Groq/Mixtral-8x7b-32768
  ↓ (if rate-limited or errors)
Fallback: Mistral/Mistral-medium
  ↓ (if fallback also fails)
Error: Return to user
```

**Costs** (monthly):
- Groq: ~$0.0002 per 1K tokens (free tier: 120 requests/day)
- Mistral: ~$0.0008 per 1K tokens

**Token Usage Tracking** (Phase 2):
```python
{
  "query": "What is machine learning?",
  "embedding_tokens": 10,
  "retrieval_docs": 5,
  "llm_prompt_tokens": 150,
  "llm_completion_tokens": 50,
  "total_tokens": 210,
  "estimated_cost": 0.0005
}
```

## Data Flow: Query to Response

```
┌─────────────────────────────────────┐
│ 1. User Query (React UI)            │
│   "What is machine learning?"       │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 2. HTTP POST /query → FastAPI       │
│   {query: "...", top_k: 5}          │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 3. Generate Query Embedding         │
│   (LiteLLM → Mistral Embed)         │
│   Output: [0.123, 0.456, ...]       │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 4. Vector Search in Qdrant          │
│   Similarity search for top-5 docs  │
│   Output: [{text, score}, ...]      │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 5. Build LLM Prompt                 │
│   System: "You are helpful..."      │
│   Context: Retrieved docs           │
│   User: Original query              │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 6. LLM Generation                   │
│   (LiteLLM → Groq/Mixtral)          │
│   Output: "Machine learning is..."  │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 7. Format Response                  │
│   {                                 │
│     "answer": "...",                │
│     "sources": [...],               │
│     "tokens_used": 210,             │
│     "execution_time_ms": 245        │
│   }                                 │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 8. HTTP Response → React UI         │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 9. Display in Chat                  │
│   Answer + source documents         │
└─────────────────────────────────────┘
```

**Total Time**: ~2-5 seconds (depending on LLM)

## Document Ingestion Pipeline

```
┌──────────────────────────────────┐
│ 1. Source Documents              │
│    docs/ folder in repo          │
│    OR Blob Storage               │
└────────────┬─────────────────────┘
             ↓
┌──────────────────────────────────┐
│ 2. Read Files                    │
│    Parse Markdown                │
│    Extract text                  │
└────────────┬─────────────────────┘
             ↓
┌──────────────────────────────────┐
│ 3. Chunking                      │
│    Split into ~512 token chunks  │
│    Add metadata (source, index)   │
└────────────┬─────────────────────┘
             ↓
┌──────────────────────────────────┐
│ 4. Generate Embeddings           │
│    LiteLLM → Mistral Embed       │
│    Output: vectors (384-dim)     │
└────────────┬─────────────────────┘
             ↓
┌──────────────────────────────────┐
│ 5. Upsert to Qdrant              │
│    Store vectors + metadata      │
│    Create indexes                │
└────────────┬─────────────────────┘
             ↓
┌──────────────────────────────────┐
│ 6. Index Complete                │
│    Log summary statistics        │
└──────────────────────────────────┘
```

**Triggered By** (Phase 2):
- GitHub webhook (on docs/ changes)
- Manual `/ingest` API call
- Schedule: Daily at 2 AM UTC

## Deployment Architecture (Azure)

```
┌──────────────────────────────────────────────────┐
│        Azure Subscription                        │
├──────────────────────────────────────────────────┤
│                                                   │
│ ┌──────────────────────────────────────────────┐│
│ │ Resource Group: rag-prod                     ││
│ │                                               ││
│ │ ┌────────────────────────────────────────┐  ││
│ │ │ App Service Plan                       │  ││
│ │ │ (B1: 1 vCPU, 1.75GB RAM)               │  ││
│ │ │                                         │  ││
│ │ │ ┌──────────────────────────────────┐   │  ││
│ │ │ │ Web App (FastAPI Backend)        │   │  ││
│ │ │ │ • Docker container               │   │  ││
│ │ │ │ • Always-on                      │   │  ││
│ │ │ │ • HTTPS endpoint                 │   │  ││
│ │ │ └──────────────────────────────────┘   │  ││
│ │ └────────────────────────────────────────┘  ││
│ │                                              ││
│ │ ┌────────────────────────────────────────┐  ││
│ │ │ Container Instances (ACI)              │  ││
│ │ │                                         │  ││
│ │ │ ┌──────────────────────────────────┐   │  ││
│ │ │ │ Qdrant Container                 │   │  ││
│ │ │ │ • 1 vCPU, 1GB RAM                │   │  ││
│ │ │ │ • Port 6333 (firewalled)         │   │  ││
│ │ │ │ • 10GB persistent volume         │   │  ││
│ │ │ └──────────────────────────────────┘   │  ││
│ │ └────────────────────────────────────────┘  ││
│ │                                              ││
│ │ ┌────────────────────────────────────────┐  ││
│ │ │ Storage Account                        │  ││
│ │ │ • Blob Storage                         │  ││
│ │ │ • documents/ container                 │  ││
│ │ │ • $web container (static site)         │  ││
│ │ │ • Lifecycle policies (hot→cool→archive)││
│ │ └────────────────────────────────────────┘  ││
│ │                                              ││
│ │ ┌────────────────────────────────────────┐  ││
│ │ │ Application Insights (optional)        │  ││
│ │ │ • Logging & monitoring                 │  ││
│ │ │ • Performance metrics                  │  ││
│ │ └────────────────────────────────────────┘  ││
│ │                                              ││
│ │ ┌────────────────────────────────────────┐  ││
│ │ │ Network Security Group                 │  ││
│ │ │ • Inbound: 443 (HTTPS only)            │  ││
│ │ │ • Internal: App Service ↔ Qdrant      │  ││
│ │ └────────────────────────────────────────┘  ││
│ │                                              ││
│ └──────────────────────────────────────────────┘│
│                                                  │
└──────────────────────────────────────────────────┘

External:
  ├─ GitHub (code, CI/CD)
  ├─ Groq (LLM API)
  ├─ Mistral (Embedding API, fallback LLM)
  └─ Users (HTTPS requests to App Service)
```

## Security Zones

```
┌──────────────────────┐
│  Public (Internet)   │
│  ├─ React SPA        │ ← Users
│  └─ API endpoint     │
└──────────────┬───────┘
               │ HTTPS
┌──────────────▼───────────────────────┐
│  Application Layer (Azure)           │
│  ├─ App Service (FastAPI)            │
│  │  └─ Public IP                      │
│  │     ├─ /health (public)            │
│  │     ├─ /query (public)             │
│  │     └─ /ingest (internal only)     │
└──────────────┬───────────────────────┘
               │ Internal network (NSG)
┌──────────────▼───────────────────────┐
│  Data Layer (Private)                │
│  ├─ Qdrant (ACI)                     │
│  │  └─ Port 6333 (firewalled)        │
│  │     Only accessible from App Svc  │
│  └─ Blob Storage                     │
│     └─ Private endpoint (optional)    │
└──────────────────────────────────────┘
```

## Performance Characteristics

### Latency Breakdown (per query)

| Step | Time | Notes |
|------|------|-------|
| API gateway | 10ms | Azure routing |
| Request validation | 5ms | Pydantic |
| Generate embedding | 200ms | Mistral Embed |
| Qdrant search | 20ms | Top-5 vectors |
| Build prompt | 5ms | Formatting |
| LLM inference | 1500-3000ms | Groq response |
| Format response | 10ms | JSON serialization |
| **Total** | **1.75-3.25s** | End-to-end |

### Throughput

- **Single instance**: ~20 concurrent requests
- **Qdrant**: Handles ~1000 vectors/sec search
- **LLM**: Limited by provider rate limits (Groq: 120 req/day free)

### Storage Capacity

- **1000 documents** (avg 3 chunks each): ~1.1MB vectors + metadata
- **100,000 documents**: ~100MB data
- **10GB persistent volume**: Handles ~10M chunks

## Error Handling

```
Request Error
  ↓
├─ Validation Error (400) → Pydantic
├─ Authentication Error (401) → Missing headers
├─ Backend Error (500) → Exception handling
├─ Qdrant Error (503) → Connection timeout
└─ LLM Error (429) → Rate limit / API error
  ↓
Log error with context
  ↓
Return structured error response
  ↓
Frontend displays error message
```

## Monitoring Points

1. **Request volume** (requests/min)
2. **Response latency** (p50, p99)
3. **Error rate** (errors/min)
4. **LLM tokens used** (per query)
5. **Qdrant collection size** (vectors count)
6. **Blob Storage usage** (GB)
7. **Compute utilization** (CPU, memory %)

## Next Steps (Phase 2-3)

- Implement `rag_pipeline.py` with full flow
- Add document ingestion scripts
- Implement caching layer (Redis optional)
- Add telemetry/logging
- Deploy Terraform infrastructure

---

For questions, see FAQ or open an issue.
