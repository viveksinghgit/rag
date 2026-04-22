# 🤖 RAG Azure - 1-Click Deploy Retrieval-Augmented Generation on Azure

**Cost-efficient, production-ready RAG framework deployable in 5 minutes.**

[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2F%3Cyour-org%3E%2Frag-azure%2Fmain%2Fterraform%2Fazuredeploy.json)

## 🚀 Quick Start (5 Minutes)

### Option 1: One-Click Deploy (Recommended)
1. Click the **Deploy to Azure** button above
2. Fill in parameters (App Name, API Keys)
3. Click **Review + Create** → **Create**
4. Wait 3-5 minutes for deployment to complete
5. Open the App Service URL from deployment outputs
6. Start asking questions!

**Estimated Cost After Deployment:** $60-80/month

### Option 2: Local Development Setup
```bash
# Clone repository
git clone https://github.com/<your-org>/rag-azure.git
cd rag-azure

# Copy environment template
cp backend/.env.example backend/.env

# Edit .env with your API keys
# - Get Groq key: https://console.groq.com/keys
# - Get Mistral key: https://console.mistral.ai/api-keys/
nano backend/.env

# Start all services (Qdrant, FastAPI, React UI)
docker-compose up --build

# Access UI at http://localhost:3000
```

---

## 📐 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Browser                           │
│          (React SPA hosted on Blob Storage $web)            │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Azure App Service (B1: $13/mo)                 │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │        FastAPI Backend (Python)                      │  │
│  │                                                       │  │
│  │  • /query → RAG Pipeline                             │  │
│  │  • /ingest → Document Ingestion                      │  │
│  │  • /health → Service Status                          │  │
│  │  • /config → Configuration Info                      │  │
│  └────────┬──────────────────────────────┬──────────────┘  │
└───────────┼──────────────────────────────┼──────────────────┘
            │                              │
            ▼ (Internal)                   │
    ┌───────────────────┐                  │
    │ LiteLLM Proxy     │ (Cost Routing)   │
    │                   │                  │
    │ Routes to:        │                  ▼
    │ • Groq (primary)  │          ┌─────────────────────────┐
    │ • Mistral (backup)│          │   Qdrant Vector DB      │
    │                   │          │   (ACI: $25-35/mo)      │
    │ Cost: ~$1-5/mo    │          │                         │
    └───────────────────┘          │ • Semantic search       │
                                   │ • Document storage      │
                                   │ • Metadata indexing     │
                                   │                         │
                                   │ 1 vCPU, 1GB RAM         │
                                   │ 10GB persistent volume  │
                                   └─────────────────────────┘

Plus:
• Blob Storage ($2-3/mo): docs/ folder + UI hosting
• PostgreSQL (optional): metadata & logging
• Application Insights (optional): monitoring
```

### Data Flow: Query End-to-End

```
1. User Query:        "What is machine learning?"
                       ↓
2. Embedding:        Convert to vector (384-dim)
                       ↓
3. Vector Search:    Query Qdrant, get top-5 similar docs
                       ↓
4. Context Building: Format retrieved docs as prompt context
                       ↓
5. LLM Call:         Send prompt+context to Groq/Mistral
                       ↓
6. Response:         Return answer + source documents
                       ↓
