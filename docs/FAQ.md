# FAQ - Frequently Asked Questions

## Costs & Pricing

### Q: How much will this cost?
**A:** $40-80/month for MVP (< 100 users). See COST-BREAKDOWN.md for detailed pricing.

Breakdown:
- App Service B1: $13/mo
- Qdrant (ACI): $25-35/mo
- Blob Storage: $2-3/mo
- LLM (Groq): $1-5/mo

### Q: Why is LiteLLM cheaper than Azure OpenAI?
**A:** Groq offers 50-100x cheaper pricing (~$0.0002/1K tokens vs. Azure OpenAI's $0.03/1K tokens).

LiteLLM routes requests to the cheapest provider while maintaining compatibility. Trade-off: Mixtral-8x7b is less capable than GPT-4, but still powerful for RAG.

### Q: Can I use Azure OpenAI instead?
**A:** Yes! Edit your `.env`:
```bash
LITELLM_LLM_MODEL=azure/gpt-4
LITELLM_EMBEDDING_MODEL=azure/text-embedding-3-small
```

Costs will be ~$50-100/month instead of $1-5/month.

### Q: How do I control costs if they spike?
**A:** Set up Azure Cost Management alerts:
1. Go to Azure Portal → Cost Management + Billing
2. Set alerts at 50%, 75%, 90% of budget
3. Auto-shutdown scripts available (Phase 5)

### Q: What happens if I exceed my budget?
**A:** Your App Service won't automatically stop, but you can:
1. Manually stop the service in Azure Portal
2. Delete the resource group
3. Implement auto-shutdown policies

---

## Deployment

### Q: How do I deploy?
**A:** Two options:

**Option 1: One-Click Deploy (Recommended)**
- Click the "Deploy to Azure" button in README.md
- Fill in parameters
- Wait 5 minutes

**Option 2: Manual with Terraform**
- Clone repo
- `cd terraform/`
- `terraform init && terraform apply`

### Q: How long does deployment take?
**A:** 3-5 minutes total.

Breakdown:
- Terraform provisions resources: 1-2 min
- Docker image builds & deploys: 1-2 min
- Services initialize: 1-2 min

### Q: What if deployment fails?
**A:** Check:
1. Resource group exists in Azure Portal
2. API keys are valid (Groq, Mistral)
3. Terraform state file (.terraform/) not corrupted
4. Azure credentials configured: `az login`

### Q: Can I deploy to multiple regions?
**A:** Not in MVP (Phase 1). Multi-region coming in Phase 8.

For now, deploy to nearest region to users.

---

## Documents & Indexing

### Q: How do I add documents?
**A:** Add Markdown files to `docs/` folder:

```bash
# Create new document
cat > docs/my_doc.md << EOF
# My Document

Content here...
EOF

# Commit and push
git add docs/my_doc.md
git commit -m "Add new document"
git push

# GitHub Actions auto-indexes
```

Or trigger manually:
```bash
curl -X POST https://<your-app>/ingest
```

### Q: How many documents can I store?
**A:** Depends on chunk size:
- 512 token chunks: ~10,000 docs
- 256 token chunks: ~20,000 docs
- Qdrant scales to millions of vectors

For MVP (10GB storage): ~10,000 documents.

### Q: Can I upload documents via the UI?
**A:** Not in MVP. Phase 2 will add document upload endpoint.

Currently, add via `docs/` folder or Blob Storage.

### Q: How often are documents indexed?
**A:** 
- Manual: Every time you push to GitHub
- Scheduled: Daily (configurable, Phase 5)

Re-indexing takes ~1-5 minutes depending on document count.

### Q: Can I delete a document?
**A:** Remove from `docs/` folder and push:
```bash
rm docs/old_doc.md
git add -A
git commit -m "Remove old document"
git push
```

Full re-index happens automatically.

Or manually via API (Phase 2):
```bash
curl -X DELETE https://<your-app>/documents/<doc_id>
```

---

## Data & Privacy

### Q: Is my data private?
**A:** 

**What stays in your subscription:**
- Documents in Blob Storage
- Vector embeddings in Qdrant
- Chat history (not stored currently)

**What's sent externally:**
- Queries sent to Groq/Mistral (LLM provider)
- Only the query + context, not raw documents

**Recommendation:** For sensitive data, use Azure OpenAI (keeps data within Microsoft).

### Q: How do I delete my data?
**A:** 

**Delete specific documents:**
```bash
rm docs/sensitive.md && git push
```

**Delete all data:**
```bash
# Delete entire resource group (ALL resources)
az group delete --name rag-prod

# Or run cleanup script
./scripts/cleanup-azure.sh
```

### Q: Can I encrypt data at rest?
**A:** 

**Current:** Qdrant volumes not encrypted (MVP).

**For production:**
1. Enable Blob Storage encryption (automatic)
2. Use Azure Key Vault for secrets
3. Enable Qdrant encryption (configure in Terraform)

### Q: Is there audit logging?
**A:** 

Minimal in MVP. Phase 5 adds:
- Request logging (who, what, when)
- Application Insights integration
- Compliance logs for audit trails

---

## Technical

### Q: What if Groq API goes down?
**A:** LiteLLM automatically falls back to Mistral.

Fallback chain (Phase 2):
1. Groq (primary)
2. Mistral (secondary)
3. Error if both fail

### Q: Can I use a different embedding model?
**A:** Yes! Edit `.env`:
```bash
LITELLM_EMBEDDING_MODEL=text-embedding-ada-002
```

Supported: Mistral Embed, OpenAI, Cohere, etc.

### Q: What's the vector dimension limit?
**A:** Qdrant supports up to 65,536 dimensions.

Default: 384 (Mistral Embed).

Changing requires re-indexing all documents.

### Q: How do I debug issues locally?
**A:** Run locally with docker-compose:
```bash
docker-compose up --build

# View logs
docker-compose logs backend -f
docker-compose logs qdrant -f

# Access API docs
http://localhost:8000/docs
```

### Q: Can I run Qdrant locally without Docker?
**A:** Yes, but not recommended for MVP.

Suggested: Use docker-compose for consistency.

---

## Scalability

### Q: When should I upgrade from B1?
**A:** When you see:
- Requests queuing (>80% CPU)
- Response times >5s
- Errors due to timeout

Upgrade path:
1. B1 ($13) → B2 ($50)
2. B2 → S1 ($100)
3. S1 → S2 ($200)

### Q: Can I auto-scale?
**A:** 

**App Service**: Yes, with Auto-Scale rules (Phase 5)
**Qdrant**: Manual scaling needed (Phase 8)

### Q: What's the maximum throughput?
**A:** 

Single B1 instance: ~20 concurrent requests
Add more instances via App Service plan.

---

## Support & Troubleshooting

### Q: Backend won't start (502 Bad Gateway)
**A:** 

Try:
```bash
# Check logs
az webapp log tail --name <app-name> --resource-group rag-prod

# Restart
az webapp restart --name <app-name> --resource-group rag-prod

# Redeploy
git push  # Triggers GitHub Actions
```

### Q: Qdrant connection timeout
**A:** 

Qdrant takes 5-10 minutes to initialize on first deploy.

Wait and try again. Check:
```bash
curl https://<your-app>/config
# Should show qdrant_host & qdrant_port
```

### Q: Models not responding (LLM errors)
**A:** 

Check API keys:
1. Groq free tier rate limit (120 req/day) — buy credits for more
2. Token limit exceeded — reduce retrieval_limit
3. API key invalid — regenerate from Groq console

### Q: UI shows "Failed to connect to backend"
**A:** 

Check:
1. Backend is running: `curl https://<your-app>/health`
2. CORS enabled (should be default)
3. Network connection
4. Browser console (F12) for detailed errors

### Q: React app won't load
**A:** 

Check:
1. Blob Storage static site hosting enabled
2. $web container created
3. CORS settings in App Service
4. Browser cache (Ctrl+Shift+Delete)

---

## Contributing & Roadmap

### Q: Can I contribute?
**A:** Yes! Fork the repo and submit a PR.

Good areas for contribution:
- Bug fixes
- Documentation improvements
- New features (under Phase 2-9)
- Test cases

### Q: What's planned for future releases?
**A:** 

**Phase 2:** RAG pipeline + ingestion
**Phase 3:** Infrastructure (Terraform)
**Phase 5:** CI/CD (GitHub Actions)
**Phase 6:** Deploy button
**Phase 7:** Full documentation
**Phase 8:** Testing & staging
**Phase 9:** Production release

Plus future: Auth, analytics, voice I/O, fine-tuning, etc.

### Q: How do I report a bug?
**A:** Open GitHub issue with:
1. Error message/screenshot
2. Steps to reproduce
3. Environment (local/Azure)
4. API keys obscured (for privacy)

---

## License & Legal

### Q: What license is this project?
**A:** MIT License (see LICENSE file).

You can use, modify, distribute freely. See LICENSE for terms.

### Q: Am I liable for AI hallucinations?
**A:** No, but you should:
1. Validate AI responses (don't trust blindly)
2. Add disclaimers in your product
3. Show source documents always
4. Consider liability insurance for high-risk use cases

### Q: Can I use this commercially?
**A:** Yes! MIT license allows commercial use.

---

Still have questions? 
- 💬 Open a GitHub Discussion
- 🐛 Open an Issue
- 📧 Email support (in README)

---

Last updated: April 2026
