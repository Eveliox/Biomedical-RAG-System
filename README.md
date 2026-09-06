# Biomedical Literature RAG System

A biomedical research assistant that lets you search **PubMed**, ingest scientific papers, and ask natural-language questions that are answered **only from the retrieved literature** — with numbered citations back to the source papers.

> Example: *"What genes have been associated with pancreatic cancer?"* → grounded answer citing the specific PubMed papers it used.

---

## Status

Work in progress. Building in phases.

- [ ] Phase 1 — MVP (search + ingest + ask + cite)
- [ ] Phase 2 — Reranking, hybrid search, filters
- [ ] Phase 3 — Gene entity recognition, dashboards

## Architecture (target)

```
User → Next.js Frontend → FastAPI Backend
                              │
             ┌────────────────┼──────────────────┐
             ▼                ▼                  ▼
        PubMed API       Chunk + Embed      Vector Store
                                                 │
                            LLM ← retrieved chunks
                             │
                     Grounded answer + [1][2][3] citations
```

## Tech stack

- **Backend:** Python 3.12, FastAPI, Pydantic, httpx
- **Frontend:** Next.js, TypeScript, Tailwind
- **Embeddings:** `sentence-transformers` (local, free)
- **LLM:** Ollama (local, free)
- **Vector store:** Chroma (swappable → pgvector)
- **Data source:** NCBI PubMed / Entrez API

## Local development

Setup instructions will be filled in as each layer is built.

## License

MIT (to be added).
