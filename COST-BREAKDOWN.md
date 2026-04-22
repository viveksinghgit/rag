# Cost Breakdown & Analysis

Detailed cost analysis for RAG Azure deployment on different scales.

## Itemized Monthly Costs

### MVP Configuration (Recommended for <100 users)

| Resource | Azure Service | Cost/Month | Specs | Notes |
|----------|---------------|-----------|-------|-------|
| **Compute** | App Service B1 | $13 | 1 vCPU, 1.75GB RAM | Always-on, shared infrastructure |
| **Compute** | Container Instances | $25-35 | 1 vCPU, 1GB RAM, 24/7 | Qdrant vector database |
| **Storage** | Blob Storage (Hot) | $0.12 | 8GB @ $0.015/GB | Application data |
| **Storage** | Blob Storage (Cool) | $0.08 | 2GB @ $0.01/GB | Archive documents |
| **Storage** | Blob Storage (Archive) | $0.01 | 1GB @ $0.002/GB | Old documents |
| **Data Transfer** | Outbound | $1 | ~1GB outbound | Cross-region transfer |
| **LLM** | Groq API | $1-5 | ~100K tokens | Per-token pricing |
| **Embeddings** | Mistral Embed | $0 | Included with prompt | Free tier |
| **Developer** | Your Time | × | × | Priceless 😄 |
| | **TOTAL** | **$40-56/mo** | | |

### Small Production (100-500 users, <1K req/day)

| Resource | Service | Cost |
|----------|---------|------|
| App Service B2 | $50 | 2 vCPU, 3.5GB RAM |
| Container Instances | $35 | 1 vCPU (same load) |
| Blob Storage | $5 | Increased data |
| Database (PostgreSQL) | $50 | Optional metadata store |
| LLM (Groq) | $10-20 | Higher token usage |
| Application Insights | $5 | Monitoring |
| **TOTAL** | **$155-165/mo** | |

### Medium Production (500-2K req/day)

| Resource | Service | Cost |
|----------|---------|------|
| App Service S1 | $100 | 1 vCPU (standard tier) |
| Container Instances | $50 | 2 vCPU for Qdrant |
| Blob Storage | $10 | More data |
| Database (PostgreSQL) | $80 | S tier, more storage |
| LLM (Groq) | $30-50 |  Higher usage |
| Application Insights | $10 | Advanced monitoring |
| **TOTAL** | **$280-310/mo** | |

### Enterprise (>10K req/day)

| Resource | Service | Cost |
|----------|---------|------|
| App Service P1V2 | $200 | Premium, auto-scale |
| Kubernetes (AKS) | $100-200 | Multi-node Qdrant |
| Blob Storage | $30 | Large datasets |
| Database (PostgreSQL) | $150 | Premium tier |
| LLM (Azure OpenAI) | $500-1000 | Switched to Azure native |
| Application Insights | $50 | Full observability |
| **TOTAL** | **$1030-1630/mo** | |

## Cost Optimization Strategies

### 1. Intelligent LLM Provider Routing (~50-100x savings)

**Default Setup (MVP)**
```
Request → LiteLLM → Groq (~$0.0002/1K tokens)
              ↓
          Mistral (~$0.0008/1K tokens) [fallback]
```

**Comparison**
| Provider | Price/1K tokens | 100K tokens/mo | 1M tokens/mo |
|----------|-----------------|---|---|
| Groq (used by LiteLLM) | $0.0002 | $0.02 | $0.20 |
| Mistral | $0.0008 | $0.08 | $0.80 |
| **Azure OpenAI (GPT-4)** | $0.03 | $3 | $30 |
| **Claude 3 (Anthropic)** | $0.015 | $1.50 | $15 |

**Savings with LiteLLM**: 99% cheaper than Azure OpenAI for MVP.

### 2. Query Caching (30-50% LLM savings)

**Implementation**
- In-memory cache: Identical queries return cached responses (2-4 hour TTL)
- Embedding cache: Store generated embeddings, reuse for similar texts

**Example**
```
Query: "What is machine learning?" (asked 10 times/day)
├─ Request 1: Generate embedding + LLM call = 150 tokens
├─ Requests 2-10: Cache hit, 0 tokens
└─ Monthly savings: $4.50
```