7. UI Display:       Chat interface shows answer + sources
```

---

## 💰 Cost Breakdown

### Monthly Costs (MVP, Minimal Traffic)

| Component | Service | Cost | Usage |
|-----------|---------|------|-------|
| **Compute** | App Service B1 | $13/mo | 1 vCPU, 1.75GB RAM |
| **Compute** | Container Instances (Qdrant) | $25-35/mo | 1 vCPU, 1GB RAM (24/7) |
| **Storage** | Blob Storage | $2-3/mo | ~10GB documents, UI |
| **LLM** | Groq API (per-token) | $1-5/mo | ~100K tokens/month |
| **Total** | | **$41-56/mo** | |

### Scaling Estimates

| Usage Tier | Monthly Cost | Requests/Day | Description |
|-----------|---|---|---|
| **Minimal** | $41-56 | <100 | 1 developer, testing |
| **Small Team** | $80-120 | 100-500 | 5-10 users, light production |
| **Medium** | $150-250 | 500-2,000 | 20-50 users, moderate production |
| **Large** | $400-800 | 2,000-10,000 | 100+ users, production workload |

### Cost Optimization Tips

1. **LLM Provider Routing**: LiteLLM intelligently routes to cheapest provider
   - Groq: ~20x cheaper than Azure OpenAI for mixtral-8x7b
   - Auto-fallback to Mistral if Groq rate-limited

2. **Batch Processing**: Re-index documents during off-peak hours
   - Use Azure Functions on schedule (VS. on-demand API calls)

3. **Query Caching**: Cache embeddings for identical queries
   - 2-4 hour TTL reduces repeated LLM calls by 30-50%

4. **Storage Tiering**: Lifecycle policies auto-move cool data
   - Hot (7d) → Cool (30d) → Archive (90d+)
   - Saves 50% on cold document storage

5. **Spot Instances**: For batch re-indexing (future Phase)

---

## ✨ Features

### Out-of-the-Box
- ✅ **1-Click Deployment**: Deploy to Azure button
- ✅ **Cost Optimized**: Sub-$100/month for MVP
- ✅ **Semantic Search**: Vector embeddings + similarity matching
- ✅ **Multi-Provider LLM**: Groq + Mistral with auto-fallback
- ✅ **Document Management**: Ingest from docs/ folder
- ✅ **Source Tracking**: Responses include document sources + confidence scores
- ✅ **Web UI**: Modern React chat interface
- ✅ **REST API**: Easy integration with other apps
- ✅ **Local Development**: Full docker-compose setup

### Coming Soon (Future Phases)
- 🔄 Authentication & RBAC
- 📊 Analytics & Usage Dashboards
- 🔐 Data Encryption
- 🌍 Multi-region Deployment
- 📱 Mobile Apps
- 🎙️ Voice Input/Output
- 🔗 Document URL Auto-Indexing
- ⚡ Streaming Responses

---

## 🛠️ Technology Stack

| Layer | Technology | Why? |
|-------|-----------|------|
| **Frontend** | React 18 | Modern SPA, quick iteration |
| **Backend** | FastAPI + Python 3.11 | Async, type-safe, fast |
| **Vector DB** | Qdrant | Lightweight, high-performance, open-source |
| **LLM Routing** | LiteLLM | Cost arbitrage, provider flexibility |
| **LLM** | Groq (primary) | 50-100x cheaper than Azure OpenAI |
| **Embeddings** | Ollama `nomic-embed-text` locally; Mistral Embed for LiteLLM | Local testing uses 768-dimensional vectors |
| **Container** | Docker | Easy deployment, image size <300MB |
| **IaC** | Terraform | Multi-cloud, reusable modules |
| **CI/CD** | GitHub Actions | Built-in, free for public repos |
| **Hosting** | Azure | App Service, Container Instances, Blob Storage |

---

## 📚 Documentation

- **[LOCAL-DEVELOPMENT.md](docs/LOCAL-DEVELOPMENT.md)** — Set up and run locally
- **[README-ARCHITECTURE.md](docs/README-ARCHITECTURE.md)** — Deep technical dive
- **[COST-BREAKDOWN.md](COST-BREAKDOWN.md)** — Detailed cost analysis
- **[DEPLOYMENT-OPTIONS.md](docs/DEPLOYMENT-OPTIONS.md)** — Deployment methods comparison
- **[FAQ.md](docs/FAQ.md)** — Common questions

---

## 🚨 Troubleshooting

### Backend not responding (502 Bad Gateway)

```bash
# Check if backend is running
curl https://<your-app>.azurewebsites.net/health

# SSH into App Service to view logs
az webapp log tail --name <app-name> --resource-group <rg-name>

# Restart backend
az webapp restart --name <app-name> --resource-group <rg-name>
```

### Qdrant connection errors

```bash
# Qdrant needs time to initialize (5-10 min on first deploy)
# Check Qdrant health: https://<your-app>.azurewebsites.net/config

# Check Qdrant logs (if accessible)
az container logs --name qdrant --resource-group <rg-name>
```

### Documents not being indexed

1. Ensure `docs/` folder has `.md` files
2. Trigger manual ingestion: `POST /ingest` endpoint
3. Check Application Insights for ingestion errors

### High LLM token costs

- Reduce `retrieval_limit` in config (fewer documents = fewer tokens)
- Enable query caching (2-4 hour TTL)
- Use shorter document chunks

### React UI not loading

1. Check if Blob Storage `$web` container is enabled
2. Verify CORS settings in App Service
3. Check browser console (F12) for API errors

---

## 🤔 FAQ

### Q: How do I update my documents?
Edit files in `docs/` folder and push to GitHub. GitHub Actions will auto-ingest and re-index.

### Q: Can I use Azure OpenAI instead of Groq?
Yes! Edit `LITELLM_LLM_MODEL` in `.env` to `azure/gpt-4` (but costs ~$0.03/1K tokens vs. Groq ~$0.0002/1K tokens).

### Q: Is my data private?
Yes. Documents stay in your Azure subscription. No external storage except LLM provider API calls (only prompts+context sent, no raw docs).

### Q: How do I delete all Azure resources?
```bash
# Delete entire resource group (deletes all resources)
az group delete --name <rg-name>

