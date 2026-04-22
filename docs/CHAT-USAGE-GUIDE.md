# Chat Interface Usage Guide

> This guide covers how to use the RAG chat interface effectively, what each UI element does, and tips for getting better answers.

---

## Overview

The chat interface at `http://localhost:3000` lets you query your document knowledge base using natural language. Under the hood, every question goes through the full RAG pipeline: embed → retrieve → generate → cite.

---

## UI Layout

```
┌─────────────────────────────────────────────────────┐
│  Header: app name + connection status badge          │
├─────────────────────────────────────────────────────┤
│  RAG Intro Panel (shown on first load, dismissible) │
│  • What is RAG                                       │
│  • 4 collapsible pipeline steps                      │
│  • Pipeline visualisation                            │
│  • What more can be done                             │
│  • "Start chatting →" button                         │
├─────────────────────────────────────────────────────┤
│  Messages area                                       │
│  ┌────────────────────────────────────────────┐     │
│  │  [User message] (right-aligned, blue bg)   │     │
│  │  [Assistant reply] (left-aligned, grey bg) │     │
│  │    └─ Sources: doc.md — confidence 87.3%  │     │
│  │    └─ 1 234 ms · 312 tokens               │     │
│  └────────────────────────────────────────────┘     │
├─────────────────────────────────────────────────────┤
│  Input: text field + Send button                     │
├─────────────────────────────────────────────────────┤
│  Settings panel                                      │
│  • Top-K Results (number input, 1–20)                │
│  • Current model config (LLM + embeddings)           │
│  • Re-ingest Documents button                        │
└─────────────────────────────────────────────────────┘
```

---

## Asking Questions

**Good questions to try on the built-in sample docs:**

| Question | What it demonstrates |
|---|---|
| What is RAG? | Core concept from `rag_guide.md` |
| What are the Azure Free Tier limits? | Factual retrieval from `azure_fundamentals.md` |
| How do I set up Ollama on a new machine? | Ops runbook recall from `ollama_gemma4_ops_runbook.md` |
| What is gradient descent? | ML basics from `machine_learning_basics.md` |
| Compare supervised and unsupervised learning | Multi-chunk synthesis |

**Tips for better answers:**

- **Be specific** — "What is COSINE similarity in Qdrant?" gets a sharper answer than "how does search work?"
- **Follow-up questions** — the system has no memory between turns, so repeat context if needed: "In the context of RAG, what is chunking?"
- **Raise Top-K** — increase the Top-K slider to 10–15 when asking broad synthesis questions that span multiple documents
- **Lower Top-K** — set it to 1–3 for tight factual lookups where you want the single best source

---

## Understanding the Response

Each assistant message includes:

### Answer text
The LLM-generated answer, grounded in the retrieved chunks. If no relevant document was found, the model will typically say so rather than guess.

### Sources section
```
Sources:
• azure_fundamentals.md — confidence: 91.2%
• rag_guide.md — confidence: 74.8%
```
- **Filename**: which document the chunk came from
- **Confidence**: cosine similarity score (0–100%). Higher = more semantically similar to your query. Scores above 70% are usually highly relevant.

### Performance metadata
```
1 234 ms  ·  312 tokens
```
- **ms**: total round-trip time (embed + search + LLM call)
- **tokens**: tokens consumed by the LLM generation step (used for cost tracking)

---

## RAG Intro Panel

The intro panel appears on first load and explains:

1. **Document Ingestion** — how your docs are split, embedded, and stored
2. **Semantic Search** — how the query is matched against vectors
3. **Context + Generation** — how the LLM uses retrieved chunks
4. **Source Attribution** — how confidence scores are calculated

Click any step header to expand its detailed explanation. Dismiss the panel with ✕ or "Start chatting →". You can re-open it by clicking **Show RAG explanation** in the empty messages state.

---

## Settings Panel

### Top-K Results
Controls how many document chunks are retrieved and injected into the LLM context.

| Value | Use case |
|---|---|
| 1–3 | Quick factual lookup, speed-focused |
| 5 (default) | Balanced — good for most questions |
| 10–15 | Broad synthesis, multi-document summaries |
| 20 | Maximum recall — may include noise |

Higher Top-K = more context = slightly slower + more tokens used.

### Model Configuration
Shows what LLM and embedding model the backend is currently using. Configured via `OLLAMA_MODEL` / `LITELLM_LLM_MODEL` in `.env`.

### Re-ingest Documents
Triggers the backend to re-read all `.md` files from `docs/example_docs/`, re-chunk them, re-embed, and upsert into Qdrant. Use this after:
- Adding new documents to `docs/example_docs/`
- Changing `CHUNK_SIZE` or `CHUNK_OVERLAP` in `.env`
- Changing the embedding model (vector size change requires volume reset)

---

## Adding Your Own Documents

1. Drop `.md` files into `docs/example_docs/`
2. Click **Re-ingest Documents** in the settings panel (or `POST /ingest`)
3. Wait for the success message
4. Start asking questions about your new content

Supported format: **Markdown** (`.md`). HTML tags and code fences are stripped during ingestion. Plain text is chunked into ~512-word segments with 50-word overlap.

---

## API Usage (Programmatic)

The same query pipeline is available via REST:

```bash
# Ask a question
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?", "top_k": 5}'

# Trigger ingestion
curl -X POST http://localhost:8000/ingest

# Check system health
curl http://localhost:8000/health

# View current config
curl http://localhost:8000/config
```

Full Swagger docs: `http://localhost:8000/docs`

---

## Troubleshooting Chat Issues

| Symptom | Likely cause | Fix |
|---|---|---|
| "Failed to connect to backend" | Backend container not running | `docker-compose logs backend` |
| Empty answer / "no documents found" | Ingestion not run yet | Click Re-ingest or `POST /ingest` |
| Slow responses (>10s) | Ollama model still loading or cold start | Wait 30s and retry |
| Low confidence scores (<40%) | Query doesn't match document content | Try rephrasing or add relevant docs |
| "Qdrant invalid key" in logs | Key mismatch between backend and Qdrant | `docker-compose down -v && docker-compose up` |
| Answer ignores context | `top_k=1` and chunk is partially relevant | Raise Top-K to 5–10 |
