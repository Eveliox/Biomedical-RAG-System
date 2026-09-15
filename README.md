# Biomedical Literature RAG System

A biomedical research assistant that lets you search **PubMed**, ingest scientific papers, and ask natural-language questions that are answered **only from the retrieved literature** — with numbered citations back to the source papers.

> Example: *"What genes have been associated with pancreatic cancer?"* → grounded answer citing the specific PubMed papers it used.

---

## Architecture

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

| Layer | Choice | Why |
|---|---|---|
| Backend | FastAPI + Pydantic | Typed, async, auto docs |
| Frontend | Next.js 14 + TypeScript + Tailwind | Fast to iterate, typed API client |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` | Local, free, ~5ms/sentence on CPU |
| LLM | Ollama (`llama3.2:3b`) | Local, free, no data leaves your machine |
| Vector store | Chroma (persistent) | Zero setup, swappable via `VectorStore` Protocol |
| Data source | NCBI PubMed / Entrez API | Free, official, exhaustive biomedical corpus |

## Directory layout

```
biomed/
├── backend/
│   ├── app/
│   │   ├── api/            # thin HTTP routes
│   │   ├── services/       # pubmed / chunking / ingestion / rag
│   │   ├── providers/      # embedding + llm implementations behind Protocols
│   │   ├── vectorstore/    # chroma today, pgvector tomorrow
│   │   ├── models/         # Paper + Pydantic schemas
│   │   ├── prompts/        # RAG prompt template
│   │   ├── config.py
│   │   └── main.py
│   ├── tests/              # pytest suite
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── app/                # Next.js App Router pages + layout
│   ├── components/         # Answer + SourcesList
│   ├── lib/api.ts          # typed backend client
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
└── README.md
```

---

## Quickstart (local, no Docker)

Prereqs:
- Python 3.12+
- Node 20+
- [Ollama](https://ollama.com/download) installed on the host

### 1. Ollama

```bash
ollama pull llama3.2:3b
ollama serve         # usually already running
```

### 2. Backend

```bash
cd backend
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # fill in NCBI_EMAIL (required by NCBI's usage policy)
uvicorn app.main:app --reload
# → http://localhost:8000/docs
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

---

## Quickstart (Docker)

```bash
# from repo root
docker compose up --build
# frontend: http://localhost:3000
# backend:  http://localhost:8000/docs
```

Ollama still needs to run on the **host** (see above) — the backend container reaches it via `host.docker.internal:11434`.

Persistent data (indexed chunks + embeddings) lives in the `chroma_data` volume. Wipe with `docker compose down -v`.

---

## Example workflow

1. Open http://localhost:3000
2. Search PubMed for `pancreatic cancer genetics`
3. Check the boxes on a handful of relevant papers → **Ingest N selected**
4. Ask: *"Which genes are most frequently associated with pancreatic cancer?"*
5. Read the answer — every `[N]` is a clickable pill that scrolls to the corresponding source below.
6. Click a source title to open the paper on PubMed.

---

## API

Interactive docs at `http://localhost:8000/docs`. Summary:

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Liveness probe |
| `GET` | `/api/search?q=…&limit=…` | Keyword search PubMed |
| `POST` | `/api/papers/ingest` `{ "pmids": [...] }` | Fetch → chunk → embed → store |
| `POST` | `/api/ask` `{ "question": "...", "top_k": 6 }` | RAG answer with citations |

### `/api/ask` response

```json
{
  "question": "...",
  "answer": "KRAS mutations are common in PDAC [1]. TP53 alterations occur too [2].",
  "sources": [
    { "pmid": "...", "title": "...", "journal": "...", "publication_date": "...",
      "pubmed_url": "...", "relevance_score": 0.83 },
    ...
  ]
}
```

The number in `[N]` corresponds to `sources[N-1]` — the frontend uses this to render clickable pill superscripts.

---

## Configuration

All backend settings come from environment variables (see [`backend/.env.example`](backend/.env.example)):

| Var | Default | Purpose |
|---|---|---|
| `NCBI_EMAIL` | `anonymous@example.com` | Required by NCBI's usage policy |
| `NCBI_API_KEY` | — | Optional; raises rate limit from 3 to 10 req/s |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | HuggingFace model id |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Where Ollama listens |
| `LLM_MODEL` | `llama3.2:3b` | Any model you've `ollama pull`ed |
| `CHUNK_SIZE` | `600` | Approx. tokens per chunk |
| `CHUNK_OVERLAP` | `120` | Overlap between consecutive chunks |
| `RAG_TOP_K` | `6` | Unique papers cited per answer |
| `CHROMA_PERSIST_DIR` | `./data/chroma_db` | Where the vector store writes to disk |

---

## Tests

```bash
cd backend
pytest -v
```

Covers chunking, PubMed XML parsing, prompt construction, and the RAG service's dedup + citation-numbering contract. External calls (PubMed, Ollama, sentence-transformers) are faked — the whole suite runs in under a second.

---

## Deploy

The repo ships two blueprints for the backend and a Vercel config for the frontend.

### Frontend → Vercel

1. Push this repo to GitHub (already done).
2. In Vercel: **New Project** → import `Biomedical-RAG-System` → **Root Directory** = `frontend`.
3. Set the env var `NEXT_PUBLIC_API_BASE_URL` to your deployed backend URL.
4. Deploy. Vercel picks up `frontend/vercel.json` automatically.

### Backend → Render (recommended) or Fly.io

**Render:** click **New Blueprint** in Render, point it at this repo — it reads [`render.yaml`](render.yaml) and provisions a web service + a 1GB persistent disk for Chroma. Fill in `NCBI_EMAIL` and (optional) `OLLAMA_BASE_URL` in the dashboard.

**Fly.io:** [`backend/fly.toml`](backend/fly.toml). Setup:

```bash
cd backend
flyctl launch --no-deploy --copy-config --name biomed-rag-backend
flyctl volumes create chroma_data --size 1 --region iad
flyctl secrets set NCBI_EMAIL=you@example.com
flyctl deploy
```

### Note on the LLM

The deployed backend deliberately doesn't include Ollama — hobby-tier instances can't run a 3B-parameter model comfortably. Search + ingest + `/api/library/*` work fully; `/api/ask` will error unless you either

- point `OLLAMA_BASE_URL` at a reachable Ollama host (a home box with a public tunnel via Cloudflare Tunnel / ngrok / Tailscale works), or
- add a hosted-LLM provider next to `providers/llm/ollama_provider.py` and switch it in via env var.

For portfolio demos, the read-only surface (search, ingest, browse citations, insights dashboard) is enough — reviewers can still see the whole pipeline in action.

## Safety

This tool summarizes biomedical literature and is **not** a substitute for professional medical advice. The RAG prompt is explicit: no personalized diagnosis, dosage, or treatment recommendations.

## License

MIT (to be added).