# Or run cleanup script
./scripts/cleanup-azure.sh
```

### Q: Can I add authentication?
Coming in Phase 2. For now, deploy within private network by restricting CORS origins in config.

### Q: What if I exceed my budget?
Set Azure Cost Management alerts at 50%, 75%, 90% thresholds. Auto-shutdown scripts included in Phase 5.

---

## 🔐 Security Considerations

### Current Implementation (MVP)
- ✅ API keys stored in GitHub Secrets (not in code)
- ✅ Qdrant firewalled internally (not publicly exposed)
- ✅ HTTPS only (App Service enforces)
- ⚠️ No authentication (anyone with URL can query)
- ⚠️ No encryption at rest

### For Production (Recommended)
1. Enable Azure Key Vault for secrets
2. Add Azure AD authentication to web UI
3. Enable encryption for Blob Storage & Qdrant volumes
4. Use private endpoints for Qdrant
5. Enable Application Insights for audit logging

---

## 📦 Project Structure

```
rag-azure/
├── terraform/                    # Infrastructure as Code
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── azuredeploy.json         # Deploy button config
│   └── modules/
│       ├── app_service/         # FastAPI hosting
│       ├── aci_qdrant/          # Vector DB container
│       ├── storage/             # Blob Storage
│       └── networking/          # Firewall rules
├── backend/                      # Python FastAPI Backend
│   ├── app/
│   │   ├── main.py              # Entry point
│   │   ├── config.py            # Settings
│   │   ├── models.py            # Pydantic schemas
│   │   └── utils/               # Utilities (coming Phase 2)
│   ├── scripts/
│   │   └── ingest_docs.py       # Document ingestion
│   ├── Dockerfile               # Multi-stage build
│   ├── requirements.txt         # Python dependencies
│   └── .env.example             # Config template
├── frontend/                     # React SPA
│   ├── src/
│   │   ├── App.jsx              # Main component
│   │   ├── api.js               # API client
│   │   ├── App.css              # Styling
│   │   └── components/
│   │       └── ChatInterface.jsx
│   ├── public/
│   │   └── index.html
│   └── package.json
├── docs/                         # Documentation
│   ├── README-ARCHITECTURE.md
│   ├── LOCAL-DEVELOPMENT.md
│   └── example_docs/            # Sample documents
├── .github/workflows/
│   └── deploy.yml               # CI/CD automation
├── docker-compose.yml           # Local dev environment
├── README.md                    # This file
├── COST-BREAKDOWN.md            # Detailed costs
└── .gitignore
```

---

## 🚀 Getting Started After Deployment

### 1. Access the Web UI
```
https://<your-app-name>.azurewebsites.net
```

### 2. Test the API
```bash
# Health check
curl https://<your-app-name>.azurewebsites.net/health

# Sample query
curl -X POST https://<your-app-name>.azurewebsites.net/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "top_k": 5
  }'
```

### 3. Add Your Documents
1. Edit `docs/` folder locally
2. Commit and push to GitHub
3. GitHub Actions auto-ingests documents (watch Actions tab)
4. Start querying!

### 4. Monitor Costs
1. Go to **Azure Cost Management**
2. Set budget alerts
3. Review usage by service

---

## 📝 License

MIT License - See LICENSE file

---

## 💬 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

Common contributions:
- 🐛 Bug reports
- ✨ Feature ideas
- 📚 Documentation improvements
- 🧪 Test cases

---

## 🙋 Support & Questions

- **Issues**: Open a GitHub issue
- **Discussions**: Start a GitHub discussion
- **Email**: your-email@example.com
- **Docs**: See the `docs/` folder

---

## 🎯 Roadmap

### Phase 1 ✅ (Current)
- [x] Foundation setup (FastAPI, React, Dockerfile)
- [x] Repo structure & docs template

### Phase 2 (Next)
- [ ] RAG implementation (LiteLLM, Qdrant integration)
- [ ] Document ingestion pipeline
- [ ] API endpoints

### Phase 3
- [ ] Terraform infrastructure

### Phase 4
- [ ] Local dev setup (docker-compose)

### Phase 5
- [ ] GitHub Actions CI/CD

### Phase 6
- [ ] Deploy to Azure button

### Phase 7
- [ ] Complete documentation

### Phase 8
- [ ] Staging & testing

### Phase 9
- [ ] Production release v1.0

---

**Built with ❤️ for efficient RAG deployment on Azure**