### 3. Document Chunking Optimization (20-30% ingestion cost)

**Current**: 512 tokens per chunk
- Pros: Accurate context, fewer chunks
- Cons: More embeddings needed per document

**Alternative**: 256 tokens per chunk
- Pros: Fewer embeddings in Qdrant, smaller vectors
- Cons: Need more chunks for full documents

**Cost Impact**
| Chunk Size | Total Chunks | Embeddings Cost | Search Speed |
|-----------|---|---|---|
| 256 tokens | 2x more | +100% cost | Faster |
| **512 tokens** | **baseline** | **baseline** | Baseline |
| 1024 tokens | 50% fewer | -50% cost | Slower |

**Recommendation**: 512 tokens is sweet spot (Phase 2).

### 4. Storage Tiering (50-80% storage savings)

**Azure Blob Lifecycle Policy**
```
Day 1-7:      Hot tier ($0.015/GB/mo)    — Fast access
Day 8-30:     Cool tier ($0.01/GB/mo)    — Occasional access
Day 31+:      Archive tier ($0.002/GB/mo) — Rare access
```

**Example with 100GB data**
```
Without tiering:    100GB × $0.015 = $1.50/mo
With tiering:       ~$0.60/mo
Savings:            60% reduction
```

### 5. Off-Peak Batch Processing (30-40% compute savings)

**Option**: Run re-indexing during Azure off-peak hours
- Qdrant scales down (fewer vCPU allocation)
- Ingestion tasks run on Spot Instances (-70% cost)
- Savings: $5-10/month

### 6. Request Deduplication (15-25% API savings)

**Technique**: Hash incoming queries, skip duplicates
```
Query 1: "What is RAG?" → hash abc123 → LLM call needed
Query 2: "What is RAG?" → hash abc123 → Cache hit! (0 cost)
```

### 7. Response Streaming (minimal savings, UX improvement)

**Benefit**: Stream LLM response token-by-token
- Slight bandwidth savings (still count same tokens)
- BUT: Better user experience (response appears sooner)

---

## Cost Reduction Tactics by Use Case

### For Experimentation (Cost < $50/mo)
1. ✅ Use Groq API (free tier: 120 requests/day, unlimited tokens)
2. ✅ Host on App Service B1 (free tier available too)
3. ✅ Start with small document set (<1GB)
4. ✅ Local development only (skip Azure deploy until ready)

### For Small Team (Cost < $100/mo)
1. ✅ Implement query caching (prevents duplicate LLM calls)
2. ✅ Optimize chunk size (512-1024 tokens)
3. ✅ Schedule ingestion (off-peak hours)
4. ✅ Monitor daily costs in Azure Cost Management

### For Production (Cost ~ $150-300/mo)
1. ✅ All above +
2. ✅ Upgrade to App Service S1 for redundancy
3. ✅ Add PostgreSQL for metadata & analytics
4. ✅ Enable Application Insights
5. ✅ Implement rate limiting (prevent abuse)

### For Enterprise (Cost > $500/mo)
1. ✅ All above +
2. ✅ Switch to Azure OpenAI (better SLA)
3. ✅ Multi-region deployment
4. ✅ Kubernetes for auto-scaling
5. ✅ Dedicated support

---

## Cost Comparison: RAG vs Alternatives

| Solution | Setup Cost | Monthly Cost | Hosted? | Customizable? |
|----------|-----------|---|---|---|
| **RAG Azure (this project)** | $0 | $40-150 | ✅ Self-hosted | ✅✅✅ Highly customizable |
| **OpenAI ChatGPT Plus** | $0 | $29 | ✅ OpenAI | ❌ No customization |
| **Pinecone + OpenAI** | $0 | $150-500 | ✅ Managed | ✅ Moderate |
| **Azure Cognitive Search + OpenAI** | $0 | $200-1000 | ✅ Azure | ✅ Good |
| **Weaviate Cloud** | $0 | $50-400 | ✅ Weaviate | ✅ Good |
| **Self-hosted Qdrant + Local LLM** | $500 | $0 (hardware only) | ✅ Your infra | ✅✅✅ Full |

---

## Hidden Costs to Watch

