"""Request/response schemas for the HTTP API.

These are the shapes the frontend will see. Keep them stable —
if we change them, the frontend breaks.

Rule of thumb:
  - Internal models live in `models/paper.py`, `models/chunk.py`, etc.
  - API-facing schemas live here.
  - We *can* reuse an internal model as a response type if it's already
    the right shape (like `Paper`), but the *request* shapes are always new.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.paper import Paper


# --- /api/search ---

class SearchResponse(BaseModel):
    query: str
    papers: list[Paper]


# --- /api/papers/ingest ---

class IngestRequest(BaseModel):
    pmids: list[str] = Field(..., min_length=1, max_length=200)


class IngestResponse(BaseModel):
    ingested: list[str]         # PMIDs newly added
    skipped: list[str]          # PMIDs already in the store
    failed: list[str]           # PMIDs that couldn't be fetched/parsed
    chunk_count: int            # total chunks written this call


# --- /api/ask ---

class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)
    top_k: int = Field(default=6, ge=1, le=20)


class Source(BaseModel):
    pmid: str
    title: str
    journal: str = ""
    publication_date: str = ""
    pubmed_url: str
    relevance_score: float | None = None


class AskResponse(BaseModel):
    question: str
    answer: str
    sources: list[Source]
