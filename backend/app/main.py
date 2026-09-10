"""FastAPI application entry point.

Keep this file thin. Its job is to:
  1. Build the FastAPI instance,
  2. Wire up middleware (CORS so the Next.js frontend can call us),
  3. Mount routers from `app.api.*`.

Business logic belongs in `app/services/`, not here.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import papers as papers_api
from app.api import search as search_api

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = FastAPI(
    title="Biomedical Literature RAG",
    version="0.1.0",
    description="Search PubMed, ingest papers, and ask grounded questions.",
)

# Frontend runs on :3000 during dev; loosen this later if deploying.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    """Liveness probe. Cheap, no dependencies."""
    return {"status": "ok"}


app.include_router(search_api.router)
app.include_router(papers_api.router)