### 1. Data Egress (Cross-region transfer)
- Intra-region: Free
- Cross-region: $0.02/GB
- Internet egress: $0.09/GB
- **Tip**: Keep everything in same region

### 2. API Rate Limiting (Groq free tier)
- 120 requests/day limit
- Hit limit? Need to buy paid tier
- **Tip**: Cache queries, batch processes

### 3. Large Model Costs
- Switching to GPT-4: +100-150x cost
- Fine-tuned models: +50-100x cost
- **Tip**: Mistral-8x7b + Groq is 99% cheaper

### 4. Qdrant Scaling
- Grows with data: 1GB vectors ≈ $0.05/day
- 10GB vectors ≈ $0.50/day (stays constant with ACI)
- **Tip**: Monitor collection sizes monthly

### 5. Azure "Pay-as-you-go" Rate Hikes
- Prices increase ~2-3% annually
- Long-term contracts get discounts
- **Tip**: Use Reserved Instances for 1-3 year costs

---

## Budgeting Recommendations

### Monthly Budget Template

```
┌─────────────────────────────────────┐
│   RAG Azure Budget Planner           │
├─────────────────────────────────────┤
│ Choose target monthly budget:        │
│                                      │
│ □ $50 (Experiment only)              │
│ ☑ $100 (Small team MVP)              │
│ □ $200 (Growing production)          │
│ □ $500+ (Enterprise)                 │
├─────────────────────────────────────┤
│ Projected costs for $100/mo:         │
│                                      │
│ App Service B1          $13           │
│ Qdrant (ACI)            $30           │
│ Blob Storage            $2            │
│ LLM (Groq)              $50           │
│ Database (PostgreSQL)   $5 (optional) │
│ ─────────────────────────────        │
│ TOTAL                   $100          │
│                                      │
│ Remaining buffer: $0 (tight!)        │
└─────────────────────────────────────┘
```

### Alert Thresholds

Set up Azure Cost Management alerts:
- **50% of budget**: Warning ⚠️
- **75% of budget**: Alert 🟡
- **90% of budget**: Critical 🔴
- **100% of budget**: Stop services ⛔

---

## ROI & Break-Even Analysis

### For Businesses

**TCO Comparison: RAG Azure vs ChatGPT Plus**

| Metric | RAG Azure | ChatGPT Plus |
|--------|-----------|---|
| Dev time to production | 2 hours | 0 hours |
| Monthly cost (10 users) | $100 | $290 ($29 × 10) |
| Annual cost | $1,200 | $3,480 |
| **Savings/year** | × | **$2,280** |
| Customization | Unlimited | None |
| Data privacy | Full control | OpenAI only |

**Break-Even**: Pays for itself in productivitygains and cost savings within 1-2 months.

### For Individuals

**Cost per query**
- RAG Azure: $5/month ÷ 1,000 queries = $0.005/query
- ChatGPT Plus: $29/month ÷ 1,000 queries = $0.029/query
- **Savings: 83% per query**

---

## Estimated Total Cost of Ownership (3 Years)

### Scenario: Growing From 10 to 1000 Users

| Year | Users | Monthly Cost | Annual | 3-Year Total |
|------|-------|---|---|---|
| Year 1 | 10 | $100 | $1,200 | |
| Year 2 | 50 | $200 | $2,400 | |
| Year 3 | 1,000 | $600 | $7,200 | **$10,800** |

### vs Azure OpenAI + Cognitive Search

| Year | Users | Monthly Cost | Annual | 3-Year Total |
|------|-------|---|---|---|
| Year 1 | 10 | $500 | $6,000 | |
| Year 2 | 50 | $1,200 | $14,400 | |
| Year 3 | 1,000 | $4,000 | $48,000 | **$68,400** |

**Savings with RAG Azure: $57,600 over 3 years** (84% reduction!)

---

## Next Steps

1. ✅ Deploy MVP ($40-60/mo)
2. 📊 Monitor costs in Azure Cost Management
3. 🔄 Implement caching (save 30-50%)
4. 📈 Scale gradually as usage grows
5. 🎯 Re-evaluate annually

For detailed cost calculations, see the [Cost Calculator Spreadsheet](https://docs.google.com/spreadsheets/d/...your-sheet-here).

---

**Questions about costs?** Open a GitHub issue or see FAQ.md.
