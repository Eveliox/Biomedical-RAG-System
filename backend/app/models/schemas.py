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
    year_from: int | None = Field(default=None, ge=1900, le=2100)
    year_to: int | None = Field(default=None, ge=1900, le=2100)


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


# --- /api/library/stats ---

class JournalCount(BaseModel):
    journal: str
    count: int


class LibraryStatsResponse(BaseModel):
    paper_count: int
    chunk_count: int
    journal_count: int
    top_journals: list[JournalCount]
    year_min: int | None = None
    year_max: int | None = None


class YearCount(BaseModel):
    year: int
    count: int


class NameCount(BaseModel):
    name: str
    count: int


class LibraryInsightsResponse(BaseModel):
    papers_per_year: list[YearCount]
    top_genes: list[NameCount]
    top_journals: list[NameCount]
    top_authors: list[NameCount]
